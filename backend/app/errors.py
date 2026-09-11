"""Unified error types and FastAPI exception handlers."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("croprisk")


class AppError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        status_code: int = 500,
        fields: dict[str, str] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.fields = fields


class ValidationError(AppError):
    def __init__(self, message: str, fields: dict[str, str] | None = None):
        super().__init__(
            message=message,
            code="validation_error",
            status_code=422,
            fields=fields,
        )


class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Invalid email or password."):
        super().__init__(
            message=message,
            code="invalid_credentials",
            status_code=401,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required."):
        super().__init__(
            message=message,
            code="unauthorized",
            status_code=401,
        )


class EmailTakenError(AppError):
    def __init__(self, message: str = "An account with this email already exists."):
        super().__init__(
            message=message,
            code="email_taken",
            status_code=409,
        )


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(
            message=message,
            code="not_found",
            status_code=404,
        )


class UpstreamUnavailableError(AppError):
    def __init__(self, message: str = "Upstream weather or AI service is unavailable."):
        super().__init__(
            message=message,
            code="upstream_unavailable",
            status_code=503,
        )


def _format_error_response(code: str, message: str, fields: dict[str, str] | None = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if fields is not None:
        err["fields"] = fields
    return {"error": err}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        content = _format_error_response(exc.code, exc.message, exc.fields)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        fields: dict[str, str] = {}
        first_message = "Validation error."
        for err in exc.errors():
            loc = err.get("loc", [])
            field_name = str(loc[-1]) if loc else "non_field_error"
            msg = err.get("msg", "Invalid value.")
            # Clean pydantic message prefix like "Value error, "
            msg = msg.removeprefix("Value error, ")
            fields[field_name] = msg
            if first_message == "Validation error.":
                first_message = msg

        content = _format_error_response("validation_error", first_message, fields)
        return JSONResponse(status_code=422, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            401: "unauthorized",
            403: "unauthorized",
            404: "not_found",
            409: "email_taken",
            422: "validation_error",
            503: "upstream_unavailable",
        }
        code = code_map.get(exc.status_code, "internal_error")
        message = exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred."
        content = _format_error_response(code, message)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", exc)
        content = _format_error_response("internal_error", "An unexpected internal server error occurred.")
        return JSONResponse(status_code=500, content=content)
