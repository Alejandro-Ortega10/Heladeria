from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import sys
import os

# Ajustar rutas para importar db/database.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.database import DB_PATH

app = FastAPI(title="Heladeria Unificada API")

# Configurar CORS para permitir que Streamlit (generalmente en puerto 8501) se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/health")
async def root():
    return {"status": "online", "service": "heladeria_api"}

# --- MODELOS ---
class Sabor(BaseModel):
    id : int
    nombre : str
    precio : float
    stock : int

class NuevoSabor(BaseModel):
    nombre: str
    precio : float
    stock : int

class VentaItem(BaseModel):
    idSabor: int
    cantidad: int

class Venta(BaseModel):
    items: List[VentaItem]

class ItemCompra(BaseModel):
    sabor_id: int
    cantidad_comprada: int

class Compra(BaseModel):
    items: List[ItemCompra]
    total_compra: float

# --- RUTAS DE INVENTARIO ---
@app.get("/inventario")
async def inventario():
    conn = get_db_connection()
    try:
        sabores = conn.execute('SELECT * FROM sabores').fetchall()
        return [dict(row) for row in sabores]
    finally:
        conn.close()

@app.put("/inventario")
async def actualizar_inventario(sabor: Sabor):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE sabores SET nombre = ?, precio = ?, stock = ? WHERE id = ?", (sabor.nombre, sabor.precio, sabor.stock, sabor.id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Sabor con ID {sabor.id} no existe")
        return {"mensaje": "Inventario actualizado con éxito"}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Error en base de datos")
    finally:
        conn.close()

@app.post("/inventario")
async def nuevo_sabor(sabor : NuevoSabor):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO sabores (nombre, precio, stock) VALUES (?, ?, ?)", (sabor.nombre, sabor.precio, sabor.stock,))
        conn.commit()
        return {"mensaje": "Sabor agregado con éxito"}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Error en base de datos")
    finally:
        conn.close()

@app.delete("/inventario/{id}")
async def eliminar_sabor(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM sabores WHERE id = ?", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Sabor con ID {id} no existe")
        return {"mensaje": "Sabor eliminado con éxito"}
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Error al eliminar")
    finally:
        conn.close()

# --- RUTAS DE OPERACIONES ---
@app.get("/ventas")
async def listar_ventas():
    conn = get_db_connection()
    try:
        ventas = conn.execute('SELECT * FROM ventas ORDER BY fecha DESC').fetchall()
        resultado = []
        for v in ventas:
            id_venta = v["id"]
            detalles = conn.execute('''
                SELECT dv.*, s.nombre 
                FROM detalle_ventas dv 
                JOIN sabores s ON dv.sabor_id = s.id 
                WHERE dv.venta_id = ?
            ''', (id_venta,)).fetchall()
            
            venta_dict = dict(v)
            venta_dict["items"] = [dict(d) for d in detalles]
            resultado.append(venta_dict)
        return resultado
    finally:
        conn.close()

@app.post("/ventas")
async def registrar_venta(venta: Venta):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        total_venta = 0.0
        lista_detalle = []
        
        for item in venta.items:
            sabor = conn.execute("SELECT nombre, stock, precio FROM sabores WHERE id = ?", (item.idSabor,)).fetchone()
            if not sabor: 
                raise HTTPException(status_code=404, detail=f"ID {item.idSabor} no existe")
            if sabor["stock"] < item.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para {sabor['nombre']}")
            
            total_venta += (sabor["precio"] * item.cantidad)
            lista_detalle.append((item.idSabor, item.cantidad, sabor["precio"]))
        
        cursor.execute("INSERT INTO ventas (total) VALUES (?)", (total_venta,))
        venta_id = cursor.lastrowid
        
        for det in lista_detalle:
            cursor.execute("INSERT INTO detalle_ventas (venta_id, sabor_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)", (venta_id, det[0], det[1], det[2],))
        
        conn.commit()
        return {"mensaje": "Venta realizada", "venta_id": venta_id, "total": total_venta}
    except Exception as e:
        conn.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/compras")
async def listar_compras():
    conn = get_db_connection()
    try:
        compras = conn.execute('SELECT * FROM compras ORDER BY fecha DESC').fetchall()
        resultado = []
        for c in compras:
            id_compra = c["id"]
            detalles = conn.execute('''
                SELECT dc.*, s.nombre 
                FROM detalle_compras dc 
                JOIN sabores s ON dc.sabor_id = s.id 
                WHERE dc.compra_id = ?
            ''', (id_compra,)).fetchall()
            
            compra_dict = dict(c)
            compra_dict["items"] = [dict(d) for d in detalles]
            resultado.append(compra_dict)
        return resultado
    finally:
        conn.close()

@app.post("/compras")
async def registrar_compra(compra: Compra):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("INSERT INTO compras (total_compra) VALUES (?)", (compra.total_compra,))
        compra_id = cursor.lastrowid

        for item in compra.items:
            cursor.execute("INSERT INTO detalle_compras (compra_id, sabor_id, cantidad_comprada) VALUES (?, ?, ?)", (compra_id, item.sabor_id, item.cantidad_comprada,))
        
        conn.commit()
        return {"mensaje": "Compra registrada con éxito", "compra_id": compra_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
