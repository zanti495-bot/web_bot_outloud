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
        size = os.path.getsize(cert_path)
        logger.info(f"ca.crt найден! Размер: {size} байт")
        try:
            with open(cert_path, 'r') as f:
                first_line = f.readline().strip()
                logger.info(f"Начало сертификата: {first_line}")
        except Exception as e:
            logger.warning(f"Не удалось прочитать ca.crt: {e}")
    else:
        logger.error("ca.crt НЕ НАЙДЕН!")

    parsed = urlparse(raw_dsn)
    query_params = parse_qs(parsed.query)

    query_params['sslmode'] = ['verify-ca']
    query_params['sslrootcert'] = [cert_path]

    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)

    dsn = urlunparse(new_parsed)
    logger.info("DSN сформирован (sslmode=verify-ca)")
    return dsn

async def init_db():
    global _pool
    if _pool is not None:
        logger.info("Пул уже создан")
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
        logger.info("Пул соединений создан успешно")

        async with _pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Таблица users готова")
    except Exception as e:
        logger.exception("Ошибка init_db")
        raise

class User:
    @staticmethod
    async def create(telegram_id: int) -> bool:
        if _pool is None:
            raise RuntimeError("Пул не инициализирован")

        async with _pool.acquire() as conn:
            try:
                result = await conn.execute('''
                    INSERT INTO users (telegram_id) VALUES ($1)
                    ON CONFLICT (telegram_id) DO NOTHING
                ''', telegram_id)
                inserted = result == "INSERT 0 1"
                if inserted:
                    logger.info(f"Новый пользователь: {telegram_id}")
                return inserted
            except Exception as e:
                logger.error(f"Ошибка создания пользователя: {e}")
                raise