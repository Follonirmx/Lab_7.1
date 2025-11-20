import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataTransformer:
    def __init__(self):
        self.transformed_data = {}
        self.analysis_results = {}
        
    def transform_sensor_data(self, raw_data: Dict) -> Dict:
        """Transforma los datos brutos en formato estructurado"""
        try:
            logger.info(f"Iniciando transformación de {len(raw_data)} hojas")
            
            for sheet_name, sheet_data in raw_data.items():
                logger.info(f"Transformando {sheet_name}")
                df = sheet_data['data']
                
                # Log información del DataFrame
                logger.info(f"  Dimensiones: {df.shape}")
                logger.info(f"  Columnas: {df.columns.tolist()}")
                
                # Aplicar transformaciones
                cleaned_df = self._clean_data(df)
                structured_df = self._structure_sensor_data(cleaned_df, sheet_name)
                
                if not structured_df.empty:
                    self.transformed_data[sheet_name] = {
                        'data': structured_df,
                        'statistics': self._calculate_statistics(structured_df),
                        'quality_metrics': self._calculate_quality_metrics(structured_df)
                    }
                    logger.info(f"  ✓ {sheet_name}: {len(structured_df)} registros procesados")
                else:
                    self.transformed_data[sheet_name] = {
                        'data': pd.DataFrame(),
                        'statistics': {},
                        'quality_metrics': {}
                    }
                    logger.warning(f"  ✗ {sheet_name}: Sin datos estructurados")
            
            # Análisis cruzado solo si hay datos
            if any(not data['data'].empty for data in self.transformed_data.values()):
                self._perform_cross_sheet_analysis()
            
            logger.info("Transformación completada")
            return self.transformed_data
            
        except Exception as e:
            logger.error(f"Error en transformación: {str(e)}")
            logger.exception("Detalles del error:")  # Esto da traceback completo
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y prepara los datos"""
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Remover filas completamente vacías
        cleaned_df = cleaned_df.dropna(how='all')
        
        # Remover columnas completamente vacías
        cleaned_df = cleaned_df.dropna(axis=1, how='all')
        
        # Convertir columnas con valores de voltaje a numéricos
        for col in cleaned_df.columns:
            if cleaned_df[col].dtype == 'object':
                cleaned_df[col] = cleaned_df[col].apply(self._convert_voltage_to_numeric)
                
        return cleaned_df
    
    def _convert_voltage_to_numeric(self, value):
        """Convierte valores de voltaje en strings a numéricos"""
        if pd.isna(value) or value == '':
            return np.nan
        
        if isinstance(value, (int, float)):
            return float(value)
            
        if isinstance(value, str):
            # Extraer número del string (ej: "1.23 V" -> 1.23)
            match = re.search(r'([-+]?\d*\.\d+|\d+)', str(value))
            if match:
                try:
                    return float(match.group())
                except ValueError:
                    return np.nan
        
        return np.nan

    def _is_numeric_string(self, value: str) -> bool:
        """Verifica si un string puede convertirse a número"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _find_sensor_rows(self, df: pd.DataFrame) -> List[int]:
        """Encuentra filas que contienen datos de sensores"""
        sensor_rows = []
        
        # Verificar si el DataFrame está vacío
        if df.empty:
            return sensor_rows
        
        for idx, row in df.iterrows():
            # Contar valores numéricos en la fila
            numeric_count = 0
            for val in row.values:
                try:
                    if pd.notna(val) and (isinstance(val, (int, float)) or 
                                        (isinstance(val, str) and self._is_numeric_string(val))):
                        numeric_count += 1
                except:
                    continue
            
            # Si tiene al menos 3 valores numéricos, probablemente es fila de sensores
            if numeric_count >= 3:
                sensor_rows.append(idx)
                
        return sensor_rows
    
    def _structure_sensor_data(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Estructura los datos de sensores en formato tidy"""
        # Verificar si el DataFrame está vacío
        if df.empty:
            logger.warning(f"DataFrame vacío para {sheet_name}")
            return pd.DataFrame()
        
        # Encontrar fila que contiene los valores de sensores
        sensor_rows = self._find_sensor_rows(df)
        
        if not sensor_rows:
            logger.warning(f"No se encontraron filas de sensores en {sheet_name}")
            logger.info(f"Dimensiones del DataFrame: {df.shape}")
            logger.info(f"Primeras filas:\n{df.head(3)}")
            return pd.DataFrame()
        
        # Crear DataFrame estructurado
        structured_data = []
        
        for row_idx in sensor_rows:
            # VERIFICAR que el índice esté dentro de los límites
            if row_idx >= len(df):
                logger.warning(f"Índice {row_idx} fuera de rango para DataFrame de tamaño {len(df)}")
                continue
                
            row_data = df.iloc[row_idx]
            
            for col_idx, value in enumerate(row_data.values):
                # Verificar que tenemos un valor válido
                try:
                    numeric_value = self._convert_voltage_to_numeric(value)
                    if pd.notna(numeric_value):
                        structured_data.append({
                            'sensor_id': f"{sheet_name}_S{col_idx + 1}",
                            'sensor_number': col_idx + 1,
                            'reading_number': row_idx - min(sensor_rows) + 1,
                            'timestamp': self._generate_timestamp(row_idx, min(sensor_rows)),
                            'voltage': float(numeric_value),
                            'sheet_name': sheet_name,
                            'row_index': row_idx,
                            'column_index': col_idx
                        })
                except Exception as e:
                    logger.debug(f"Error procesando valor en ({row_idx}, {col_idx}): {value} - {e}")
                    continue
        
        result_df = pd.DataFrame(structured_data)
        logger.info(f"Estructurados {len(result_df)} registros para {sheet_name}")
        return result_df
    
    def _generate_timestamp(self, row_idx: int, start_row: int) -> datetime:
        """Genera timestamp basado en índice de fila"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        time_delta = timedelta(minutes=(row_idx - start_row) * 5)  # 5 minutos entre lecturas
        return base_time + time_delta
    
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """Calcula estadísticas por sensor"""
        if df.empty:
            return {}
            
        # Asegurarse de que tenemos las columnas necesarias
        required_cols = ['sensor_id', 'voltage']
        if not all(col in df.columns for col in required_cols):
            logger.warning(f"Faltan columnas requeridas para estadísticas: {df.columns.tolist()}")
            return {}
            
        try:
            stats = df.groupby('sensor_id')['voltage'].agg([
                'count', 'mean', 'median', 'std', 'min', 'max', 
                lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)
            ]).rename(columns={
                '<lambda_0>': 'q25', 
                '<lambda_1>': 'q75'
            })
            
            # Detectar outliers usando IQR
            stats['outliers_count'] = df.groupby('sensor_id').apply(
                lambda x: self._count_outliers(x['voltage'])
            )
            
            return stats.to_dict('index')
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
            return {}
    
    def _count_outliers(self, series: pd.Series) -> int:
        """Cuenta outliers usando método IQR"""
        if len(series) < 4:
            return 0
            
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            return ((series < lower_bound) | (series > upper_bound)).sum()
        except:
            return 0
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas de calidad de datos"""
        if df.empty:
            return {}
            
        try:
            metrics = {
                'completeness': df['voltage'].count() / len(df) if len(df) > 0 else 0,
                'unique_sensors': df['sensor_id'].nunique(),
                'total_readings': len(df),
            }
            
            # Solo calcular si tenemos datos de timestamp
            if 'timestamp' in df.columns and not df['timestamp'].empty:
                metrics['date_range'] = {
                    'start': df['timestamp'].min(),
                    'end': df['timestamp'].max(),
                    'duration_days': (df['timestamp'].max() - df['timestamp'].min()).days
                }
            
            # Solo calcular si tenemos datos de voltage
            if 'voltage' in df.columns and not df['voltage'].empty:
                metrics['value_range'] = {
                    'min_voltage': df['voltage'].min(),
                    'max_voltage': df['voltage'].max(),
                    'mean_voltage': df['voltage'].mean()
                }
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculando métricas de calidad: {e}")
            return {}
    
    def _perform_cross_sheet_analysis(self):
        """Realiza análisis comparativo entre diferentes hojas"""
        try:
            # Recolectar todos los DataFrames no vacíos
            all_dfs = []
            for sheet_name, data in self.transformed_data.items():
                if not data['data'].empty:
                    all_dfs.append(data['data'])
            
            if not all_dfs:
                logger.warning("No hay datos para análisis cruzado")
                return
                
            all_data = pd.concat(all_dfs, ignore_index=True)
            
            self.analysis_results['cross_sheet'] = {
                'total_sensors': all_data['sensor_id'].nunique(),
                'total_readings': len(all_data),
                'global_stats': {
                    'mean_voltage': all_data['voltage'].mean(),
                    'voltage_std': all_data['voltage'].std(),
                    'voltage_range': [all_data['voltage'].min(), all_data['voltage'].max()]
                },
                'sensors_by_sheet': all_data.groupby('sheet_name')['sensor_id'].nunique().to_dict()
            }
            
            logger.info("Análisis cruzado completado")
        except Exception as e:
            logger.error(f"Error en análisis cruzado: {e}")
            self.analysis_results['cross_sheet'] = {}
    
    def get_anomaly_report(self) -> Dict:
        """Genera reporte de anomalías"""
        anomalies = {}
        
        for sheet_name, sheet_data in self.transformed_data.items():
            if sheet_data['data'].empty:
                continue
                
            df = sheet_data['data']
            stats = sheet_data['statistics']
            
            sheet_anomalies = []
            
            # Detectar sensores con comportamiento anómalo
            for sensor_id, sensor_stats in stats.items():
                # Verificar que tenemos las estadísticas necesarias
                if not all(key in sensor_stats for key in ['std', 'outliers_count']):
                    continue
                    
                if sensor_stats['std'] > 1.0:  # Alta variabilidad
                    sheet_anomalies.append({
                        'sensor_id': sensor_id,
                        'issue': 'Alta variabilidad',
                        'std': sensor_stats['std'],
                        'severity': 'MEDIUM'
                    })
                
                sensor_readings = len(df[df['sensor_id'] == sensor_id])
                if sensor_readings > 0 and sensor_stats['outliers_count'] > sensor_readings * 0.1:
                    sheet_anomalies.append({
                        'sensor_id': sensor_id,
                        'issue': 'Muchos outliers',
                        'outliers_count': sensor_stats['outliers_count'],
                        'total_readings': sensor_readings,
                        'outlier_percentage': (sensor_stats['outliers_count'] / sensor_readings) * 100,
                        'severity': 'HIGH'
                    })
            
            if sheet_anomalies:
                anomalies[sheet_name] = sheet_anomalies
                
        return anomalies

    def get_summary_report(self) -> Dict:
        """Genera un reporte resumen de la transformación"""
        summary = {
            'total_sheets': len(self.transformed_data),
            'sheets_with_data': sum(1 for data in self.transformed_data.values() if not data['data'].empty),
            'total_transformed_records': 0,
            'sheets_processed': list(self.transformed_data.keys()),
            'processing_errors': []
        }
        
        for sheet_name, data in self.transformed_data.items():
            if not data['data'].empty:
                summary['total_transformed_records'] += len(data['data'])
            else:
                summary['processing_errors'].append(f"{sheet_name}: Sin datos estructurados")
        
        # Añadir análisis cruzado si está disponible
        if self.analysis_results.get('cross_sheet'):
            summary.update(self.analysis_results['cross_sheet'])
        
        return summary

if __name__ == "__main__":
    # Ejemplo de uso
    transformer = DataTransformer()
    # Aquí puedes añadir código de prueba si es necesario
    logger.info("DataTransformer class cargada correctamente")