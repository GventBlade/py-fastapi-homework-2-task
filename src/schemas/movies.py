from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date, timedelta


class MovieShort(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    movies: List[MovieShort]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

class GenreOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class ActorOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class LanguageOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

class CountryOut(BaseModel):
    id: int
    code: str
    name: str | None = None

    model_config = ConfigDict(from_attributes=True)

class MovieDetail(BaseModel):
    id: int
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: CountryOut
    genres: list[GenreOut]
    actors: list[ActorOut]
    languages: list[LanguageOut]


class MovieCreate(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: str
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_release_date(cls, v: date) -> date:
        # Обчислюємо максимальну дозволену дату (сьогодні + 365 днів)
        max_date = date.today() + timedelta(days=365)
        if v > max_date:
            raise ValueError("Invalid input data.")  # Використовуємо саме цей текст для помилки
        return v

class MovieUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    @field_validator("date")
    @classmethod
    def validate_update_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today() + timedelta(days=365):
            raise ValueError("Invalid input data.")
        return v
