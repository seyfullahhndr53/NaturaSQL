
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QSettings

class QueryHistoryManager:
    """Sorgu geçmişi yönetimi"""
    
    def __init__(self):
        self.db_path = "data/query_history.db"
        self._init_database()
    
    def _init_database(self):
        """Veritabanını başlat"""
        Path("data").mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                database_name TEXT,
                execution_time REAL,
                result_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_favorite BOOLEAN DEFAULT FALSE,
                tags TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_query(self, question, sql, db_name=None, exec_time=None, result_count=0, tags=None):
        """Sorgu geçmişine ekle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO query_history 
            (question, generated_sql, database_name, execution_time, result_count, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (question, sql, db_name, exec_time, result_count, json.dumps(tags) if tags else None))
        
        conn.commit()
        conn.close()
    
    def get_recent_queries(self, limit=20):
        """Son sorguları getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM query_history 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_favorites(self):
        """Favori sorguları getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM query_history 
            WHERE is_favorite = TRUE 
            ORDER BY created_at DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def toggle_favorite(self, query_id):
        """Favori durumunu değiştir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE query_history 
            SET is_favorite = NOT is_favorite 
            WHERE id = ?
        """, (query_id,))
        
        conn.commit()
        conn.close()
    
    def search_queries(self, search_term):
        """Sorgu geçmişinde ara"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM query_history 
            WHERE question LIKE ? OR generated_sql LIKE ?
            ORDER BY created_at DESC
        """, (f"%{search_term}%", f"%{search_term}%"))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_statistics(self):
        """İstatistikleri getir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM query_history")
        total_queries = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT database_name, COUNT(*) as usage_count 
            FROM query_history 
            WHERE database_name IS NOT NULL
            GROUP BY database_name 
            ORDER BY usage_count DESC 
            LIMIT 1
        """)
        most_used_db = cursor.fetchone()
        
        cursor.execute("""
            SELECT AVG(execution_time) 
            FROM query_history 
            WHERE execution_time IS NOT NULL
        """)
        avg_exec_time = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_queries": total_queries,
            "most_used_database": most_used_db[0] if most_used_db else "N/A",
            "average_execution_time": round(avg_exec_time, 2) if avg_exec_time else 0
        }

class AutoCompleteManager:
    """Otomatik tamamlama yöneticisi"""
    
    def __init__(self):
        self.suggestions_file = "data/suggestions.json"
        self.suggestions = self._load_suggestions()
        
    def _load_suggestions(self):
        """Önerileri yükle"""
        try:
            with open(self.suggestions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_suggestions()
    
    def _create_default_suggestions(self):
        """Varsayılan önerileri oluştur"""
        default_suggestions = {
            "tr": [
                "Tüm verileri göster",
                "En yüksek değerli kayıtları listele",
                "Son eklenen kayıtları getir",
                "Toplam sayıyı hesapla",
                "Ortalama değeri bul",
                "Gruplara göre sayıları göster",
                "Boş olmayan kayıtları filtrele",
                "Tarihe göre sırala",
                "Benzersiz değerleri listele",
                "En popüler öğeleri göster"
            ],
            "en": [
                "Show all data",
                "List highest value records",
                "Get recently added records", 
                "Calculate total count",
                "Find average value",
                "Show counts by groups",
                "Filter non-empty records",
                "Sort by date",
                "List unique values",
                "Show most popular items"
            ]
        }
        
        Path("data").mkdir(exist_ok=True)
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(default_suggestions, f, indent=2, ensure_ascii=False)
        
        return default_suggestions
    
    def get_suggestions(self, text, language="tr", limit=10):
        """Metin için öneriler getir"""
        lang_suggestions = self.suggestions.get(language, [])
        
        if not text:
            return lang_suggestions[:limit]
        
        matching_suggestions = []
        text_lower = text.lower()
        
        for suggestion in lang_suggestions:
            if text_lower in suggestion.lower():
                matching_suggestions.append(suggestion)
        
        return matching_suggestions[:limit]
    
    def add_suggestion(self, suggestion, language="tr"):
        """Yeni öneri ekle"""
        if language not in self.suggestions:
            self.suggestions[language] = []
        
        if suggestion not in self.suggestions[language]:
            self.suggestions[language].append(suggestion)
            self._save_suggestions()
    
    def _save_suggestions(self):
        """Önerileri kaydet"""
        with open(self.suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(self.suggestions, f, indent=2, ensure_ascii=False)

class PerformanceMonitor:
    """Performans izleme sistemi"""
    
    def __init__(self):
        self.settings = QSettings("NaturaSQL", "Performance")
        self.metrics = {}
    
    def start_timer(self, operation):
        """Zamanlayıcı başlat"""
        self.metrics[operation] = {"start": datetime.now()}
    
    def end_timer(self, operation):
        """Zamanlayıcı bitir"""
        if operation in self.metrics:
            end_time = datetime.now()
            start_time = self.metrics[operation]["start"]
            duration = (end_time - start_time).total_seconds()
            
            self.metrics[operation]["duration"] = duration
            self.metrics[operation]["end"] = end_time
            
            self._save_metric(operation, duration)
            
            return duration
        return None
    
    def _save_metric(self, operation, duration):
        """Metriği kaydet"""
        history_key = f"history_{operation}"
        history = self.settings.value(history_key, [])
        
        if not isinstance(history, list):
            history = []
        
        history.append({
            "timestamp": datetime.now().isoformat(),
            "duration": duration
        })
        
        history = history[-100:]
        self.settings.setValue(history_key, history)
    
    def get_performance_report(self):
        """Performans raporu getir"""
        report = {}
        
        for operation in ["query_generation", "sql_execution", "data_loading"]:
            history_key = f"history_{operation}"
            history = self.settings.value(history_key, [])
            
            if history:
                durations = [item["duration"] for item in history if isinstance(item, dict)]
                if durations:
                    report[operation] = {
                        "count": len(durations),
                        "average": sum(durations) / len(durations),
                        "min": min(durations),
                        "max": max(durations),
                        "last": durations[-1] if durations else 0
                    }
        
        return report
    
    def clear_metrics(self):
        """Metrikleri temizle"""
        self.settings.clear()

class ExportManager:
    """Dışa aktarma yöneticisi"""
    
    @staticmethod
    def export_to_excel(data, file_path, headers=None, sheet_name="Query Results"):
        """Excel'e aktar"""
        try:
            import pandas as pd
            
            if headers:
                df = pd.DataFrame(data, columns=headers)
            else:
                df = pd.DataFrame(data)
            
            df.to_excel(file_path, sheet_name=sheet_name, index=False)
            return True
        except ImportError:
            raise ImportError("pandas kütüphanesi bulunamadı. Excel export için pandas gerekli.")
    
    @staticmethod
    def export_to_json(data, file_path, headers=None):
        """JSON'a aktar"""
        if headers:
            json_data = []
            for row in data:
                json_data.append(dict(zip(headers, row)))
        else:
            json_data = data
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return True

class ShortcutManager:
    """Kısayol tuşları yöneticisi"""
    
    def __init__(self):
        self.shortcuts = {
            "run_query": "Ctrl+Return",
            "load_data": "Ctrl+O", 
            "clear_query": "Ctrl+K",
            "new_tab": "Ctrl+T",
            "close_tab": "Ctrl+W",
            "save_query": "Ctrl+S",
            "search_history": "Ctrl+H",
            "toggle_theme": "Ctrl+Shift+T",
            "show_help": "F1",
            "quit": "Ctrl+Q"
        }
    
    def get_shortcut(self, action):
        """Kısayol tuşunu getir"""
        return self.shortcuts.get(action, "")
    
    def set_shortcut(self, action, shortcut):
        """Kısayol tuşunu ayarla"""
        self.shortcuts[action] = shortcut
    
    def get_all_shortcuts(self):
        """Tüm kısayolları getir"""
        return self.shortcuts.copy()