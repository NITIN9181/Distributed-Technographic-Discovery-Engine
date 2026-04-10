"""
Health check endpoint for container orchestration.
"""
from aiohttp import web
import redis

class HealthServer:
    def __init__(self, redis_url: str, port: int = 8080):
        self.redis_url = redis_url
        self.port = port
        self.processed_count = 0
        self.last_processed_at = None
    
    async def health_handler(self, request):
        """Health check endpoint."""
        try:
            r = redis.from_url(self.redis_url)
            r.ping()
            return web.json_response({
                "status": "healthy",
                "processed_count": self.processed_count,
                "last_processed_at": self.last_processed_at
            })
        except Exception as e:
            return web.json_response(
                {"status": "unhealthy", "error": str(e)},
                status=503
            )
    
    async def run(self):
        app = web.Application()
        app.router.add_get('/health', self.health_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
