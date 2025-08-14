#!/usr/bin/env python3
"""
Systematic Component Testing Script
Tests each component individually to isolate issues
"""

import os
import sys
from services.data_service import DataService
from database.db_manager import DatabaseManager

def test_data_service_methods():
    """Test all DataService methods with a test county"""
    print("Testing DataService methods...")
    
    db_manager = DatabaseManager()
    data_service = DataService(db_manager)
    test_county = "06037"  # Los Angeles County
    
    methods_to_test = [
        'get_industry_data',
        'get_sba_data', 
        'get_rfp_data',
        'get_awards_data',
        'get_license_data',
        'get_firm_age_data',
        'get_formation_data',
        'get_coverage_status'
    ]
    
    results = {}
    
    for method_name in methods_to_test:
        try:
            method = getattr(data_service, method_name)
            print(f"Testing {method_name}...")
            
            if method_name == 'get_coverage_status':
                result = method(test_county)
            else:
                result = method(test_county)
            
            results[method_name] = {
                'success': True,
                'type': type(result).__name__,
                'length': len(result) if hasattr(result, '__len__') else 'N/A',
                'error': None
            }
            print(f"✅ {method_name}: {type(result).__name__} with {len(result) if hasattr(result, '__len__') else 'N/A'} items")
            
        except Exception as e:
            results[method_name] = {
                'success': False,
                'type': None,
                'length': None,
                'error': str(e)
            }
            print(f"❌ {method_name}: {str(e)}")
    
    return results

def test_database_connection():
    """Test basic database connectivity"""
    print("Testing database connection...")
    try:
        db_manager = DatabaseManager()
        tables = db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table';")
        print(f"✅ Database connected. Found {len(tables)} tables: {[t['name'] for t in tables]}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_adapters():
    """Test individual adapter functionality"""
    print("Testing adapters...")
    
    # Test imports
    try:
        from adapters.cbp import CBPAdapter
        from adapters.sam import SAMAdapter
        print("✅ Adapter imports successful")
    except Exception as e:
        print(f"❌ Adapter import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Systematic Component Testing ===\n")
    
    # Test 1: Database
    db_ok = test_database_connection()
    print()
    
    # Test 2: Adapters
    adapters_ok = test_adapters()
    print()
    
    # Test 3: DataService methods
    if db_ok and adapters_ok:
        service_results = test_data_service_methods()
        print()
        
        print("=== Summary ===")
        for method, result in service_results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {method}")
            if not result['success']:
                print(f"    Error: {result['error']}")
    else:
        print("❌ Skipping DataService tests due to prerequisite failures")