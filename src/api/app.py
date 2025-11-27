from fastapi import FastAPI
from api.routes import books, changes


app = FastAPI(title="Book Scrapper")

app.include_router(books.router)
app.include_router(changes.router)


@app.get("/")
async def read_root():
    return {"hello": "world"}
