# 🚀 TrustSpan - Complete Setup Guide

**A step-by-step guide for setting up TrustSpan from scratch**

This guide will walk you through setting up the entire TrustSpan platform, from cloning the repository to running both frontend and backend services.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone the Repository](#clone-the-repository)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Database Setup](#database-setup)
6. [Environment Configuration](#environment-configuration)
7. [Job Platform API Keys Setup](#job-platform-api-keys-setup)
8. [Run Database Migrations](#run-database-migrations)
9. [Start the Application](#start-the-application)
10. [Verify Installation](#verify-installation)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software

1. **Git** - For cloning the repository
   ```bash
   # Check if Git is installed
   git --version
   
   # If not installed:
   # Ubuntu/Debian:
   sudo apt-get install git
   # macOS:
   brew install git
   # Windows: Download from https://git-scm.com/
   ```

2. **Python 3.12+** - For the backend
   ```bash
   # Check Python version
   python3 --version
   # Should show Python 3.12.x or higher
   
   # If not installed:
   # Ubuntu/Debian:
   sudo apt-get install python3.12 python3.12-venv python3-pip
   # macOS:
   brew install python@3.12
   # Windows: Download from https://www.python.org/downloads/
   ```

3. **Node.js 18+ and npm** - For the frontend
   ```bash
   # Check Node.js version
   node --version
   # Should show v18.x.x or higher
   
   # Check npm version
   npm --version
   
   # If not installed:
   # Ubuntu/Debian:
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   # macOS:
   brew install node
   # Windows: Download from https://nodejs.org/
   ```

4. **PostgreSQL 14+** - For the database
   ```bash
   # Check PostgreSQL version
   psql --version
   # Should show PostgreSQL 14.x or higher
   
   # If not installed:
   # Ubuntu/Debian:
   sudo apt-get install postgresql postgresql-contrib
   # macOS:
   brew install postgresql@14
   # Windows: Download from https://www.postgresql.org/download/windows/
   ```

### Optional (for blockchain features)

5. **Rust and Solana CLI** - Only needed if you want to deploy blockchain programs
   ```bash
   # Install Rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Install Solana CLI
   sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
   ```

---

## Clone the Repository

1. **Open your terminal/command prompt**

2. **Navigate to where you want to clone the project**
   ```bash
   cd ~/projects  # or wherever you keep your projects
   ```

3. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/trustspan.git
   # Replace 'yourusername' with the actual GitHub username/organization
   ```

4. **Navigate into the project directory**
   ```bash
   cd trustspan
   ```

5. **Verify the project structure**
   ```bash
   ls -la
   # You should see: backend/, frontend/, blockchain/, docs/, etc.
   ```

---

## Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# On macOS/Linux, activate it:
source venv/bin/activate

# On Windows, activate it:
# venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### Step 3: Upgrade pip (Recommended)

```bash
pip install --upgrade pip
```

### Step 4: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This will install:
# - FastAPI and uvicorn (web framework)
# - SQLAlchemy and psycopg2 (database)
# - Mistral AI (for AI features)
# - Solana libraries (for blockchain)
# - ReportLab and python-docx (for document generation)
# - And many more...
```

**Expected output:** You should see packages being installed. This may take 2-5 minutes.

### Step 5: Verify Backend Installation

```bash
# Check if key packages are installed
pip list | grep -E "fastapi|sqlalchemy|mistralai|solana"

# You should see these packages listed
```

---

## Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
# From project root
cd frontend
```

### Step 2: Install Node.js Dependencies

```bash
# Install all npm packages
npm install

# This will install:
# - Next.js and React (frontend framework)
# - Tailwind CSS (styling)
# - Solana Wallet Adapter (blockchain integration)
# - Axios (HTTP client)
# - And many more...
```

**Expected output:** You should see packages being installed. This may take 2-5 minutes.

### Step 3: Verify Frontend Installation

```bash
# Check if node_modules exists
ls node_modules

# You should see a large node_modules directory
```

---

## Database Setup

### Step 1: Start PostgreSQL Service

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# If not running, start it:
sudo systemctl start postgresql

# On macOS:
brew services start postgresql@14

# On Windows:
# PostgreSQL should run as a service automatically
```

### Step 2: Create Database and User

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Or on macOS/Windows:
psql -U postgres
```

**Inside PostgreSQL prompt, run:**

```sql
-- Create database
CREATE DATABASE trustspandb;

-- Create user
CREATE USER trustspan WITH PASSWORD 'trustspan';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE trustspandb TO trustspan;

-- Exit PostgreSQL
\q
```

### Step 3: Verify Database Creation

```bash
# Test connection
psql -U trustspan -d trustspandb -h localhost

# If it connects successfully, type \q to exit
```

---

## Environment Configuration

### Backend Environment Variables

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create `.env` file**
   ```bash
   # If .env.example exists, copy it:
   cp .env.example .env
   
   # Or create a new .env file:
   touch .env
   ```

3. **Edit `.env` file with your configuration**
   ```bash
   # Use your preferred editor
   nano .env
   # or
   vim .env
   # or
   code .env  # if using VS Code
   ```

4. **Add the following configuration:**
   ```env
   # Database Configuration
   DATABASE_URL=postgresql://trustspan:trustspan@localhost:5432/trustspandb
   
   # JWT Secret Key (generate a secure random string)
   SECRET_KEY=your-secret-key-here-change-in-production
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Mistral AI API Key (get from https://mistral.ai/)
   MISTRAL_API_KEY=your-mistral-api-key-here
   
   # Solana Configuration
   SOLANA_RPC_URL=https://api.devnet.solana.com
   WALLET_PATH=~/.config/solana/id.json
   
   # Job Platform API Keys (see Job Platform Setup section below)
   # RemoteOK: Free - no API key needed
   # Arbeitnow: Free - no API key needed
   
   # Freelancer.com OAuth Token (optional)
   FREELANCER_OAUTH_TOKEN=your-freelancer-oauth-token
   FREELANCER_SANDBOX=False
   
   # Adzuna API (free tier: 250 requests/day)
   ADZUNA_APP_ID=your-adzuna-app-id
   ADZUNA_API_KEY=your-adzuna-api-key
   
   # RapidAPI Key (for Y-Combinator Jobs and Internships)
   RAPIDAPI_KEY=your-rapidapi-key
   
   # Application Settings
   APP_NAME=TrustSpan
   APP_VERSION=1.0.0
   DEBUG=True
   
   # File Upload Settings
   UPLOAD_DIR=./static/uploads
   MAX_UPLOAD_SIZE=10485760  # 10MB
   ```

5. **Generate a secure SECRET_KEY:**
   ```bash
   # Run this command to generate a secure key:
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Copy the output and paste it as your SECRET_KEY
   ```

### Job Platform API Keys Setup

TrustSpan integrates with multiple job platforms. Some are free and require no API keys, while others need registration:

#### Free Platforms (No API Keys Required)

1. **RemoteOK** - Remote tech jobs
   - **Status:** Free public API
   - **Action:** No setup needed, works out of the box

2. **Arbeitnow** - Quality remote jobs
   - **Status:** Free public API
   - **Action:** No setup needed, works out of the box

#### Platforms Requiring API Keys

3. **Adzuna** - Global job aggregator
   - **Status:** Free tier (250 requests/day)
   - **How to get keys:**
     1. Visit: https://developer.adzuna.com/
     2. Sign up for a free account
     3. Create a new application
     4. Copy your `Application ID` and `API Key`
   - **Add to `.env`:**
     ```env
     ADZUNA_APP_ID=your-application-id-here
     ADZUNA_API_KEY=your-api-key-here
     ```
   - **Note:** Free tier allows 250 requests per day. Upgrade for more.

4. **Freelancer.com** - Freelance projects
   - **Status:** Requires OAuth token
   - **How to get token:**
     1. Visit: https://www.freelancer.com/api-docs
     2. Register as a developer
     3. Create an OAuth application
     4. Generate an OAuth token
   - **Add to `.env`:**
     ```env
     FREELANCER_OAUTH_TOKEN=your-oauth-token-here
     FREELANCER_SANDBOX=False  # Set to True for testing
     ```
   - **Note:** This is optional. Job matching will work without it, but Freelancer.com jobs won't be included.

5. **RapidAPI** - For Y-Combinator Jobs and Internships
   - **Status:** Free tier available
   - **How to get key:**
     1. Visit: https://rapidapi.com/
     2. Sign up for a free account
     3. Go to your dashboard
     4. Copy your API key from "My Apps" → "Default Application"
   - **Add to `.env`:**
     ```env
     RAPIDAPI_KEY=your-rapidapi-key-here
     ```
   - **Note:** Free tier has rate limits. The platform will work without this, but Y-Combinator jobs and internships won't be available.

#### Summary Table

| Platform | API Key Required | Free Tier | Setup Difficulty |
|----------|-----------------|-----------|------------------|
| RemoteOK | ❌ No | ✅ Yes | ⭐ Easy - Works immediately |
| Arbeitnow | ❌ No | ✅ Yes | ⭐ Easy - Works immediately |
| Adzuna | ✅ Yes | ✅ Yes (250/day) | ⭐⭐ Medium - Quick signup |
| Freelancer.com | ✅ Yes (OAuth) | ⚠️ Limited | ⭐⭐⭐ Hard - OAuth setup |
| RapidAPI (YC/Internships) | ✅ Yes | ✅ Yes | ⭐⭐ Medium - Quick signup |

**Recommendation for First-Time Setup:**
- Start with RemoteOK and Arbeitnow (no setup needed)
- Add Adzuna for more job sources (quick 5-minute signup)
- Add RapidAPI if you want startup jobs and internships
- Freelancer.com is optional and can be added later

### Frontend Environment Variables

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Create `.env.local` file**
   ```bash
   touch .env.local
   ```

3. **Edit `.env.local` file**
   ```bash
   nano .env.local
   # or use your preferred editor
   ```

4. **Add the following configuration:**
   ```env
   # Backend API URL
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # Privy App ID (optional - for social login)
   NEXT_PUBLIC_PRIVY_APP_ID=your-privy-app-id
   ```

---

## Run Database Migrations

### Step 1: Activate Virtual Environment

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Run Migrations

```bash
# This will create all database tables
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade -> xxxxx, Create initial tables
INFO  [alembic.runtime.migration] Running upgrade xxxxx -> yyyyy, Add new columns
...
```

### Step 3: Verify Tables Created

```bash
# Connect to database
psql -U trustspan -d trustspandb -h localhost

# List tables
\dt

# You should see tables like: users, startups, investments, cvs, etc.
\q
```

### Step 4: (Optional) Seed Database with Sample Data

```bash
# From backend directory with venv activated
python scripts/seed_database.py

# This will create sample users, startups, and investments
```

---

## Start the Application

You'll need **two terminal windows** - one for backend, one for frontend.

### Terminal 1: Start Backend Server

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend is now running at:**
- API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Terminal 2: Start Frontend Server

```bash
# Navigate to frontend
cd frontend

# Start the development server
npm run dev
```

**Expected output:**
```
▲ Next.js 14.2.18
- Local:        http://localhost:3000
- Ready in 2.3s
```

**Frontend is now running at:** `http://localhost:3000`

---

## Verify Installation

### 1. Check Backend Health

```bash
# In a new terminal
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
```

### 2. Check API Documentation

Open in your browser: `http://localhost:8000/docs`

You should see the Swagger UI with all available API endpoints.

### 3. Check Frontend

Open in your browser: `http://localhost:3000`

You should see the TrustSpan landing page.

### 4. Test User Registration

1. Go to `http://localhost:3000/register`
2. Fill in the registration form
3. Submit and verify you can log in

### 5. Test CV Builder

1. Log in to the application
2. Navigate to CV Builder
3. Try creating a CV

### 6. Test Investment Platform

1. Log in as an investor
2. Navigate to Investor Platform
3. Browse startups (if you seeded the database)

---

## Troubleshooting

### Issue: Python Virtual Environment Not Activating

**Symptoms:** `source venv/bin/activate` doesn't work

**Solutions:**
```bash
# Make sure you're in the backend directory
cd backend

# Check if venv exists
ls -la venv

# If it doesn't exist, create it:
python3 -m venv venv

# On Windows, use:
venv\Scripts\activate
```

### Issue: Database Connection Error

**Symptoms:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
```bash
# 1. Check if PostgreSQL is running
sudo systemctl status postgresql

# 2. Start PostgreSQL if not running
sudo systemctl start postgresql

# 3. Verify database exists
sudo -u postgres psql -l | grep trustspandb

# 4. Check your DATABASE_URL in backend/.env
# Make sure it matches your PostgreSQL setup
```

### Issue: Port Already in Use

**Symptoms:** `Address already in use` error

**Solutions:**
```bash
# Find what's using port 8000 (backend)
lsof -i :8000
# or
netstat -tulpn | grep 8000

# Kill the process
kill -9 <PID>

# Or use a different port:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# Then update frontend/.env.local: NEXT_PUBLIC_API_URL=http://localhost:8001
```

```bash
# Find what's using port 3000 (frontend)
lsof -i :3000

# Kill the process or use a different port:
npm run dev -- -p 3001
```

### Issue: Module Not Found Errors

**Symptoms:** `ModuleNotFoundError: No module named 'xxx'`

**Solutions:**
```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Issue: npm Install Fails

**Symptoms:** Errors during `npm install`

**Solutions:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install

# If still failing, try with legacy peer deps:
npm install --legacy-peer-deps
```

### Issue: Migration Errors

**Symptoms:** `alembic upgrade head` fails

**Solutions:**
```bash
# Check current migration status
alembic current

# Check migration history
alembic history

# If needed, downgrade and re-upgrade
alembic downgrade -1
alembic upgrade head

# Or reset migrations (WARNING: This will delete data)
# Drop and recreate database, then run migrations
```

### Issue: Mistral AI API Errors

**Symptoms:** `401 Unauthorized` or API key errors

**Solutions:**
```bash
# 1. Verify your API key in backend/.env
# Make sure MISTRAL_API_KEY is set correctly

# 2. Get a new API key from https://mistral.ai/

# 3. Restart the backend server after updating .env
```

### Issue: Solana Wallet Errors

**Symptoms:** Wallet connection fails

**Solutions:**
```bash
# 1. Make sure you have a Solana wallet installed (Phantom, Solflare)

# 2. For development, you can use devnet:
# Update backend/.env: SOLANA_RPC_URL=https://api.devnet.solana.com

# 3. Generate a test wallet if needed:
solana-keygen new --outfile ~/.config/solana/id.json
```

---

## Quick Reference Commands

### Backend

```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run migrations
alembic upgrade head

# Check migration status
alembic current

# Seed database
python scripts/seed_database.py
```

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Database

```bash
# Connect to database
psql -U trustspan -d trustspandb -h localhost

# List all tables
\dt

# View table structure
\d table_name

# Exit
\q
```

---

## Project Structure Overview

```
trustspan/
├── backend/                 # Python FastAPI backend
│   ├── app/                 # Main application code
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── cv/                 # CV builder module
│   ├── investments/        # Investment platform module
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables
│   └── main.py            # Application entry point
│
├── frontend/               # Next.js React frontend
│   ├── components/        # React components
│   ├── pages/            # Next.js pages/routes
│   ├── contexts/         # React Context providers
│   ├── lib/              # Utilities and API client
│   ├── package.json      # Node.js dependencies
│   └── .env.local       # Frontend environment variables
│
├── blockchain/            # Solana blockchain programs
│   ├── programs/         # Rust programs
│   └── scripts/         # Deployment scripts
│
└── docs/                 # Documentation
```

---

## Next Steps

After successful setup:

1. **Explore the API:** Visit `http://localhost:8000/docs` to see all available endpoints
2. **Read the Documentation:** Check `docs/ARCHITECTURE.md` for system architecture
3. **Review the Code:** Start with `backend/app/main.py` and `frontend/pages/index.jsx`
4. **Run Tests:** (if test suite exists)
   ```bash
   cd backend
   source venv/bin/activate
   pytest
   ```

---

## Getting Help

- **Check Logs:** Backend logs are in `backend/logs/`
- **API Documentation:** `http://localhost:8000/docs`
- **GitHub Issues:** Report bugs or ask questions
- **Documentation:** See `docs/` directory for more details

---

## Common Development Workflow

1. **Make changes to code**
2. **Backend auto-reloads** (thanks to `--reload` flag)
3. **Frontend hot-reloads** (Next.js feature)
4. **Test your changes** in the browser
5. **Check console/terminal** for any errors

---

**Happy Coding! 🚀**

If you encounter any issues not covered here, please check the troubleshooting section or open an issue on GitHub.
