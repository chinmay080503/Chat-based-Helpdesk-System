#!/usr/bin/env bash

# Exit immediately if a command fails
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Applying database migrations..."
python manage.py migrate

# Optional: Create admin user (runs only if not exists)
echo "from core.models import User; \
User.objects.filter(username='admin').exists() or \
User.objects.create_superuser('admin', 'admin@example.com', 'yourpassword', role='admin')" | python manage.py shell

echo "Build completed successfully!"