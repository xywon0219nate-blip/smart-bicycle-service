from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import List, Optional
from datetime import datetime


class LoginItem(BaseModel):
   email: EmailStr
   password: str

   model_config = ConfigDict(
      json_schema_extra={
         "examples": [
            {"email": "test1@example.com", "password": "12341234"}
         ]
      }
   )


class SignupItem(BaseModel):
   email: EmailStr
   password: str
   passwordConfirm: str
   name: str
   ridingStyles: Optional[List[str]] = []

   @field_validator("password")
   @classmethod
   def password_min_length(cls, v):
      if len(v) < 8:
         raise ValueError("비밀번호는 8자 이상이어야 합니다.")
      return v

   @field_validator("passwordConfirm")
   @classmethod
   def password_match(cls, v, info):
      if "password" in info.data and v != info.data["password"]:
         raise ValueError("비밀번호가 일치하지 않습니다.")
      return v

   model_config = ConfigDict(
      json_schema_extra={
         "examples": [
            {
               "email": "test1@example.com",
               "password": "pw123456",
               "passwordConfirm": "pw123456",
               "name": "김민준",
               "ridingStyles": ["로드", "MTB"],
            }
         ]
      }
   )


class Member(BaseModel):
   id: int
   email: str
   name: str
   role: str
   created_at: datetime