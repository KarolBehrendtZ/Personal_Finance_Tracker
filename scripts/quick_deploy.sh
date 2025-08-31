#!/bin/bash

# Quick Deploy Script for Personal Finance Tracker
# This script rebuilds and restarts all containers after code changes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}📋 $1${NC}"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(echo $1 | sed 's/./=/g')${NC}"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed or not in PATH"
    exit 1
fi

print_header "🚀 Personal Finance Tracker - Quick Deploy"

print_info "Starting deployment process..."

# Step 1: Build all containers
print_info "Building all containers (this may take a while)..."
if docker-compose build; then
    print_status "All containers built successfully"
else
    print_error "Failed to build containers"
    exit 1
fi

# Step 2: Stop running containers
print_info "Stopping running containers..."
if docker-compose down; then
    print_status "Containers stopped"
else
    print_warning "Some containers might not have been running"
fi

# Step 3: Start all services
print_info "Starting all services..."
if docker-compose up -d; then
    print_status "All services started"
else
    print_error "Failed to start services"
    exit 1
fi

# Step 4: Wait a moment for services to initialize
print_info "Waiting for services to initialize..."
sleep 5

# Step 5: Check container status
print_info "Checking container status..."
echo ""
docker-compose ps

# Step 6: Health check
print_info "Performing health checks..."
echo ""

# Check database
print_info "Checking database connection..."
if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
    print_status "Database is ready"
else
    print_warning "Database might still be starting up"
fi

# Check API
print_info "Checking API endpoint..."
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    print_status "API is responding"
else
    print_warning "API might still be starting up - trying again in 5 seconds..."
    sleep 5
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        print_status "API is responding"
    else
        print_warning "API still not responding - check logs if needed"
    fi
fi

# Step 7: Show logs for any failing services
print_info "Checking for any service issues..."
if docker-compose ps | grep -q "Exit\|Restarting"; then
    print_warning "Some services have issues. Showing recent logs:"
    docker-compose logs --tail=20
fi

echo ""
print_status "Deployment completed!"
echo ""
print_info "🌐 Application URLs:"
echo -e "   📊 Dashboard: ${CYAN}http://localhost:8501${NC}"
echo -e "   🔌 API: ${CYAN}http://localhost:8080${NC}"
echo -e "   📁 API Health: ${CYAN}http://localhost:8080/health${NC}"
echo ""
print_info "📋 Useful commands:"
echo -e "   ${YELLOW}docker-compose logs -f [service]${NC}    # Follow logs for a service"
echo -e "   ${YELLOW}docker-compose ps${NC}                   # Check service status"
echo -e "   ${YELLOW}docker-compose down${NC}                 # Stop all services"
echo -e "   ${YELLOW}docker-compose restart [service]${NC}    # Restart specific service"
echo ""
print_info "🧪 Test the application:"
echo "   1. Open http://localhost:8501"
echo "   2. Login with: john.doe@example.com / password123"
echo "   3. Check if data loads properly"
echo ""
print_status "Happy coding! 🎯"
