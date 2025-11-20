# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

def init_db_connection():
    """Inicializa conexión a la base de datos"""
    db_path = r"C:\Users\LENOVO\Downloads\ETL\data\sensor_data.db"
    
    st.sidebar.write("---")
    st.sidebar.subheader("Información de la Base de Datos")
    st.sidebar.write(f"**Ruta:** `{db_path}`")
    
    # Verificar si la base de datos existe
    if not os.path.exists(db_path):
        st.sidebar.error("❌ Base de datos no encontrada")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Verificar si la tabla existe
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        st.sidebar.write(f"**Tablas encontradas:** {len(table_names)}")
        for table in table_names:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            st.sidebar.write(f"  - `{table}`: {count} registros")
        
        if 'sensor_readings' not in table_names:
            st.sidebar.error("❌ Tabla 'sensor_readings' no existe")
            conn.close()
            return None
            
        return conn
        
    except Exception as e:
        st.sidebar.error(f"❌ Error de conexión: {e}")
        return None

def load_sensor_data():
    """Carga datos de sensores desde SQLite"""
    conn = init_db_connection()
    
    if conn is None:
        return None
    
    try:
        # Cargar datos principales
        query = "SELECT * FROM sensor_readings LIMIT 1"  # Primero probamos con 1 registro
        df_sample = pd.read_sql(query, conn)
        
        # Si funciona, cargar todos los datos
        query_full = "SELECT * FROM sensor_readings"
        df = pd.read_sql(query_full, conn)
        
        # Verificar si hay datos
        if df.empty:
            st.warning("⚠️ La tabla existe pero no contiene datos")
            return pd.DataFrame()
        
        # Convertir timestamp si existe
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        st.sidebar.success(f"✅ {len(df)} registros cargados")
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        conn.close()
        return None

def show_etl_instructions():
    """Muestra instrucciones para ejecutar el ETL"""
    st.error("""
    ❌ **No se pudieron cargar los datos**
    
    **Para solucionar este problema:**
    
    1. **Abre una terminal** en la carpeta del proyecto
    2. **Ejecuta el pipeline ETL:**
    ```bash
    cd C:\\Users\\LENOVO\\Downloads\\ETL\\etl
    python run_etl.py
    ```
    3. **Verifica que no hay errores** en la ejecución
    4. **Recarga este dashboard**
    
    **Archivos necesarios:**
    - `run_etl.py` - Pipeline principal
    - `extract.py` - Extracción de datos
    - `transform.py` - Transformación de datos  
    - `load.py` - Carga a base de datos
    """)
    
    # Botón para verificar estado actual
    if st.button("🔍 Verificar estado actual del sistema"):
        check_system_status()

def check_system_status():
    """Verifica el estado del sistema"""
    st.subheader("🔍 Diagnóstico del Sistema")
    
    # Verificar archivos
    files_to_check = [
        r"C:\Users\LENOVO\Downloads\ETL\etl\run_etl.py",
        r"C:\Users\LENOVO\Downloads\ETL\etl\extract.py", 
        r"C:\Users\LENOVO\Downloads\ETL\etl\transform.py",
        r"C:\Users\LENOVO\Downloads\ETL\etl\load.py",
        r"C:\Users\LENOVO\Downloads\ETL\data\BD_SENSORES.xlsx",
        r"C:\Users\LENOVO\Downloads\ETL\data\sensor_data.db"
    ]
    
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        icon = "✅" if exists else "❌"
        st.write(f"{icon} `{file_path}`")
    
    # Verificar base de datos
    db_path = r"C:\Users\LENOVO\Downloads\ETL\data\sensor_data.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            
            st.success(f"📊 Tablas en la base de datos: {[table[0] for table in tables]}")
        except Exception as e:
            st.error(f"❌ Error accediendo a la base de datos: {e}")
    else:
        st.error("❌ La base de datos no existe")

def main():
    st.set_page_config(
        page_title="Dashboard de Monitoreo de Sensores",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📊 Dashboard de Monitoreo de Sensores")
    st.markdown("---")
    
    # Sidebar con información
    st.sidebar.title("🔧 Configuración")
    
    # Cargar datos
    with st.spinner("🔄 Cargando datos de sensores..."):
        df = load_sensor_data()
    
    if df is None:
        show_etl_instructions()
        return
    
    if df.empty:
        st.warning("⚠️ No hay datos disponibles para mostrar")
        return
    
    # Si llegamos aquí, tenemos datos para mostrar
    st.success(f"✅ Datos cargados correctamente: {len(df)} registros")
    
    # Mostrar métricas principales
    st.header("📈 Métricas Principales")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Sensores", df['sensor_id'].nunique())
    
    with col2:
        st.metric("Total de Lecturas", len(df))
    
    with col3:
        st.metric("Voltaje Promedio", f"{df['voltage'].mean():.2f} V")
    
    with col4:
        st.metric("Rango de Voltaje", f"{df['voltage'].min():.2f} - {df['voltage'].max():.2f} V")
    
    # Gráficos
    st.header("📊 Visualizaciones")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución de Voltajes")
        fig_hist = px.histogram(df, x='voltage', nbins=20, 
                               title="Distribución de Lecturas de Voltaje")
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("Voltaje por Sensor")
        sensor_avg = df.groupby('sensor_id')['voltage'].mean().reset_index()
        fig_bar = px.bar(sensor_avg, x='sensor_id', y='voltage',
                        title="Voltaje Promedio por Sensor")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Datos crudos
    st.header("📋 Datos Detallados")
    st.dataframe(df.head(1000), use_container_width=True)

if __name__ == "__main__":
    main()