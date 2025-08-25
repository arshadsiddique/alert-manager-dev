#!/bin/bash
set -e

echo "🚀 Starting Devo Alert Manager Backend v1.0.0..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import sys
import time
import psycopg2
from app.core.config import settings

def wait_for_db():
    for i in range(60):
        try:
            conn = psycopg2.connect(settings.DATABASE_URL)
            conn.close()
            print('✅ Database is ready!')
            return
        except psycopg2.OperationalError:
            print(f'⏳ Database not ready yet... ({i+1}/60)')
            time.sleep(1)
    print('❌ Database connection timeout')
    sys.exit(1)

wait_for_db()
"

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Test JSM connectivity
echo "🔌 Testing JSM connectivity..."
python -c "
import asyncio
from app.services.jsm_service import JSMService
from app.core.config import settings

async def test_jsm():
    try:
        jsm_service = JSMService()
        cloud_id = await jsm_service.get_cloud_id()
        if cloud_id:
            print(f'✅ JSM connectivity successful - Cloud ID: {cloud_id}')
        else:
            print('⚠️  JSM connectivity test failed - Cloud ID not retrieved')
    except Exception as e:
        print(f'⚠️  JSM connectivity test failed: {e}')

asyncio.run(test_jsm())
" || echo "⚠️  JSM connectivity test failed, but continuing startup..."

# Start the FastAPI server
echo "🎯 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
