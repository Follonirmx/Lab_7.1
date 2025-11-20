# extract.py
import pandas as pd
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self):
        """Inicializa el extractor de datos"""
        # No necesita file_path en el constructor
        pass
    
    def extract_from_excel(self, file_path: str) -> Dict:
        """
        Extrae datos de un archivo Excel con múltiples hojas
        
        Args:
            file_path: Ruta al archivo Excel
            
        Returns:
            Dict con los datos de cada hoja
        """
        try:
            logger.info(f"Leyendo archivo Excel: {file_path}")
            
            # Leer todas las hojas del Excel
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            logger.info(f"Hojas encontradas: {sheet_names}")
            
            raw_data = {}
            
            for sheet_name in sheet_names:
                try:
                    logger.info(f"Extrayendo datos de {sheet_name}")
                    
                    # Leer hoja completa
                    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                    
                    raw_data[sheet_name] = {
                        'data': df,
                        'dimensions': df.shape,
                        'columns': df.columns.tolist()
                    }
                    
                    logger.info(f"  ✓ {sheet_name}: {df.shape[0]} filas, {df.shape[1]} columnas")
                    
                except Exception as e:
                    logger.error(f"  ✗ Error extrayendo {sheet_name}: {e}")
                    raw_data[sheet_name] = {
                        'data': pd.DataFrame(),
                        'error': str(e)
                    }
            
            logger.info(f"Extracción completada. {len([d for d in raw_data.values() if not d['data'].empty])} hojas procesadas")
            return raw_data
            
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error en extracción: {e}")
            raise
    
    def validate_data_structure(self, raw_data: Dict) -> bool:
        """
        Valida la estructura básica de los datos extraídos
        """
        if not raw_data:
            logger.error("No hay datos para validar")
            return False
        
        valid_sheets = 0
        for sheet_name, sheet_data in raw_data.items():
            if not sheet_data['data'].empty:
                valid_sheets += 1
                logger.info(f"  ✓ {sheet_name}: válida")
            else:
                logger.warning(f"  ✗ {sheet_name}: vacía o con error")
        
        logger.info(f"Validación: {valid_sheets} hojas válidas de {len(raw_data)}")
        return valid_sheets > 0

if __name__ == "__main__":
    # Ejemplo de uso
    extractor = DataExtractor()
    data = extractor.extract_from_excel(r"C:\Users\LENOVO\Downloads\ETL\data\BD_SENSORES.xlsx")
    print(f"Extraídas {len(data)} hojas")