# modules/db_handler.py

import sqlite3
import os

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT,
            monto REAL,
            periodicidad TEXT,
            fecha TEXT,
            etapa TEXT,
            origen TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            monto REAL,
            periodicidad TEXT,
            fecha TEXT,
            descripcion TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insertar_gasto(categoria, monto, periodicidad, fecha, etapa, origen="general"):
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gastos (categoria, monto, periodicidad, fecha, etapa, origen)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (categoria, monto, periodicidad, fecha, etapa, origen))
    conn.commit()
    conn.close()

def insertar_ingreso(tipo, monto, periodicidad, fecha, descripcion):
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ingresos (tipo, monto, periodicidad, fecha, descripcion)
        VALUES (?, ?, ?, ?, ?)
    ''', (tipo, monto, periodicidad, fecha, descripcion))
    conn.commit()
    conn.close()

def obtener_gastos():
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gastos')
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_ingresos():
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ingresos')
    rows = cursor.fetchall()
    conn.close()
    return rows

def borrar_todos_los_datos():
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gastos')
    cursor.execute('DELETE FROM ingresos')
    conn.commit()
    conn.close()

def borrar_datos_por_id(record_id):
    conn = sqlite3.connect("data/plan_vida.db")
    cursor = conn.cursor()
    cursor.execute('DELETE FROM gastos WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
