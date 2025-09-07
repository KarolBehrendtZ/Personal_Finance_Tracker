

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

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}📋 $1${NC}"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(echo $1 | sed 's/./=/g')${NC}"
}

show_help() {
    print_header "🚀 Deployment Utilities"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Deployment Commands:"
    echo "  setup                 Initial project setup (first time)"
    echo "  quick                 Quick deploy after code changes"
    echo "  full                  Full deployment (rebuild everything)"
    echo "  start                 Start all services"
    echo "  restart [service]     Restart all services or specific service"
    echo "  status                Show deployment status"
    echo "  health                Check application health"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 quick"
    echo "  $0 restart api"
    echo ""
}

setup_project() {
    print_header "🚀 Setting up Personal Finance Tracker"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_info "📁 Creating directories..."
    mkdir -p data logs configs/ssl backups
    
    if [ ! -f .env ]; then
        print_info "📝 Creating .env file..."
        cat > .env << EOF
DB_HOST=postgres
DB_PORT=5432
DB_NAME=finance_tracker
DB_USER=postgres
DB_PASSWORD=postgres123

API_PORT=8080
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

DASHBOARD_PORT=8501
API_URL=http://api:8080/api/v1

ENVIRONMENT=development
DEBUG=true

DATABASE_URL=postgres://postgres:postgres123@postgres:5432/finance_tracker?sslmode=disable
EOF
        print_status ".env file created"
    else
        print_info ".env file already exists"
    fi
    
    print_info "🔨 Building Docker images..."
    docker-compose build
    
    print_info "🚀 Starting services..."
    docker-compose up -d
    
    print_info "⏳ Waiting for database to be ready..."
    sleep 10
    
    print_info "🗃️  Running database migrations..."
    docker-compose exec api go run cmd/migrate/main.go || print_warning "Migrations may have already been run"
    
    check_health
    
    print_status "Setup completed successfully!"
    print_info "🌐 Access the dashboard at: http://localhost:8501"
    print_info "🔗 API available at: http://localhost:8080"
}

quick_deploy() {
    print_header "⚡ Quick Deploy - Rebuilding and Restarting Services"
    
    print_info "🛑 Stopping services..."
    docker-compose down
    
    print_info "🔨 Rebuilding images..."
    docker-compose build
    
    print_info "🚀 Starting services..."
    docker-compose up -d
    
    print_info "⏳ Waiting for services to be ready..."
    sleep 5
    
    check_health
    print_status "Quick deployment completed!"
}

full_deploy() {
    print_header "🔄 Full Deployment - Complete Rebuild"
    
    print_warning "This will rebuild everything from scratch"
    
    print_info "🛑 Stopping and removing containers..."
    docker-compose down --rmi all
    
    print_info "🧹 Cleaning up Docker system..."
    docker system prune -f
    
    print_info "🔨 Building fresh images..."
    docker-compose build --no-cache
    
    print_info "🚀 Starting services..."
    docker-compose up -d
    
    print_info "⏳ Waiting for services to be ready..."
    sleep 10
    
    check_health
    print_status "Full deployment completed!"
}

start_services() {
    print_info "🚀 Starting Personal Finance Tracker services..."
    docker-compose up -d
    
    print_info "⏳ Waiting for services to be ready..."
    sleep 5
    
    check_health
    print_status "All services started!"
}

restart_services() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        print_info "🔄 Restarting all services..."
        docker-compose restart
    else
        print_info "🔄 Restarting $service service..."
        docker-compose restart "$service"
    fi
    
    print_info "⏳ Waiting for services to be ready..."
    sleep 3
    
    if [ -z "$service" ]; then
        check_health
    fi
    
    print_status "Restart completed!"
}

show_status() {
    print_header "📊 Deployment Status"
    
    print_info "🐳 Docker containers:"
    docker-compose ps
    
    echo ""
    print_info "💾 Docker images:"
    docker-compose images
    
    echo ""
    print_info "📊 Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

check_health() {
    print_info "🏥 Checking application health..."
    
    local api_attempts=0
    local api_max_attempts=10
    
    while [ $api_attempts -lt $api_max_attempts ]; do
        if curl -f http://localhost:8080/health >/dev/null 2>&1; then
            print_status "API is healthy"
            break
        else
            api_attempts=$((api_attempts + 1))
            if [ $api_attempts -eq $api_max_attempts ]; then
                print_error "API health check failed after $api_max_attempts attempts"
                print_info "API logs:"
                docker-compose logs --tail=10 api
            else
                print_info "Waiting for API... attempt $api_attempts/$api_max_attempts"
                sleep 2
            fi
        fi
    done
    
    local dashboard_attempts=0
    local dashboard_max_attempts=10
    
    while [ $dashboard_attempts -lt $dashboard_max_attempts ]; do
        if curl -f http://localhost:8501 >/dev/null 2>&1; then
            print_status "Dashboard is healthy"
            break
        else
            dashboard_attempts=$((dashboard_attempts + 1))
            if [ $dashboard_attempts -eq $dashboard_max_attempts ]; then
                print_error "Dashboard health check failed after $dashboard_max_attempts attempts"
                print_info "Dashboard logs:"
                docker-compose logs --tail=10 dashboard
            else
                print_info "Waiting for Dashboard... attempt $dashboard_attempts/$dashboard_max_attempts"
                sleep 2
            fi
        fi
    done
    
    if docker-compose exec postgres pg_isready -U postgres >/dev/null 2>&1; then
        print_status "Database is healthy"
    else
        print_error "Database health check failed"
    fi
    
    print_info "🌐 Access URLs:"
    print_info "  Dashboard: http://localhost:8501"
    print_info "  API: http://localhost:8080"
    print_info "  API Health: http://localhost:8080/health"
}

case "${1:-help}" in
    "setup")
        setup_project
        ;;
    "quick")
        quick_deploy
        ;;
    "full")
        full_deploy
        ;;
    "start")
        start_services
        ;;
    "restart")
        restart_services "$2"
        ;;
    "status")
        show_status
        ;;
    "health")
        check_health
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
