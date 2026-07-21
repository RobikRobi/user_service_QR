from typing import Any


def success_response(message: str, data: Any | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data

    return response


def error_response(
    status_code: int,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": False,
        "error": {
            "code": status_code,
            "message": message,
        },
    }
    if details is not None:
        response["error"]["details"] = details

    return response
