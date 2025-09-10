#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
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

SERVICES=("api" "dashboard" "etl_worker" "nginx" "postgres")

show_usage() {
    print_header "🔧 Build Script Usage"
    echo ""
    echo "Usage: $0 [service1] [service2] ... | all"
    echo ""
    echo "Available services:"
    for service in "${SERVICES[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo "Examples:"
    echo "  $0 api dashboard    # Build only API and dashboard"
    echo "  $0 all             # Build all services"
    echo "  $0                 # Show this help"
}

build_services() {
    local services_to_build=("$@")
    
    print_header "🔧 Building Services"
    
    for service in "${services_to_build[@]}"; do
        print_info "Building $service..."
        if docker-compose build "$service"; then
            print_status "$service built successfully"
        else
            print_error "Failed to build $service"
            exit 1
        fi
    done
    
    print_status "All requested services built successfully!"
}

validate_services() {
    local services_to_check=("$@")
    local invalid_services=()
    
    for service in "${services_to_check[@]}"; do
        if [[ ! " ${SERVICES[@]} " =~ " ${service} " ]]; then
            invalid_services+=("$service")
        fi
    done
    
    if  [ ${#invalid_services[@]} -ne 0 ]; then
        print_error "Invalid service(s): ${invalid_services[*]}"
        echo ""
        show_usage
        exit 1
    fi
}

if [ $# -eq 0 ]; then
    show_usage
    exit 0
fi

if [ "$1" = "all" ]; then
    print_info "Building all services..."
    if docker-compose build; then
        print_status "All services built successfully!"
    else
        print_error "Failed to build some services"
        exit 1
    fi
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
else
    validate_services "$@"
    
    build_services "$@"
fi

print_info "Build process completed!"
echo ""
print_info "Tip: Use docker-compose up -d [service] to restart specific services"

