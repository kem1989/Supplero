#!/usr/bin/env python3
"""
Simple test script to debug the external data aggregation service.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

print("Testing imports step by step...")

try:
    print("1. Importing config...")
    from app.core.config import settings
    print("   ✅ Config imported successfully")
    print(f"   NEWS_API_KEY: {settings.NEWS_API_KEY}")
except Exception as e:
    print(f"   ❌ Config import failed: {e}")
    sys.exit(1)

try:
    print("2. Importing external data aggregation...")
    from app.core.external_data_aggregation import ExternalDataAggregationService
    print("   ✅ External data aggregation imported successfully")
except Exception as e:
    print(f"   ❌ External data aggregation import failed: {e}")
    sys.exit(1)

try:
    print("3. Creating service instance...")
    service = ExternalDataAggregationService()
    print("   ✅ Service instance created successfully")
    print(f"   Service news_api_key: {service.news_api_key}")
except Exception as e:
    print(f"   ❌ Service instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ All tests passed!")








