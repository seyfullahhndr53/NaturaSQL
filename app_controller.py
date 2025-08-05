import traceback
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

from nlp_engine import NLPEngine
from db_connector import DBConnector
from schema_extractor import SchemaExtractor
from prompt_builder import PromptBuilder

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn; self.args = args; self.kwargs = kwargs
        self.signals = WorkerSignals()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            error_trace = traceback.format_exc()
            self.signals.error.emit(type(e).__name__, str(e), error_trace)

class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str, str, str)

class AppController(QObject):
    schema_ready = pyqtSignal(dict, str)
    sql_generated = pyqtSignal(str)
    query_results_ready = pyqtSignal(list, list)
    error_occurred = pyqtSignal(str, str)
    status_changed = pyqtSignal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread_pool = QThreadPool(); self.thread_pool.setMaxThreadCount(4)
        self.db_connector = None; self.db_schema = None; self.db_type = None
        self.nlp_engine = NLPEngine(model='openhermes')
        self.status_changed.emit("Hazır. Bir veri kaynağı seçin.", False)

    def _run_task(self, task_function, on_finish, status_message, *args, **kwargs):
        self.status_changed.emit(status_message, True)
        worker = Worker(task_function, *args, **kwargs)
        worker.signals.finished.connect(on_finish)
        worker.signals.error.connect(self._on_task_error)
        self.thread_pool.start(worker)

    def _on_task_error(self, error_type, message, error_trace):
        print(f"HATA OLUŞTU:\n{error_trace}")
        self.error_occurred.emit(f"{error_type} Hatası", message)
        self.status_changed.emit(f"Hata: {message}", False)

    def load_database(self, db_type, params):
        self.db_type = db_type
        
        def task():
            self.db_connector = DBConnector(db_type, **params)
            
            self.db_connector.test_connection() 
            
            schema_extractor = SchemaExtractor(db_type, **params)
            schema = schema_extractor.extract_schema()
            return schema

        self._run_task(task, self._on_schema_extracted, "Veritabanı kontrol ediliyor ve şema çıkarılıyor...")

    def _on_schema_extracted(self, schema):
        self.db_schema = schema
        display_text = ""
        for table, details in schema.items():
            display_text += f"TABLE: {table}\n  - COLUMNS: {', '.join(details['columns'])}\n\n"
        self.schema_ready.emit(schema, display_text.strip())
        self.status_changed.emit("Veritabanı başarıyla yüklendi. Şimdi bir soru sorabilirsiniz.", False)

    def process_natural_language_question(self, question):
        if not self.db_connector or not self.db_schema:
            self.error_occurred.emit("İşlem Hatası", "Lütfen önce bir veritabanı yükleyin.")
            return

        def generate_sql_task():
            prompt = PromptBuilder.build(self.db_schema, question, self.db_type)
            sql_query = self.nlp_engine.generate_sql(prompt)
            return sql_query
        
        self._run_task(generate_sql_task, self._on_sql_generated, "Yapay zekâ SQL sorgusunu üretiyor...")

    def _validate_sql_query(self, sql_query):
        """SQL sorgusunu güvenlik açısından kontrol eder"""
        if not sql_query or not sql_query.strip():
            raise ValueError("Boş SQL sorgusu")
        
        sql_upper = sql_query.upper().strip()
        
        if not sql_upper.startswith('SELECT'):
            raise ValueError("Güvenlik nedeniyle sadece SELECT sorguları desteklenir")
        
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
            'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE', 'MERGE',
            'CALL', 'REPLACE', 'LOAD', 'OUTFILE', 'DUMPFILE'
        ]
        
        for keyword in dangerous_keywords:
            if f' {keyword} ' in f' {sql_upper} ' or sql_upper.endswith(f' {keyword}'):
                raise ValueError(f"Güvenlik nedeniyle '{keyword}' komutu yasaklı")
        
        statements = [s.strip() for s in sql_query.split(';') if s.strip()]
        if len(statements) > 1:
            raise ValueError("Güvenlik nedeniyle tek SQL sorgusu desteklenir")
        
        injection_patterns = ['--', '/*', '*/', 'xp_', 'sp_']
        for pattern in injection_patterns:
            if pattern in sql_query:
                raise ValueError(f"Güvenlik nedeniyle '{pattern}' pattern'i yasaklı")
        
        return True

    def _on_sql_generated(self, sql_query):
        if '```sql' in sql_query:
            sql_query = sql_query.split('```sql')[1].split('```')[0].strip()
        elif '```' in sql_query:
            sql_query = sql_query.replace('```', '').strip()

        if not sql_query:
            self._on_task_error("Yapay Zekâ Hatası", "Model boş bir SQL sorgusu döndürdü.", "Boş yanıt")
            return

        try:
            self._validate_sql_query(sql_query)
        except ValueError as e:
            self._on_task_error("Güvenlik Hatası", str(e), f"SQL: {sql_query}")
            return

        self.sql_generated.emit(sql_query)

        def execute_query_task():
            return self.db_connector.execute_query(sql_query)

        self._run_task(execute_query_task, self._on_query_executed, "SQL sorgusu çalıştırılıyor...")

    def _on_query_executed(self, results):
        headers, data = results
        self.query_results_ready.emit(headers, data)
        self.status_changed.emit(f"Sorgu başarıyla tamamlandı. {len(data)} sonuç bulundu.", False)

    def cleanup(self):
        """Uygulama kapanırken yapılacak temizlik."""
        self.thread_pool.clear()
        print("Kontrolcü temizlendi ve kaynaklar serbest bırakıldı.")