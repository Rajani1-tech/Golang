from fastapi import FastAPI
from pytest import Session


## add user authentication and file upload logic
from fastapi import Depends, File, UploadFile, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi_users import FastAPIUsers, models, SQLAlchemyUserDatabase
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker



DATABASE_URL = "sqlite:///./test.db"
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

class UserCreate(models.BaseModel):
    username: str
    password: str

class UserDB(UserCreate):
    id: int

class UserInDB(UserDB):
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# OAuth2 password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create FastAPIUsers instance
fastapi_users = FastAPIUsers(
    user_db=SQLAlchemyUserDatabase(UserDB, get_db),
    secret=SECRET_KEY,
    lifetime_seconds=3600,
    tokenUrl="token",
)

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    return fastapi_users.get_current_user(token)

# Login route
@app.post("/token", response_model=models.Token)
async def login_for_access_token(data: UserCreate, db: Session = Depends(get_db)):
    user = await fastapi_users.authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(
            status_code=int,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await fastapi_users.create_access_token(data=dict(sub=user.id))

# Route to get current user information
@app.get("/users/me", response_model=UserDB)
async def read_users_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

# Route to upload files
@app.post("/files/")
async def create_file(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
):
    # You can save the file or perform any desired action here
    return {"filename": file.filename}

# Include the FastAPIUsers routes
app.include_router(fastapi_users.get_auth_router())
app.include_router(fastapi_users.get_register_router())
app.include_router(fastapi_users.get_reset_password_router())

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
