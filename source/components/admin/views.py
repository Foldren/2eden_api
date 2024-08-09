from typing import Dict, Any, Optional, List, Sequence, Union, Type
from starlette.requests import Request
from starlette_admin import BaseModelView
from tortoise import Model


class TortoiseModelView(BaseModelView):
    def __init__(self, obj: Type[Model]):
        super().__init__()
        self.obj = obj

    async def find_all(self, request: Request, skip: int = 0, limit: int = 100,
                       where: Union[Dict[str, Any], str, None] = None,
                       order_by: Optional[List[str]] = None) -> Sequence[Any]:
        if (where is not None) and isinstance(where, dict):
            query_objs = self.obj.filter(**where).all()
        else:
            query_objs = self.obj.all()

        if order_by is not None:
            """Multiple sort"""
            ord_vals = []
            for item in reversed(order_by):
                key, dirc = item.split(maxsplit=1)
                ord_val = "-" if dirc == "desc" else "" + key
                ord_vals.append(ord_val)
            query_objs = query_objs.order_by(*ord_vals)

        objs = await query_objs

        if limit > 0:
            return objs[skip:skip + limit]

        return objs[skip:]

    async def count(self, request: Request, where: Union[Dict[str, Any], str, None] = None) -> int:
        if where is not None:
            if isinstance(where, dict):
                query_objs = self.obj.filter(**where)
            else:
                query_objs = self.obj.filter(pk=where)
            return await query_objs.count()
        return await self.obj.all().count()

    async def find_by_pk(self, request: Request, pk: int) -> Any:
        pk_obj = await self.obj.filter(pk=int(pk)).first()
        if pk_obj:
            return pk_obj
        return None

    async def find_by_pks(self, request: Request, pks: List[int]) -> Sequence[Any]:
        return await self.obj.filter(pk__in=pks).all()

    async def create(self, request: Request, data: Dict) -> Any:
        return await self.obj.create(**data)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        await self.obj.filter(pk=pk).update(**data)
        return await self.obj.filter(pk=pk).first()

    async def delete(self, request: Request, pks: List[int]) -> Optional[int]:
        objs = await self.obj.filter(pk__in=pks).all()
        await self.obj.filter(pk__in=pks).delete()
        return objs.__len__()
