# TrustBridge

<div align="center">

**AI-Powered Career Development & Investment Platform**

_Connecting Talent with Opportunity | Empowering Global Investments_

[![Next.js](https://img.shields.io/badge/Next.js-14.0-black?logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)](https://www.postgresql.org/)
[![Solana](https://img.shields.io/badge/Solana-Blockchain-purple?logo=solana)](https://solana.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)

[Features](#-features) • [Installation](#-installation) • [Configuration](#-configuration) • [API Documentation](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [Database Setup](#-database-setup)
- [Blockchain Integration](#-blockchain-integration)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

---

## 🎯 Overview

**TrustBridge** is an enterprise-grade platform that revolutionizes career development and investment through AI-powered technology, blockchain verification, and global market integration.

### Key Capabilities

- 🤖 **AI-Powered CV Builder** - Create professional, ATS-optimized resumes
- 🔍 **Intelligent Job Matching** - Multi-source job aggregation with smart matching
- 💼 **Investment Platform** - Blockchain-verified startup investments
- 🌐 **Progressive Web App** - Offline-capable, installable web application
- 🔐 **Blockchain Verification** - Solana-based credential and investment tracking

---

## ✨ Features

### Career Development

- ✅ AI-powered CV generation and optimization
- ✅ ATS (Applicant Tracking System) compatibility scoring
- ✅ Real-time language enhancement suggestions
- ✅ Industry-specific templates and keywords
- ✅ Cover letter generator
- ✅ Interview preparation tools
- ✅ Application tracking system
- ✅ Multi-format export (PDF, DOCX, Web)

### Job Matching

- ✅ **RemoteOK integration** (free - remote tech jobs)
- ✅ **We Work Remotely** (free - quality remote jobs)
- ✅ **Freelancer.com integration** (OAuth - freelance gigs)
- ✅ **Adzuna integration** (free tier - global job aggregator)
- ✅ AI-powered matching algorithm
- ✅ CV-based automatic keyword extraction
- ✅ Location-based filtering
- ✅ Skills and experience matching
- ✅ Real-time job updates

### Investment Platform

- ✅ Blockchain-verified startup registration
- ✅ Credibility scoring system
- ✅ Investment tracking on Solana
- ✅ USDC payment integration
- ✅ Portfolio management
- ✅ Transaction history
- ✅ Due diligence tools

### User Experience

- ✅ LinkedIn-inspired professional UI/UX
- ✅ Progressive Web App (PWA) support
- ✅ Offline functionality
- ✅ Responsive design (mobile-first)
- ✅ Premium animations and transitions
- ✅ Dark mode ready

---

## 🛠️ Technology Stack

### Frontend

- **Framework**: [Next.js 14](https://nextjs.org/) (React 18.2)
- **Styling**: [Tailwind CSS 3.3](https://tailwindcss.com/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **HTTP Client**: [Axios](https://axios-http.com/)
- **Notifications**: [React Hot Toast](https://react-hot-toast.com/)
- **Authentication**: [Privy](https://privy.io/) (optional)

### Backend

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Authentication**: JWT (JSON Web Tokens)
- **API Documentation**: Automatic OpenAPI/Swagger

### AI & Machine Learning

- **AI Service**: [Mistral AI](https://mistral.ai/) (mistral-medium-latest)
- **NLP**: Custom matching algorithms
- **CV Analysis**: ATS optimization and scoring

### Blockchain

- **Blockchain**: [Solana](https://solana.com/)
- **Programs**: Rust-based Solana programs
- **Wallets**: Solana Wallet Adapter
- **Payments**: USDC (SPL tokens)

### Infrastructure

- **PWA**: Service Worker, Web App Manifest
- **Deployment**: Docker-ready
- **CI/CD**: GitHub Actions ready

---

## 📁 Project Structure

```
trustbridge/
├── frontend/                 # Next.js frontend application
│   ├── components/          # React components
│   ├── pages/               # Next.js pages/routes
│   ├── styles/              # Global styles and Tailwind config
│   ├── public/              # Static assets and PWA files
│   └── lib/                 # Utility functions and API client
│
├── backend/                 # FastAPI backend application
│   ├── app/                 # Main application code
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration and security
│   │   ├── db/             # Database models and session
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── cv/                 # CV-related modules
│   ├── investments/        # Investment platform modules
│   ├── scripts/            # Utility scripts
│   ├── tests/              # Test suite
│   └── routes.py           # Main API router
│
├── blockchain/             # Solana blockchain programs
│   ├── programs/           # Rust programs
│   ├── scripts/            # Deployment and interaction scripts
│   └── tests/              # Blockchain tests
│
└── docs/                   # Documentation
    ├── API_SPEC.md        # API documentation
    ├── ARCHITECTURE.md    # System architecture
    └── PITCH_DECK.md      # Business pitch deck
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Node.js** 18+ and npm/yarn
- **Python** 3.12+
- **PostgreSQL** 14+
- **Git**

### Optional (for blockchain features)

- **Rust** 1.70+ (for Solana programs)
- **Solana CLI** 1.16+ (for blockchain deployment)
- **Anchor** 0.28+ (for Solana program development)

### Recommended Tools

- **Docker** (for containerized deployment)
- **Postman** or **Insomnia** (for API testing)
- **VS Code** (with recommended extensions)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/trustbridge.git
cd trustbridge
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
yarn install
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb trustbridge_db

# Or using psql:
psql -U postgres
CREATE DATABASE trustbridge_db;
\q
```

---

## ⚙️ Configuration

### Backend Configuration

1. Copy the example environment file:

```bash
cd backend
cp .env.example .env
```

2. Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trustbridge_db

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Solana
SOLANA_RPC_URL=https://api.devnet.solana.com

# AI Service (Mistral AI - for CV parsing)
MISTRAL_API_KEY=your-mistral-api-key

# Job Search - No API keys needed!
# RemoteOK: Free public API
```

### Frontend Configuration

1. Create `.env.local` in the frontend directory:

```bash
cd frontend
touch .env.local
```

2. Add environment variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_PRIVY_APP_ID=your-privy-app-id  # Optional
```

### Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🏃 Running the Application

### Development Mode

#### Start Backend

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

#### Start Frontend

```bash
cd frontend
npm run dev
# or
yarn dev
```

Frontend will be available at: `http://localhost:3000`

### Production Mode

#### Build Frontend

```bash
cd frontend
npm run build
npm start
```

#### Run Backend with Production Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🗄️ Database Setup

### Run Migrations

```bash
cd backend
source venv/bin/activate

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Seed Database

```bash
cd backend
source venv/bin/activate

# Initialize database tables
python init_db.py
```

### Sample Data

The seed scripts create:

- Sample users (job seekers, startups, investors)
- Sample startups with verification
- Sample investments

**Default Login Credentials:**

- Job Seeker: `alice@example.com` / `password123`
- Startup Founder: `david@startup.com` / `password123`
- Investor: `frank@investor.com` / `password123`

---

## ⛓️ Blockchain Integration

### Prerequisites

```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install latest
avm use latest
```

### Deploy Programs

```bash
cd blockchain

# Build programs
anchor build

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Update program IDs in backend/.env
```

### Run Blockchain Tests

```bash
cd blockchain
anchor test
```

---

## 📚 API Documentation

### Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Key Endpoints

#### User Management

- `POST /api/users/register` - Register new user
- `POST /api/users/login` - User login
- `GET /api/users/{user_id}` - Get user details
- `DELETE /api/users/{user_id}` - Delete user

#### CV Builder

- `POST /api/cv/generate` - Generate CV with AI
- `POST /api/cv/save` - Save CV to database
- `GET /api/cv/{user_id}` - Get user's CV
- `POST /api/cv/jobs` - Search jobs based on CV
- `POST /api/cv/suggestions` - Get AI suggestions
- `POST /api/cv/ats-score` - Calculate ATS score

#### Job Matching

- `POST /api/jobs/match` - Match user to jobs
- `GET /api/jobs/search-global` - Global job search
- `POST /api/jobs/apply` - Apply to job

#### Investment Platform

- `POST /api/startups/register` - Register startup
- `GET /api/startups/list` - List verified startups
- `POST /api/startups/{id}/invest` - Make investment
- `GET /api/investments/portfolio/{investor_id}` - Get portfolio

### Full API Documentation

Visit `http://localhost:8000/docs` when the backend is running for interactive API documentation with Swagger UI.

See [docs/API_SPEC.md](docs/API_SPEC.md) for detailed API documentation.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/api/test_users.py

# Run with coverage
pytest --cov=app tests/
```

### Frontend Tests

```bash
cd frontend

# Run tests (when test suite is added)
npm test
```

### Integration Tests

```bash
# Run blockchain tests
cd blockchain
anchor test

# Run end-to-end tests (when E2E suite is added)
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

1. **Backend**: Deploy to cloud platform (AWS, GCP, Azure, Heroku)
2. **Frontend**: Deploy to Vercel, Netlify, or similar
3. **Database**: Use managed PostgreSQL service
4. **Blockchain**: Deploy programs to Solana mainnet/devnet

### Environment Variables

Ensure all environment variables are set in production:

- Database connection strings
- JWT secret keys (use strong, unique keys)
- API keys for external services
- Blockchain RPC URLs

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS in production
- [ ] Enable CORS properly
- [ ] Set up rate limiting
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Set up monitoring and logging

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **JavaScript/TypeScript**: Follow ESLint rules, use Prettier
- **Commits**: Use conventional commit messages

### Pull Request Guidelines

- Clearly describe the changes
- Include tests for new features
- Update documentation as needed
- Ensure all tests pass

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💬 Support

### Documentation

- [API Documentation](docs/API_SPEC.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Pitch Deck](PITCH_DECK.md)

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/trustbridge/issues)
- **Email**: support@trustbridge.com
- **Discord**: [Join our community](https://discord.gg/trustbridge)

### Reporting Bugs

Please use the GitHub issue tracker to report bugs. Include:

- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, browser, versions)

---

## 🗺️ Roadmap

### Phase 1: Foundation ✅

- [x] Core platform development
- [x] CV builder with AI
- [x] Job matching engine
- [x] Blockchain verification
- [x] PWA implementation

### Phase 2: Launch (Q1 2024)

- [ ] Beta testing
- [ ] University partnerships
- [ ] Mobile app development
- [ ] Enhanced AI features

### Phase 3: Growth (Q2-Q3 2024)

- [ ] Market expansion
- [ ] Premium features
- [ ] Corporate partnerships
- [ ] API marketplace

### Phase 4: Scale (Q4 2024+)

- [ ] Multi-language support
- [ ] Advanced analytics
- [ ] Enterprise solutions
- [ ] Global expansion

---

## 🙏 Acknowledgments

- **OpenAI** for AI capabilities
- **Solana Foundation** for blockchain infrastructure
- **Next.js** and **FastAPI** communities
- All contributors and supporters

---

## 📊 Project Status

![GitHub stars](https://img.shields.io/github/stars/yourusername/trustbridge?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/trustbridge?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/trustbridge)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/trustbridge)

---

<div align="center">

**Built with ❤️ by the TrustBridge Team**

[Website](https://trustbridge.com) • [Twitter](https://twitter.com/trustbridge) • [LinkedIn](https://linkedin.com/company/trustbridge)

</div>
