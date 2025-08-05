import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

def main():
    """
    NaturaSQL uygulamasını başlatan ana fonksiyon.
    """
    APP_ROOT = Path(__file__).parent.resolve()
    
    ICONS_PATH = APP_ROOT / "icons"
    
    print(f"--- UYGULAMA BAŞLATILIYOR ---")
    print(f"Uygulama Kök Dizini: {APP_ROOT}")
    print(f"İkonlar burada aranacak: {ICONS_PATH}")
    print(f"-----------------------------")

    app = QApplication(sys.argv)
    
    from ui_main import MainWindow

    font = QFont("Inter", 10)
    QApplication.setFont(font)
    app.setApplicationName("NaturaSQL")
    app.setApplicationVersion("1.3.0")

    main_window = MainWindow(icons_path=str(ICONS_PATH))
    main_window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()