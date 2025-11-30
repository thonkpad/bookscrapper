import uvicorn


def main():
    """
    WARNING: `main.py` might not be necessary if launching the app
    like mentioned in the README
    """
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
