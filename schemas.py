import pydantic as _pydantic
import datetime as _datetime

# User Schemas


class UserBase(_pydantic.BaseModel):
    email: str
    name: str
    phone: int


class UserReq(UserBase):
    password: str

    class Config:
        from_attributes = True


class UserRep(UserBase):
    id: int
    created_at: _datetime.datetime

    class Config:
        from_attributes = True


# Post Schemas

class PostBase(_pydantic.BaseModel):
    post_title: str
    post_description: str
    image: str


class PostReq(PostBase):
    pass


class PostRes(PostBase):
    id: int
    user_id: int
    created_at: _datetime.datetime

    class Config:
        from_attributes = True
