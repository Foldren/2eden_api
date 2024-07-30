from typing import Any
from fastapi.responses import UJSONResponse
from fastapi import Response


class CustomJSONResponse(UJSONResponse):
    def __init__(self, data: dict[str, Any] | None = None, message: str = "", status_code: int = 200) -> None:
        """
        Класс над ujson, либо в data указываем данные +- message, либо в message - сообщение.
        :param data: данные респонса
        :param message: сообщение
        :param status_code: статус код, starlette.status
        """
        response = {}

        if data:
            response['data'] = data

        if message:
            status = 'Success' if status_code in [200, 201, 202, 302] else 'Error'
            response['message'] = {'status': status, 'text': message}

        UJSONResponse.__init__(self, content=response, status_code=status_code)
