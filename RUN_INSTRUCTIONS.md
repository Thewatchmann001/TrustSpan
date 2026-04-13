# 🚀 How to Run TrustSpan

## ✅ Setup Complete!

All dependencies have been installed successfully. Here's how to run the application:

---

## 🐳 Option A: Run with Docker (single root file — recommended for deployment)

From the **project root**:

```bash
# Copy env if you have one (optional)
# cp backend/.env.example backend/.env

docker compose up -d
```

- **Backend:** http://localhost:8000  
- **Frontend:** http://localhost:3000  
- **Database:** PostgreSQL in container (port 5432)

To use Stripe card payments, set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` in the environment or in a `.env` file next to `docker-compose.yml`.  
For **GCP deployment** (Cloud Run + Cloud SQL), see **GCP_DEPLOYMENT.md**.

---

## 💳 Stripe 100% (card payments: investor → startup)

Stripe is fully integrated: **Checkout** (pay with card) and **recording the investment** in two ways.

### Stripe testing setup (no webhook, no real money)

Use your **Stripe test account** (test keys = no real charges, only test cards).

1. **In `backend/.env` set only:**
   ```bash
   STRIPE_SECRET_KEY=sk_test_...   # From Dashboard → Developers → API keys (Test mode)
   ```
   Leave **`STRIPE_WEBHOOK_SECRET`** empty. No webhook needed for testing.

2. **Test cards** (Stripe test mode):  
   - **Success:** `4242 4242 4242 4242`  
   - Any future expiry (e.g. 12/34), any 3-digit CVC, any postal code.

3. **Flow:** Investor clicks “Pay with card” → enters amount → redirects to Stripe Checkout → use test card → after payment Stripe redirects back → your app calls `confirm-session` and records the investment. No webhook required.

### 1. Env vars (required for Checkout)

In **`backend/.env`** set:

```bash
STRIPE_SECRET_KEY=sk_test_...   # From https://dashboard.stripe.com/apikeys
```

Optional for local: `STRIPE_WEBHOOK_SECRET` (see below).

### 2. Two ways to record the investment (both supported)

**A) Success redirect (works everywhere, including local without CLI)**  
After payment, Stripe redirects to  
`/investor-platform?payment=success&session_id=cs_xxx`.  
The frontend calls **`POST /api/payments/confirm-session`** with that `session_id`; the backend confirms the session with Stripe and creates the investment if not already there. **No webhook needed** for the investment to show up.

**B) Webhook (recommended for production and optional for local)**  
Stripe sends `checkout.session.completed` to your backend; the webhook handler also creates the investment (idempotent, so safe if both redirect and webhook run).

- **Production:** In [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/webhooks), add endpoint  
  `https://YOUR_BACKEND_URL/api/payments/webhook`  
  and subscribe to **`checkout.session.completed`**. Set the **Signing secret** (`whsec_...`) as `STRIPE_WEBHOOK_SECRET` in your backend env.

- **Local (Stripe CLI):**  
  1. Install [Stripe CLI](https://stripe.com/docs/stripe-cli).  
  2. In a separate terminal run:
     ```bash
     stripe login
     stripe listen --forward-to localhost:8000/api/payments/webhook
     ```
  3. The CLI prints a **webhook signing secret** (`whsec_...`). Copy it into **`backend/.env`**:
     ```bash
     STRIPE_WEBHOOK_SECRET=whsec_...
     ```
  4. Restart the backend. Payments will be recorded by the webhook as well as by the success redirect.

### 3. Flow summary

| Step | What happens |
|------|----------------|
| Investor clicks **Pay with card** | Frontend calls `POST /api/payments/create-checkout-session` → redirects to Stripe Checkout. |
| User pays on Stripe | Stripe redirects to `/investor-platform?payment=success&session_id=cs_xxx`. |
| Frontend loads | Calls `POST /api/payments/confirm-session` with `session_id` → backend records investment (if not already). |
| (Optional) Webhook | Stripe sends `checkout.session.completed` → same recording (idempotent). |

So **Stripe is 100% incorporated**: with only `STRIPE_SECRET_KEY` set, card payments and investment recording work via the success redirect; add the webhook (or Stripe CLI locally) for redundancy and production.

---

## 📋 Prerequisites Check (non-Docker)

- ✅ Python 3.12.3 installed
- ✅ Virtual environment created at `backend/venv`
- ✅ All dependencies installed (including httpx>=0.28.0, solana, qrcode, mistralai)
- ✅ Database configured: `postgresql://trustspan:trustspan@localhost:5432/trustspandb`
- ✅ Mistral AI API key configured
- ✅ .env files created

**If you hit "Too many open files" (backend or frontend):** run `ulimit -n 4096` once in that terminal, then start the server. That fixes both uvicorn and Next.js dev watchers.

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
CREATE DATABASE trustspandb;
CREATE USER trustspan WITH PASSWORD 'trustspan';
GRANT ALL PRIVILEGES ON DATABASE trustspandb TO trustspan;
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

If you see **"Too many open files (os error 24)"**, either:

- **Run without reload** (no auto-restart on code changes):
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
- **Or** exclude `venv` from the watcher so reload still works:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-exclude 'venv/*' --reload-exclude '.venv/*'
  ```
- **Or** raise the open-file limit then run with reload:
  ```bash
  ulimit -n 4096
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

### Option 2: Using Python Module

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

(Same "Too many open files" fixes as Option 1 apply: drop `--reload`, add `--reload-exclude 'venv/*'`, or run `ulimit -n 4096` first.)

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

If you see **"EMFILE: too many open files"** or **Watchpack Error (watcher)** in the frontend:

- **Raise the open-file limit** (recommended; applies to the whole shell):
  ```bash
  ulimit -n 4096
  npm run dev
  ```
- **Or** use polling instead of native file watching (fewer file descriptors, slightly slower):
  ```bash
  CHOKIDAR_USEPOLLING=true npm run dev
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
- `DATABASE_URL=postgresql://trustspan:trustspan@localhost:5432/trustspandb`
- `MISTRAL_API_KEY=your_mistral_api_key_here` (Get from https://mistral.ai/)
- `STRIPE_SECRET_KEY=sk_test_...` (optional — for card payments: https://dashboard.stripe.com/apikeys)
- `STRIPE_WEBHOOK_SECRET=whsec_...` (optional — for Stripe webhook: add endpoint `POST /api/payments/webhook`, event `checkout.session.completed`)
- `SOLANA_RPC_URL=https://api.devnet.solana.com`
- See `backend/.env.example` for all required variables

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
sudo -u postgres psql -l | grep trustspandb

# Test connection
psql -U trustspan -d trustspandb -h localhost
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
