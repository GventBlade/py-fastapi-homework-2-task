from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import MovieDetail, MovieUpdate, MovieListResponse, MovieCreate


router = APIRouter()

@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = await db.get(MovieModel, movie_id)
    if query is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    await db.delete(query)
    await db.commit()


@router.get("/{movie_id}/", response_model=MovieDetail)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    query = (select(MovieModel).
             options(joinedload(MovieModel.genres)).
             options(joinedload(MovieModel.actors)).
             options(joinedload(MovieModel.languages)).
             options(joinedload(MovieModel.country)).
             where(MovieModel.id == movie_id))

    result = await db.execute(query)
    movie = result.unique().scalar_one_or_none()

    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")

    return movie


@router.patch("/{movie_id}/", status_code=status.HTTP_200_OK)
async def update_movie(movie_id: int, movie_update: MovieUpdate, db: AsyncSession = Depends(get_db)):
    movie = await db.get(MovieModel, movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie with the given ID was not found.")
    update_data = movie_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)
    try:
        await db.commit()
    except Exception:  # Якщо дані не валідні для БД
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid input data.")
    return {"detail": "Movie updated successfully."}

@router.get("/", response_model=MovieListResponse)
async def get_movies(page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=20),
                     db: AsyncSession = Depends(get_db)):
    # 1. Рахуємо загальну кількість (виконуємо запит!)
    count_query = select(func.count(MovieModel.id))
    total_result = await db.execute(count_query)
    total_items = total_result.scalar()

    # 2. Перевірка згідно з ТЗ
    if total_items == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found.")

    # 3. Отримуємо список фільмів
    # Офсет для page=1 має бути 0
    offset = (page - 1) * per_page
    query = select(MovieModel).order_by(MovieModel.id.desc()).limit(per_page).offset(offset)

    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No movies found for the specified page.")
    # 4. Розрахунки для відповіді
    total_pages = (total_items + per_page - 1) // per_page

    base_url = "/api/v1/theater/movies/"
    # Попередння сторінка
    prev_p = f"{base_url}?page={page - 1}&per_page={per_page}" if page > 1 else None
    # Наступна сторінка
    next_p = f"{base_url}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_p,
        "next_page": next_p,
        "total_pages": total_pages,
        "total_items": total_items
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreate, db: AsyncSession = Depends(get_db)):
    existing_movie = await db.execute(
        select(MovieModel).where(MovieModel.name == movie.name, MovieModel.date == movie.date)
    )
    if existing_movie.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    res_c = await db.execute(select(CountryModel).where(CountryModel.code == movie.country))
    country_obj = res_c.scalar_one_or_none()
    if not country_obj:
        country_obj = CountryModel(code=movie.country)
        db.add(country_obj)
        await db.flush()

    genre_objects = []
    for g_name in movie.genres:
        result = await db.execute(select(GenreModel).where(GenreModel.name == g_name))
        obj = result.scalar_one_or_none()

        if not obj:
            obj = GenreModel(name=g_name)
            db.add(obj)
            await db.flush()

        genre_objects.append(obj)

    actor_objects = []
    for a_name in movie.actors:
        res = await db.execute(select(ActorModel).where(ActorModel.name == a_name))
        current_actor = res.scalar_one_or_none()  # Використовуй одну назву змінної

        if not current_actor:
            current_actor = ActorModel(name=a_name)
            db.add(current_actor)
            await db.flush()

        actor_objects.append(current_actor)

    lang_objects = []
    for l_name in movie.languages:
        res = await db.execute(select(LanguageModel).where(LanguageModel.name == l_name))
        current_lang = res.scalar_one_or_none()

        if not current_lang:
            current_lang = LanguageModel(name=l_name)
            db.add(current_lang)
            await db.flush()

        lang_objects.append(current_lang)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country_obj,
        genres=genre_objects,
        actors=actor_objects,
        languages=lang_objects
    )
    try:
        db.add(new_movie)
        await db.commit()
        await db.refresh(new_movie)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{movie.name}' and release date '{movie.date}' already exists."
        )

    return new_movie

