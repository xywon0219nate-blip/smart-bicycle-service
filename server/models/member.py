from sqlalchemy import String, Enum, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base
from datetime import datetime, timezone


class UserModel(Base):
   __tablename__ = "user"

   id: Mapped[int] = mapped_column(
      Integer,
      primary_key=True,
      autoincrement=True,
   )
   email: Mapped[str] = mapped_column(
      String(255),
      unique=True,
      nullable=False,
   )
   pwd: Mapped[str] = mapped_column(
      String(255),
      nullable=False,
   )
   name: Mapped[str] = mapped_column(
      String(100),
      nullable=False,
   )
   riding_styles: Mapped[str] = mapped_column(
      String(255),
      nullable=True,
   )
   role: Mapped[str] = mapped_column(
      Enum("USER", "ADMIN", name="member_role"),
      nullable=False,
      default="USER",
   )
   created_at: Mapped[datetime] = mapped_column(
      DateTime, default=lambda: datetime.now(timezone.utc)
   )