from app.domain.models.role import Role
from app.domain.models.user import User
from app.domain.models.user_role import UserRole


class RBACService:

    @staticmethod
    def assign_role(
        user: User,
        role: Role,
    ):

        user.roles.append(
            UserRole(
                role=role
            )
        )


        