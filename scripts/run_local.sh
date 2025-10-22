#!/bin/bash
# Run StockRL-Agent locally without Docker

set -e

echo "========================================="
echo "StockRL-Agent Local Development Setup"
echo "========================================="

# Check if in project root
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: Please run this script from the project root"
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env to configure your settings"
fi

# Setup backend
echo ""
echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Create demo data
echo "Creating demo user and portfolio..."
python ../scripts/create_demo_user.py

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "To start the backend server:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "Demo login credentials:"
echo "  Username: demo"
echo "  Password: demo123"
