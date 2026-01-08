# 🚀 How to Run TrustBridge

## ✅ Setup Complete!

All dependencies have been installed successfully. Here's how to run the application:

---

## 📋 Prerequisites Check

- ✅ Python 3.12.3 installed
- ✅ Virtual environment created at `backend/venv`
- ✅ All dependencies installed (including httpx>=0.28.0, solana, qrcode, mistralai)
- ✅ Database configured: `postgresql://trustbridge:trustbridge@localhost:5432/trustbridgedb`
- ✅ Mistral AI API key configured
- ✅ .env files created

---

## 🗄️ Database Setup

### 1. Ensure PostgreSQL is Running

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# If not running, start it:
sudo systemctl start postgresql
```

### 2. Create Database (if not exists)

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE trustbridgedb;
CREATE USER trustbridge WITH PASSWORD 'trustbridge';
GRANT ALL PRIVILEGES ON DATABASE trustbridgedb TO trustbridge;
\q
```

### 3. Run Database Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

This will create all tables including the new `conversations` and `messages` tables for chat.

---

## 🔧 Running the Backend

### Option 1: Using the Virtual Environment

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Using Python Module

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be available at:**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## 🎨 Running the Frontend

```bash
cd frontend
npm install  # Only needed first time
npm run dev
```

**Frontend will be available at:** `http://localhost:3000`

---

## 🧪 Testing the Application

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 2. Check API Documentation

Open in browser: `http://localhost:8000/docs`

### 3. Test Chat Endpoints

- Create conversation: `POST /api/conversations?investor_id=1&startup_id=1`
- Send message: `POST /api/messages`
- Get messages: `GET /api/conversations/{conversation_id}/messages`
- WebSocket: `ws://localhost:8000/ws/{conversation_id}/{user_id}`

### 4. Test QR Code

- Generate QR: `GET /api/startups/{startup_id}/qr`
- View verification page: `http://localhost:3000/verify/startup/{startup_id}`

---

## 📝 Environment Variables

All configuration is in:
- **Backend**: `backend/.env`
- **Frontend**: `frontend/.env.local`

### Key Variables:

**Backend (.env):**
- `DATABASE_URL=postgresql://trustbridge:trustbridge@localhost:5432/trustbridgedb`
- `MISTRAL_API_KEY=GdIifsPZmtuRu16zlwFZpu4jXjxBOI0i`
- `SOLANA_RPC_URL=https://api.devnet.solana.com`
- `WALLET_PATH=~/.config/solana/id.json`
- Your Wallet Address: `AEUc2iSkkkDeRNMLT52HCGMvyGrn17RtayN3DgMvomU4`

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `NEXT_PUBLIC_PRIVY_APP_ID=your-privy-app-id` (optional)

---

## 🐛 Troubleshooting

### Issue: Database Connection Error

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if database exists
sudo -u postgres psql -l | grep trustbridgedb

# Test connection
psql -U trustbridge -d trustbridgedb -h localhost
```

### Issue: Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process or use a different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Issue: Module Not Found

```bash
# Make sure virtual environment is activated
cd backend
source venv/bin/activate

# Verify packages
pip list | grep -E "httpx|solana|qrcode|mistralai"
```

### Issue: Migration Errors

```bash
# Check current migration status
cd backend
source venv/bin/activate
alembic current

# If needed, downgrade and re-upgrade
alembic downgrade -1
alembic upgrade head
```

---

## 🎯 Quick Start Commands

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Database migrations (if needed)
cd backend
source venv/bin/activate
alembic upgrade head
```

---

## ✨ New Features Available

1. **💬 In-App Chat**
   - Real-time messaging between investors and startups
   - WebSocket support for live updates
   - Conversation management

2. **📱 QR Code Verification**
   - Generate QR codes for startup verification
   - Public verification pages
   - Downloadable QR codes

3. **🔔 Notifications**
   - Toast notifications using react-hot-toast
   - Real-time updates via WebSocket

---

## 📚 Additional Resources

- API Documentation: `http://localhost:8000/docs`
- Architecture: See `docs/ARCHITECTURE.md`
- API Spec: See `docs/API_SPEC.md`
- Merge Details: See `MERGE_COMPLETE.md`

---

**Happy Coding! 🚀**
