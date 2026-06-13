"""
Backend test
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_imports():
    """Test that we can import the backend modules"""
    try:
        from src.backend.app import create_app
        from src.backend.models import User, Group
        from src.backend.services.auth_service import AuthService
        from src.backend.services.group_service import GroupService
        from src.backend.services.expense_service import ExpenseService
        from src.backend.services.import_service import ImportService
        from src.backend.services.balances_service import BalancesService
        from src.backend.controllers.auth_controller import auth_bp
        from src.backend.controllers.groups_controller import groups_bp
        from src.backend.controllers.expenses_controller import expenses_bp
        from src.backend.controllers.imports_controller import imports_bp
        from src.backend.controllers.balances_controller import balances_bp

        print("[PASS] All backend modules imported successfully")
        return True
    except Exception as e:
        print("[FAIL] Failed to import backend modules: {}".format(e))
        return False

def test_app_creation():
    """Test that we can create the Flask app"""
    try:
        from src.backend.app import create_app
        app = create_app()
        print("[PASS] Flask app created successfully")
        return True
    except Exception as e:
        print("[FAIL] Failed to create Flask app: {}".format(e))
        return False

if __name__ == '__main__':
    print("Testing backend structure...")
    success = True
    success &= test_imports()
    success &= test_app_creation()

    if success:
        print("\n[PASS] All backend tests passed!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some backend tests failed!")
        sys.exit(1)