
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from pathlib import Path

def test_app_startup():
    """Test app startup and close immediately"""
    app = QApplication(sys.argv)
    
    from ui_main import MainWindow
    
    APP_ROOT = Path(__file__).parent.resolve()
    ICONS_PATH = APP_ROOT / "icons"
    
    print(f"Starting NaturaSQL...")
    print(f"Icons path: {ICONS_PATH}")
    
    main_window = MainWindow(icons_path=str(ICONS_PATH))
    main_window.show()
    
    print("Application window created and shown!")
    print("Window title:", main_window.windowTitle())
    print("Window size:", main_window.size().width(), "x", main_window.size().height())
    
    QTimer.singleShot(2000, app.quit)
    
    print("App will auto-close in 2 seconds...")
    
    result = app.exec()
    print(f"App closed with exit code: {result}")
    
    return result == 0

if __name__ == "__main__":
    success = test_app_startup()
    if success:
        print("SUCCESS: Application started and closed properly!")
    else:
        print("FAILED: Application had issues")
    
    sys.exit(0 if success else 1)