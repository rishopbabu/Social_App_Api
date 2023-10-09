from pydantic import BaseModel, EmailStr, conint
from datetime import datetime
from .models import Users, Post
from typing import List, Optional
from fastapi import Form
import base64

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
        profile_picture_base64 = encode_image_to_base64(users.profile_pic) if users.profile_pic else None
        return cls(id=users.id,
                   first_name=users.first_name,
                   last_name=users.last_name,
                   phone=users.phone,
                   email=users.email,
                   profile_pic=profile_picture_base64,
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
    profile_pic: Optional[str] = None
    updated_by: datetime

    @classmethod
    def from_db(cls, user):
        profile_picture_base64 = encode_image_to_base64(user.profile_pic) if user.profile_pic else None
        return cls(id=user.id,
                   first_name=user.first_name,
                   last_name=user.last_name,
                   phone=user.phone,
                   email=user.email,
                   profile_pic=profile_picture_base64,
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
        profile_picture_base64 = encode_image_to_base64(users.profile_pic) if users.profile_pic else None
        return cls(id=users.id,
                   first_name=users.first_name,
                   last_name=users.last_name,
                   phone=users.phone,
                   email=users.email,
                   profile_pic=profile_picture_base64,
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
    is_published: bool

    @classmethod
    def as_form(cls, caption: str = Form(...), is_published: bool = True):
        return cls(caption=caption, is_published=is_published)


class CreatePost(PostBase):
    pass

    class Config:
        from_attributes = True


class PostResponseBase(BaseModel):
    post_id: int
    user_id: int
    caption: str
    is_published: bool
    post_image: str
    updated_by: datetime
    user_detail: UserDetail
    votes: int

    @classmethod
    def from_db(cls, posts: Post):
        return cls(post_id=posts.post_id,
                   user_id=posts.user_id,
                   caption=posts.caption,
                   is_published=posts.is_published,
                   post_image=posts.post_image,
                   updated_by=posts.updated_by,
                   user_detail=posts.user_detail,
                   votes=0)

    class Config:
        from_attributes = True


class postResponse(BaseModel):
    post_detail: PostResponseBase
    votes: int

    class Config:
        from_attributes = True


class CreatePostResponse(BaseModel):
    message: str
    post_detail: PostResponseBase

    class Config:
        from_attributes = True


class GetPostsResponse(BaseModel):
    message: str
    total_posts: int
    post_details: List[PostResponseBase]

    class Config:
        from_attributes = True


class GetIndividualPostResponse(BaseModel):
    message: str
    post_detail: PostResponseBase

    class Config:
        from_attributes = True


class Vote(BaseModel):
    post_id: int
    dir: conint(le=1)

    class Config:
        from_attributes = True


class VoteResponse(BaseModel):
    message: str
    vote: Vote


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read())
        return encoded_image.decode('utf-8')