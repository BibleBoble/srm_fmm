# -*- coding: utf-8 -*-
"""
Test script for Phase 3 implementation
"""

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    try:
        from services.client_service import ClientService
        print("✅ ClientService import OK")
    except Exception as e:
        print(f"❌ ClientService import failed: {e}")
        return False
    
    try:
        from services.task_service import TaskService
        print("✅ TaskService import OK")
    except Exception as e:
        print(f"❌ TaskService import failed: {e}")
        return False
    
    try:
        from services import ClientService, TaskService
        print("✅ Services __init__ import OK")
    except Exception as e:
        print(f"❌ Services __init__ import failed: {e}")
        return False
    
    return True

def test_managers():
    """Test managers methods"""
    print("\nTesting managers...")
    
    try:
        from managers.tasks_manager import TasksManager
        from managers.contact_persons_manager import ContactPersonsManager
        from managers.clients_manager import ClientsManager
        
        tm = TasksManager()
        cpm = ContactPersonsManager()
        cm = ClientsManager()
        
        # Test new methods
        tasks = tm.get_sorted_by_priority()
        print(f"✅ TasksManager.get_sorted_by_priority() OK: {len(tasks)} tasks")
        
        contacts = cpm.get_sorted_by_name()
        print(f"✅ ContactPersonsManager.get_sorted_by_name() OK: {len(contacts)} contacts")
        
        clients = cm.get_sorted_by_company()
        print(f"✅ ClientsManager.get_sorted_by_company() OK: {len(clients)} clients")
        
        return True
    except Exception as e:
        print(f"❌ Managers test failed: {e}")
        return False

def test_utils():
    """Test utils"""
    print("\nTesting utils...")
    
    try:
        from utils.formatters import DateFormatter, PriorityFormatter, StatusFormatter
        from utils.parsers import DateParser, safe_get
        from utils.dto import ClientTableRowDTO
        from utils.constants import Icons
        
        # Test formatters
        date_str = DateFormatter.format_date(None)
        print(f"✅ DateFormatter OK: '{date_str}'")
        
        priority_str = PriorityFormatter.format("Высокий")
        print(f"✅ PriorityFormatter OK: '{priority_str}'")
        
        status_str = StatusFormatter.format("Активная")
        print(f"✅ StatusFormatter OK: '{status_str}'")
        
        # Test parsers
        parsed_date = DateParser.parse_date("2024-01-01")
        print(f"✅ DateParser OK: {parsed_date}")
        
        value = safe_get({'test': 'value'}, 'test')
        print(f"✅ safe_get OK: {value}")
        
        # Test DTO
        dto = ClientTableRowDTO(1, "Test")
        print(f"✅ DTO OK: {dto}")
        
        # Test constants
        icons = Icons.PRIORITY
        print(f"✅ Icons OK: {icons}")
        
        return True
    except Exception as e:
        print(f"❌ Utils test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("PHASE 3 TESTING")
    print("=" * 50)
    
    all_ok = True
    
    # Test imports
    if not test_imports():
        all_ok = False
    
    # Test managers
    if not test_managers():
        all_ok = False
    
    # Test utils
    if not test_utils():
        all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ ALL TESTS PASSED - Phase 3 implementation complete!")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("=" * 50)

if __name__ == "__main__":
    main()
