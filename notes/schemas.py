from pydantic import BaseModel, field_validator


class NoteInput(BaseModel):
    title: str
    body: str = ""

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be blank.")
        return v

    @field_validator("body")
    @classmethod
    def strip_body(cls, v: str) -> str:
        return v.strip()
