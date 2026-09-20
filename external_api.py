from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import requests
from bs4 import BeautifulSoup
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_header(request: Request, exec: RateLimitExceeded):
    return JSONResponse(
        status_code = 429,
        content={
            "detail": "Too many request"
        }
    )

@app.get("/posts")
@limiter.limit("3/minute")
def get_posts(request: Request):
    response = requests.get("https://jsonplaceholder.typicode.com/posts")

    if not response:
        raise HTTPException(
            status_code= 404, detail= "Hello some error here, check again"
        )
    
    data = response.json();
    return data

@app.get("/posts/{id}")
def get_post(id: int):
    resp = requests.get(f"https://jsonplaceholder.typicode.com/posts/{id}")
    if not resp:
        raise HTTPException(status_code=404, detail="Post not found")
    data = resp.json()
    return data;


@app.get("/crawl")
def crawl_website():
    try:
        resp = requests.get("https://news.google.com/home?hl=en-IN&gl=IN&ceid=IN:en", timeout=10)
        resp.raise_for_status()
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail=str(error))

    soup = BeautifulSoup(resp.text, "html.parser")
    titles = [
        item.get_text(strip=True)
        for item in soup.find_all("a", class_="gPFEn")
    ]

    return {"news": titles}