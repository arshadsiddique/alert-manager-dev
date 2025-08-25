#!/usr/bin/env python3
"""
Test script for JSM connectivity and alert matching
Usage: python test_jsm_connectivity.py
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.jsm_service import JSMService
from app.services.grafana_service import GrafanaService
from app.core.config import settings

async def test_jsm_connectivity():
    """Test JSM API connectivity and basic operations"""
    print("🔌 Testing JSM Connectivity...")
    
    jsm_service = JSMService()
    
    # Test 1: Get Cloud ID
    print("\n1. Testing Cloud ID retrieval...")
    try:
        cloud_id = await jsm_service.get_cloud_id()
        if cloud_id:
            print(f"✅ Cloud ID retrieved: {cloud_id}")
        else:
            print("❌ Failed to retrieve Cloud ID")
            return False
    except Exception as e:
        print(f"❌ Cloud ID test failed: {e}")
        return False
    
    # Test 2: Fetch JSM Alerts
    print("\n2. Testing JSM alerts retrieval...")
    try:
        alerts = await jsm_service.get_jsm_alerts(limit=5)
        print(f"✅ Retrieved {len(alerts)} JSM alerts")
        
        if alerts:
            sample_alert = alerts[0]
            print(f"   Sample alert ID: {sample_alert.get('id')}")
            print(f"   Sample alert status: {sample_alert.get('status')}")
            print(f"   Sample alert source: {sample_alert.get('source')}")
    except Exception as e:
        print(f"❌ JSM alerts test failed: {e}")
        return False
    
    # Test 3: Test Grafana connectivity
    print("\n3. Testing Grafana connectivity...")
    try:
        grafana_service = GrafanaService()
        grafana_alerts = await grafana_service.get_active_alerts()
        print(f"✅ Retrieved {len(grafana_alerts)} Grafana alerts")
    except Exception as e:
        print(f"❌ Grafana test failed: {e}")
        return False
    
    # Test 4: Test Alert Matching
    print("\n4. Testing alert matching...")
    try:
        grafana_service = GrafanaService()
        grafana_alerts = await grafana_service.get_active_alerts()
        jsm_alerts = await jsm_service.get_jsm_alerts(limit=10)
        
        matched = jsm_service.match_grafana_with_jsm(grafana_alerts[:5], jsm_alerts)
        matches_found = sum(1 for m in matched if m['jsm_alert'] is not None)
        print(f"✅ Matching test completed: {matches_found}/{len(matched)} alerts matched")
        
        # Show matching details
        for i, match in enumerate(matched[:3]):
            print(f"   Alert {i+1}: {match['match_type']} - {match['match_confidence']}% confidence")
            
    except Exception as e:
        print(f"❌ Alert matching test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! JSM integration is working correctly.")
    return True

if __name__ == "__main__":
    print("Devo Alert Manager - Connectivity Test")
    print("=" * 50)
    
    # Check configuration
    print(f"JSM Cloud ID: {settings.JSM_CLOUD_ID}")
    print(f"Jira URL: {settings.JIRA_URL}")
    print(f"Grafana URL: {settings.GRAFANA_API_URL}")
    print(f"JSM Mode: {settings.USE_JSM_MODE}")
    
    if not settings.JSM_CLOUD_ID:
        print("❌ JSM_CLOUD_ID not configured! Please set it in your .env file.")
        sys.exit(1)
    
    if not settings.JIRA_API_TOKEN:
        print("❌ JIRA_API_TOKEN not configured! Please set it in your .env file.")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(test_jsm_connectivity())
    
    if not success:
        print("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1)
    else:
        print("\n✅ All tests successful! Your JSM integration is ready.")


# deploy.sh (deployment script)
#!/bin/bash
set -e

echo "🚀 Deploying Devo Alert Manager v1.0..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists docker; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
source .env

# Validate critical environment variables
echo "🔍 Validating configuration..."

if [ -z "$JSM_CLOUD_ID" ]; then
    echo "❌ JSM_CLOUD_ID is not set in .env file"
    exit 1
fi

if [ -z "$JIRA_API_TOKEN" ]; then
    echo "❌ JIRA_API_TOKEN is not set in .env file"
    exit 1
fi

if [ -z "$GRAFANA_API_KEY" ]; then
    echo "❌ GRAFANA_API_KEY is not set in .env file"
    exit 1
fi

echo "✅ Configuration validated"

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose pull

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check backend health
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend service is healthy"
else
    echo "❌ Backend service health check failed"
    echo "📋 Backend logs:"
    docker-compose logs backend | tail -20
    exit 1
fi

# Check frontend
if curl -f http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Frontend service is healthy"
else
    echo "❌ Frontend service health check failed"
    echo "📋 Frontend logs:"
    docker-compose logs frontend | tail -20
    exit 1
fi

# Check database connectivity
echo "🗄️  Checking database connectivity..."
if docker-compose exec -T postgres pg_isready -U user -d alertdb >/dev/null 2>&1; then
    echo "✅ Database is ready"
else
    echo "❌ Database connectivity check failed"
    exit 1
fi

# Test JSM connectivity
echo "🔌 Testing JSM connectivity..."
if docker-compose exec -T backend python -c "
import asyncio
import sys
sys.path.append('/app')
from app.services.jsm_service import JSMService

async def test():
    try:
        service = JSMService()
        cloud_id = await service.get_cloud_id()
        if cloud_id:
            print('✅ JSM connectivity successful')
            return True
        else:
            print('❌ JSM connectivity failed')
            return False
    except Exception as e:
        print(f'❌ JSM connectivity error: {e}')
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
" 2>/dev/null; then
    echo "✅ JSM connectivity test passed"
else
    echo "⚠️  JSM connectivity test failed, but deployment continues"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Service URLs:"
echo "   • Web Interface: http://localhost:3000"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart services: docker-compose restart"
echo ""
echo "📊 Monitor the application:"
echo "   • Check logs: docker-compose logs -f backend"
echo "   • View database: docker-compose exec postgres psql -U user alertdb"
echo "   • Test API: curl http://localhost:8000/api/info"
