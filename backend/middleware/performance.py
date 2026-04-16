"""Performance Monitoring Middleware
Tracks request/response times and logs slow endpoints
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_logger

logger = get_logger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor request performance and log slow requests"""

    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration:.2f}s",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "status_code": response.status_code,
                },
            )

        # Add performance headers
        response.headers["X-Process-Time"] = str(duration)

        return response
