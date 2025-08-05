import json
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

class ThemeManager:
    """Tema yönetimi ve stil sistemi"""
    
    def __init__(self):
        self.settings = QSettings("NaturaSQL", "ThemeSettings")
        self.current_theme = self.settings.value("current_theme", "modern_dark")
        self.themes = self._load_themes()
        
    def _load_themes(self):
        """Mevcut temaları yükle"""
        return {
            "modern_dark": {
                "name": "Modern Dark",
                "description": "Koyu, modern gradient tema",
                "file": "styles/modern_theme.qss",
                "preview_color": "#1a1a2e"
            },
            "modern_light": {
                "name": "Modern Light", 
                "description": "Açık, minimal tema",
                "file": "styles/light_theme.qss",
                "preview_color": "#f8f9fa"
            }
        }
    
    def apply_theme(self, theme_name):
        """Temayı uygula"""
        if theme_name not in self.themes:
            return False
            
        theme_file = self.themes[theme_name]["file"]
        if not os.path.exists(theme_file):
            self._create_theme_file(theme_name)
            
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                
            app = QApplication.instance()
            if app:
                app.setStyleSheet(stylesheet)
                self.current_theme = theme_name
                self.settings.setValue("current_theme", theme_name)
                return True
        except Exception as e:
            print(f"Tema yüklenirken hata: {e}")
            return False
    
    def _create_theme_file(self, theme_name):
        """Eksik tema dosyasını oluştur"""
        styles_dir = Path("styles")
        styles_dir.mkdir(exist_ok=True)
        
        if theme_name == "modern_light":
            self._create_light_theme()
    
    def _create_light_theme(self):
        """Açık tema dosyası oluştur"""
        light_theme = """/* NaturaSQL Light Theme */
QMainWindow {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                stop: 0 #f8f9fa, stop: 1 #e9ecef);
    color: #212529;
}

QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #4285f4, stop: 1 #1a73e8);
    border: none;
    border-radius: 8px;
    color: white;
    padding: 12px 24px;
    font-weight: 600;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #5294ff, stop: 1 #2d7ceb);
}

QTextEdit {
    background: #ffffff;
    border: 2px solid #dee2e6;
    border-radius: 12px;
    color: #212529;
    padding: 16px;
}

QTextEdit:focus {
    border: 2px solid #4285f4;
}

QTableWidget {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 12px;
    gridline-color: #dee2e6;
    color: #212529;
}

QHeaderView::section {
    background: #f8f9fa;
    color: #212529;
    padding: 12px;
    border: none;
    border-bottom: 2px solid #4285f4;
    font-weight: 600;
}

QLabel {
    color: #212529;
}

QComboBox {
    background: #ffffff;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 8px 12px;
    color: #212529;
}"""
        
        with open("styles/light_theme.qss", 'w', encoding='utf-8') as f:
            f.write(light_theme)
    
    def get_available_themes(self):
        """Mevcut temaları döndür"""
        return self.themes
    
    def get_current_theme(self):
        """Aktif temayı döndür"""
        return self.current_theme
    
    def reset_to_default(self):
        """Varsayılan temaya dön"""
        self.apply_theme("modern_dark")
    
    def create_custom_theme(self, name, base_theme, customizations):
        """Özel tema oluştur"""
        if base_theme not in self.themes:
            return False
            
        with open(self.themes[base_theme]["file"], 'r', encoding='utf-8') as f:
            base_css = f.read()
        
        custom_css = base_css
        for selector, properties in customizations.items():
            pass
        
        custom_file = f"styles/custom_{name.lower().replace(' ', '_')}.qss"
        with open(custom_file, 'w', encoding='utf-8') as f:
            f.write(custom_css)
        
        self.themes[f"custom_{name.lower()}"] = {
            "name": name,
            "description": "Özel kullanıcı teması",
            "file": custom_file,
            "preview_color": "#custom"
        }
        
        return True
    
    def export_theme(self, theme_name, file_path):
        """Temayı dışa aktar"""
        if theme_name not in self.themes:
            return False
            
        theme_data = {
            "theme": self.themes[theme_name],
            "version": "1.0",
            "created_by": "NaturaSQL"
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def import_theme(self, file_path):
        """Temayı içe aktar"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            theme_info = theme_data["theme"]
            theme_name = f"imported_{theme_info['name'].lower().replace(' ', '_')}"
            
            self.themes[theme_name] = theme_info
            return True
        except Exception as e:
            print(f"Tema içe aktarılırken hata: {e}")
            return False