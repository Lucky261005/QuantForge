"""Domain exceptions raised by the service layer, translated to HTTP responses
by a single exception handler in app.main (RFC 7807-style problem details)."""


class QuantForgeError(Exception):
    status_code: int = 400
    title: str = "Bad Request"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(QuantForgeError):
    status_code = 404
    title = "Not Found"


class AlreadyExistsError(QuantForgeError):
    status_code = 409
    title = "Conflict"


class InvalidCredentialsError(QuantForgeError):
    status_code = 401
    title = "Unauthorized"


class TokenError(QuantForgeError):
    status_code = 401
    title = "Invalid Token"


class PermissionDeniedError(QuantForgeError):
    status_code = 403
    title = "Forbidden"


class ValidationFailedError(QuantForgeError):
    status_code = 422
    title = "Validation Failed"


class ExternalServiceError(QuantForgeError):
    status_code = 502
    title = "External Service Error"
