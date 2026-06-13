from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import engine, get_db
import models
import os
import shutil
from passlib.hash import bcrypt

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

os.makedirs("uploads/posters", exist_ok=True)
os.makedirs("uploads/trailers", exist_ok=True)

sessions = {}

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============ ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ============

def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authorized")
    return sessions[session_id]

# ============ АВТОРИЗАЦИЯ ============

@app.post("/api/auth/login")
def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not bcrypt.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong login or password")
    
    import uuid
    session_id = str(uuid.uuid4())
    sessions[session_id] = user.id
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "Успешный вход", "user_id": user.id}

@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    response.delete_cookie("session_id")
    return {"message": "Выход выполнен"}

@app.post("/api/auth/register")
def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = bcrypt.hash(password)
    user = models.User(username=username, password_hash=hashed)
    db.add(user)
    db.commit()
    return {"message": "User created"}

# ============ ЖАНРЫ ============

@app.get("/api/genres")
def get_genres(db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    genres = db.query(models.Genre).all()
    return [{"id": g.id, "name": g.name, "description": g.description} for g in genres]

@app.post("/api/genres")
def create_genre(name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    genre = models.Genre(name=name, description=description)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return {"id": genre.id, "name": genre.name, "description": genre.description}

@app.put("/api/genres/{genre_id}")
def update_genre(genre_id: int, name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    genre.name = name
    genre.description = description
    db.commit()
    return {"id": genre.id, "name": genre.name}

@app.delete("/api/genres/{genre_id}")
def delete_genre(genre_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    genre = db.query(models.Genre).filter(models.Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    if genre.movies:
        raise HTTPException(status_code=400, detail="Cannot delete genre with movies")
    db.delete(genre)
    db.commit()
    return {"message": "Genre deleted"}   

# ============ ФИЛЬМЫ ============

@app.get("/api/movies")
def get_movies(search: str = "", genre_id: int = None, year_from: int = None, year_to: int = None, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    query = db.query(models.Movie)
    if search:
        query = query.filter(models.Movie.title.ilike(f"%{search}%"))
    if genre_id:
        query = query.filter(models.Movie.genre_id == genre_id)
    if year_from:
        query = query.filter(models.Movie.release_year >= year_from)
    if year_to:
        query = query.filter(models.Movie.release_year <= year_to)
    movies = query.all()
    return [{
        "id": m.id,
        "title": m.title,
        "description": m.description,
        "release_year": m.release_year,
        "genre_id": m.genre_id,
        "genre_name": m.genre.name if m.genre else None,
        "poster_path": m.poster_path,
        "trailer_path": m.trailer_path
    } for m in movies]

@app.post("/api/movies")
def create_movie(
    title: str = Form(...),
    description: str = Form(""),
    release_year: int = Form(...),
    genre_id: int = Form(...),
    poster: UploadFile = File(None),
    trailer: UploadFile = File(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    poster_path = None
    trailer_path = None

    if poster and poster.filename:
        poster_path = f"uploads/posters/{poster.filename}"
        with open(poster_path, "wb") as f:
            shutil.copyfileobj(poster.file, f)

    if trailer and trailer.filename:
        trailer_path = f"uploads/trailers/{trailer.filename}"
        with open(trailer_path, "wb") as f:
            shutil.copyfileobj(trailer.file, f)

    movie = models.Movie(
        title=title,
        description=description,
        release_year=release_year,
        genre_id=genre_id,
        poster_path=poster_path,
        trailer_path=trailer_path
    )
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return {"id": movie.id, "title": movie.title}

@app.put("/api/movies/{movie_id}")
def update_movie(
    movie_id: int,
    title: str = Form(...),
    description: str = Form(""),
    release_year: int = Form(...),
    genre_id: int = Form(...),
    poster: UploadFile = File(None),
    trailer: UploadFile = File(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie.title = title
    movie.description = description
    movie.release_year = release_year
    movie.genre_id = genre_id

    if poster and poster.filename:
        if movie.poster_path and os.path.exists(movie.poster_path):
            os.remove(movie.poster_path)
        movie.poster_path = f"uploads/posters/{poster.filename}"
        with open(movie.poster_path, "wb") as f:
            shutil.copyfileobj(poster.file, f)

    if trailer and trailer.filename:
        if movie.trailer_path and os.path.exists(movie.trailer_path):
            os.remove(movie.trailer_path)
        movie.trailer_path = f"uploads/trailers/{trailer.filename}"
        with open(movie.trailer_path, "wb") as f:
            shutil.copyfileobj(trailer.file, f)

    db.commit()
    return {"id": movie.id, "title": movie.title}

@app.delete("/api/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie.poster_path and os.path.exists(movie.poster_path):
        os.remove(movie.poster_path)
    if movie.trailer_path and os.path.exists(movie.trailer_path):
        os.remove(movie.trailer_path)
    db.delete(movie)
    db.commit()
    return {"message": "Movie deleted"}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")