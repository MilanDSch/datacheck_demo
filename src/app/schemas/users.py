from pydantic import BaseModel


class MeOut(BaseModel):
    oid: str
    name: str
    roles: list[str]
