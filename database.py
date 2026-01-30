import asyncio
import os
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import asyncpg

logger = logging.getLogger(__name__)

_pool = None


def get_dsn() -> str:
    raw_dsn = os.environ.get('DATABASE_URL')
    if not raw_dsn:
        raise ValueError("DATABASE_URL не установлен в переменных окружения")

    parsed = urlparse(raw_dsn)
    query = parse_qs(parsed.query)

    query['sslmode'] = ['verify-full']
    query['sslrootcert'] = ['/app/ca.crt']

    new_query = urlencode(query, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


async def init_db():
    global _pool
    if _pool is not None:
        return

    dsn = get_dsn()
    try:
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=10,
            timeout=30,
            command_timeout=60,
        )
        logger.info("Пул соединений с PostgreSQL успешно создан")

        async with _pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id          SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            logger.info("Таблица users проверена / создана")
    except Exception as e:
        logger.exception("Ошибка при инициализации базы данных")
        raise


class User:
    @staticmethod
    async def create(telegram_id: int) -> bool:
        if _pool is None:
            raise RuntimeError("База не инициализирована. Вызовите init_db()")

        async with _pool.acquire() as conn:
            try:
                result = await conn.execute(
                    '''
                    INSERT INTO users (telegram_id) 
                    VALUES ($1) 
                    ON CONFLICT (telegram_id) DO NOTHING
                    ''',
                    telegram_id
                )
                inserted = result == "INSERT 0 1"
                if inserted:
                    logger.info(f"Создан новый пользователь: {telegram_id}")
                return inserted
            except Exception as e:
                logger.error(f"Ошибка при добавлении пользователя {telegram_id}: {e}")
                raise