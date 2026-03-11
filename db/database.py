import sqlite3 as sql
import os

# Ruta absoluta para evitar problemas al ejecutar desde carpetas hermanas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "heladeria.db")

def crearDB():
    conn = sql.connect(DB_PATH)
    c = conn.cursor()
    conn.executescript(f'''PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sabores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    precio REAL NOT NULL CHECK (precio > 0),
    stock INTEGER NOT NULL CHECK (stock >= 0)
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    sabor_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (sabor_id) REFERENCES sabores(id)
);

CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_compra REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS detalle_compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id INTEGER NOT NULL,
    sabor_id INTEGER NOT NULL,
    cantidad_comprada INTEGER NOT NULL,
    FOREIGN KEY (compra_id) REFERENCES compras(id),
    FOREIGN KEY (sabor_id) REFERENCES sabores(id)
);

CREATE TRIGGER IF NOT EXISTS actualizar_stock_venta
AFTER INSERT ON detalle_ventas
BEGIN
    UPDATE sabores 
    SET stock = stock - NEW.cantidad 
    WHERE id = NEW.sabor_id;
END;

CREATE TRIGGER IF NOT EXISTS actualizar_stock_compra
AFTER INSERT ON detalle_compras
BEGIN
    UPDATE sabores 
    SET stock = stock + NEW.cantidad_comprada 
    WHERE id = NEW.sabor_id;
END;

INSERT OR IGNORE INTO sabores (id, nombre, precio, stock) VALUES (1, 'Vainilla', 3500, 50);
INSERT OR IGNORE INTO sabores (id, nombre, precio, stock) VALUES (2, 'Chocolate', 4000, 40);
INSERT OR IGNORE INTO sabores (id, nombre, precio, stock) VALUES (3, 'Fresa', 3500, 35);
INSERT OR IGNORE INTO sabores (id, nombre, precio, stock) VALUES (4, 'Mango', 4500, 30);
INSERT OR IGNORE INTO sabores (id, nombre, precio, stock) VALUES (5, 'Cookies and Cream', 5000, 25);
''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    crearDB()
