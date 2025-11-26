from fastapi import FastAPI

app = FastAPI()


@app.get("/books")
async def get_books(
    category: str, min_price: int, max_price: int, rating: int, sort_by: str
):
    return {"todo": "books"}


@app.get("/books/{book_id}")
async def get_book_id(book_id):
    return {"todo": book_id}


@app.get("/changes")
async def get_changes():
    return {"todo": "changes"}


@app.get("/")
async def read_root():
    return {"hello": "world"}
