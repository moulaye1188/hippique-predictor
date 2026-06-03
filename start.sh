#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🐴 Hippique Predictor${NC}"
echo -e "${BLUE}================================${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo -e "${YELLOW}Please start Docker Desktop and try again${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}\n"

# Build and start containers
echo -e "${BLUE}🔨 Building Docker image...${NC}"
docker-compose build --no-cache

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}\n"

echo -e "${BLUE}🚀 Starting application...${NC}"
docker-compose up -d

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start application${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Application started${NC}\n"

# Wait for application to be ready
echo -e "${YELLOW}⏳ Waiting for application to be ready (30-40 seconds for model training)...${NC}"
sleep 5

# Check health
MAX_RETRIES=8
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy${NC}\n"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 5
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️ Application is starting but not yet fully ready${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose logs -f app${NC}\n"
fi

# Print access information
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}🎉 Application Ready!${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "📍 Frontend: ${BLUE}http://localhost:5000${NC}"
echo -e "🔌 API Health: ${BLUE}http://localhost:5000/api/health${NC}"
echo -e "${BLUE}================================${NC}\n"

echo -e "${YELLOW}Useful commands:${NC}"
echo "  docker-compose logs -f app    # View logs"
echo "  docker-compose down           # Stop application"
echo "  docker-compose ps             # Check status"
echo ""
