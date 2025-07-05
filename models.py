from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


def serialize_roles(roles: str) -> list[int]:
    """Convert a comma-separated string of role IDs into a list of integers."""
    return [int(role_id) for role_id in roles.split(",") if role_id.isdigit()]


def deserialize_roles(roles: list[int]) -> str:
    """Convert a list of role IDs into a comma-separated string."""
    return ",".join(str(role_id) for role_id in roles)


class Employee(Base):
    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(primary_key=True)
    firstname: Mapped[str] = mapped_column(String, nullable=False)
    lastname: Mapped[str] = mapped_column(String, nullable=False)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False) # hashed password
    refresh_token: Mapped[str] = mapped_column(String, nullable=True)

    # comma-separated string for roles, e.g., "2001,1984,5150"
    roles: Mapped[str] = mapped_column(String, nullable=False, default="2001")
