#!/usr/bin/env python3
"""Test database migration to v2"""
from database_schema_v2 import migrate_to_schema_v2

print("Running migration to database schema v2...\n")
migrate_to_schema_v2()
print("\n✅ Migration complete!")
