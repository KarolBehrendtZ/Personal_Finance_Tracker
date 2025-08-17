#!/bin/bash

# Reset the entire application (WARNING: This will delete all data!)

echo "⚠️  WARNING: This will delete all data and reset the application!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Resetting application..."
    
    # Stop all services
    docker-compose down
    
    # Remove volumes (this deletes all data!)
    docker-compose down -v
    
    # Remove images
    docker-compose down --rmi all
    
    # Clean up
    docker system prune -f
    
    echo "✅ Application reset complete!"
    echo "Run ./scripts/setup.sh to start fresh."
else
    echo "❌ Reset cancelled."
fi
