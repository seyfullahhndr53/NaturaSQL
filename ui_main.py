import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QLabel, QComboBox, QSplitter, QMenuBar, QMenu, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QRadioButton, QButtonGroup,
    QStatusBar, QProgressBar, QFrame
)
from PyQt6.QtGui import QIcon, QMovie, QAction, QFont
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QThread, pyqtSignal

from app_controller import AppController
from theme_manager import ThemeManager
from ui_animations import AnimationManager, LoadingSpinner
from features_manager import QueryHistoryManager, AutoCompleteManager

TRANSLATIONS = {
    "en": { "window_title": "NaturaSQL - NL to SQL", "load_data": "Load Data", "run_query": "Run Query", "question_placeholder": "Type your question here...", "db_schema_label": "Database Schema", "results_label": "Query Results", "sql_label": "Generated SQL", "status_ready": "Ready. Load data.", "error_title": "Error", "no_results": "Query returned no results.", "conn_success": "Connected.", "empty_question": "Please enter a question.", "no_db_loaded": "Please load a database first.", "db_conn_dialog_title": "Select Database" },
    "tr": { "window_title": "NaturaSQL - Doğal Dilden SQL'e", "load_data": "Veri Yükle", "run_query": "Sorguyu Çalıştır", "question_placeholder": "Sorunuzu buraya yazın...", "db_schema_label": "Veritabanı Şeması", "results_label": "Sorgu Sonuçları", "sql_label": "Üretilen SQL", "status_ready": "Hazır. Veri yükleyin.", "error_title": "Hata", "no_results": "Sorgu sonuç döndürmedi.", "conn_success": "Bağlandı.", "empty_question": "Lütfen bir soru girin.", "no_db_loaded": "Önce veritabanı yükleyin.", "db_conn_dialog_title": "Veritabanı Seç" }
}

class DbConnectionDialog(QDialog):
    def __init__(self, current_lang="tr", parent=None):
        super().__init__(parent)
        self.setWindowTitle(TRANSLATIONS[current_lang]["db_conn_dialog_title"])
        self.setWindowIcon(QIcon(parent.get_asset_path("database.svg")) if parent else QIcon())
        self.setModal(True); self.db_type = None; self.params = {}
        layout = QVBoxLayout(self)
        self.file_radio = QRadioButton("Tekil Dosya (SQLite / JSON)"); self.multi_json_radio = QRadioButton("Çoklu JSON Dosyası")
        self.file_radio.setChecked(True)
        
        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.file_radio); self.radio_group.addButton(self.multi_json_radio)
        
        radio_layout = QHBoxLayout(); radio_layout.addWidget(self.file_radio); radio_layout.addWidget(self.multi_json_radio)
        layout.addLayout(radio_layout)
        
        self.form_widget = QWidget(); form = QFormLayout(self.form_widget)
        self.host = QLineEdit(); self.port = QLineEdit(); self.user = QLineEdit(); self.password = QLineEdit(); self.dbname = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password); self.port.setPlaceholderText("örn: 5432")
        form.addRow("Host:", self.host); form.addRow("Port:", self.port); form.addRow("Kullanıcı:", self.user); form.addRow("Şifre:", self.password); form.addRow("Veritabanı:", self.dbname)
        layout.addWidget(self.form_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.radio_group.buttonToggled.connect(self.toggle_form)
        self.toggle_form(self.file_radio, True)

    def toggle_form(self, button, checked):
        if not checked:
            return
        is_server_based = False
        self.form_widget.setVisible(is_server_based)
        
    def get_result(self):
        if self.file_radio.isChecked(): return 'file', {}
        elif self.multi_json_radio.isChecked(): return 'multi_json', {}
        return None, {}

class MainWindow(QMainWindow):
    def __init__(self, icons_path: str):
        super().__init__()
        self.icons_path = icons_path
        self.current_lang = "tr"
        self.controller = AppController()
        
        self.theme_manager = ThemeManager()
        self.animation_manager = AnimationManager()
        self.query_history = QueryHistoryManager()
        self.autocomplete = AutoCompleteManager()
        
        self.loading_spinner = None
        self.progress_bar = None
        
        self.preview_data = []
        self.preview_headers = []
        self.MAX_PREVIEW_ROWS = 100000
        
        self.init_ui()
        self.init_menu_bar()
        self.init_status_bar()
        self.connect_signals()
        self.apply_modern_theme()
        self.show_startup_animation()

    def get_asset_path(self, asset_name: str) -> str:
        return os.path.join(self.icons_path, asset_name)

    def init_ui(self):
        self.setWindowTitle(TRANSLATIONS[self.current_lang]["window_title"])
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
        self.apply_stylesheet()
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        top_bar_layout = QHBoxLayout()
        self.load_data_button = QPushButton()
        self.load_data_button.setIcon(QIcon(self.get_asset_path("upload.svg")))
        self.load_data_button.clicked.connect(self.handle_load_data)
        top_bar_layout.addWidget(self.load_data_button)
        self.run_query_button = QPushButton()
        self.run_query_button.setIcon(QIcon(self.get_asset_path("play.svg")))
        self.run_query_button.setObjectName("runButton")
        self.load_data_button.setObjectName("loadButton")
        self.run_query_button.clicked.connect(self.handle_run_query)
        top_bar_layout.addWidget(self.run_query_button)
        top_bar_layout.addStretch()
        self.lang_combo = QComboBox(); self.lang_combo.addItems(["Türkçe", "English"])
        self.lang_combo.currentIndexChanged.connect(self.switch_language)
        top_bar_layout.addWidget(QLabel("Dil / Language:")); top_bar_layout.addWidget(self.lang_combo)
        main_layout.addLayout(top_bar_layout)
        main_splitter = QSplitter(Qt.Orientation.Horizontal); main_layout.addWidget(main_splitter, 1)
        left_panel = QWidget(); left_layout = QVBoxLayout(left_panel)
        self.schema_label = QLabel(); self.schema_label.setObjectName("Header")
        self.schema_display = QTextEdit(); self.schema_display.setReadOnly(True)
        self.question_input = QTextEdit(); self.question_input.setFixedHeight(150)
        left_layout.addWidget(self.schema_label); left_layout.addWidget(self.schema_display); left_layout.addWidget(self.question_input)
        main_splitter.addWidget(left_panel)
        right_panel = QWidget(); right_layout = QVBoxLayout(right_panel)
        self.results_label = QLabel(); self.results_label.setObjectName("Header")
        
        self.results_table = QTableWidget()
        self.results_table.setMinimumHeight(600)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.verticalHeader().setDefaultSectionSize(30)
        
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSortingEnabled(False)
        self.results_table.setWordWrap(False)
        
        self.results_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.results_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.results_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        
        self.apply_table_theme()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        self.results_text.setVisible(False)  # Başlangıçta gizli
        
        self.sql_label = QLabel(); self.sql_label.setObjectName("SubHeader")
        self.generated_sql_display = QTextEdit(); self.generated_sql_display.setReadOnly(True); self.generated_sql_display.setMinimumHeight(150)  # SQL kutusu büyütüldü
        right_layout.addWidget(self.results_label)
        right_layout.addWidget(self.results_table)  # Tablo görüntüleme
        right_layout.addWidget(self.results_text)   # Yedek metin görüntüleme
        right_layout.addWidget(self.sql_label)
        right_layout.addWidget(self.generated_sql_display)
        main_splitter.addWidget(right_panel); main_splitter.setSizes([250, 950])  # Sağ panele çok daha fazla alan
        
        right_layout.setStretchFactor(self.results_table, 10)  # Tabloya en çok alan ver
        right_layout.setStretchFactor(self.generated_sql_display, 1)  # SQL kutusuna az alan
        self.status_bar = self.statusBar(); self.status_label = QLabel()
        self.loading_label = QLabel(); self.loading_movie = QMovie(self.get_asset_path("loader.gif"))
        self.loading_label.setMovie(self.loading_movie)
        self.status_bar.addPermanentWidget(self.status_label); self.status_bar.addPermanentWidget(self.loading_label)
        self.update_ui_text()

    def connect_signals(self):
        self.controller.status_changed.connect(self.on_status_changed)
        self.controller.error_occurred.connect(self.on_error_occurred)
        self.controller.schema_ready.connect(self.on_schema_ready)
        self.controller.sql_generated.connect(self.on_sql_generated)
        self.controller.query_results_ready.connect(self.on_query_results_ready)

    def handle_load_data(self):
        dialog = DbConnectionDialog(self.current_lang, self)
        if not dialog.exec(): return
        db_type, params = dialog.get_result()
        if db_type == 'file':
            file_path, _ = QFileDialog.getOpenFileName(self, "Veritabanı veya JSON Seçin", "", "Tüm Desteklenen Dosyalar (*.sqlite *.db *.json);;SQLite (*.sqlite *.db);;JSON (*.json)")
            if not file_path: return
            params['db_path'] = file_path
            if file_path.endswith(('.sqlite', '.db')):
                db_type = 'sqlite'
            elif file_path.endswith('.json'):
                db_type = 'json'
            else:
                self.on_error_occurred("Hata", "Desteklenmeyen dosya formatı!")
                return
        elif db_type == 'multi_json':
            file_paths, _ = QFileDialog.getOpenFileNames(self, "JSON Dosyalarını Seçin", "", "JSON Files (*.json)")
            if not file_paths: return
            
            total_size = 0
            large_files = []
            
            for file_path in file_paths:
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        large_files.append(f"{os.path.basename(file_path)} ({file_size/1024/1024:.1f}MB)")
                except:
                    continue
            
            if large_files or total_size > 50 * 1024 * 1024:
                warning_msg = f"⚠️ Büyük dosyalar tespit edildi:\n"
                if large_files:
                    warning_msg += "\n".join(large_files) + "\n"
                warning_msg += f"\nToplam boyut: {total_size/1024/1024:.1f}MB"
                warning_msg += "\n\nİşlem biraz zaman alabilir. Devam edilsin mi?"
                
                reply = QMessageBox.question(self, "Büyük Dosya Uyarısı", warning_msg,
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                           QMessageBox.StandardButton.Yes)
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            params['file_paths'] = file_paths
            db_type = 'multi_json'
        self.controller.load_database(db_type, params)

    def handle_run_query(self):
        question = self.question_input.toPlainText().strip()
        if not question:
            self.on_error_occurred(TRANSLATIONS[self.current_lang]["error_title"], TRANSLATIONS[self.current_lang]["empty_question"])
            return
        
        self.start_modern_loading("Sorgu işleniyor...")
        
        QTimer.singleShot(100, lambda: self.query_history.add_query(question, "", "temp"))
        
        self.animation_manager.pulse_effect(self.run_query_button, 300, 1)
        self.animation_manager.typewriter_effect(self.generated_sql_display, "SQL üretiliyor...", 30)
        
        self.controller.process_natural_language_question(question)

    @pyqtSlot(str, bool)
    def on_status_changed(self, message, is_loading):
        if is_loading:
            self.start_modern_loading(message)
        else:
            self.stop_modern_loading(message)

    @pyqtSlot(str, str)
    def on_error_occurred(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
        msg.setText(message)
        msg.exec()

    @pyqtSlot(dict, str)
    def on_schema_ready(self, schema_dict, display_text):
        self.schema_display.setText(display_text)
        self.results_table.clearContents()  # Tablo temizle
        self.results_table.setRowCount(0)
        self.results_table.setColumnCount(0)
        self.generated_sql_display.clear(); self.question_input.clear()

    @pyqtSlot(str)
    def on_sql_generated(self, sql_query):
        self.animation_manager.typewriter_effect(self.generated_sql_display, sql_query, 25)
        
        question = self.question_input.toPlainText().strip()
        if question:
            self.query_history.add_query(question, sql_query)

    @pyqtSlot(list, list)
    def on_query_results_ready(self, headers, data):
        self.stop_modern_loading("✅ Sorgu tamamlandı!")
        
        if not data:
            self.results_table.clearContents()
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return
        
        total_rows = len(data)
        
        if total_rows > self.MAX_PREVIEW_ROWS:
            data = data[:self.MAX_PREVIEW_ROWS]  
            display_msg = f"⚠️ Büyük veri: {total_rows:,} satırdan ilk {self.MAX_PREVIEW_ROWS:,} gösteriliyor"
        else:
            display_msg = f"✅ {total_rows:,} satır tamamı gösteriliyor"
        
        self.preview_data = data
        self.preview_headers = headers
        self.last_results = data  # Export için
        self.last_headers = headers
        
        self.display_data_as_safe_table()
        
        self.status_label.setText(display_msg)
    
    def display_data_as_safe_table(self):
        """TAM BOYUT TABLO - Tüm veriyi göster"""
        if not self.preview_data or not self.preview_headers:
            self.results_table.clearContents()
            self.results_table.setRowCount(0)
            self.results_table.setColumnCount(0)
            return
        
        total_rows = len(self.preview_data)
        total_cols = len(self.preview_headers)
        
        self.results_table.setRowCount(total_rows)
        self.results_table.setColumnCount(total_cols)
        
        self.results_table.setHorizontalHeaderLabels(self.preview_headers)
        
        try:
            print(f"🚀 {total_rows:,} satır, {total_cols} sütun tablo yükleniyor...")
            
            self.results_table.setSortingEnabled(False)
            self.results_table.setUpdatesEnabled(False)
            
            batch_size = 1000
            for batch_start in range(0, total_rows, batch_size):
                batch_end = min(batch_start + batch_size, total_rows)
                
                for row_idx in range(batch_start, batch_end):
                    row_data = self.preview_data[row_idx]
                    for col_idx in range(total_cols):
                        if col_idx < len(row_data):
                            cell_data = str(row_data[col_idx])[:500]  # 500 karakter max
                            
                            item = QTableWidgetItem(cell_data)
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            self.results_table.setItem(row_idx, col_idx, item)
                        else:
                            item = QTableWidgetItem("")
                            self.results_table.setItem(row_idx, col_idx, item)
                
                if batch_end % 5000 == 0:
                    print(f"⚡ {batch_end:,} satır yüklendi...")
            
            self.results_table.setUpdatesEnabled(True)
            
            for col in range(min(10, total_cols)):  # İlk 10 sütun
                self.results_table.setColumnWidth(col, 150)  # Sabit genişlik
            
            self.results_table.horizontalHeader().setStretchLastSection(True)
            
            print(f"🚀 HIZLI YÜKLEME: {total_rows:,} satır, {total_cols} sütun TAM BOYUT!")
            
        except Exception as e:
            print(f"❌ Güvenli tablo hatası: {e}")
            self.results_table.setVisible(False)
            self.results_text.setVisible(True)
            self.display_data_as_simple_text()
    
    def display_data_as_simple_text(self):
        """SADECE 10 SATIR - Ultra minimal"""
        if not self.preview_data or not self.preview_headers:
            self.results_text.setPlainText("Veri yok.")
            return
        
        lines = []
        
        max_cols = min(3, len(self.preview_headers))
        headers = self.preview_headers[:max_cols]
        
        header_line = " | ".join([h[:15] for h in headers])
        lines.append(header_line)
        lines.append("-" * len(header_line))
        
        for i, row in enumerate(self.preview_data[:10]):
            row_parts = []
            for j in range(max_cols):
                if j < len(row):
                    cell_str = str(row[j])[:15]  # 15 karakter max
                    row_parts.append(cell_str)
                else:
                    row_parts.append("")
            
            line = " | ".join(row_parts)
            lines.append(f"{i+1}: {line}")
        
        total_rows = len(self.preview_data)
        if total_rows > 10:
            lines.append(f"\n... ve {total_rows - 10} satır daha var")
        
        lines.append(f"\nToplam: {total_rows} satır, {len(self.preview_headers)} sütun")
        
        result_text = "\n".join(lines)
        self.results_text.setPlainText(result_text)

    def switch_language(self, index):
        self.current_lang = "tr" if index == 0 else "en"; self.update_ui_text()

    def update_ui_text(self):
        lang = TRANSLATIONS[self.current_lang]
        self.setWindowTitle(lang["window_title"]); self.load_data_button.setText(lang["load_data"]); self.run_query_button.setText(lang["run_query"])
        self.question_input.setPlaceholderText(lang["question_placeholder"]); self.schema_label.setText(lang["db_schema_label"])
        self.results_label.setText(lang["results_label"]); self.sql_label.setText(lang["sql_label"]); self.status_label.setText(lang["status_ready"])
        
    def apply_stylesheet(self):
        pass
    
    def apply_modern_theme(self):
        """Modern tema sistemini uygula"""
        current_theme = self.theme_manager.get_current_theme()
        success = self.theme_manager.apply_theme(current_theme)
        
        if success:
            print(f"Modern tema uygulandı: {current_theme}")
        else:
            self.apply_basic_fallback_theme()
    
    def apply_basic_fallback_theme(self):
        """Yedek tema"""
        self.setStyleSheet("""
            QMainWindow, QDialog { background-color: #2c3e50; } QWidget { color: #ecf0f1; font-size: 10pt; }
            QLabel#Header { font-size: 12pt; font-weight: bold; color: #1abc9c; margin-top: 10px; margin-bottom: 5px; }
            QLabel#SubHeader { font-size: 10pt; font-weight: bold; color: #95a5a6; margin-top: 5px; }
            QPushButton { background-color: #3498db; color: white; border: none; padding: 10px 15px; border-radius: 5px; }
            QPushButton:hover { background-color: #2980b9; } QPushButton:disabled { background-color: #566573; }
            QPushButton#RunButton { background-color: #1abc9c; font-weight: bold; } QPushButton#RunButton:hover { background-color: #16a085; }
            QTextEdit, QTableWidget, QLineEdit { background-color: #34495e; border: 1px solid #2c3e50; border-radius: 5px; padding: 5px; }
            QTableWidget::item { padding: 5px; } QHeaderView::section { background-color: #3498db; color: white; padding: 5px; border: 1px solid #2c3e50; }
            QComboBox { padding: 5px; border-radius: 3px; background-color: #34495e; } QSplitter::handle { background-color: #2c3e50; }
            QSplitter::handle:horizontal { width: 5px; } QStatusBar { background-color: #34495e; } QRadioButton { margin: 5px; }
        """)
    
    def init_menu_bar(self):
        """Modern menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        theme_menu = menubar.addMenu('🎨 Tema')
        
        themes = self.theme_manager.get_available_themes()
        for theme_id, theme_info in themes.items():
            action = QAction(theme_info['name'], self)
            action.setStatusTip(theme_info['description'])
            action.triggered.connect(lambda checked, t=theme_id: self.change_theme(t))
            theme_menu.addAction(action)
        
        history_menu = menubar.addMenu('📚 Geçmiş')
        
        recent_action = QAction('Son Sorgular', self)
        recent_action.triggered.connect(self.show_query_history)
        history_menu.addAction(recent_action)
        
        favorites_action = QAction('Favoriler', self)
        favorites_action.triggered.connect(self.show_favorites)
        history_menu.addAction(favorites_action)
        
        tools_menu = menubar.addMenu('🔧 Araçlar')
        
        export_action = QAction('Sonuçları Dışa Aktar', self)
        export_action.triggered.connect(self.export_results)
        tools_menu.addAction(export_action)
        
        performance_action = QAction('Performans Raporu', self)
        performance_action.triggered.connect(self.show_performance_report)
        tools_menu.addAction(performance_action)
        
        help_menu = menubar.addMenu('❓ Yardım')
        
        help_action = QAction('Kullanım Kılavuzu', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('Hakkında', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def init_status_bar(self):
        """Modern status bar oluştur"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_label = QLabel("Hazır - Modern NaturaSQL v2.0")
        status_bar.addWidget(self.status_label)
    
    def show_startup_animation(self):
        """Başlangıç animasyonu"""
        self.animation_manager.fade_in(self, 800)
        
        QTimer.singleShot(1000, lambda: self.status_label.setText("🚀 Modern NaturaSQL hazır!"))
    
    def change_theme(self, theme_name):
        """Tema değiştir"""
        success = self.theme_manager.apply_theme(theme_name)
        if success:
            self.status_label.setText(f"Tema değiştirildi: {self.theme_manager.themes[theme_name]['name']}")
            
            self.apply_table_theme()
            
            QTimer.singleShot(100, self.fix_layout_on_theme_change)
            
            self.animation_manager.pulse_effect(self, 500, 1)
        else:
            self.status_label.setText("Tema yüklenemedi!")
    
    def show_query_history(self):
        """Sorgu geçmişini göster"""
        try:
            recent_queries = self.query_history.get_recent_queries(10)
            if recent_queries:
                history_text = "Son Sorgular:\n\n"
                for i, query in enumerate(recent_queries, 1):
                    history_text += f"{i}. {query[1][:50]}...\n"
                
                msg = QMessageBox()
                msg.setWindowTitle("Sorgu Geçmişi")
                msg.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
                msg.setText(history_text)
                msg.exec()
            else:
                self.status_label.setText("Henüz sorgu geçmişi yok")
        except Exception as e:
            self.status_label.setText(f"Geçmiş yüklenemedi: {str(e)}")
    
    def show_favorites(self):
        """Favori sorguları göster"""
        msg = QMessageBox()
        msg.setWindowTitle("Favoriler")
        msg.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
        msg.setText("🚧 Bu özellik şu anda geliştirilmekte.\n\nYakında kullanıma sunulacaktır!")
        msg.exec()
    
    def export_results(self):
        """Sonuçları dışa aktar"""
        if hasattr(self, 'last_results') and self.last_results:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Sonuçları Kaydet", "", "Excel Files (*.xlsx);;JSON Files (*.json)"
            )
            if file_path:
                try:
                    from features_manager import ExportManager
                    
                    if file_path.endswith('.xlsx'):
                        ExportManager.export_to_excel(self.last_results, file_path)
                    elif file_path.endswith('.json'):
                        ExportManager.export_to_json(self.last_results, file_path)
                    
                    self.status_label.setText(f"Sonuçlar kaydedildi: {file_path}")
                except Exception as e:
                    self.status_label.setText(f"Kaydetme hatası: {str(e)}")
        else:
            self.status_label.setText("Dışa aktarılacak sonuç yok")
    
    def show_performance_report(self):
        """Performans raporu göster"""
        msg = QMessageBox()
        msg.setWindowTitle("Performans Raporu")
        msg.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
        msg.setText("🚧 Bu özellik şu anda geliştirilmekte.\n\nDetaylı performans analizi yakında eklenecektir!")
        msg.exec()
    
    def show_help(self):
        """Kullanım kılavuzu penceresi"""
        help_text = """
        🌿 NaturaSQL Kullanım Kılavuzu
        
        📋 Adım Adım Kullanım:
        
        1. 📁 Veri Yükleme:
           • "Veri Yükle" butonuna tıklayın
           • Tekil Dosya: SQLite (.db, .sqlite) veya JSON (.json)
           • Çoklu JSON: Birkaç JSON dosyasını birden seçin
           
        2. ❓ Soru Sorma:
           • Sol paneldeki metin kutusuna sorunuzu yazın
           • Türkçe veya İngilizce olarak sorabilirsiniz
           • Örnek: "En yüksek değerleri göster"
           
        3. ▶️ Sorgu Çalıştırma:
           • "Sorguyu Çalıştır" butonuna basın
           • Ollama AI otomatik SQL oluşturup çalıştırır
           
        4. 📊 Sonuçları Görüntüleme:
           • Sonuçlar sağ paneldeki tabloda görüntülenir
           • Üretilen SQL sorgusu altta gösterilir
           
        5. 💾 Export İşlemleri:
           • "Araçlar" menüsünden "Sonuçları Dışa Aktar"
           • Excel (.xlsx) veya JSON formatında kaydedin
           
        🎨 Diğer Özellikler:
        • Tema değiştirme (Dark/Light)
        • Dil değiştirme (Türkçe/İngilizce)
        • Sorgu geçmişi (geliştiriliyor)
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("Kullanım Kılavuzu")
        msg.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
        msg.setText(help_text)
        msg.exec()
    
    def show_about(self):
        """Hakkında penceresi"""
        about_text = """
        🌿 NaturaSQL v2.0 - Modern Edition
        
        Doğal dilden SQL'e dönüştürme aracı
        Ollama AI ile çalışan offline çözüm
        
        ✨ Mevcut Özellikler:
        • SQLite ve JSON dosya desteği
        • Çoklu JSON dosya yükleme
        • Dark/Light tema sistemi
        • Türkçe/İngilizce dil desteği
        • Excel (.xlsx) ve JSON export
        • Modern animasyonlu arayüz
        
        🚧 Geliştirilen Özellikler:
        • Sorgu geçmişi sistemi
        • Performans analiz raporu
        • Favori sorgular
        
        💻 Teknolojiler:
        PyQt6, Ollama AI, Pandas, openpyxl
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("NaturaSQL Hakkında")
        msg.setWindowIcon(QIcon(self.get_asset_path("database.svg")))
        msg.setText(about_text)
        msg.exec()
    
    def start_modern_loading(self, message="Yükleniyor..."):
        """Modern loading sistemi başlat"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Infinite progress
        
        self.status_label.setText(message)
        
        self.loading_timer = self.animation_manager.loading_dots(self.status_label, message, 500)
        
        self.load_data_button.setEnabled(False)
        self.run_query_button.setEnabled(False)
    
    def stop_modern_loading(self, success_message="Tamamlandı"):
        """Modern loading sistemi durdur"""
        self.progress_bar.setVisible(False)
        
        if hasattr(self, 'loading_timer'):
            self.animation_manager.stop_loading_dots(self.loading_timer, self.status_label, success_message)
        
        self.load_data_button.setEnabled(True)
        self.run_query_button.setEnabled(True)
        
        self.animation_manager.glow_effect(self.run_query_button)
    
    def optimize_table_columns(self, headers):
        """Artık kullanılmıyor - tablo kaldırıldı"""
        pass
    
    def fix_layout_on_theme_change(self):
        """Tema değişiminde layout sorunlarını düzelt"""
        self.update()
        self.repaint()
        
        
        if hasattr(self, 'status_label'):
            self.status_label.update()
    
    def apply_table_theme(self):
        """Tema uyumlu tablo stilleri"""
        current_theme = self.theme_manager.get_current_theme()
        
        if current_theme == "modern_light":
            table_style = """
                QTableWidget {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    gridline-color: #e9ecef;
                    color: #212529;
                    font-size: 10pt;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #f8f9fa;
                }
                QTableWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #1976d2;
                }
                QTableWidget::item:alternate {
                    background-color: #f8f9fa;
                }
                QHeaderView::section {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #f1f3f4, stop: 1 #e8eaed);
                    color: #212529;
                    padding: 10px;
                    border: none;
                    border-bottom: 2px solid #1976d2;
                    font-weight: 600;
                    font-size: 10pt;
                }
            """
        else:
            table_style = """
                QTableWidget {
                    background-color: #2d3748;
                    border: 1px solid #4a5568;
                    border-radius: 8px;
                    gridline-color: #4a5568;
                    color: #e2e8f0;
                    font-size: 10pt;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #4a5568;
                }
                QTableWidget::item:selected {
                    background-color: #4299e1;
                    color: #ffffff;
                }
                QTableWidget::item:alternate {
                    background-color: #374151;
                }
                QHeaderView::section {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                                stop: 0 #4a5568, stop: 1 #2d3748);
                    color: #e2e8f0;
                    padding: 10px;
                    border: none;
                    border-bottom: 2px solid #4299e1;
                    font-weight: 600;
                    font-size: 10pt;
                }
            """
        
        self.results_table.setStyleSheet(table_style)

    def closeEvent(self, event):
        self.preview_data = []
        self.preview_headers = []
        if hasattr(self, 'last_results'):
            self.last_results = []
        if hasattr(self, 'last_headers'):
            self.last_headers = []
        
        self.controller.cleanup()
        event.accept()