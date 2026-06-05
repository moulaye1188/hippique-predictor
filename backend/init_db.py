#!/usr/bin/env python3
from database import init_database
from database_schema_v2 import migrate_to_schema_v2

print("Initializing database...")
init_database()
print("✓ DB initialized")

print("\nMigrating to schema v2...")
migrate_to_schema_v2()
print("✓ Migration complete")
