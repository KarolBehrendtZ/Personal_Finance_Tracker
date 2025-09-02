#!/bin/bash

# Development Watch Script for Personal Finance Tracker
# Monitors file changes and rebuilds/restarts affected services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# Check if inotify-tools is available
if ! command -v inotifywait &> /dev/null; then
    print_error "inotifywait is not installed. Please install inotify-tools:"
    echo "  Ubuntu/Debian: sudo apt-get install inotify-tools"
    echo "  CentOS/RHEL: sudo yum install inotify-tools"
    echo "  Arch: sudo pacman -S inotify-tools"
    exit 1
fi

print_header "👀 Development Watch Mode"
print_info "Monitoring file changes and auto-rebuilding services..."
echo ""

# Function to rebuild and restart a service
rebuild_service() {
    local service=$1
    print_warning "Detected changes in $service, rebuilding..."
    
    if docker-compose build "$service"; then
        print_status "$service rebuilt successfully"
        
        if docker-compose restart "$service"; then
            print_status "$service restarted successfully"
        else
            print_error "Failed to restart $service"
        fi
    else
        print_error "Failed to rebuild $service"
    fi
    
    echo ""
    print_info "Continuing to watch for changes..."
}

# Initial setup
print_info "Starting development environment..."
docker-compose up -d
print_status "All services started"
echo ""

# Cleanup function
cleanup() {
    print_warning "Stopping development environment..."
    docker-compose down
    print_status "Development environment stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_info "Watching for file changes..."
print_info "Press Ctrl+C to stop watching and shut down services"
echo ""
print_info "📁 Monitored paths:"
echo "   • cmd/ (Go API changes)"
echo "   • internal/ (Go API changes)"
echo "   • dashboard/ (Python dashboard changes)"
echo "   • python/etl/ (ETL worker changes)"
echo "   • docker/ (Nginx changes)"
echo ""

# Watch for changes
inotifywait -m -r -e modify,create,delete,move \
    --include '\.(go|py|js|html|css|conf)$' \
    --exclude '/(\.venv|node_modules|__pycache__|dist|build|\.git|\.mypy_cache)(/|$)' \
    cmd/ internal/ dashboard/ python/etl/ docker/ 2>/dev/null | \
while read path action file; do
    timestamp=$(date '+%H:%M:%S')
    echo -e "${CYAN}[$timestamp]${NC} File changed: ${path}${file}"
    
    # Determine which service to rebuild based on path
    if [[ "$path" =~ ^(cmd/|internal/) ]]; then
        rebuild_service "api"
    elif [[ "$path" =~ ^dashboard/ ]]; then
        rebuild_service "dashboard"
    elif [[ "$path" =~ ^python/etl/ ]]; then
        rebuild_service "etl_worker"
    elif [[ "$path" =~ ^docker/ ]]; then
        rebuild_service "nginx"
    fi
done
