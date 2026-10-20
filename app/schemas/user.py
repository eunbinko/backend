from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LoginReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class SignUpReq(LoginReq):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class UserResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    email: str | None
    name: str


class SignUpRes(BaseModel):
    code: int
    message: str
    result: UserResult


class LoginRes(SignUpRes):
    pass
