from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routes import movie_router

app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

# Додаємо обробник помилок для всього додатка
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid input data."},
    )

api_version_prefix = "/api/v1"

# Твій роутер
app.include_router(movie_router, prefix=f"{api_version_prefix}/theater/movies", tags=["movies"])
