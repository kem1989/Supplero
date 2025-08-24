#!/usr/bin/env python3
"""
Debug script to investigate the settings object issue.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

print("Debugging settings object...")

try:
    print("1. Importing config settings...")
    from app.core.config import settings as config_settings
    print(f"   Config settings ID: {id(config_settings)}")
    print(f"   Config settings NEWS_API_KEY: {config_settings.NEWS_API_KEY}")
    print(f"   Config settings has NEWS_API_KEY: {hasattr(config_settings, 'NEWS_API_KEY')}")
    
    print("\n2. Importing external data aggregation...")
    from app.core.external_data_aggregation import settings as module_settings
    print(f"   Module settings ID: {id(module_settings)}")
    print(f"   Module settings NEWS_API_KEY: {module_settings.NEWS_API_KEY}")
    print(f"   Module settings has NEWS_API_KEY: {hasattr(module_settings, 'NEWS_API_KEY')}")
    
    print("\n3. Comparing objects...")
    print(f"   Same object? {config_settings is module_settings}")
    
    print("\n4. Checking attributes...")
    news_attrs = [attr for attr in dir(module_settings) if 'NEWS' in attr]
    print(f"   NEWS-related attributes: {news_attrs}")
    
    print("\n5. Trying to access NEWS_API_KEY...")
    try:
        value = module_settings.NEWS_API_KEY
        print(f"   Direct access successful: {value}")
    except Exception as e:
        print(f"   Direct access failed: {e}")
    
    print("\n6. Trying getattr...")
    try:
        value = getattr(module_settings, 'NEWS_API_KEY', None)
        print(f"   getattr successful: {value}")
    except Exception as e:
        print(f"   getattr failed: {e}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()














