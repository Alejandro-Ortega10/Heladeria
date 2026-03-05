from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

# uvicorn main:app --reload

app = FastAPI()
class sabores(BaseModel):
    sabor_id : int
    nombre : str
    precio : float
    stock : int

def get_db_connection():
    conn = sqlite3.connect("DataBase/heladeria.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/sabores")
async def inventario():
    conn = get_db_connection()
    sabores = conn.execute('select * from sabores').fetchall()
    conn.close()
    return [dict(row) for row in sabores]