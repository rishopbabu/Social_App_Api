from pydantic import BaseModel, EmailStr
from datetime import datetime
from .models import Users
from typing import List, Optional


class CommonMessageResponse(BaseModel):
    message: str


class TokenData(BaseModel):
    id: Optional[int] = None
    

class RegisterUser(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    password: str
    
    class Config:
        from_attributes = True


class UserDetail(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    profile_pic: Optional[str] = None
    updated_by: datetime

    @classmethod
    def from_users_model(cls, users: Users) -> 'UserDetail':
        return cls(id=users.id,
                   first_name=users.first_name,
                   last_name=users.last_name,
                   phone=users.phone,
                   email=users.email,
                   profile_pic=users.profile_pic,
                   updated_by=users.updated_by)

    class Config:
        from_attributes = True
        

class RegisterUserResponse(BaseModel):
    message: str
    user_detail: UserDetail

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    profile_pic: str = None
    updated_by: datetime

    @classmethod
    def from_db(cls, user):
        return cls(id=user.id,
                   first_name=user.first_name,
                   last_name=user.last_name,
                   phone=user.phone,
                   email=user.email,
                   profile_pic=user.profile_pic,
                   updated_by=user.updated_by)


class UserLoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user_detail: UserLogin

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    message: str
    total_users_count: int
    users_list: List[UserDetail]
    
    class Config:
        from_attributes = True


class GetUsersByIDResponse(BaseModel):
    message: str
    user_detail: UserDetail
    
    class Config:
        from_attributes = True
    
class UpdateUserDetail(BaseModel):
    first_name: str = None
    last_name: str = None
    email: EmailStr = None
    phone: str = None
    
    class Config:
        from_attributes = True

class UpdateUserDetailResponse(BaseModel):
    message: str
    user_detail: UserDetail
    
    class Config:
        from_attributes = True

class UpdatePassword(BaseModel):
    password: str

    class Config:
        from_attributes = True

class UserDetailAfterProfileUpdate(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone: str
    email: EmailStr
    profile_pic: str
    updated_by: datetime
    
    @classmethod
    def from_users_model(cls, users: Users) -> 'UserDetail':
        return cls(id=users.id,
                   first_name=users.first_name,
                   last_name=users.last_name,
                   phone=users.phone,
                   email=users.email,
                   profile_pic=users.profile_pic,
                   updated_by=users.updated_by)
    
    class Config:
        from_attributes = True
    
class UpdateProfileResponse(BaseModel):
    message: str
    user_detail: UserDetailAfterProfileUpdate
    
    class Config:
        from_attributes = True
        
class PostBase(BaseModel):
    caption: str
    is_published: bool = True

class CreatePost(PostBase):
    pass

    class Config:
        from_attributes = True