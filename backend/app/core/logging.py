import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class RequestIdFormatter(logging.Formatter):
    """
    Custom formatter that safely defaults request_id to 'system'
    when not present on the LogRecord (e.g. from background tasks or uvicorn).
    """
    def format(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "system"
        return super().format(record)

# Configure handler with safe RequestIdFormatter
handler = logging.StreamHandler()
handler.setFormatter(
    RequestIdFormatter("%(asctime)s [%(levelname)s] [req_id=%(request_id)s] %(name)s: %(message)s")
)

# Apply to root logger and wayline logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [handler]

logger = logging.getLogger("wayline")
logger.setLevel(logging.INFO)

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = req_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
