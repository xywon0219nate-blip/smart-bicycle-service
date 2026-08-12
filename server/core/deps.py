from fastapi import Header, HTTPException, Depends, status
from sqlalchemy.orm import Session

from core.security import decode_token, ACCESS_SECRET
from database.connection import get_db
from models.member import UserModel


def get_current_user(
   authorization: str = Header(None),
   db: Session = Depends(get_db),
) -> UserModel:
   if not authorization or not authorization.startswith("Bearer "):
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="인증 정보가 없습니다.",
      )

   token = authorization.split(" ")[1]
   payload = decode_token(token, ACCESS_SECRET)
   if payload is None:
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="토큰이 유효하지 않거나 만료되었습니다.",
      )

   userModel = db.query(UserModel).filter(UserModel.id == payload["sub"]).first()
   if userModel is None:
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="유효하지 않은 사용자입니다.",
      )

   return userModel