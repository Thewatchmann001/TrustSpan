#!/bin/bash
# Database Setup Script for TrustSpan
# This script helps set up PostgreSQL database for the application

set -e

echo "🔧 TrustSpan Database Setup"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL is not installed!${NC}"
    echo "Please install PostgreSQL first:"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL is installed${NC}"

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql 2>/dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL is not running. Attempting to start...${NC}"
    sudo systemctl start postgresql || {
        echo -e "${RED}❌ Failed to start PostgreSQL. Please start it manually.${NC}"
        exit 1
    }
    sleep 2
fi

echo -e "${GREEN}✅ PostgreSQL is running${NC}"

# Create database and user
echo ""
echo "Creating database and user..."
sudo -u postgres psql <<EOF
-- Create database if it doesn't exist
SELECT 'CREATE DATABASE trustspandb'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trustspandb')\gexec

-- Create user if it doesn't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'trustspan') THEN
        CREATE USER trustspan WITH PASSWORD 'trustspan';
    END IF;
END
\$\$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trustspandb TO trustspan;
ALTER DATABASE trustspandb OWNER TO trustspan;
EOF

echo -e "${GREEN}✅ Database and user created${NC}"

# Run migrations
echo ""
echo "Running database migrations..."
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Virtual environment not found. Please activate it manually.${NC}"
    echo "Then run: alembic upgrade head"
    exit 1
}

alembic upgrade head
echo -e "${GREEN}✅ Database migrations completed${NC}"

# Ask if user wants to seed the database
echo ""
read -p "Do you want to seed the database with sample data? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Seeding database..."
    python scripts/seed_database.py
    echo -e "${GREEN}✅ Database seeded with sample data${NC}"
    echo ""
    echo "You can now login with:"
    echo "  Email: alice@example.com"
    echo "  Password: password123"
fi

echo ""
echo -e "${GREEN}🎉 Database setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start the backend server: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "2. If you need to create a new user, register via the API: POST /api/users/register"
