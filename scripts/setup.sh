#!/bin/bash

# Personal Finance Tracker Setup Script

set -e

echo "🚀 Setting up Personal Finance Tracker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs configs/ssl

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=finance_tracker
DB_SSLMODE=disable

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Application Configuration
PORT=8080
GIN_MODE=release

# Python Configuration
PYTHONPATH=/app
EOF
    echo "✅ Created .env file. Please update the JWT_SECRET and other sensitive values."
fi

# Build and start services
echo "🐳 Building and starting Docker containers..."
docker-compose up -d --build

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec postgres psql -U postgres -d finance_tracker -f /docker-entrypoint-initdb.d/001_initial_schema.up.sql

echo "✅ Setup complete!"
echo ""
echo "🌐 Services are now running:"
echo "  - API: http://localhost:8080"
echo "  - Dashboard: http://localhost:8501"
echo "  - Proxy: http://localhost (routes to dashboard)"
echo ""
echo "📚 API Documentation:"
echo "  - Health Check: http://localhost:8080/api/v1/health"
echo "  - Register: POST http://localhost:8080/api/v1/auth/register"
echo "  - Login: POST http://localhost:8080/api/v1/auth/login"
echo ""
echo "🛠️ Management commands:"
echo "  - Stop: ./scripts/stop.sh"
echo "  - View logs: ./scripts/logs.sh"
echo "  - Backup: ./scripts/backup.sh"
echo "  - Reset: ./scripts/reset.sh"
