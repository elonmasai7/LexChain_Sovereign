
# LexChain Sovereign

**AI-Powered Decentralized Legal Infrastructure for Compliant Real World Asset Tokenization**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-red.svg)](https://fastapi.tiangolo.com/)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.23+-purple.svg)](https://soliditylang.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![GitHub CI](https://github.com/elonmasai7/LexChain_Sovereign/actions/workflows/ci.yml/badge.svg)](https://github.com/elonmasai7/LexChain_Sovereign/actions)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io)

---

## Overview

LexChain Sovereign is an **enterprise-grade legal operating system for Web3** that combines **AI-powered legal automation**, **blockchain compliance verification**, **Real World Asset (RWA) tokenization**, and **decentralized identity** into a unified platform.

Built for law firms, DAOs, real estate operators, investment firms, and startups who need to automate legal workflows while maintaining regulatory transparency and blockchain-native verification.

### Why LexChain Sovereign?

| Problem | Solution |
|---------|----------|
| Manual legal contract review | AI-powered contract analysis & clause extraction |
| Cross-border compliance complexity | Multi-jurisdiction regulatory intelligence engine |
| RWA tokenization legal risk | Built-in compliance verification & legal metadata anchoring |
| Fragmented legal tools | Unified platform: auth, AI, tokens, documents, compliance, governance |
| Evidence integrity | Immutable vault with IPFS + blockchain timestamp proofs |
| DAO legal uncertainty | Compliance-aware governance with smart legal contracts |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                              │
│   Web Browser │ REST API │ Wallet (MetaMask) │ API Consumer                     │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    v
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           NGINX REVERSE PROXY                                     │
│                    TLS 1.3 │ Rate Limiting │ Security Headers                     │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    v                               v
┌─────────────────────────────────────┐   ┌──────────────────────────────────────┐
│         FRONTEND LAYER              │   │         BACKEND API LAYER            │
│  Pure HTML5 / CSS3 / Vanilla JS     │   │       FastAPI + Celery Workers       │
│  HTMX for dynamic UX                │   │       REST / WebSocket               │
│  Canvas charts (no libraries)       │   │       Async SQLAlchemy               │
│  Server-rendered architecture       │   │       Pydantic v2 Validation         │
└─────────────────────────────────────┘   └──────────────────────────────────────┘
                                           │              │               │
                    ┌──────────────────────┘              │               └──────────────┐
                    v                                    v                             v
┌────────────────────────────┐         ┌────────────────────────────┐     ┌────────────────────────┐
│        POSTGRESQL 16       │         │           REDIS 7           │     │   BLOCKCHAIN LAYER     │
│  Users │ Assets │ Docs    │         │  Sessions │ Cache │ Queues  │     │  Ethereum │ Base       │
│  Governance │ Compliance   │         │  Rate Limiting             │     │  Polygon │ Arbitrum   │
│  Evidence │ Audit          │         │                            │     │  Solidity Contracts   │
└────────────────────────────┘         └────────────────────────────┘     └────────────────────────┘
                                                                                    │
                                                                                    v
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL SERVICES                                         │
│   OpenAI │ Anthropic │ IPFS │ Chainalysis │ TRM Labs │ Persona │ Sumsub │ ENS   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       LEXCHAIN SOVEREIGN PLATFORM                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Identity &  │  │      AI      │  │     RWA      │  │   Smart     │ │
│  │    Access    │  │   Legal AI   │  │ Tokenization │  │   Legal     │ │
│  │              │  │              │  │              │  │  Contracts  │ │
│  │  • JWT Auth  │  │ • Contract  │  │ • Real Estate│  │ • Templates │ │
│  │  • MFA/TOTP  │  │   Analysis  │  │ • Carbon     │  │ • Clauses   │ │
│  │  • WebAuthn  │  │ • Clause    │  │   Credits    │  │ • Signatures│ │
│  │  • Wallet    │  │   Extraction│  │ • Agriculture│  │ • Anchoring │ │
│  │  • RBAC      │  │ • Risk      │  │ • Art        │  │ • PDF Export│ │
│  │  • Sessions  │  │   Detection │  │ • Commodities│  │ • Versions  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Compliance & │  │ Decentralized│  │  Governance  │  │   Legal     │ │
│  │   RegTech    │  │  Identity   │  │   & DAO      │  │  Evidence   │ │
│  │              │  │             │  │              │  │    Vault    │ │
│  │  • AML/KYC   │  │ • W3C DID  │  │ • Proposals  │  │ • IPFS      │ │
│  │  • Sanctions │  │ • Verifiable│  │ • Quadratic  │  │ • Hashing   │ │
│  │  • Wallet    │  │   Credential│  │   Voting     │  │ • Timestamp │ │
│  │    Risk      │  │ • ENS       │  │ • Delegation │  │   Proofs    │ │
│  │  • Scoring   │  │ • zk-proofs │  │ • Treasury   │  │ • Anchoring │ │
│  │  • Monitoring│  │ • DAO       │  │ • Timelock   │  │ • Custody   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    ANALYTICS DASHBOARD                               │ │
│  │  KPIs │ Charts │ Compliance Metrics │ Risk Exposure │ Activity Feed│ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Platform Modules

### 1. Authentication & Access Infrastructure

| Feature | Implementation |
|---------|---------------|
| Email/Password | bcrypt hashing, rate-limited login, progressive lockout |
| Wallet Auth | Signature verification via EIP-1193, WalletConnect |
| WebAuthn/Passkeys | Browser-native biometric authentication |
| MFA (TOTP) | Time-based one-time passwords via authenticator apps |
| JWT Management | Access + Refresh token rotation, secure cookie handling |
| RBAC | 8 roles: Super Admin, Legal Officer, Compliance Officer, Investor, DAO Member, Asset Issuer, Auditor, Client |
| Session Management | Device fingerprinting, concurrent session tracking, forced revocation |
| Audit Logging | Immutable logs for all authentication events |

### 2. AI Legal Intelligence Engine

```
User submits contract text
         │
         v
┌─────────────────────┐
│ Prompt Validation   │ < Injection prevention & content moderation
└─────────┬───────────┘
          v
┌─────────────────────┐
│ AI Provider Router  │ < OpenAI / Anthropic / Local fallback
└─────────┬───────────┘
          v
┌─────────────────────┐
│ Analysis Pipeline   │
├─────────────────────┤
│ • Contract Summary  │
│ • Clause Extraction │
│ • Risk Detection    │
│ • Compliance Score  │
│ • Recommendations   │
└─────────────────────┘
```

### 3. Real World Asset Tokenization

**Supported Asset Types:**
- Real Estate - Property-backed tokens with legal metadata
- Carbon Credits - Verified emission reductions
- Agriculture - Crop and land-backed assets
- Art - Digital certificate of authenticity
- Commodities - Gold, oil, and other resources

**Tokenization Workflow:**
```
Draft > Legal Review > Compliance Check > Verification > Approval > Minting > Lifecycle
  │          │               │               │             │          │
  v          v               v               v             v          v
Create   Submit docs    KYC/AML check    Verify       Final     Mint on-chain
asset    for review     Sanctions       ownership    approval  metadata stored
                        screening       & valuation
```

### 4. Smart Legal Contract System

**Document Types:**
- Non-Disclosure Agreements (NDA)
- Token Purchase Agreements
- DAO Governance Agreements
- Investment Agreements
- Real Estate Purchase Contracts
- KYC/AML Consent Forms
- Service Agreements
- Partnership Agreements

**Features:**
- Template-based generation with smart clause variables
- Jurisdiction-aware clause assembly
- Digital signature capture
- SHA-256 document hashing
- Blockchain hash anchoring
- Version history with diff tracking
- PDF export

### 5. Compliance & RegTech Engine

| Capability | Description | Providers |
|-----------|-------------|-----------|
| AML Screening | Anti-money laundering checks | Chainalysis, TRM Labs |
| KYC Verification | Identity document verification | Persona, Sumsub, Stripe Identity |
| OFAC Sanctions | Sanctions list matching | OFAC SDN List |
| Wallet Risk | Address risk scoring | Chainalysis, TRM Labs |
| Suspicious Activity | Behavioral monitoring | Custom ML models |
| Risk Scoring | Composite risk calculation | Weighted multilayered model |

**Compliance Score Calculation:**
```
Overall Score = (KYC_Score × 0.40) + (AML_Score × 0.30) + (Wallet_Score × 0.30)

KYC Score: Identity verification completeness and recency
AML Score: Transaction screening results and historical activity
Wallet Score: Address risk, interaction with flagged entities

Risk Level:
  80-100  > Low
  50-79   > Medium
  0-49    > High
```

### 6. Decentralized Identity (W3C DID)

- **DID Methods:** `ethr` (Ethereum), `key` (multibase), `web` (domain-based)
- **Verifiable Credentials:** W3C VC standard v1.1
- **Credential Types:** Identity, DAO Membership, Educational, Accreditation
- **Proof Format:** EcdsaSecp256k1Signature2019
- **Integration:** ENS resolution, zk-proof architecture

### 7. DAO Governance Module

```
┌─────────────────────────────────────┐
│        Proposal Lifecycle           │
├─────────────────────────────────────┤
│  DRAFT > PENDING > ACTIVE >        │
│           QUEUED > EXECUTED        │
│           DEFEATED                  │
└─────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│        Voting Mechanisms            │
├─────────────────────────────────────┤
│  • Single Choice Voting             │
│  • Quadratic Voting (weighted)      │
│  • Delegated Voting                 │
│  • Quorum-based approval            │
│  • Timelock execution               │
└─────────────────────────────────────┘
```

### 8. Legal Evidence Vault

- **Storage:** Encrypted files with IPFS CIDs
- **Integrity:** SHA-256 file hashing
- **Verification:** Chain of custody tracking
- **Anchoring:** Blockchain timestamp proofs
- **Export:** Verification proof packages

### 9. Analytics Dashboard

- **KPIs:** Total Assets, Compliance Rate, Risk Score, Active Governance
- **Charts:** Compliance by type, Asset distribution, Governance activity
- **Alerts:** Regulatory updates, Compliance reminders, Risk warnings
- **Activity Feed:** Real-time platform event stream

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12+ | Runtime |
| FastAPI | 0.109+ | REST framework |
| SQLAlchemy | 2.0+ | Async ORM |
| PostgreSQL | 16 | Primary database |
| Redis | 7 | Cache, sessions, queues |
| Celery | 5.3+ | Background task processing |
| Alembic | 1.13+ | Database migrations |
| Pydantic | 2.6+ | Data validation |
| JWT (python-jose) | 3.3+ | Token auth |
| Passlib | 1.7+ | Password hashing |
| Web3.py | 6.15+ | Blockchain interaction |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| HTML5 | - | Semantic markup |
| CSS3 | - | Custom properties design system |
| Vanilla JS | ES6+ | Core logic |
| HTMX | 1.9+ | Dynamic HTML |
| Canvas API | - | Charts (zero dependencies) |

### Smart Contracts (Solidity)
| Contract | Purpose |
|----------|---------|
| `LexGovernor` | DAO governance with quadratic voting |
| `LexAssetToken` | RWA token (ERC20 + ERC1155) with compliance |
| `LegalMetadataRegistry` | Document hash anchoring |
| `ComplianceRegistry` | On-chain KYC/AML status |
| `LegalEvidenceStore` | Evidence verification and custody |
| `LexRoles` | Access control (AccessControlEnumerable) |
| `LexProxy` | UUPS upgradeable proxy |

### Infrastructure
| Tool | Purpose |
|------|---------|
| Docker | Containerization |
| Docker Compose | Multi-service orchestration |
| NGINX | Reverse proxy + TLS termination |
| GitHub Actions | CI/CD pipeline |
| Prometheus | Metrics collection |
| Grafana | Visualization & dashboards |

---

## Project Structure

```
LexChain_Sovereign/
│
├── README.md                        < You are here
├── LICENSE
├── Makefile                         < Development commands
├── Dockerfile                       < Production build
├── docker-compose.yml               < Multi-service orchestration
├── docker-compose.prod.yml          < Production overrides
├── .env.example                     < Environment template
├── .gitignore
│
├── backend/                         * FastAPI Backend
│   ├── app/
│   │   ├── main.py                  < Application entrypoint
│   │   ├── api/
│   │   │   └── v1/                  < API versioned routes
│   │   │       ├── auth.py          < Authentication endpoints
│   │   │       ├── users.py         < User management
│   │   │       ├── assets.py        < RWA asset CRUD
│   │   │       ├── documents.py     < Legal documents
│   │   │       ├── compliance.py    < Compliance checks
│   │   │       ├── legal_ai.py      < AI analysis
│   │   │       ├── governance.py    < DAO proposals
│   │   │       ├── did.py           < Decentralized ID
│   │   │       ├── evidence.py      < Legal evidence vault
│   │   │       ├── analytics.py     < Dashboard data
│   │   │       └── audit.py         < Audit logs
│   │   ├── core/                    < Core infrastructure
│   │   │   ├── config.py            < Pydantic settings
│   │   │   ├── security.py          < Auth, JWT, encryption
│   │   │   ├── database.py          < Async SQLAlchemy
│   │   │   ├── middleware.py         < HTTP middleware
│   │   │   ├── dependencies.py      < FastAPI dependencies
│   │   │   ├── rate_limiter.py       < Redis rate limiting
│   │   │   ├── audit.py             < Audit service
│   │   │   ├── encryption.py        < Fernet encryption
│   │   │   ├── validation.py        < Input validation
│   │   │   └── logging.py           < Structured logging
│   │   ├── models/                  < SQLAlchemy models
│   │   │   ├── user.py              < Users + sessions
│   │   │   ├── asset.py             < RWA assets
│   │   │   ├── document.py          < Legal documents
│   │   │   ├── compliance.py        < Compliance records
│   │   │   ├── governance.py        < Proposals + votes
│   │   │   ├── evidence.py          < Legal evidence
│   │   │   └── ... (14 models total)
│   │   ├── schemas/                 < Pydantic validation
│   │   │   ├── user.py
│   │   │   ├── asset.py
│   │   │   ├── document.py
│   │   │   ├── compliance.py
│   │   │   ├── governance.py
│   │   │   ├── evidence.py
│   │   │   ├── analytics.py
│   │   │   └── common.py
│   │   ├── services/                < Business logic
│   │   │   ├── auth_service.py      < Authentication service
│   │   │   ├── legal_ai_service.py  < AI analysis service
│   │   │   ├── tokenization_service.py < RWA engine
│   │   │   ├── document_service.py  < Document operations
│   │   │   ├── compliance_service.py < Compliance engine
│   │   │   ├── did_service.py       < DID operations
│   │   │   ├── governance_service.py < DAO operations
│   │   │   ├── evidence_service.py  < Evidence vault
│   │   │   └── analytics_service.py < Dashboard metrics
│   │   ├── workers/                 < Celery tasks
│   │   │   ├── celery_app.py        < Celery configuration
│   │   │   └── tasks.py             < Background jobs
│   │   └── utils/                   < Utilities
│   │       ├── helpers.py
│   │       ├── email.py
│   │       └── web3_helper.py
│   ├── migrations/                  < Alembic migrations
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py
│   ├── seed_data.py                 < Demo data seeder
│   └── requirements.txt             < Python dependencies
│
├── frontend/                        * Pure HTML/CSS/JS
│   ├── public/
│   │   ├── css/
│   │   │   ├── design-tokens.css    < Design system variables
│   │   │   ├── base.css             < Reset + utilities
│   │   │   ├── components.css       < UI components
│   │   │   ├── layout.css           < App layout
│   │   │   ├── pages.css            < Page-specific styles
│   │   │   ├── animations.css       < Subtle animations
│   │   │   └── dark.css             < Dark theme
│   │   ├── js/
│   │   │   ├── app.js              < Main app module
│   │   │   ├── api.js              < REST API client
│   │   │   ├── charts.js           < Canvas charts
│   │   │   └── web3.js             < Blockchain integration
│   │   └── img/
│   │       └── icons.svg           < SVG icon sprite
│   └── templates/
│       ├── layouts/
│       │   ├── base.html           < App shell
│       │   └── auth.html           < Auth pages
│       └── pages/
│           ├── login.html          < Login page
│           ├── register.html       < Registration
│           ├── dashboard.html      < Executive dashboard
│           ├── assets.html         < Asset management
│           ├── documents.html      < Legal documents
│           ├── compliance.html     < Compliance dashboard
│           ├── governance.html     < DAO governance
│           ├── legal-ai.html       < AI legal assistant
│           ├── evidence.html       < Evidence vault
│           ├── did.html            < Decentralized identity
│           ├── settings.html       < User settings
│           └── admin.html          < Admin panel
│
├── contracts/                       * Solidity Smart Contracts
│   ├── foundry.toml                < Foundry configuration
│   ├── src/
│   │   ├── governance/
│   │   │   └── LexGovernor.sol     < DAO governor
│   │   ├── token/
│   │   │   └── LexAssetToken.sol   < RWA token
│   │   ├── registry/
│   │   │   └── LegalMetadataRegistry.sol < Legal hashes
│   │   ├── compliance/
│   │   │   ├── ComplianceRegistry.sol    < Compliance state
│   │   │   └── LegalEvidenceStore.sol    < Evidence storage
│   │   ├── access/
│   │   │   └── LexRoles.sol        < Access control
│   │   └── proxy/
│   │       └── LexProxy.sol        < Upgradeable proxy
│   ├── scripts/
│   │   ├── Deploy.s.sol            < Deployment script
│   │   └── DeployConfig.s.sol      < Configuration
│   ├── test/
│   │   ├── LexGovernor.t.sol       < Governor tests
│   │   ├── LexAssetToken.t.sol     < Token tests
│   │   ├── ComplianceRegistry.t.sol
│   │   └── LegalMetadataRegistry.t.sol
│   └── remappings.txt
│
├── docs/                            * Documentation
│   ├── architecture/
│   │   └── ARCHITECTURE.md         < System design
│   ├── deployment/
│   │   ├── DEPLOYMENT.md           < Deployment guide
│   │   └── TROUBLESHOOTING.md      < Common issues
│   └── api/README.md               < API reference
│
├── tests/                           * Comprehensive Tests
│   ├── backend/
│   │   ├── test_auth.py
│   │   ├── test_assets.py
│   │   ├── test_documents.py
│   │   ├── test_compliance.py
│   │   └── test_governance.py
│   └── security/
│       ├── test_xss.py
│       ├── test_sql_injection.py
│       ├── test_csrf.py
│       ├── test_rate_limiting.py
│       └── test_authentication.py
│
├── security/                        * Security Engineering
│   ├── SECURITY_ARCHITECTURE.md    < Security model
│   ├── THREAT_MODEL.md             < STRIDE analysis
│   ├── policies/
│   │   ├── CSP_POLICY.md
│   │   ├── PASSWORD_POLICY.md
│   │   ├── API_SECURITY.md
│   │   └── DATA_CLASSIFICATION.md
│   └── audit/
│       └── security_checklist.md
│
├── scripts/                         * Operations
│   ├── setup.sh                    < First-time setup
│   ├── backup.sh                   < Database backup
│   └── healthcheck.sh              < Service health check
│
└── infrastructure/                 * DevOps
    ├── monitoring/
    │   ├── prometheus.yml
    │   └── grafana-dashboard.json
    └── backup/
        └── backup_strategy.md
```

---

## Quick Start

### One-Click Setup

```bash
git clone https://github.com/elonmasai7/LexChain_Sovereign.git
cd LexChain_Sovereign
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Manual Setup

**Prerequisites:**
- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (optional)
- Node.js 20+ (for smart contracts)
- Foundry (for Solidity development)

**1. Clone and install dependencies:**
```bash
git clone https://github.com/elonmasai7/LexChain_Sovereign.git
cd LexChain_Sovereign

python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

**2. Configure environment:**
```bash
cp .env.example .env
# Edit .env with your:
# - Database credentials
# - Redis password
# - JWT secrets
# - API keys (OpenAI, etc.)
```

**3. Setup database:**
```bash
cd backend
alembic upgrade head
cd ..
```

**4. Seed demo data:**
```bash
cd backend
python -m seed_data
cd ..
```

**5. Start development server:**
```bash
uvicorn backend.app.main:app --reload --port 8000
```

**6. Open in browser:**
```
http://localhost:8000
http://localhost:8000/docs  (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed data
docker-compose exec backend python -m seed_data

# Stop
docker-compose down
```

---

## API Reference

The complete API is documented via OpenAPI/Swagger when the server is running.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **Authentication** |
| POST | `/api/v1/auth/register` | Register new user | - |
| POST | `/api/v1/auth/login` | Email/password login | - |
| POST | `/api/v1/auth/wallet` | Wallet auth | - |
| POST | `/api/v1/auth/refresh` | Refresh JWT | Refresh Token |
| POST | `/api/v1/auth/mfa/verify` | Verify MFA code | MFA Token |
| POST | `/api/v1/auth/mfa/setup` | Setup TOTP MFA | Bearer |
| POST | `/api/v1/auth/logout` | Logout | Bearer |
| GET | `/api/v1/auth/me` | Current user info | Bearer |
| **Assets** |
| GET | `/api/v1/assets` | List assets | Bearer |
| POST | `/api/v1/assets` | Create asset | Bearer |
| GET | `/api/v1/assets/{id}` | Get asset | Bearer |
| POST | `/api/v1/assets/{id}/verify` | Submit for review | Bearer |
| POST | `/api/v1/assets/{id}/approve` | Approve asset | Bearer |
| POST | `/api/v1/assets/{id}/tokenize` | Mint tokens | Bearer |
| POST | `/api/v1/assets/{id}/transfer` | Transfer ownership | Bearer |
| DELETE | `/api/v1/assets/{id}` | Revoke asset | Bearer |
| **Documents** |
| GET | `/api/v1/documents` | List documents | Bearer |
| POST | `/api/v1/documents` | Create document | Bearer |
| POST | `/api/v1/documents/{id}/sign` | Sign document | Bearer |
| POST | `/api/v1/documents/{id}/anchor` | Anchor to chain | Bearer |
| GET | `/api/v1/documents/{id}/history` | Version history | Bearer |
| GET | `/api/v1/documents/{id}/export/pdf` | Export PDF | Bearer |
| **Compliance** |
| POST | `/api/v1/compliance/aml` | Run AML check | Bearer |
| POST | `/api/v1/compliance/kyc` | Run KYC check | Bearer |
| POST | `/api/v1/compliance/sanctions` | Sanctions screen | Bearer |
| POST | `/api/v1/compliance/wallet-risk` | Wallet risk analysis | Bearer |
| GET | `/api/v1/compliance/status/{user}` | User status | Bearer |
| GET | `/api/v1/compliance/risk-score/{user}` | Risk score | Bearer |
| **Legal AI** |
| POST | `/api/v1/legal-ai/analyze` | Analyze contract | Bearer |
| POST | `/api/v1/legal-ai/clauses` | Extract clauses | Bearer |
| POST | `/api/v1/legal-ai/risks` | Detect risks | Bearer |
| POST | `/api/v1/legal-ai/summarize` | Generate summary | Bearer |
| POST | `/api/v1/legal-ai/explain-contract` | Explain Solidity | Bearer |
| **Governance** |
| GET | `/api/v1/governance/proposals` | List proposals | Bearer |
| POST | `/api/v1/governance/proposals` | Create proposal | Bearer |
| POST | `/api/v1/governance/proposals/{id}/vote` | Cast vote | Bearer |
| POST | `/api/v1/governance/proposals/{id}/execute` | Execute | Bearer |
| POST | `/api/v1/governance/delegate` | Delegate votes | Bearer |
| **DID** |
| POST | `/api/v1/did/create` | Create DID | Bearer |
| GET | `/api/v1/did/resolve/{did}` | Resolve DID | Bearer |
| POST | `/api/v1/did/issue-credential` | Issue VC | Bearer |
| POST | `/api/v1/did/verify-credential` | Verify VC | Bearer |
| **Evidence** |
| POST | `/api/v1/evidence` | Store evidence | Bearer |
| POST | `/api/v1/evidence/{id}/verify` | Verify hash | Bearer |
| POST | `/api/v1/evidence/{id}/anchor` | Anchor to chain | Bearer |
| GET | `/api/v1/evidence/{id}/proof` | Verif. proof | Bearer |
| GET | `/api/v1/evidence/{id}/chain-of-custody` | Custody trail | Bearer |
| **Analytics** |
| GET | `/api/v1/analytics/dashboard` | Dashboard metrics | Bearer |
| GET | `/api/v1/analytics/compliance` | Compliance metrics | Bearer |
| GET | `/api/v1/analytics/assets` | Asset distribution | Bearer |
| GET | `/api/v1/analytics/governance` | Governance activity | Bearer |
| GET | `/api/v1/analytics/regulatory-alerts` | Regulatory alerts | Bearer |
| **Audit** |
| GET | `/api/v1/audit/logs` | Query audit logs | Bearer |
| GET | `/api/v1/audit/user/{user}` | User audit trail | Bearer |
| GET | `/api/v1/audit/resource/{type}/{id}` | Resource history | Bearer |
| **System** |
| GET | `/health` | Health check | - |
| GET | `/metrics` | Prometheus metrics | - |
| GET | `/docs` | Swagger UI | - |
| GET | `/redoc` | ReDoc | - |

---

## Security Features

### Authentication & Access Control
- **bcrypt** password hashing with configurable rounds
- **JWT** with automatic rotation (access: 30min, refresh: 7 days)
- **MFA** via TOTP (Google Authenticator, Authy)
- **WebAuthn** passkey support
- **Brute force** protection with progressive lockout (5 attempts > 15min lock)
- **Session fingerprinting** (IP + User-Agent + device)

### API Security
- **Rate limiting**: Per-user (60/min), per-IP (100/min), per-endpoint
- **CSRF tokens** on all mutating operations
- **Input validation**: Pydantic schemas + sanitization
- **SQL injection**: ORM parameterized queries
- **XSS prevention**: Output encoding, CSP headers
- **CORS**: Configurable origin allowlist

### Transport Security
- **TLS 1.3** required in production
- **HSTS** preload header
- **Content Security Policy** with strict rules
- **X-Frame-Options**: SAMEORIGIN
- **X-Content-Type-Options**: nosniff

### Data Protection
- **Encryption at rest**: Fernet (AES-128-CBC) for sensitive fields
- **Encryption in transit**: TLS 1.3
- **Secrets management**: Environment variables, no hardcoded secrets
- **Key rotation**: Encryption key rotation support

### Audit & Compliance
- **Immutable audit logs** for all sensitive operations
- **User activity tracking** with IP, user agent, timestamp
- **Resource change history** with complete diff trail
- **SIEM-ready** JSON log format
- **Compliance event logging** for regulatory requirements

---

## Database Schema

### Entity Relationship

```
┌───────────┐       ┌──────────────┐       ┌──────────────┐
│   Users   │1──N──│    Sessions  │       │    Assets    │
│           │       │              │       │              │
│  id (PK)  │       │  id (PK)    │       │  id (PK)     │
│  email    │       │  user_id(FK)│       │  owner_id(FK)│
│  role     │       │  token_hash │       │  asset_type  │
│  ...      │       │  expires_at │       │  status      │
└───────────┘       └──────────────┘       └──────────────┘
     │ 1                                        │
     │                                          │
     │ N                                        │ N
┌───────────┐       ┌──────────────┐       ┌──────────────┐
│ AuditLogs │       │  Documents   │       │  Proposals   │
│           │       │              │       │              │
│  id (PK)  │       │  id (PK)     │       │  id (PK)     │
│  user_id  │       │  created_by  │       │  proposer_id │
│  action   │       │  status      │       │  status      │
│  ...      │       │  ...         │       │  ...         │
└───────────┘       └──────────────┘       └──────────────┘
                              │ N                    │ 1
                              │                      │
                              │                      │ N
                         ┌──────────┐          ┌──────────┐
                         │Signatures│          │   Votes  │
                         │          │          │          │
                         └──────────┘          └──────────┘
```

### Key Database Tables

| Table | Size | Key Columns | Indexes |
|-------|------|-------------|---------|
| `users` | Core | email, role, wallet_address, did | 3 B-tree indexes |
| `user_sessions` | Auth | token_hash, ip_address, device_fingerprint | 2 B-tree |
| `audit_logs` | Audit | action, resource_type, created_at | 3 B-tree |
| `assets` | RWA | asset_type, status, chain_id, contract_address | 3 B-tree |
| `legal_documents` | Legal | document_type, status, ipfs_hash, blockchain_tx_hash | 4 B-tree |
| `compliance_checks` | Compliance | check_type, status, score | 2 B-tree |
| `risk_scores` | Risk | overall_score, risk_level | 2 B-tree |
| `proposals` | DAO | status, voting_type, start_time | 2 B-tree |
| `votes` | DAO | proposal_id, voter_id, choice | 2 B-tree + unique |
| `legal_evidence` | Evidence | file_hash, ipfs_cid, status | 4 B-tree |
| `notifications` | System | user_id, is_read, type | 2 B-tree |

---

## Testing Strategy

```bash
# Run all tests
pytest tests/ -v --cov=backend/app

# Backend tests
pytest tests/backend/ -v

# Security tests
pytest tests/security/ -v

# Smart contract tests (requires Foundry)
cd contracts && forge test

# Lint and type checking
ruff check backend/
mypy backend/app
```

**Coverage Target:** 85%+ meaningfully covered

| Test Category | What We Test |
|--------------|--------------|
| Unit Tests | Services, validators, helpers |
| API Tests | All endpoints, auth flows, permissions |
| Integration | Database operations, Redis caching |
| Security | XSS, SQL injection, CSRF, rate limiting |
| Contract | Function calls, access control, edge cases |
| E2E | Full workflows (register > tokenize > anchor) |

---

## Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Override with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

### Production Environment Variables

```bash
# Security (REQUIRED)
SECRET_KEY=<generate-random-64char-string>
JWT_SECRET=<generate-random-64char-string>
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Database
DB_PASSWORD=<strong-random-password>

# Redis
REDIS_PASSWORD=<strong-random-password>

# Domain
DOMAIN=lexchain-sovereign.com
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` |  | - | 64-char random string |
| `JWT_SECRET` |  | - | JWT signing secret |
| `ENCRYPTION_KEY` |  | - | Fernet key for data encryption |
| `DATABASE_URL` |  | `postgresql+asyncpg://lexchain@localhost:5432/lexchain` | Async PostgreSQL |
| `REDIS_URL` |  | `redis://:password@localhost:6379/0` | Redis connection |
| `OPENAI_API_KEY` | ✳️ | - | OpenAI for contract analysis |
| `ANTHROPIC_API_KEY` | ✳️ | - | Anthropic for legal AI |
| `WEB3_PROVIDER_URL` | ✳️ | - | Ethereum RPC endpoint |
| `CORS_ORIGINS` | ✳️ | `http://localhost:8000` | Allowed origins |
| `SENTRY_DSN` | ✳️ | - | Error tracking |

✳️ = Optional (features degrade gracefully when not set)

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Lighthouse Score | 95+ |
| First Contentful Paint | <1.5s |
| Time to Interactive | <3s |
| API Response Time (p95) | <200ms |
| Database Query Time | <50ms |
| JS Bundle Size | <100KB |
| Accessibility Score | 100 |
| SEO Score | 100 |

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'feat: Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request against `develop`

### Development Guidelines

- Follow Python `ruff` linting and `mypy` type checking
- Write tests for all new features
- Use the existing code style and patterns
- Update documentation for API changes
- Run the full test suite before submitting PR

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contact & Support

- **GitHub Issues**: [Report bugs or feature requests](https://github.com/elonmasai7/LexChain_Sovereign/issues)
- **Documentation**: Full docs in the `/docs` directory
- **Email**: elonmasai7@gmail.com

---

## Hackathon

Built for the **Blockchain Legal Institute Global Hackathon**

> *"Democratizing access to legal infrastructure through blockchain technology and artificial intelligence."*
