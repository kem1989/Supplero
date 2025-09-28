#!/usr/bin/env python3
"""
Database optimization script to improve query performance.
Run this script to create missing indexes and optimize the database.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.database_optimization import optimize_database
import structlog

logger = structlog.get_logger(__name__)


def main():
    """Run database optimization."""
    try:
        logger.info("Starting database optimization...")
        
        # Run optimization
        performance_data = optimize_database()
        
        logger.info("Database optimization completed successfully!")
        
        # Print summary
        print("\n=== Database Optimization Summary ===")
        print("✅ Performance indexes created")
        print("✅ Table statistics updated")
        print("✅ Query performance analyzed")
        
        # Print table sizes
        if "query_2" in performance_data:
            print("\n=== Table Sizes ===")
            for table_info in performance_data["query_2"]:
                print(f"{table_info['tablename']}: {table_info['size']}")
        
        print("\n=== Next Steps ===")
        print("1. Test query performance with optimized queries")
        print("2. Monitor query execution times")
        print("3. Consider adding more specific indexes based on usage patterns")
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        print(f"❌ Database optimization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

