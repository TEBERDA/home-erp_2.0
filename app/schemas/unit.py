from pydantic import BaseModel, ConfigDict


class UnitBase(BaseModel):
    name: str
    description: str | None = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class UnitRead(UnitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
