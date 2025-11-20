# run_etl.py
import logging
import sys
import os
import sqlite3

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('etl_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def run_etl_pipeline():
    try:
        logger.info("🚀 Iniciando pipeline de procesamiento de sensores")
        
        # Importar módulos
        from extract import DataExtractor
        from Transform import DataTransformer
        from load import DataLoader
        
        # 1. EXTRACCIÓN
        logger.info("=== FASE 1: EXTRACCIÓN ===")
        
        file_path = r"C:\Users\LENOVO\Downloads\ETL\data\BD_SENSORES.xlsx"
        logger.info(f"📁 Leyendo archivo: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"❌ Archivo no encontrado: {file_path}")
            return False
        
        extractor = DataExtractor()
        raw_data = extractor.extract_from_excel(file_path)
        
        if not raw_data:
            logger.error("❌ No se pudieron extraer datos")
            return False
        
        # 2. TRANSFORMACIÓN
        logger.info("=== FASE 2: TRANSFORMACIÓN ===")
        transformer = DataTransformer()
        transformed_data = transformer.transform_sensor_data(raw_data)
        
        # 3. CARGA
        logger.info("=== FASE 3: CARGA ===")
        loader = DataLoader()
        
        # Cargar a SQLite
        db_path = r"C:\Users\LENOVO\Downloads\ETL\data\sensor_data.db"
        logger.info(f"💾 Guardando en base de datos: {db_path}")
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        loader.load_to_sqlite(transformed_data, db_path)
        
        # VERIFICACIÓN FINAL
        logger.info("🔍 Verificando resultados...")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            logger.info(f"📊 Tablas creadas: {table_names}")
            
            if 'sensor_readings' in table_names:
                cursor.execute("SELECT COUNT(*) FROM sensor_readings")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Tabla 'sensor_readings' creada con {count} registros")
                
                cursor.execute("SELECT * FROM sensor_readings LIMIT 5")
                sample_data = cursor.fetchall()
                logger.info(f"📝 Datos de ejemplo: {sample_data}")
            else:
                logger.error("❌ La tabla 'sensor_readings' no fue creada")
                return False
            
            conn.close()
            logger.info("🎉 Pipeline ETL completado exitosamente")
            return True
        else:
            logger.error("❌ La base de datos no fue creada")
            return False
        
    except Exception as e:
        logger.error(f"💥 Error en el pipeline: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 Iniciando Pipeline ETL...")
    success = run_etl_pipeline()
    if success:
        print("✅ Pipeline ejecutado correctamente. Ahora puedes ejecutar Streamlit.")
    else:
        print("❌ Error en el pipeline. Revisa el archivo etl_pipeline.log para más detalles.")