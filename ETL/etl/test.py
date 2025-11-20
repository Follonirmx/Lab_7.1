# test_etl.py
import sqlite3
import os
import pandas as pd

def check_database():
    db_path = r"C:\Users\LENOVO\Downloads\ETL\data\sensor_data.db"
    
    print("🔍 Verificando base de datos...")
    print(f"Ruta de DB: {db_path}")
    print(f"¿Existe el archivo?: {os.path.exists(db_path)}")
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Listar todas las tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"📊 Tablas en la base de datos: {tables}")
            
            # Verificar datos en cada tabla
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} registros")
                
                # Mostrar algunas columnas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"    Columnas: {[col[1] for col in columns]}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error al verificar la base de datos: {e}")
    else:
        print("❌ La base de datos no existe")
        print("💡 Ejecuta: python run_etl.py")

if __name__ == "__main__":
    check_database()