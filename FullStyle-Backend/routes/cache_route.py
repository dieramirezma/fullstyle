# Import resources
from services.cache_service import CacheStats, CacheClear, CacheTest

# Add resources to the API
def add_resources(api):
    api.add_resource(CacheTest, "/api/cache/test")  # Sin JWT para testing
    api.add_resource(CacheStats, "/api/cache/stats")
    api.add_resource(CacheClear, "/api/cache/clear")
