from fastapi import Depends, HTTPException

from ..models.user import User
from .dependencies import get_current_user


class RequireRole:
    def __init__(self, *roles: str) -> None:
        self.roles = set(roles)

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        user_roles = {role.name for role in current_user.roles}
        if not self.roles.intersection(user_roles):
            raise HTTPException(status_code=403, detail={"error_code": "role_not_allowed", "message": "Insufficient role"})
        return current_user


def require_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail={"error_code": "inactive_user", "message": "User is inactive"})
    return current_user
