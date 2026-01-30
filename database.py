import asyncio
import os
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_pool = None

def get_dsn() -> str:
    raw_dsn = os.environ.get('DATABASE_URL')
    if not raw_dsn:
        raise ValueError("DATABASE_URL не установлен!")

    cert_path = '/app/ca.crt'
    
    if os.path.exists(cert_path):
        try:
            size = os.path.getsize(cert_path)
            logger.info(f"ca.crt найден, размер: {size} байт")
            with open(cert_path, 'r') as f:
                first = f.readline().strip()
                logger.info(f"Первая строка сертификата: {first}")
        except Exception as e:
            logger.error(f"Ошибка чтения ca.crt: {e}")
    else:
        logger.error("Файл ca.crt НЕ НАЙДЕН в /app/ !")

    parsed = urlparse(raw_dsn)
    query = parse_qs(parsed.query)

    query['sslmode'] = ['verify-ca']
    query['sslrootcert'] = [cert_path]

    new_query = urlencode(query, doseq=True)
    new_dsn = urlunparse(parsed._replace(query=new_query))

    logger.info(f"Сформированный DSN: {new_dsn}")
    return new_dsn

async def init_db():
    global _pool
    if _pool is not None:
        logger.info("Пул уже существует")
        return

    dsn = get_dsn()
    try:
        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=10,
            timeout=45,
            command_timeout=60,
        )
        logger.info("Пул соединений успешно создан")

        async with _pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            logger.info("Таблица users проверена/создана")
    except Exception as e:
        logger.exception("Критическая ошибка при создании пула или таблицы")
        raise

class User:
    @staticmethod
    async def create(telegram_id: int) -> bool:
        if _pool is None:
            raise RuntimeError("Пул соединений не инициализирован")

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
                    logger.info(f"Добавлен новый пользователь: {telegram_id}")
                return inserted
            except Exception as e:
                logger.error(f"Ошибка при добавлении пользователя {telegram_id}: {e}")
                return False