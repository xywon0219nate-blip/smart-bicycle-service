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
   nickname: str
   email: EmailStr
   password: str
   passwordConfirm: str
   ridingStyles: Optional[List[str]] = []
   agreeRequired: bool = False
   agreeMarketing: bool = False

   @field_validator("nickname")
   @classmethod
   def nickname_not_blank(cls, v):
      if not v.strip():
         raise ValueError("닉네임을 입력해주세요.")
      return v

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

   @field_validator("agreeRequired")
   @classmethod
   def agree_required_must_be_true(cls, v):
      if not v:
         raise ValueError("필수 약관에 동의해주세요.")
      return v

   model_config = ConfigDict(
      json_schema_extra={
         "examples": [
            {
               "nickname": "김민준",
               "email": "test1@naver.com",
               "password": "12341234",
               "passwordConfirm": "12341234",
               "ridingStyles": ["로드", "MTB"],
               "agreeRequired": True,
               "agreeMarketing": True,
            }
         ]
      }
   )


class Member(BaseModel):
   id: int
   email: str
   nickname: str
   role: str
   created_at: datetime