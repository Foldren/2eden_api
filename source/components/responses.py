from typing import Any
from fastapi.responses import UJSONResponse


class CustomJSONResponse(UJSONResponse):
    def __init__(self, data: dict[str, Any] | None = None, error: str = "",
                 message: str = "", status_code: int = 200):
        response = {}

        if data:
            response['data'] = data

        if error:
            response['error'] = error

        if message:
            response['message'] = message

        UJSONResponse.__init__(self, content=response, status_code=status_code)
