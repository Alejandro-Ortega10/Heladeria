import sqlite3 as sql

def crearDB():
    conn = sql.connect("DataBase/heladeria.db")
    c = conn.cursor()
    c.executescript('''PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sabores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    precio REAL NOT NULL,
    stock INTEGER NOT NULL
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
END;''')
    conn.commit()
    conn.close

if __name__ == "__main__":
    crearDB()