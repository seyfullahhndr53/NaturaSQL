import sqlite3
import json
import os


class DBConnector:
    def __init__(self, db_type, **kwargs):
        self.db_type = db_type.lower()
        self.conn_params = kwargs
        self.is_json = self.db_type == 'json'
        self.is_multi_json = self.db_type == 'multi_json'

    def _get_new_connection(self):
        """Her çağrıldığında yeni bir veritabanı bağlantısı döndürür."""
        if self.db_type == 'sqlite':
            db_path = self.conn_params.get('db_path')
            if not db_path or not os.path.exists(db_path):
                raise FileNotFoundError(f"SQLite dosyası bulunamadı: {db_path}")
            return sqlite3.connect(db_path)
        else:
            raise ValueError(f"Desteklenmeyen veritabanı türü: {self.db_type}")

    def test_connection(self):
        """Bağlantı parametrelerinin geçerli olup olmadığını test eder."""
        if self.is_json:
            db_path = self.conn_params.get('db_path')
            if not db_path or not os.path.exists(db_path):
                raise FileNotFoundError(f"JSON dosyası bulunamadı: {db_path}")
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Geçersiz JSON formatı: {e}")
            return True
        
        if self.is_multi_json:
            file_paths = self.conn_params.get('file_paths', [])
            if not file_paths:
                raise ValueError("Hiç JSON dosyası seçilmedi")
            
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"JSON dosyası bulunamadı: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Geçersiz JSON formatı ({file_path}): {e}")
            return True
        
        conn = None
        try:
            conn = self._get_new_connection()
            return True
        finally:
            if conn:
                conn.close()

    def execute_query(self, query):
        """
        Bir SQL sorgusunu çalıştırır. Her seferinde yeni bir bağlantı kurar ve kapatır.
        """
        if self.is_json:
            return self._query_json(query)
        
        if self.is_multi_json:
            return self._query_multi_json(query)

        if self.db_type == 'sqlite':
            return self._query_sqlite_optimized(query)
        
        conn = None
        try:
            conn = self._get_new_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return columns, rows
        finally:
            if conn:
                conn.close()

    def _query_sqlite_optimized(self, query):
        """🚀 ULTRA HIZLI SQLite - Büyük veritabanları için"""
        print(f"🚀 HIZLI SQLite modu başlatılıyor...")
        
        conn = None
        try:
            conn = self._get_new_connection()
            
            conn.execute("PRAGMA journal_mode = MEMORY")  # Disk yazımı azalt
            conn.execute("PRAGMA synchronous = OFF")      # Sync kapalı  
            conn.execute("PRAGMA cache_size = 10000")     # Büyük cache
            conn.execute("PRAGMA temp_store = MEMORY")    # Temp memory'de
            
            cursor = conn.cursor()
            
            print(f"🔍 Sorgu çalıştırılıyor...")
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            if not columns:
                return [], []
            
            rows = []
            batch_size = 10000  # 10K batch - çok daha büyük!
            max_total = 100000  # 100K satıra kadar
            
            while len(rows) < max_total:
                batch = cursor.fetchmany(batch_size)
                if not batch:
                    break
                    
                rows.extend(batch)
                
                if len(rows) % 25000 == 0:
                    print(f"⚡ {len(rows):,} satır yüklendi...")
            
            print(f"🚀 HIZLI YÜKLEME: {len(rows):,} satır {len(columns)} sütun")
            return columns, rows
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            try:
                cursor = conn.cursor()
                cursor.execute(f"{query} LIMIT 20000")  # 20K limit
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                print(f"🛡️ Fallback: {len(rows)} satır")
                return columns, rows
            except:
                return ['hata'], [['Sorgu çalıştırılamadı']]
            
        finally:
            if conn:
                conn.close()

    def _query_json(self, query):
        """JSON dosyasından gerçek veri oku"""
        if not query.strip().lower().startswith('select'):
            raise NotImplementedError("JSON dosyalarında sadece SELECT sorguları desteklenir.")
        
        db_path = self.conn_params.get('db_path')
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON dosyası okundu: {os.path.basename(db_path)}")
            
            if isinstance(data, list) and data:
                if isinstance(data[0], dict):
                    columns = list(data[0].keys())
                    rows = []
                    for item in data:
                        row = [item.get(col, '') for col in columns]
                        rows.append(row)
                    return columns, rows
                else:
                    columns = ['value']
                    rows = [[str(item)] for item in data]
                    return columns, rows
                    
            elif isinstance(data, dict):
                columns = list(data.keys())
                rows = [list(data.values())]
                return columns, rows
            
            return ['veri'], [[str(data)]]
            
        except Exception as e:
            print(f"❌ JSON okuma hatası: {e}")
            return ['hata'], [[f"JSON okuma hatası: {str(e)}"]]

    def _query_multi_json(self, query):
        """Birden fazla JSON dosyasından belirli tabloya göre veri oku"""
        if not query.strip().lower().startswith('select'):
            raise NotImplementedError("JSON dosyalarında sadece SELECT sorguları desteklenir.")
        
        file_paths = self.conn_params.get('file_paths', [])
        if not file_paths:
            return [], []
        
        query_lower = query.lower()
        target_table = None
        
        if 'from ' in query_lower:
            from_part = query_lower.split('from ')[1].split()[0]
            target_table = from_part.strip()
            print(f"🎯 Hedef tablo: {target_table}")
        
        print(f"✅ {len(file_paths)} JSON dosyası analiz ediliyor...")
        
        if target_table:
            return self._query_specific_json_table(target_table, file_paths)
        
        return self._query_all_json_files(file_paths)
    
    def _query_specific_json_table(self, target_table, file_paths):
        """Belirli bir JSON tablosundan veri oku"""
        for file_path in file_paths:
            try:
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                
                if file_name == target_table:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"✅ Hedef tablo bulundu: {file_name}")
                    return self._process_single_json_data(data, file_name)
                
                if target_table.startswith(f"{file_name}_"):
                    sub_table_name = target_table[len(file_name)+1:]
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and sub_table_name in data:
                        print(f"✅ Alt tablo bulundu: {file_name}_{sub_table_name}")
                        return self._process_single_json_data(data[sub_table_name], target_table)
                        
            except Exception as e:
                print(f"❌ {file_path} okuma hatası: {e}")
                continue
        
        print(f"❌ Tablo bulunamadı: {target_table}")
        return ['error'], [[f'Tablo bulunamadı: {target_table}']]
    
    def _query_all_json_files(self, file_paths):
        """Tüm JSON dosyalarını birleştirerek sorgula (eski davranış)"""
        all_columns = set()
        all_rows = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                print(f"✅ Okundu: {file_name}")
                
                self._process_json_data_optimized(data, file_name, all_columns, all_rows)
                
            except Exception as e:
                print(f"❌ {file_path} okuma hatası: {e}")
                continue
        
        if not all_columns or not all_rows:
            return ['dosya'], [['Hiç veri okunamadı']]
        
        columns = self._optimize_column_order(all_columns)
        
        formatted_rows = []
        for row_dict in all_rows:
            row = [str(row_dict.get(col, '')) for col in columns]
            formatted_rows.append(row)
        
        print(f"✅ Toplam {len(formatted_rows)} satır, {len(columns)} sütun hazırlandı")
        return columns, formatted_rows
    
    def _process_single_json_data(self, data, table_name):
        """Tek JSON veri yapısını işle"""
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                columns = list(data[0].keys())
                rows = []
                for item in data:
                    row = [item.get(col, '') for col in columns]
                    rows.append(row)
                return columns, rows
            else:
                columns = ['value']
                rows = [[str(item)] for item in data]
                return columns, rows
                
        elif isinstance(data, dict):
            columns = list(data.keys())
            rows = [list(data.values())]
            return columns, rows
        
        return ['data'], [[str(data)]]
    
    def _process_json_data_optimized(self, data, file_name, all_columns, all_rows):
        """JSON veriyi optimize edilmiş şekilde işler"""
        
        if isinstance(data, list) and data:
            first_item = data[0]
            
            if isinstance(first_item, dict):
                columns_from_first = set(first_item.keys())
                all_columns.update(columns_from_first)
                all_columns.add('_source_file')
                
                batch_size = 1000
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    for item in batch:
                        row_dict = {**item, '_source_file': file_name}
                        all_rows.append(row_dict)
            else:
                all_columns.update(['value', '_source_file'])
                for item in data:
                    all_rows.append({'value': item, '_source_file': file_name})
                    
        elif isinstance(data, dict):
            if self._is_multi_table_format(data):
                all_columns.add('_table')
                for table_name, table_data in data.items():
                    if isinstance(table_data, list) and table_data:
                        if isinstance(table_data[0], dict):
                            all_columns.update(table_data[0].keys())
                            
                            for item in table_data:
                                row_dict = {**item, '_source_file': file_name, '_table': table_name}
                                all_rows.append(row_dict)
                        else:
                            all_columns.update(['value', '_source_file', '_table'])
                            for item in table_data:
                                all_rows.append({
                                    'value': item, 
                                    '_source_file': file_name, 
                                    '_table': table_name
                                })
            else:
                all_columns.update(data.keys())
                row_dict = {**data, '_source_file': file_name}
                all_rows.append(row_dict)
    
    def _is_multi_table_format(self, data):
        """JSON'un multi-table formatında olup olmadığını kontrol eder"""
        if not isinstance(data, dict):
            return False
        
        for key, value in list(data.items())[:3]:
            if not isinstance(value, list):
                return False
        return True
    
    def _optimize_column_order(self, all_columns):
        """Sütunları optimize edilmiş sırayla döndürür"""
        columns = []
        
        for special_col in ['_source_file', '_table']:
            if special_col in all_columns:
                columns.append(special_col)
                all_columns.remove(special_col)
        
        columns.extend(sorted(all_columns))
        
        return columns