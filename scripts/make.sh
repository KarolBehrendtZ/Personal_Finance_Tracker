#!/bin/bash

# Make-style command interface for Personal Finance Tracker
# Provides easy access to common development tasks

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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

show_help() {
    print_header "🛠️  Personal Finance Tracker - Make Commands"
    echo ""
    echo "Usage: $0 <command> [args...]"
    echo ""
    echo "📦 Build Commands:"
    echo "  build [service...]    Build specific services or all if no service specified"
    echo "  build-all            Build all services"
    echo ""
    echo "🚀 Deployment Commands:"
    echo "  deploy               Quick deploy - build all and restart services"
    echo "  start                Start all services"
    echo "  stop                 Stop all services"
    echo "  restart [service]    Restart specific service or all services"
    echo ""
    echo "📊 Monitoring Commands:"
    echo "  status               Show status of all services"
    echo "  logs [service]       Show logs for specific service or all services"
    echo "  follow [service]     Follow logs for specific service"
    echo "  watch                Start development watch mode"
    echo ""
    echo "🗃️  Database Commands:"
    echo "  db-reset             Reset database and regenerate sample data"
    echo "  db-shell             Open PostgreSQL shell"
    echo "  generate-data        Generate sample data"
    echo ""
    echo "🧪 Testing Commands:"
    echo "  test-api             Test API endpoints"
    echo "  health               Check service health"
    echo ""
    echo "🧹 Cleanup Commands:"
    echo "  clean                Clean up stopped containers and images"
    echo "  clean-all            Clean up everything (containers, images, volumes)"
    echo ""
    echo "Examples:"
    echo "  $0 deploy            # Full deployment"
    echo "  $0 build api         # Build only API service"
    echo "  $0 logs dashboard    # Show dashboard logs"
    echo "  $0 watch             # Start development mode"
}

case "${1:-help}" in
    "build")
        if [ $# -eq 1 ]; then
            print_info "Building all services..."
            docker-compose build
        else
            shift
            print_info "Building services: $*"
            "$SCRIPT_DIR/build.sh" "$@"
        fi
        ;;
        
    "build-all")
        print_info "Building all services..."
        docker-compose build
        ;;
        
    "deploy")
        print_info "Starting quick deployment..."
        "$SCRIPT_DIR/quick_deploy.sh"
        ;;
        
    "start")
        print_info "Starting all services..."
        docker-compose up -d
        print_status "All services started"
        ;;
        
    "stop")
        print_info "Stopping all services..."
        docker-compose down
        print_status "All services stopped"
        ;;
        
    "restart")
        if [ $# -eq 1 ]; then
            print_info "Restarting all services..."
            docker-compose restart
        else
            print_info "Restarting service: $2"
            docker-compose restart "$2"
        fi
        print_status "Restart completed"
        ;;
        
    "status")
        print_info "Service status:"
        docker-compose ps
        ;;
        
    "logs")
        if [ $# -eq 1 ]; then
            print_info "Showing logs for all services..."
            docker-compose logs --tail=50
        else
            print_info "Showing logs for service: $2"
            docker-compose logs --tail=50 "$2"
        fi
        ;;
        
    "follow")
        if [ $# -eq 1 ]; then
            print_info "Following logs for all services..."
            docker-compose logs -f
        else
            print_info "Following logs for service: $2"
            docker-compose logs -f "$2"
        fi
        ;;
        
    "watch")
        print_info "Starting development watch mode..."
        "$SCRIPT_DIR/dev_watch.sh"
        ;;
        
    "db-reset")
        print_info "Resetting database and regenerating sample data..."
        docker-compose down
        docker volume rm project_postgres_data 2>/dev/null || true
        docker-compose up -d postgres
        sleep 5
        docker-compose up -d api
        sleep 5
        docker-compose run --rm etl_worker python sample_data_generator.py
        print_status "Database reset and sample data generated"
        ;;
        
    "db-shell")
        print_info "Opening PostgreSQL shell..."
        docker-compose exec postgres psql -U postgres -d finance_db
        ;;
        
    "generate-data")
        print_info "Generating sample data..."
        docker-compose run --rm etl_worker python sample_data_generator.py
        print_status "Sample data generated"
        ;;
        
    "test-api")
        print_info "Testing API endpoints..."
        echo ""
        echo "Testing health endpoint:"
        curl -s http://localhost:8080/health | head -c 200
        echo ""
        echo ""
        echo "Testing auth endpoint:"
        curl -s -X POST http://localhost:8080/api/auth/login \
             -H "Content-Type: application/json" \
             -d '{"email":"john.doe@example.com","password":"password123"}' | head -c 200
        echo ""
        ;;
        
    "health")
        print_info "Checking service health..."
        echo ""
        
        # Check database
        if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            print_status "Database: OK"
        else
            print_error "Database: NOT READY"
        fi
        
        # Check API
        if curl -s http://localhost:8080/health >/dev/null 2>&1; then
            print_status "API: OK"
        else
            print_error "API: NOT RESPONDING"
        fi
        
        # Check dashboard
        if curl -s http://localhost:8501 >/dev/null 2>&1; then
            print_status "Dashboard: OK"
        else
            print_error "Dashboard: NOT RESPONDING"
        fi
        ;;
        
    "clean")
        print_info "Cleaning up stopped containers and unused images..."
        docker system prune -f
        print_status "Cleanup completed"
        ;;
        
    "clean-all")
        print_warning "This will remove all containers, images, and volumes!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v
            docker system prune -a -f --volumes
            print_status "Complete cleanup completed"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
        
    "help"|"--help"|"-h"|*)
        show_help
        ;;
esac
