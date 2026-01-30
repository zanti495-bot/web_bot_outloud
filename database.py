import asyncio
import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import asyncpg

def get_dsn():
    raw_dsn = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost:5432/db')
    
    parsed = urlparse(raw_dsn)
    query_params = parse_qs(parsed.query)
    
    # Добавляем/перезаписываем ssl-параметры
    query_params['sslmode'] = ['verify-full']
    query_params['sslrootcert'] = ['/app/ca.crt']
    
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    
    return urlunparse(new_parsed)

async def init_db():
    dsn = get_dsn()
    conn = await asyncpg.connect(dsn)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    await conn.close()

class User:
    @staticmethod
    async def create(telegram_id: int):
        dsn = get_dsn()
        conn = await asyncpg.connect(dsn)
        try:
            await conn.execute('''
                INSERT INTO users (telegram_id) VALUES ($1)
                ON CONFLICT (telegram_id) DO NOTHING
            ''', telegram_id)
        finally:
            await conn.close()