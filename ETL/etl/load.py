# load.py
import sqlite3
import pandas as pd
import logging
from typing import Dict
import os

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        pass
    
    def load_to_sqlite(self, transformed_data: Dict, db_path: str):
        """Carga los datos transformados a SQLite"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            logger.info(f"Conectado a base de datos: {db_path}")
            
            # Combinar todos los datos en un solo DataFrame
            all_data = []
            for sheet_name, data in transformed_data.items():
                if not data['data'].empty:
                    df = data['data'].copy()
                    all_data.append(df)
                    logger.info(f"  ✓ {sheet_name}: {len(df)} registros para cargar")
            
            if not all_data:
                logger.error("No hay datos para cargar")
                conn.close()
                return
            
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total de registros a cargar: {len(combined_df)}")
            
            # Crear tabla principal de lecturas de sensores
            combined_df.to_sql('sensor_readings', conn, if_exists='replace', index=False)
            logger.info(f"Tabla 'sensor_readings' creada con {len(combined_df)} registros")
            
            # Crear tabla de estadísticas
            stats_data = []
            for sheet_name, data in transformed_data.items():
                if data['statistics']:
                    for sensor_id, stats in data['statistics'].items():
                        stats_data.append({
                            'sensor_id': sensor_id,
                            'sheet_name': sheet_name,
                            'count': stats.get('count', 0),
                            'mean': stats.get('mean', 0),
                            'median': stats.get('median', 0),
                            'std': stats.get('std', 0),
                            'min': stats.get('min', 0),
                            'max': stats.get('max', 0),
                            'q25': stats.get('q25', 0),
                            'q75': stats.get('q75', 0),
                            'outliers_count': stats.get('outliers_count', 0)
                        })
            
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_sql('sensor_statistics', conn, if_exists='replace', index=False)
                logger.info(f"Tabla 'sensor_statistics' creada con {len(stats_df)} registros")
            
            # Crear tabla de métricas de calidad
            quality_data = []
            for sheet_name, data in transformed_data.items():
                if data['quality_metrics']:
                    metrics = data['quality_metrics']
                    quality_data.append({
                        'sheet_name': sheet_name,
                        'completeness': metrics.get('completeness', 0),
                        'unique_sensors': metrics.get('unique_sensors', 0),
                        'total_readings': metrics.get('total_readings', 0),
                        'min_voltage': metrics.get('value_range', {}).get('min_voltage', 0),
                        'max_voltage': metrics.get('value_range', {}).get('max_voltage', 0),
                        'mean_voltage': metrics.get('value_range', {}).get('mean_voltage', 0)
                    })
            
            if quality_data:
                quality_df = pd.DataFrame(quality_data)
                quality_df.to_sql('quality_metrics', conn, if_exists='replace', index=False)
                logger.info(f"Tabla 'quality_metrics' creada con {len(quality_df)} registros")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Datos cargados exitosamente a SQLite")
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos a SQLite: {e}")
            raise
    
    def load_to_csv(self, transformed_data: Dict, output_dir: str):
        """Carga los datos transformados a archivos CSV"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for sheet_name, data in transformed_data.items():
                if not data['data'].empty:
                    # Guardar datos principales
                    csv_path = os.path.join(output_dir, f"{sheet_name}_data.csv")
                    data['data'].to_csv(csv_path, index=False)
                    logger.info(f"Guardado {csv_path}")
            
            logger.info("✅ Datos exportados a CSV exitosamente")
            
        except Exception as e:
            logger.error(f"❌ Error exportando a CSV: {e}")
            raise

if __name__ == "__main__":
    # Ejemplo de uso
    loader = DataLoader()
    print("DataLoader class cargada correctamente")