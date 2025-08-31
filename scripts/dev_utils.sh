#!/bin/bash

# Development utilities script for Personal Finance Tracker
# Collection of useful development tasks

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

show_help() {
    print_header "🔧 Development Utilities"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Available commands:"
    echo "  init-sample-csv    Create sample CSV file for testing imports"
    echo "  backup-db         Create database backup"
    echo "  restore-db        Restore database from backup"
    echo "  run-migrations    Run database migrations"
    echo "  test-imports      Test CSV import functionality"
    echo "  benchmark         Run performance benchmarks"
    echo "  lint              Run code linting"
    echo "  format            Format code"
    echo ""
}

init_sample_csv() {
    print_info "Creating sample CSV file for testing imports..."
    
    cat > sample_bank_export.csv << 'EOF'
Date,Description,Amount,Type,Category
2024-01-15,Grocery Store Purchase,-85.50,expense,groceries
2024-01-16,Salary Deposit,3500.00,income,salary
2024-01-17,Gas Station,-45.20,expense,transport
2024-01-18,Restaurant Dinner,-67.80,expense,restaurant
2024-01-19,Electric Bill,-120.00,expense,utilities
2024-01-20,Amazon Purchase,-39.99,expense,shopping
2024-01-21,ATM Withdrawal,-100.00,expense,cash
2024-01-22,Coffee Shop,-4.50,expense,restaurant
2024-01-23,Pharmacy,-25.30,expense,healthcare
2024-01-24,Uber Ride,-18.75,expense,transport
2024-01-25,Freelance Payment,750.00,income,freelance
2024-01-26,Supermarket,-92.15,expense,groceries
2024-01-27,Internet Bill,-59.99,expense,utilities
2024-01-28,Movie Theater,-24.00,expense,entertainment
2024-01-29,Bank Interest,2.50,income,interest
2024-01-30,Gym Membership,-49.99,expense,fitness
EOF

    print_status "Sample CSV created: sample_bank_export.csv"
    print_info "You can test imports with: docker-compose run --rm etl_worker python transaction_importer.py"
}

backup_db() {
    print_info "Creating database backup..."
    
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    if docker-compose exec -T postgres pg_dump -U postgres finance_db > "$backup_file"; then
        print_status "Database backup created: $backup_file"
    else
        print_error "Failed to create database backup"
        exit 1
    fi
}

restore_db() {
    print_info "Available backup files:"
    ls -la backup_*.sql 2>/dev/null || { print_error "No backup files found"; exit 1; }
    
    echo ""
    read -p "Enter backup filename to restore: " backup_file
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_info "Restoring database from $backup_file..."
    print_info "This will replace all existing data!"
    
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose exec -T postgres psql -U postgres -d finance_db < "$backup_file"
        print_status "Database restored from $backup_file"
    else
        print_info "Restore cancelled"
    fi
}

run_migrations() {
    print_info "Running database migrations..."
    
    # Check if migrations directory exists
    if [ -d "migrations" ]; then
        print_info "Found migrations directory"
        # Run migrations if you have a migration tool
        # docker-compose run --rm api go run migrations/*.go
        print_info "Migration functionality would go here"
    else
        print_info "No migrations directory found"
    fi
    
    # For now, just ensure tables exist by restarting API
    print_info "Ensuring database schema is up to date..."
    docker-compose restart api
    print_status "Database schema check completed"
}

test_imports() {
    print_info "Testing CSV import functionality..."
    
    # First create sample CSV if it doesn't exist
    if [ ! -f "sample_bank_export.csv" ]; then
        init_sample_csv
    fi
    
    # Copy CSV to container and test import
    print_info "Copying sample CSV to ETL container..."
    docker cp sample_bank_export.csv $(docker-compose ps -q etl_worker):/app/sample_bank_export.csv
    
    print_info "Running import test..."
    docker-compose exec etl_worker python -c "
from transaction_importer import TransactionImporter
importer = TransactionImporter()
count = importer.import_csv('sample_bank_export.csv', user_id=1, account_id=1)
print(f'Imported {count} transactions')
importer.close()
"
    
    print_status "Import test completed"
}

benchmark() {
    print_info "Running performance benchmarks..."
    
    print_info "Testing API response times..."
    
    # Test health endpoint
    echo "Health endpoint:"
    time curl -s http://localhost:8080/health > /dev/null
    
    # Test auth endpoint
    echo "Auth endpoint:"
    time curl -s -X POST http://localhost:8080/api/auth/login \
         -H "Content-Type: application/json" \
         -d '{"email":"john.doe@example.com","password":"password123"}' > /dev/null
    
    print_status "Benchmark completed"
}

lint_code() {
    print_info "Running code linting..."
    
    # Go linting
    if command -v golangci-lint &> /dev/null; then
        print_info "Linting Go code..."
        golangci-lint run
    else
        print_info "golangci-lint not found, using go vet..."
        docker-compose run --rm api go vet ./...
    fi
    
    # Python linting
    print_info "Linting Python code..."
    docker-compose run --rm etl_worker python -m flake8 python/ || print_info "flake8 not available"
    
    print_status "Linting completed"
}

format_code() {
    print_info "Formatting code..."
    
    # Go formatting
    print_info "Formatting Go code..."
    docker-compose run --rm api go fmt ./...
    
    # Python formatting
    print_info "Formatting Python code..."
    docker-compose run --rm etl_worker python -m black python/ || print_info "black not available"
    
    print_status "Code formatting completed"
}

# Main command processing
case "${1:-help}" in
    "init-sample-csv")
        init_sample_csv
        ;;
    "backup-db")
        backup_db
        ;;
    "restore-db")
        restore_db
        ;;
    "run-migrations")
        run_migrations
        ;;
    "test-imports")
        test_imports
        ;;
    "benchmark")
        benchmark
        ;;
    "lint")
        lint_code
        ;;
    "format")
        format_code
        ;;
    "help"|"--help"|"-h"|*)
        show_help
        ;;
esac
