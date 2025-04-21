import redis
import redis.exceptions
from tavily import  TavilyClient
from src.config.settings import settings
from loguru import logger

# Setup redis connection 
redis_client = None
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )
    redis_client.ping()
    logger.info('Redis Connection Established')
except redis.exceptions.ConnectionError as e:
    logger.error(f"Error connecting to redis: {str(e)}")
    redis_client = None
except Exception as e:
    logger.error(f"Unexpected Error connecting to redis: {str(e)}")
    redis_client = None
    