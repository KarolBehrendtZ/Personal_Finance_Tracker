#!/bin/bash

# Sample Data Generator Script for Personal Finance Tracker
# This script generates sample data for testing and development

set -e

echo "🚀 Personal Finance Tracker - Sample Data Generator"
echo "=================================================="

# Check if Docker Compose is running
if ! docker-compose ps | grep -q "finance_db.*Up"; then
    echo "❌ Database container is not running!"
    echo "Please start the database first: docker-compose up postgres"
    exit 1
fi

echo "✅ Database container is running"

# Check if ETL container is available
if ! docker-compose ps | grep -q "finance_etl"; then
    echo "❌ ETL container is not available!"
    echo "Please build and start containers: docker-compose up --build"
    exit 1
fi

echo "✅ ETL container is available"

# Prompt user for confirmation
echo ""
echo "This will generate sample data in your database:"
echo "  - 3 sample users with login credentials"
echo "  - Multiple accounts per user"
echo "  - Income and expense categories"
echo "  - 1000+ realistic transactions"
echo "  - Budget rules"
echo ""
read -p "Do you want to continue? [y/N]: " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled"
    exit 0
fi

# Option to clear existing data
echo ""
read -p "Do you want to clear existing data first? [y/N]: " clear_data

# Run the sample data generator
echo ""
echo "📊 Generating sample data..."

if [[ $clear_data =~ ^[Yy]$ ]]; then
    echo "🗑️  Clearing existing data..."
    docker-compose exec etl_worker python -c "
from python.etl.sample_data_generator import SampleDataGenerator
generator = SampleDataGenerator()
generator.clear_all_data()
generator.close()
print('Data cleared successfully!')
"
fi

echo "🏗️  Creating sample data..."
docker-compose exec etl_worker python python/etl/sample_data_generator.py

echo ""
echo "✅ Sample data generation completed!"
echo ""
echo "🌐 You can now access the application:"
echo "   Dashboard: http://localhost:8501"
echo "   API: http://localhost:8080"
echo ""
echo "👥 Sample login credentials:"
echo "   Email: john.doe@example.com"
echo "   Password: password123"
echo ""
echo "   Email: jane.smith@example.com"
echo "   Password: password123"
echo ""
echo "   Email: mike.johnson@example.com"
echo "   Password: password123"
echo ""
echo "🎯 Happy testing!"
