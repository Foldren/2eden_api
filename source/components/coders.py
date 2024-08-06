from typing import Any
from fastapi.encoders import jsonable_encoder
from fastapi_cache import Coder
from ujson import dumps, loads


class UJsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return dumps(obj=value, default=jsonable_encoder).encode()

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return loads(value)
