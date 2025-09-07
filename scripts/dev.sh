

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
    print_header "🔧 Development Utilities"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Development Commands:"
    echo "  watch [service]       Start file watching for auto-rebuild (default: all)"
    echo "  reset                 Reset entire application (destroys all data!)"
    echo "  init-sample-csv       Create sample CSV file for testing imports"
    echo "  test-imports          Test CSV import functionality"
    echo "  benchmark             Run performance benchmarks"
    echo "  lint                  Run code linting"
    echo "  format                Format code"
    echo "  backup-db             Create database backup"
    echo "  restore-db [file]     Restore database from backup"
    echo "  run-migrations        Run database migrations"
    echo ""
    echo "Examples:"
    echo "  $0 watch api"
    echo "  $0 watch"
    echo "  $0 reset"
    echo ""
}

dev_watch() {
    local service=${1:-"all"}
    
    print_header "👀 Starting Development Watch Mode"
    print_info "Monitoring changes for: $service"
    print_warning "Press Ctrl+C to stop watching"
    
    if ! command -v inotifywait &> /dev/null; then
        print_error "inotify-tools not installed. Installing..."
        sudo apt-get update && sudo apt-get install -y inotify-tools
    fi
    
    while true; do
        inotifywait -r -e modify,create,delete \
            --include '\.(go|py|js|ts|tsx|css|html|yml|yaml)$' \
            ./internal ./dashboard ./cmd 2>/dev/null || true
        
        print_info "🔄 Changes detected, rebuilding..."
        
        if [ "$service" = "all" ] || [ "$service" = "api" ]; then
            print_info "Rebuilding API..."
            docker-compose build api
            docker-compose up -d api
        fi
        
        if [ "$service" = "all" ] || [ "$service" = "dashboard" ]; then
            print_info "Rebuilding Dashboard..."
            docker-compose build dashboard
            docker-compose up -d dashboard
        fi
        
        print_status "Rebuild complete!"
        sleep 2
    done
}

dev_reset() {
    print_warning "This will delete all data and reset the application!"
    read -p "Are you sure you want to continue? y/N: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "🔄 Resetting application..."
        
        docker-compose down
        
        docker-compose down -v
        
        docker-compose down --rmi all
        
        docker system prune -f
        
        print_status "Application reset complete!"
        print_info "Run ./scripts/deploy.sh setup to start fresh."
    else
        print_error "Reset cancelled."
    fi
}

init_sample_csv() {
    print_info "Creating sample CSV file..."
    
    cat > sample_transactions.csv << EOF
date,amount,description,category,type
2024-01-01,50.00,Grocery shopping,Food,expense
2024-01-02,3000.00,Salary,Income,income
2024-01-03,25.99,Netflix subscription,Entertainment,expense
2024-01-04,12.50,Coffee,Food,expense
2024-01-05,75.00,Gas station,Transportation,expense
2024-01-06,150.00,Electricity bill,Utilities,expense
2024-01-07,45.00,Restaurant dinner,Food,expense
2024-01-08,100.00,Freelance work,Income,income
2024-01-09,30.00,Gym membership,Health,expense
2024-01-10,200.00,Investment return,Income,income
EOF
    
    print_status "Sample CSV created: sample_transactions.csv"
}

test_imports() {
    print_info "Testing CSV import functionality..."
    
    if [ ! -f "sample_transactions.csv" ]; then
        print_warning "Sample CSV not found, creating it first..."
        init_sample_csv
    fi
    
    if curl -f -X POST -H "Content-Type: multipart/form-data" \
       -F "file=@sample_transactions.csv" \
       http://localhost:8080/api/v1/transactions/import 2>/dev/null; then
        print_status "CSV import test successful!"
    else
        print_error "CSV import test failed. Is the API running?"
    fi
}

backup_db() {
    print_info "Creating database backup..."
    
    BACKUP_DIR="./backups"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="finance_tracker_backup_${TIMESTAMP}.sql"
    
    mkdir -p $BACKUP_DIR
    
    if docker-compose exec -T postgres pg_dump -U postgres finance_tracker > "${BACKUP_DIR}/${BACKUP_FILE}"; then
        gzip "${BACKUP_DIR}/${BACKUP_FILE}"
        print_status "Backup created: ${BACKUP_DIR}/${BACKUP_FILE}.gz"
        
        ls -t ${BACKUP_DIR}/finance_tracker_backup_*.sql.gz | tail -n +11 | xargs -r rm
    else
        print_error "Database backup failed!"
        exit 1
    fi
}

restore_db() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Please specify backup file to restore"
        echo "Usage: $0 restore-db <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_warning "This will overwrite the current database!"
    read -p "Are you sure you want to continue? y/N: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Restoring database from: $backup_file"
        
        if [[ $backup_file == *.gz ]]; then
            zcat "$backup_file" | docker-compose exec -T postgres psql -U postgres -d finance_tracker
        else
            cat "$backup_file" | docker-compose exec -T postgres psql -U postgres -d finance_tracker
        fi
        
        print_status "Database restored successfully!"
    else
        print_error "Restore cancelled."
    fi
}

run_migrations() {
    print_info "Running database migrations..."
    
    if docker-compose exec api go run cmd/migrate/main.go; then
        print_status "Migrations completed successfully!"
    else
        print_error "Migration failed!"
        exit 1
    fi
}

lint_code() {
    print_info "Running code linting..."
    
    if command -v golangci-lint &> /dev/null; then
        print_info "Linting Go code..."
        golangci-lint run ./...
    else
        print_warning "golangci-lint not found, using go vet..."
        go vet ./...
    fi
    
    if command -v flake8 &> /dev/null; then
        print_info "Linting Python code..."
        flake8 dashboard/ --max-line-length=100
    else
        print_warning "flake8 not found, skipping Python linting"
    fi
    
    print_status "Linting completed!"
}

format_code() {
    print_info "Formatting code..."
    
    print_info "Formatting Go code..."
    go fmt ./...
    
    if command -v black &> /dev/null; then
        print_info "Formatting Python code..."
        black dashboard/ --line-length=100
    else
        print_warning "black not found, skipping Python formatting"
    fi
    
    print_status "Code formatting completed!"
}

run_benchmarks() {
    print_info "Running performance benchmarks..."
    
    print_info "Running Go benchmarks..."
    go test -bench=. ./...
    
    print_status "Benchmarks completed!"
}

case "${1:-help}" in
    "watch")
        dev_watch "$2"
        ;;
    "reset")
        dev_reset
        ;;
    "init-sample-csv")
        init_sample_csv
        ;;
    "test-imports")
        test_imports
        ;;
    "backup-db")
        backup_db
        ;;
    "restore-db")
        restore_db "$2"
        ;;
    "run-migrations")
        run_migrations
        ;;
    "lint")
        lint_code
        ;;
    "format")
        format_code
        ;;
    "benchmark")
        run_benchmarks
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
