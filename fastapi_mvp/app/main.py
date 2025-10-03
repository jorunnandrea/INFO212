
from fastapi import FastAPI

app = FastAPI(title="Min første FastAPI")

@app.get("/")
def root():
    return {"message": "Dette er en test"}

@app.get("/hello") 
def hello(): return {"hilsen": "Hei"}   


@app.get("/hello/{navn}")
def hello(navn: str):
    return {"hilsen": f"Hei, {navn}!"}