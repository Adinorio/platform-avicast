#!/bin/bash

# AVICAST Local Network Deployment Script
# Quick setup for local network deployment

echo "🚀 AVICAST Local Network Deployment"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip first."
    exit 1
fi

echo "✅ Python and pip are installed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-processing.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment configuration..."
    cp env.example .env
    echo "📝 Please edit .env file with your database settings"
fi

# Run migrations
echo "🗄️ Setting up database..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser account..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(employee_id='010101').exists():
    User.objects.create_superuser(
        employee_id='010101',
        first_name='System',
        last_name='Administrator',
        email='admin@avicast.local',
        password='avicast123'
    )
    print('✅ Superuser created: ID=010101, Password=avicast123')
else:
    print('✅ Superuser already exists')
"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 AVICAST Deployment Complete!"
echo "==============================="
echo ""
echo "🌐 Server Information:"
echo "   Local Access:    http://localhost:8000"
echo "   Network Access:  http://$SERVER_IP:8000"
echo ""
echo "👤 Default Login:"
echo "   Employee ID:     010101"
echo "   Password:        avicast123"
echo "   ⚠️  Change password on first login!"
echo ""
echo "📋 Next Steps:"
echo "   1. Open browser and go to: http://$SERVER_IP:8000"
echo "   2. Login with the credentials above"
echo "   3. Change the default password"
echo "   4. Create user accounts for your team"
echo ""
echo "🔄 To start the server:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🛑 To stop the server: Press Ctrl+C"
echo ""
echo "📚 For more deployment options, see: docs/LOCAL_NETWORK_DEPLOYMENT_GUIDE.md"
echo ""
echo "Happy bird monitoring! 🐦"
