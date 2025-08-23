#!/bin/bash

echo "========================================"
echo "    AVICAST Platform Setup Script"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "✅ Python found"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🆕 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install requirements"
    exit 1
fi

# Create static directory
if [ ! -d "static" ]; then
    echo "📁 Creating static directory..."
    mkdir static
    echo "✅ Static directory created"
fi

# Run Django checks
echo "🔍 Running Django checks..."
python manage.py check
if [ $? -ne 0 ]; then
    echo "❌ Django check failed"
    exit 1
fi

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "❌ Migrations failed"
    exit 1
fi

# Create default superadmin user
echo "👤 Creating default superadmin user..."
python create_default_user.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to create default user"
    exit 1
fi

echo
echo "========================================"
echo "    ✅ Setup Complete!"
echo "========================================"
echo
echo "🚀 To start the server:"
echo "   python manage.py runserver"
echo
echo "🔑 Default login credentials:"
echo "   Username: 010101"
echo "   Password: avicast123"
echo
echo "🌐 Access your app at: http://localhost:8000"
echo
