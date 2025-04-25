import redis
import json
import redis.exceptions
from src.config.settings import settings
from loguru import logger
from langchain_tavily import TavilySearch

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
    
# Configure Tavily tool
class CachedTavilyTool:
    "Base class to invoke tavily calls"
    def __init__(
        self,
        search_depth: str = "basic",
        max_results: int = 5,
    ):
        self.search_depth = search_depth
        self.max_results = max_results
        self.tavily_tool = TavilySearch(
            max_results=max_results,
            topic="general",
            search_depth=search_depth,
        )
    
    def _invoke(self, query: str):
        logger.info("Cached Tavily Tool invoked with user query")
        cache_key = f"tavily:{self.search_depth}:{self.max_results}:{query}"

        logger.debug(f"Cache Key:{cache_key}")
        # First search in Redis
        if redis_client:
            try:
                cached_result_json = redis_client.get(cache_key)
                if cached_result_json:
                    logger.success("✅ Cache HIT! returning cached response.")
                    return {
                        "status": "success",
                        "query": query,
                        "tavily_response": cached_result_json,
                        "response_type": "cached"
                    }
                
            except redis.exceptions.RedisError as e:
                logger.info(f"⚠️ Redis GET Error: {e}. Proceeding without cache.")
            except Exception as e: # Catch other potential errors
                logger.info(f"⚠️ Unexpected error during Redis GET: {e}. Proceeding without cache.")
            
        # If cache miss call Tavily 
        logger.info("🔍 Cache MISS or Redis unavailable. Calling Tavily API...")
        try:
            # Use tavily 
            tavily_response = self.tavily_tool.invoke({"query": query})
            result_json = json.dumps(tavily_response)
            logger.debug("Tavily response parsed to JSON")
        except Exception as e:
            logger.error(f"❌ Error calling Tavily API: {str(e)}")
            return {
                "status": "error",
                "query": query,
                "tavily_response": None,
                "details": str(e)
            }
        
        # Store the cache key and value pair in redis 
        if redis_client and result_json:
            try:
                redis_client.setex(name=cache_key, time=settings.TTL_TIME, value=result_json)
                logger.info(f"💾 Result stored in Redis cache (TTL: {settings.TTL_TIME}s).")
            except redis.exceptions.RedisError as e:
                logger.error(f"Redis SETEX error: {str(e)}. Results not cached.")
            except Exception as e:
                logger.error(f"Unexpected error during Redis SETEX: {str(e)}. Results not cached.")

        return {
            "status": "success",
            "query": query, 
            "tavily_response": result_json,
            "response_type": "cached"
        }

# tool = CachedTavilyTool()
# tool_response = tool._invoke(query="Who won the last football worldcup ?")
# print(tool_response)


