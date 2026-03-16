#!/bin/bash
# Quick health check before running lab-zal

echo "🔍 Lab ZAL - Pre-flight Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Docker
echo ""
echo "1️⃣  Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
DOCKER_VERSION=$(docker --version | awk '{print $3}' | cut -d, -f1)
echo "✅ Docker $DOCKER_VERSION found"

# Check Docker Compose
echo ""
echo "2️⃣  Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Install with: sudo apt install docker-compose (Linux) or brew install docker-compose (Mac)"
    exit 1
fi
COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | cut -d, -f1)
echo "✅ Docker Compose $COMPOSE_VERSION found"

# Check Docker daemon
echo ""
echo "3️⃣  Checking Docker daemon..."
if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon not running. Start Docker Desktop or: sudo systemctl start docker"
    exit 1
fi
echo "✅ Docker daemon is running"

# Check Docker Compose file
echo ""
echo "4️⃣  Checking docker-compose.yml..."
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Make sure you're in the lab-zal directory"
    exit 1
fi
echo "✅ docker-compose.yml found"

# Validate docker-compose
echo ""
echo "5️⃣  Validating docker-compose.yml..."
if ! docker-compose config > /dev/null 2>&1; then
    echo "❌ Invalid docker-compose.yml"
    docker-compose config
    exit 1
fi
echo "✅ docker-compose.yml is valid"

# Check port availability
echo ""
echo "6️⃣  Checking ports..."
PORTS=(8080 9090 9093 10051 5001 9100 9095)
BUSY=0
for PORT in "${PORTS[@]}"; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $PORT already in use (may conflict)"
        BUSY=$((BUSY + 1))
    fi
done
if [ $BUSY -eq 0 ]; then
    echo "✅ All required ports available"
else
    echo "⚠️  Some ports already in use - may cause issues"
fi

# Check disk space
echo ""
echo "7️⃣  Checking disk space..."
SPACE=$(df / | awk 'NR==2 {print $4}')
if [ "$SPACE" -lt 5242880 ]; then  # 5GB in KB
    echo "⚠️  Low disk space: $(df -h / | awk 'NR==2 {print $4}') free"
else
    echo "✅ Disk space OK ($(df -h / | awk 'NR==2 {print $4}') free)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All checks passed! Ready to run:"
echo ""
echo "  docker-compose up -d"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
