from fastapi import APIRouter, Depends

from ..core.auth import User, get_current_user
from ..schemas.users import MeOut

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(oid=user.oid, name=user.name, roles=list(user.roles))
