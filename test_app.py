import sys
import os

def test_imports():
    """Test all imports"""
    try:
        print("Testing imports...")
        
        from PyQt6.QtWidgets import QApplication
        print("OK PyQt6")
        
        from ui_main import MainWindow
        print("OK UI Main")
        
        from app_controller import AppController
        print("OK App Controller")
        
        from db_connector import DBConnector
        print("OK Database Connector")
        
        from nlp_engine import NLPEngine
        print("OK NLP Engine")
        
        from theme_manager import ThemeManager
        print("OK Theme Manager")
        
        from ui_animations import AnimationManager
        print("OK Animation Manager")
        
        from features_manager import QueryHistoryManager
        print("OK Features Manager")
        
        print("\nAll imports successful!")
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic app functionality without GUI"""
    try:
        print("\nTesting basic functionality...")
        
        from theme_manager import ThemeManager
        theme_mgr = ThemeManager()
        themes = theme_mgr.get_available_themes()
        print(f"Available themes: {len(themes)}")
        
        from ui_animations import AnimationManager
        anim_mgr = AnimationManager()
        print("Animation manager created")
        
        from features_manager import QueryHistoryManager
        history_mgr = QueryHistoryManager()
        print("Query history manager created")
        
        return True
        
    except Exception as e:
        print(f"Functionality test error: {e}")
        return False

def main():
    print("NaturaSQL Test Suite")
    print("=" * 50)
    
    if not test_imports():
        sys.exit(1)
    
    if not test_basic_functionality():
        sys.exit(1)
    
    print("\nAll tests passed! Ready to run the application.")
    print("\nTo start the app: python main.py")

if __name__ == "__main__":
    main()