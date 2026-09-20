# uvicorn main:app --reload
from fastapi import FastAPI, Request, status, HTTPException, Depends, Header, UploadFile, File
from fastapi.staticfiles import StaticFiles
import os
import shutil
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from jose import jwt
from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
# from dotenv import load_dotenv
# load_dotenv()
from config import settings


# uplad file
#ensure folde rpresent
UPLOAD_DIR = settings.UPLOAD_DIR
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)



JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES

# OAuth2 - password hashing setup
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="login" )
# Dummy users DB
fake_user_DB = {
    "admin":{
        "username": "admin",
        "hashed_password": pwd_context.hash("1234")
    }
}

#Hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)




def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verifyJWT(token: str = Depends(oauth2_schema)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    print ('token' + token)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token JWT Error")

app = FastAPI()

#Setup static files
app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# uplaod file api
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    filename = os.path.basename(file.filename or "")
    if not filename:
        raise HTTPException(status_code=400, detail="A file is required")
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "message": "File uploaded successfully",
        "filename": filename,
        "url": f"/files/{filename}",
    }
# get uploaded file
@app.get("/file/{filename}")
def get_file(filename: str):
    fiel_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(fiel_path):
        raise HTTPException(
            status_code= 404,
            detail= "File not found"
        )
    return {
        "filename": filename
    }


# Login with normal JWT
# @app.post("/login")
# def login(username: str, password: str):
#     if username == "admin@gmail.com" and password == "Test@123":
#         access_token = create_access_token(data={"sub": username})
#         return {"access_token": access_token, "token_type": "Bearer"}
#     else:
#         raise HTTPException(status_code=401, detail="Invalid username or password")

# Login with OAuth2 Form
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_user_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid username or password"
        )
    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "Bearer"}



todos = []
engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
sessionlocal = sessionmaker(bind=engine)
base = declarative_base()

class TodoTable(base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    completed = Column(Boolean)

base.metadata.create_all(bind=engine)

def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home(db: Session = Depends(get_db), user = Depends(verifyJWT)):
    return {"message": "DB connected successfully!"}

@app.get("/OAuth2-secure-endpoint")
def OAuth2SecureEndpoint(username: str = Depends(verifyJWT)):
    return {
        "message": "You are authorized to access this route",
        "user": username
    }



# conn = sqlite3.connect('test.db')
# conn.execute('''CREATE TABLE IF NOT EXISTS todos
#              (id INTEGER PRIMARY KEY, title TEXT, completed BOOLEAN)''')
# conn.commit()

# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     print("=====================Request received at:", request.url.path)
#     response = await call_next(request)
#     print("+++++++++++++++++++Response status code:", response.status_code)
#     return response



# def verifyToken(x_token: str = Header(...)):
#   if x_token != "my-secret-token":
#     raise HTTPException(status_code=400, detail="Invalid X-Token header")
#   return x_token

# Global error handler
class TodoNotFoundException(Exception):
    def __init__(self, id: int):
        self.id = id

@app.exception_handler(TodoNotFoundException)
def todo_not_found_exception_handler(request: Request, exc: TodoNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"message": f"Todo with ID {exc.id} not found."},
    )


class ToDoDto(BaseModel):
    title: str
    completed: bool

@app.post("/todos", status_code=status.HTTP_201_CREATED)
def create_todo(todo: ToDoDto, db: Session = Depends(get_db)):
    todoToSave = TodoTable(title=todo.title, completed=todo.completed)
    db.add(todoToSave)
    db.commit()
    db.refresh(todoToSave)
    return {"message": "Todo created successfully", "todo": todoToSave}


@app.get("/todos")
def get_todos(title: str = None, user = Depends(verifyJWT), db: Session = Depends(get_db)):
    allTodos = db.query(TodoTable).filter(TodoTable.title.contains(title) if title else True).all()
    return allTodos

@app.get("/todos/{id}")
def get_todo(id: int, db: Session = Depends(get_db)):
    todo = db.query(TodoTable).filter(TodoTable.id == id).first()
    if todo:
        return todo
    raise TodoNotFoundException(id=id)

@app.put("/todos/{id}")
def update_todo(id:int, todoDto: ToDoDto, db: Session = Depends(get_db)):
    todo = db.query(TodoTable).filter(TodoTable.id == id).first();
    if not todo:
        raise TodoNotFoundException(id=id)
    todo.title = todoDto.title
    todo.completed = todoDto.completed
    db.commit()
    db.refresh(todo)
    return {"message": "Todo updated successfully", "todo": todo}


@app.delete("/todos/{id}")
def delete_todo(id: int, db: Session = Depends(get_db)):
    todo = db.query(TodoTable).filter(TodoTable.id == id).first()
    if not todo:
        raise TodoNotFoundException(id=id)
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}
