from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3

# uvicorn main:app --reload

#Creacion de la API
app = FastAPI()

#Funcion para verificar el estado de la api
@app.get("/")
async def root():
    return{"estatus":"online"}

#Modelo para Actualizar y mostrar el inventario
class sabores(BaseModel):
    id : int
    nombre : str
    precio : float
    stock : int

#Modelo para agregar un nuevo sabor al inventario
class nuevoSabor(BaseModel):
    nombre: str
    precio : float
    stock : int

# Crea la Conexion a la base de datos
def get_db_connection():
    conn = sqlite3.connect("DataBase/heladeria.db")
    conn.row_factory = sqlite3.Row
    return conn

#Esta furncion se ejecuta para llenar el DashBoard de Streamlit
@app.get("/inventario")
async def inventario():
    conn = get_db_connection()
    sabores = conn.execute('select * from sabores').fetchall()
    conn.close()
    return [dict(row) for row in sabores]

#Esta funcion actualiza el inventario, recibe como parametro un objeto con todos los campos de la tabla sabores para actualizar todo en una sola peticion
@app.put("/inventario/")
async def actualizar_inventario(sabor: sabores):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""UPDATE Sabores SET nombre = ?, precio = ?, stock = ? WHERE id = ?""", (sabor.nombre, sabor.precio, sabor.stock, sabor.id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"El sabor con ID {sabor.id} no existe")
        return{"mensaje":"Inventario Actualizado con extio"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Error al intentar acceder a la base de datos")
    finally:
        conn.close()

#Esta funcion agrega un nuevo sabor a la tabla sabores, se le debe enviar el nombre, precio y stock inicial
@app.post("/inventario/")
async def nuevo_sabor(sabor : nuevoSabor):
    conn = get_db_connection()
    try:
        conn.execute(""" INSERT INTO sabores (nombre, precio, stock) VALUES (?, ?, ?)""", (nuevoSabor.nombre, nuevoSabor.precio, nuevoSabor.stock))
        conn.commit()
        return {"mesaje":"El nuevo sabor ha sido agregado con exito"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail="Error al intentar acceder a la base de datos")
    finally:
        conn.close()

#Modelo de los sabores vendidos
class ventaItem (BaseModel):
    idSabor: int
    cantidad: int

#Modelo de la venta completa
class venta (BaseModel):
    items: List[ventaItem]

#Esta funcion inserta las ventas en la base de datos. Si uno de los helados vendidos hay menos stock que en la venta lanza un excepcion
#Recibe una lista con todos los sabores que necesita
@app.post("/ventas/")
async def venta(venta:venta):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        total_venta = 0.0
        lista_detalle = []
        for item in venta.items:
            sabor = conn.execute("SELECT stock, precio FROM sabores WHERE id = ?", (item.idSabor)).fetchone()
            if not sabor: 
                raise HTTPException(status_code=404, detail=f"El sabor con ID {item.idSabor} No existe")
            if sabor["stock"] < item.cantidad:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para el helado de {sabor['nombre']}, el stock disponible es de {sabor['stock']}")
            total_venta += (sabor["precio"] * item.cantidad)
            lista_detalle.append((item.idSabor, item.cantidad, sabor["precio"]))
        cursor.execute("INSERT INTO ventas (total) VALUES (?)", (total_venta))
        venta_id = cursor.lastrowid
        for detalle in lista_detalle:
            cursor.execute("INSERT INTO detalle_ventas (venta_id, sabor_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)", (venta_id, detalle[0], detalle[1], detalle[2]))
        conn.commit()
        return {"mensaje": "Vemta realizada", "venta_id": venta_id, "total": total_venta}
    except HTTPException as he:
        conn.rollback()
        raise he
    except sqlite3.Error:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"rror al intentar acceder a la base de datos")
    finally:
        conn.close()

#Modelo de los sabores comprados
class itemCompra(BaseModel):
    sabor_id: int
    cantidad_comprada: int

#Modelo compra completa
class compra(BaseModel):
    items: List[itemCompra]
    total_compra: float

#Funcion para guardar y actualizar el inventario despues de una compra
#El total de la venta se debe calcula en App.py puesto que el precio de compra lo pone el usuario
@app.post("/compras/")
async def realizar_compra(compra: compra):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor.execute("INSERT INTO compras (total_compras) VALUES (?)", (compra.total_compra))
        compra_id = cursor.lastrowid

        for item in compra.items:
            sabor_existe = conn.execute("SELECT id FROM sabores WHERE id = ?", (item.sabor_id)).fetchone()
            if not sabor_existe:
                raise HTTPException(status_code=404, detail=f"El sabor con ID {item.sabor_id} no existe")
            cursor.execute("INSERT INTO detalle_compras (compra_id, sabor_id, cantidad_comprada) VALUES (?, ?, ?)", (compra_id, item.sabor_id, item.cantidad_comprada))
        conn.commit()
        return {"mensaje": "Compra registrada y stock actualizado", "compra_id": compra_id}
    except HTTPException as he:
        conn.rollback()
        raise he
    except sqlite3.Error as se:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"rror al intentar acceder a la base de datos")
    finally:
        conn.close()