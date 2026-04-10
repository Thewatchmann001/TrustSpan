# Architecture Documentation

## Overview

This platform consists of two main solutions:

1. **AI-Powered CV Builder + Global Job Matching**
2. **Professional Investment Platform Using Stablecoins**

## System Architecture

### Backend Structure

```
/backend
    /cv                    # CV Builder Module
        cv_generator.py     # CV generation with AI
        ats_optimizer.py    # ATS optimization
        job_matcher.py      # Job matching service
        global_job_api.py   # Global job search APIs
    /investments           # Investment Platform Module
        startup_verification.py  # Blockchain startup verification
        usdc_transactions.py    # USDC transfer handling
        investor_portfolio.py    # Portfolio management
    /app                   # Core application
        /api               # Legacy API endpoints (kept for compatibility)
        /blockchain        # Blockchain clients
        /db                # Database models
        /services          # Business logic services
    main.py                # FastAPI application entry
    routes.py              # Consolidated API routes
```

### Frontend Structure

```
/frontend
    /cv-builder            # CV Builder Components
        StepperUI.jsx      # Multi-step form UI
        CVEditor.jsx       # CV editing interface
        CVSuggestions.jsx # AI suggestions display
        JobMatches.jsx     # Job matching results
    /investor              # Investment Platform Components
        StartupList.jsx    # Startup listing
        StartupDetails.jsx # Startup details view
        InvestFlow.jsx     # Investment flow
        WalletConnect.jsx  # Wallet connection
    /pages                 # Next.js pages
    /components            # Shared components
```

### Blockchain Structure

```
/blockchain
    /programs
        /startup-registry  # Startup attestation on Solana
        /investment-ledger # USDC transfer ledger
    /scripts              # Blockchain interaction scripts
```

## Technology Stack

### Backend
- **FastAPI**: Python web framework
- **PostgreSQL**: Database
- **SQLAlchemy**: ORM
- **OpenAI API**: AI-powered CV enhancements
- **Solana/Anchor**: Blockchain platform

### Frontend
- **Next.js**: React framework
- **Tailwind CSS**: Styling
- **React Hooks**: State management

### Blockchain
- **Solana**: Blockchain network
- **Anchor**: Solana framework
- **USDC**: Stablecoin for investments

## API Endpoints

### CV Builder Endpoints

- `POST /api/cv/generate` - Generate CV with AI
- `GET /api/cv/{user_id}` - Get user's CV
- `POST /api/cv/suggestions` - Get AI suggestions
- `POST /api/cv/ats-score` - Calculate ATS score

### Job Matching Endpoints

- `GET /api/jobs/search-global` - Search global job market
- `POST /api/jobs/match` - Match user to jobs
- `POST /api/jobs/match-global` - Match CV to global jobs

### Investment Platform Endpoints

- `GET /api/startups/list` - List verified startups
- `GET /api/startups/verify/{startup_id}` - Verify startup
- `GET /api/startups/{startup_id}` - Get startup details
- `POST /api/investments/usdc/send` - Send USDC investment
- `GET /api/investments/portfolio/{investor_id}` - Get portfolio

## Data Flow

### CV Generation Flow

1. User fills CV form (multi-step)
2. Frontend sends data to `/api/cv/generate`
3. Backend uses AI service to enhance CV
4. CV optimized for ATS systems
5. CV saved to database
6. PDF/Word export available

### Job Matching Flow

1. User creates/updates CV
2. System matches CV to local jobs using matching algorithm
3. System searches global job APIs (LinkedIn, Indeed, Talent.com)
4. Results ranked by relevance score
5. User can apply to matched jobs

### Investment Flow

1. Investor browses verified startups
2. Investor connects Solana wallet
3. Investor selects startup and investment amount
4. USDC transfer executed on Solana
5. Investment recorded on blockchain
6. Portfolio updated

## Security

- JWT authentication for API access
- Blockchain verification for startups
- Wallet signature verification for transactions
- Input validation and sanitization

## Deployment

### Backend
- FastAPI server (uvicorn)
- PostgreSQL database
- Environment variables for configuration

### Frontend
- Next.js production build
- Static asset optimization
- API proxy configuration

### Blockchain
- Solana devnet/mainnet
- Anchor program deployment
- Wallet management

