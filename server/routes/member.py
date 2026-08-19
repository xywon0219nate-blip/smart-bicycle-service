from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from core.security import hash_password, verify_password, create_access_token, create_refresh_token
from schemas.member import LoginItem, SignupItem
from models.member import UserModel
from database.connection import get_db

member_router = APIRouter()

REFRESH_COOKIE_NAME = "refreshToken"
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7일


def _to_user_response(userModel: UserModel) -> dict:
   return {
      "id": str(userModel.id),
      "nickname": userModel.nickname,
      "handle": "@" + userModel.email.split("@")[0],
      "email": userModel.email,
   }


# 로그인
@member_router.post("/login")
async def login(loginItem: LoginItem,
                  response: Response, 
                     db: Session = Depends(get_db)) -> dict:
   userModel = db.query(UserModel).filter(UserModel.email == loginItem.email).first()


   if userModel is None:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail="가입되지 않은 이메일입니다.",
      )

   if not verify_password(loginItem.password, userModel.pwd):
      raise HTTPException(
         status_code=status.HTTP_401_UNAUTHORIZED,
         detail="비밀번호가 올바르지 않습니다.",
      )

   access_token = create_access_token(str(userModel.id), userModel.role)
   refresh_token = create_refresh_token(str(userModel.id), userModel.role)

   response.set_cookie(
      key=REFRESH_COOKIE_NAME,
      value=refresh_token,
      httponly=True,
      secure=False,  # 배포(HTTPS) 시 True로 변경
      max_age=REFRESH_COOKIE_MAX_AGE,
   )

   return {
      "accessToken": access_token,
      "user": _to_user_response(userModel),
   }


# 로그아웃
@member_router.post("/logout")
async def logout(response: Response) -> dict:
   response.delete_cookie(REFRESH_COOKIE_NAME)
   return {"isLogout": True}


# 이메일 중복 체크
@member_router.get("/emailCheck/{email}")
async def email_check(email: str, 
                        db: Session = Depends(get_db)) -> dict:
   userModel = db.query(UserModel).filter(UserModel.email == email).first()
   return {"isFind": userModel is not None}


# 회원가입
@member_router.post("/signup")
async def signup(signupItem: SignupItem, 
                  response: Response, 
                  db: Session = Depends(get_db)) -> dict:
   existing = db.query(UserModel).filter(UserModel.email == signupItem.email).first()
   if existing:
      raise HTTPException(status_code=400, detail="이미 가입된 이메일입니다.")

   userModel = UserModel(
      email=signupItem.email,
      pwd=hash_password(signupItem.password),
      nickname=signupItem.nickname,
      riding_styles=",".join(signupItem.ridingStyles or []),
      agree_marketing=signupItem.agreeMarketing,
   )
   db.add(userModel)
   db.commit()
   db.refresh(userModel)

   access_token = create_access_token(str(userModel.id), userModel.role)
   refresh_token = create_refresh_token(str(userModel.id), userModel.role)

   response.set_cookie(
      key=REFRESH_COOKIE_NAME,
      value=refresh_token,
      httponly=True,
      secure=False,
      max_age=REFRESH_COOKIE_MAX_AGE,
   )

   return {
      "accessToken": access_token,
      "user": _to_user_response(userModel),
   }