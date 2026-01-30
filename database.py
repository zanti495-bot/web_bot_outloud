import os
import logging
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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