import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [req_id=%(request_id)s] %(name)s: %(message)s",
)

logger = logging.getLogger("wayline")

class RequestIdFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.request_id = "system"

    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = getattr(self, "request_id", "system")
        return True

request_filter = RequestIdFilter()
logger.addFilter(request_filter)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = req_id
        request_filter.request_id = req_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

