#!/bin/bash
# Simple Docker script for DIGI4ECO API

echo "🐳 DIGI4ECO - Docker Deploy"
echo "=" * 40

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build image
echo "🔨 Building Docker image..."
docker build -t digi4eco-api .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

# Start container
echo "🚀 Starting container..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container"
    exit 1
fi

# Wait and health check
echo "⏳ Waiting for API..."
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running!"
    echo ""
    echo "   Endpoint: http://localhost:8000"
    echo "   Health: http://localhost:8000/health"
    echo "   Logs: docker-compose logs -f"
    echo "   Stop: docker-compose down"
else
    echo "❌ API health check failed"
    echo "   Check logs: docker-compose logs"
    exit 1
fi

