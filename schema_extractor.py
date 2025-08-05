import sqlite3
import json
import os


class SchemaExtractor:
    def __init__(self, db_type, **kwargs):
        self.db_type = db_type.lower()
        self.conn_params = kwargs

    def extract_schema(self):
        """
        Veritabanı türüne göre ilgili şema çıkarma metodunu çağırır.

        Returns:
            dict: Veritabanı şeması. 
                  Format: {'tablo_adi': {'columns': ['sutun1', 'sutun2']}}
        """
        if self.db_type == 'json':
            return self._extract_json_schema()
        elif self.db_type == 'multi_json':
            return self._extract_multi_json_schema()
        elif self.db_type == 'sqlite':
            return self._extract_sqlite_schema()
        else:
            raise ValueError(f"Desteklenmeyen veritabanı türü: {self.db_type}")

    def _extract_sqlite_schema(self):
        db_path = self.conn_params.get('db_path')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = [col[1] for col in cursor.fetchall()]
            schema[table] = {'columns': columns}
            
        conn.close()
        return schema


    def _extract_json_schema(self):
        """JSON dosyasından şema çıkarır."""
        db_path = self.conn_params.get('db_path')
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            table_name = os.path.splitext(os.path.basename(db_path))[0]
            
            if isinstance(data, list):
                if not data:
                    return {table_name: {'columns': []}}
                
                if isinstance(data[0], dict):
                    columns = list(data[0].keys())
                    return {table_name: {'columns': columns}}
                else:
                    return {table_name: {'columns': ['value']}}
                    
            elif isinstance(data, dict):
                if all(isinstance(v, list) for v in data.values()):
                    schema = {}
                    for key, table_data in data.items():
                        if table_data and isinstance(table_data[0], dict):
                            columns = list(table_data[0].keys())
                            schema[key] = {'columns': columns}
                        else:
                            schema[key] = {'columns': ['value']}
                    return schema
                else:
                    columns = list(data.keys())
                    return {table_name: {'columns': columns}}
            
            return {table_name: {'columns': []}}
            
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON dosyası bulunamadı: {db_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Geçersiz JSON formatı: {e}")
        except Exception as e:
            raise IOError(f"JSON dosyası okunurken hata oluştu: {e}")

    def _extract_multi_json_schema(self):
        """Birden fazla JSON dosyasından ayrı tablolar şeklinde şema çıkarır."""
        file_paths = self.conn_params.get('file_paths', [])
        if not file_paths:
            return {}
        
        schema = {}
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                table_name = os.path.splitext(os.path.basename(file_path))[0]
                
                if isinstance(data, list) and data:
                    if isinstance(data[0], dict):
                        columns = list(data[0].keys())
                        schema[table_name] = {'columns': columns}
                    else:
                        schema[table_name] = {'columns': ['value']}
                        
                elif isinstance(data, dict):
                    if all(isinstance(v, list) for v in data.values()):
                        for sub_table_name, table_data in data.items():
                            full_table_name = f"{table_name}_{sub_table_name}"
                            if table_data and isinstance(table_data[0], dict):
                                columns = list(table_data[0].keys())
                                schema[full_table_name] = {'columns': columns}
                            else:
                                schema[full_table_name] = {'columns': ['value']}
                    else:
                        columns = list(data.keys())
                        schema[table_name] = {'columns': columns}
                else:
                    schema[table_name] = {'columns': ['data']}
                        
            except Exception as e:
                print(f"JSON dosyası şema çıkarma hatası ({file_path}): {e}")
                table_name = os.path.splitext(os.path.basename(file_path))[0]
                schema[table_name] = {'columns': ['error']}
                continue
        
        return schema