#!/usr/bin/env python3
"""
Export FastAPI OpenAPI schema to a static JSON file.

This script requires the backend dependencies to be installed.
Run: pip install -r backend/requirements.txt
"""
import json
import sys
sys.path.insert(0, 'backend')

from app.main import app

schema = app.openapi()
output_path = 'backend/openapi.json'
with open(output_path, 'w') as f:
    json.dump(schema, f, indent=2)
print(f"OpenAPI schema exported to {output_path}")
