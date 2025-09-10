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
    print_header "🔧 Management Utilities"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Management Commands:"
    echo "  logs [service]        View logs for all services or specific service"
    echo "  stop [service]        Stop all services or specific service"
    echo "  backup [type]         Create backup (db, full, or files)"
    echo "  restore <file>        Restore from backup file"
    echo "  clean                 Clean up Docker resources"
    echo "  monitor               Real-time system monitoring"
    echo "  export                Export application data"
    echo "  import <file>         Import application data"
    echo ""
    echo "Examples:"
    echo "  $0 logs api"
    echo "  $0 logs dashboard"
    echo "  $0 backup db"
    echo "  $0 backup full"
    echo "  $0 stop"
    echo ""
}

view_logs() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        print_info "📋 Showing logs for all services..."
        print_warning "Press Ctrl+C to stop following logs"
        docker-compose logs -f
    else
        print_info "📋 Showing logs for $service..."
        print_warning "Press Ctrl+C to stop following logs"
        docker-compose logs -f "$service"
    fi
}

stop_services() {
    local service=${1:-""}
    
    if [ -z "$service" ]; then
        print_info "🛑 Stopping all Personal Finance Tracker services..."
        docker-compose down
        print_status "All services stopped!"
    else
        print_info "🛑 Stopping $service service..."
        docker-compose stop "$service"
        print_status "$service service stopped!"
    fi
}

create_backup() {
    local backup_type=${1:-"db"}
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_dir="./backups"
    
    mkdir -p "$backup_dir"
    
    case "$backup_type" in
        "db"|"database")
            backup_database "$timestamp" "$backup_dir"
            ;;
        "files")
            backup_files "$timestamp" "$backup_dir"
            ;;
        "full")
            backup_database "$timestamp" "$backup_dir"
            backup_files "$timestamp" "$backup_dir"
            backup_config "$timestamp" "$backup_dir"
            ;;
        *)
            print_error "Unknown backup type: $backup_type"
            print_info "Available types: db, files, full"
            exit 1
            ;;
    esac
}

backup_database() {
    local timestamp=$1
    local backup_dir=$2
    local backup_file="finance_tracker_db_backup_${timestamp}.sql"
    
    print_info "📦 Creating database backup..."
    
    if docker-compose exec -T postgres pg_dump -U postgres finance_tracker > "${backup_dir}/${backup_file}"; then
        gzip "${backup_dir}/${backup_file}"
        print_status "Database backup created: ${backup_dir}/${backup_file}.gz"
        
        print_info "🧹 Cleaning up old database backups..."
        ls -t ${backup_dir}/finance_tracker_db_backup_*.sql.gz 2>/dev/null | tail -n +11 | xargs -r rm
        
        return 0
    else
        print_error "Database backup failed!"
        return 1
    fi
}

backup_files() {
    local timestamp=$1
    local backup_dir=$2
    local backup_file="finance_tracker_files_backup_${timestamp}.tar.gz"
    
    print_info "📁 Creating files backup..."
    
    tar -czf "${backup_dir}/${backup_file}" \
        --exclude='./backups' \
        --exclude='./logs' \
        --exclude='./.git' \
        --exclude='./node_modules' \
        --exclude='./__pycache__' \
        --exclude='./data/postgres' \
        . 2>/dev/null || true
    
    if [ -f "${backup_dir}/${backup_file}" ]; then
        print_status "Files backup created: ${backup_dir}/${backup_file}"
        
        print_info "🧹 Cleaning up old file backups..."
        ls -t ${backup_dir}/finance_tracker_files_backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm
        
        return 0
    else
        print_error "Files backup failed!"
        return 1
    fi
}

backup_config() {
    local timestamp=$1
    local backup_dir=$2
    local backup_file="finance_tracker_config_backup_${timestamp}.tar.gz"
    
    print_info "⚙️  Creating configuration backup..."
    
    tar -czf "${backup_dir}/${backup_file}" \
        .env \
        docker-compose.yml \
        configs/ \
        scripts/ 2>/dev/null || true
    
    if [ -f "${backup_dir}/${backup_file}" ]; then
        print_status "Configuration backup created: ${backup_dir}/${backup_file}"
        return 0
    else
        print_error "Configuration backup failed!"
        return 1
    fi
}

restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Please specify backup file to restore"
        print_info "Available backups:"
        ls -la ./backups/ 2>/dev/null || print_warning "No backups found"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_warning "This operation may overwrite existing data!"
    read -p "Are you sure you want to continue? y/N: " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Restore cancelled."
        exit 1
    fi
    
    if [[ $backup_file == *"_db_backup_"* ]]; then
        restore_database "$backup_file"
    elif [[ $backup_file == *"_files_backup_"* ]]; then
        restore_files "$backup_file"
    elif [[ $backup_file == *"_config_backup_"* ]]; then
        restore_config "$backup_file"
    else
        print_error "Cannot determine backup type from filename"
        exit 1
    fi
}

restore_database() {
    local backup_file=$1
    
    print_info "🗃️  Restoring database from: $backup_file"
    
    if [[ $backup_file == *.gz ]]; then
        zcat "$backup_file" | docker-compose exec -T postgres psql -U postgres -d finance_tracker
    else
        cat "$backup_file" | docker-compose exec -T postgres psql -U postgres -d finance_tracker
    fi
    
    print_status "Database restored successfully!"
}

restore_files() {
    local backup_file=$1
    
    print_info "📁 Restoring files from: $backup_file"
    
    tar -xzf "$backup_file"
    
    print_status "Files restored successfully!"
}

restore_config() {
    local backup_file=$1
    
    print_info "⚙️  Restoring configuration from: $backup_file"
    
    tar -xzf "$backup_file"
    
    print_status "Configuration restored successfully!"
}

clean_docker() {
    print_warning "This will remove unused Docker resources"
    read -p "Continue? y/N: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "🧹 Cleaning up Docker resources..."
        
        docker container prune -f
        
        docker image prune -f
        
        docker volume prune -f
        
        docker network prune -f
        
        print_status "Docker cleanup completed!"
    else
        print_info "Cleanup cancelled."
    fi
}

monitor_system() {
    print_header "📊 Real-time System Monitoring"
    print_warning "Press Ctrl+C to stop monitoring"
    
    while true; do
        clear
        echo -e "${PURPLE}Personal Finance Tracker - System Monitor${NC}"
        echo -e "${PURPLE}$(date)${NC}"
        echo ""
        
        print_info "🐳 Container Status:"
        docker-compose ps
        
        echo ""
        print_info "📊 Resource Usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
        
        echo ""
        print_info "💾 Disk Usage:"
        df -h | grep -E "^/dev|Filesystem"
        
        sleep 5
    done
}

export_data() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local export_dir="./exports"
    local export_file="finance_tracker_export_${timestamp}.json"
    
    mkdir -p "$export_dir"
    
    print_info "📤 Exporting application data..."
    
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        if curl -f -o "${export_dir}/${export_file}" http://localhost:8080/api/v1/export; then
            print_status "Data exported: ${export_dir}/${export_file}"
        else
            print_error "API export failed, falling back to database export"
            backup_database "$timestamp" "$export_dir"
        fi
    else
        print_warning "API not available, creating database backup instead"
        backup_database "$timestamp" "$export_dir"
    fi
}

import_data() {
    local import_file=$1
    
    if [ -z "$import_file" ]; then
        print_error "Please specify import file"
        exit 1
    fi
    
    if [ ! -f "$import_file" ]; then
        print_error "Import file not found: $import_file"
        exit 1
    fi
    
    print_info "📥 Importing application data from: $import_file"
    
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        if curl -f -X POST -F "file=@${import_file}" http://localhost:8080/api/v1/import; then
            print_status "Data imported successfully!"
        else
            print_error "API import failed"
            exit 1
        fi
    else
        print_error "API not available for import"
        exit 1
    fi
}

case "${1:-help}" in
    "logs")
        view_logs "$2"
        ;;
    "stop")
        stop_services "$2"
        ;;
    "backup")
        create_backup "$2"
        ;;
    "restore")
        restore_backup "$2"
        ;;
    "clean")
        clean_docker
        ;;
    "monitor")
        monitor_system
        ;;
    "export")
        export_data
        ;;
    "import")
        import_data "$2"
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
