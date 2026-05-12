#!/bin/bash

# LexChain Sovereign Setup Script
set -e

echo "🔷 LexChain Sovereign Setup"
echo "=============================="

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Please install Python 3.12+"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 not found. Please install pip"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo "⚠️  Docker not found. Some features may be limited."
    fi
    
    echo "✅ Prerequisites checked"
}

# Create virtual environment
create_venv() {
    echo ""
    echo "Creating virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment exists"
    fi
    
    source venv/bin/activate
}

# Install dependencies
install_deps() {
    echo ""
    echo "Installing Python dependencies..."
    
    pip install --upgrade pip
    pip install -r backend/requirements.txt
    echo "✅ Dependencies installed"
}

# Setup environment
setup_env() {
    echo ""
    echo "Setting up environment..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "✅ Environment file created from .env.example"
        echo "⚠️  Please update .env with your API keys and secrets"
    else
        echo "⚠️  .env already exists"
    fi
}

# Run database migrations
run_migrations() {
    echo ""
    echo "Running database migrations..."
    
    source venv/bin/activate
    cd backend
    alembic upgrade head
    echo "✅ Migrations complete"
    cd ..
}

# Seed database
seed_database() {
    echo ""
    echo "Seeding database with demo data..."
    
    source venv/bin/activate
    cd backend
    python -m seed_data
    echo "✅ Database seeded"
    cd ..
}

# Main function
main() {
    check_prerequisites
    create_venv
    install_deps
    setup_env
    
    if command -v docker &> /dev/null; then
        read -p "Run database migrations? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            run_migrations
        fi
        
        read -p "Seed database with demo data? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            seed_database
        fi
    fi
    
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "To start the development server:"
    echo "  source venv/bin/activate"
    echo "  cd backend && uvicorn app.main:app --reload --port 8000"
    echo ""
    echo "Or with Docker Compose:"
    echo "  docker-compose up -d"
    echo ""
}

main "$@"