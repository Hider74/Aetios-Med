# Type Generation Scripts

This project includes scripts to generate TypeScript types from the FastAPI OpenAPI schema.

## Scripts

### `npm run generate:types:from-file`
**Cross-platform** - Generates TypeScript types from a static OpenAPI JSON file.

Requirements:
1. First, export the OpenAPI schema: `python scripts/export-openapi.py`
2. Then run: `npm run generate:types:from-file`

This is the recommended approach as it works on all platforms.

### `npm run generate:types`
**Unix/macOS only** - Starts the backend server, generates types, then stops the server.

Note: This script uses Unix-specific job control (`&` and `%1`) and won't work on Windows.
For Windows, use `generate:types:from-file` instead.

## Usage

The generated types will be in `frontend/src/types/generated-api.ts` and should not be manually edited.

These types serve as the source of truth for API contracts between the Python backend and TypeScript frontend.
