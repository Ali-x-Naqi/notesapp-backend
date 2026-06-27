from pydantic import BaseModel, EmailStr, field_validator, model_validator


class RegisterInput(BaseModel):
    username: str
    email: EmailStr
    password: str
    password_confirm: str

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username cannot be blank.")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterInput":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match.")
        return self
