from passlib.context import CryptContext
from jose import jwt, JWTError
import os
from datetime import timedelta, datetime, timezone

pwd_context = CryptContext(
   schemes=["bcrypt"],
   deprecated="auto"
)

ACCESS_SECRET = os.getenv("ACCESS_SECRET", "dev-access-secret")
REFRESH_SECRET = os.getenv("REFRESH_SECRET", "dev-refresh-secret")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def hash_password(password: str) -> str:
   return pwd_context.hash(password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
   # hash/verify 모두 passlib(pwd_context)로 통일 - 원본은 hash만 passlib, verify는 bcrypt 직접 호출이라 방식이 섞여 있었음
   return pwd_context.verify(raw_password, hashed_password)


def _create_token(member_id: str, role: str, secret: str, expires_delta: timedelta) -> str:
   payload = {
      "sub": member_id,
      "role": role,
      "exp": datetime.now(timezone.utc) + expires_delta,
   }
   # 원본 코드는 여기서 { jwt.encode(...) } 로 set을 리턴하는 버그가 있었음 -> 문자열 그대로 리턴하도록 수정
   return jwt.encode(payload, secret, algorithm="HS256")


def create_access_token(member_id: str, role: str) -> str:
   return _create_token(
      member_id, role, ACCESS_SECRET, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
   )


def create_refresh_token(member_id: str, role: str) -> str:
   return _create_token(
      member_id, role, REFRESH_SECRET, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
   )


def decode_token(token: str, secret: str) -> dict | None:
   try:
      return jwt.decode(token, secret, algorithms=["HS256"])
   except JWTError:
      return None