from pydantic import BaseModel, Field


class TransferRuleCreate(BaseModel):
    from_line: str = Field(min_length=1)
    to_line: str = Field(min_length=1)
    amount: float = Field(ge=0)
    active: bool = True


class TransferRuleUpdate(BaseModel):
    from_line: str | None = Field(default=None, min_length=1)
    to_line: str | None = Field(default=None, min_length=1)
    amount: float | None = Field(default=None, ge=0)
    active: bool | None = None
