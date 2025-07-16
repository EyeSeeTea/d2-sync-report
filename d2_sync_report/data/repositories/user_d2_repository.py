from typing import List, Optional

from pydantic import BaseModel

from d2_sync_report.data import dhis2_api
from d2_sync_report.domain.entities.instance import Instance
from d2_sync_report.domain.entities.user import User
from d2_sync_report.domain.repositories.user_repository import UserRepository


UserResponse = User


class UsersResponse(BaseModel):
    users: List[UserResponse]


class UserD2Repository(UserRepository):
    def __init__(self, instance: Instance):
        self.instance = instance

    def get_list_by_group(
        self, name: Optional[str] = None, code: Optional[str] = None
    ) -> List[User]:
        filters = [
            *([("filter", f"userGroups.code:eq:{code}")] if code else []),
            *([("filter", f"userGroups.name:eq:{name}")] if name else []),
        ]

        response = dhis2_api.request(
            instance=self.instance,
            method="GET",
            path="/api/users",
            params=[("fields", "id,email"), *filters],
            response_model=UsersResponse,
        )

        return response.users
