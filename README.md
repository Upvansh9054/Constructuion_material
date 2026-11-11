# Demolition Intelligence & Material Recovery

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind%20CSS%20%2B%20shadcn-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PyTorch](https://img.shields.io/badge/AI-PyTorch%20%26%20YOLO-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

An AI-powered circular economy platform that analyses demolition sites, identifies recoverable construction materials, estimates physical quantities and condition grades, calculates secondary market recovery value and embodied carbon offsets, and connects demolition contractors with material buyers and recyclers.

---

## 1. Initial Material Categories

The system models and classifies six primary demolition material streams:
1. **Concrete**: Structural precast slabs, foundation piers, crushed aggregates.
2. **Bricks**: Reclaimed decorative facing bricks, structural masonry, refractory bricks.
3. **Steel**: Heavy structural I-beams, trusses, rebar cages, corrugated cladding.
4. **Timber**: Hardwood framing beams, dimensional rafters, reclaimed floorboards.
5. **Glass**: Facade sheets, double glazing, architectural cullet for remelting.
6. **Mixed Demolition Debris**: Inert plaster/masonry spall requiring mechanical sorting.

---

## 2. Architecture & Directory Hierarchy

The project is structured with modular separation between the web API, computer vision engine, background workers, and client interface:

```
Demolition-Intelligence/
├── backend/
│   ├── app/
│   │   ├── api/v1/                  # REST API endpoints & route groupings
│   │   │   ├── endpoints/           # auth, sites, surveys, materials, analysis, marketplace
│   │   │   ├── deps.py              # Auth & database dependency injection
│   │   │   └── router.py            # Consolidated v1 router
│   │   ├── core/                    # Settings, DB session, JWT security, logging, constants
│   │   ├── models/                  # SQLAlchemy 2.0 ORM domain entities
│   │   ├── schemas/                 # Pydantic v2 validation contracts
│   │   ├── services/                # Storage (S3/MinIO), Valuation, OpenAI LLM reports
│   │   ├── workers/                 # Celery app & background task definitions
│   │   └── main.py                  # FastAPI application entrypoint & lifespan
│   ├── ai_pipeline/                 # Decoupled AI Computer Vision Engine
│   │   ├── contracts.py             # Detector & Estimator abstract interfaces
│   │   ├── detector.py              # Production YOLOv8/v11 PyTorch detector
│   │   ├── preprocessor.py          # OpenCV EXIF orientation & tile slicing
│   │   ├── estimator.py             # Volumetric, mass, & condition grading
│   │   └── weights/                 # Model checkpoints (.pt, .onnx)
│   ├── alembic/                     # Database migration scripts
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/ui/           # shadcn/ui primitives (badge, button, card)
│   │   ├── components/layout/       # Navbar, Sidebar, PageLayout
│   │   ├── features/                # Domain UI (dashboard, surveys, materials, marketplace)
│   │   ├── lib/                     # API client, cn() utilities, formatting
│   │   ├── types/                   # TypeScript schemas and domain contracts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env.example
├── docker/
│   └── postgres/init.sql            # PostgreSQL extensions (uuid-ossp, pgcrypto)
├── docs/
│   ├── architecture.md              # System design & C4 diagrams
│   ├── er-diagram.md                # Entity-Relationship diagram & cardinality
│   └── api-spec.md                  # REST API endpoint specification
├── docker-compose.yml               # Multi-container orchestration
└── .gitignore                       # Git exclusions for secrets, venvs, model weights
```

---

## 3. Implemented Database Modules & Role Architecture

The platform architecture implements all 15 required modules with strict SQLAlchemy 2.0 ORM mappings, Alembic migration versioning, and RBAC:

| Module # | Domain Entity | Primary Model | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **1** | Users | `User` | Secure bcrypt hashing, UUID primary keys, active state |
| **2** | Roles & Permissions | `UserRole` | `ADMIN`, `DEMOLITION_CONTRACTOR`, `SURVEYOR`, `MATERIAL_BUYER`, `RECYCLER` |
| **3** | Demolition Projects | `DemolitionSite` | Project code uniqueness, timeline, geo-coordinates, contractor ownership |
| **4** | Site Information | `DemolitionSite` | Structural framing type, footprint $m^2$, asbestos & lead paint hazard screening |
| **5** | Uploaded Media | `SiteSurvey`, `SurveyImage` | Image & drone video records, camera altitude, focal length, sensor width, GSD |
| **6** | AI Analysis Records | `AnalysisJob` | Asynchronous Celery CV job status, telemetry metrics, execution duration |
| **7** | Material Categories | `MaterialCategoryDefinition` | 6 streams: standard density ($t/m^3$), ICE carbon offset factor ($kg CO_2e/t$), benchmark pricing |
| **8** | Material Inventory | `MaterialItem` | Normalized bounding boxes, surveyor verification sign-off, confidence score |
| **9** | Quantity Estimates | `MaterialItem` | Calibrated photogrammetry volume ($m^3$), weight ($tonnes$), packing factor |
| **10** | Recovery Assessments | `MaterialItem` | 5 condition grades, contamination risk, valuation ($USD$), embodied carbon offsets |
| **11** | Buyers & Recyclers | `BuyerRecyclerProfile` | Industry directory (Steel Mills, Aggregate Crushers, Salvage), distance km, ratings |
| **12** | Material Listings | `MarketplaceListing` | Secondary commercial circular lots, minimum orders, pickup location, status |
| **13** | Enquiries & Transactions | `EnquiryTransaction` | Commercial buyer bids, haulage trailer types, status negotiation (Accept/Reject) |
| **14** | Pre-Demolition Reports | `DemolitionAuditReport` | Pre-Demolition Audit (DMAR), executive synthesis, compliance notes, category breakdowns |
| **15** | Immutable Audit Ledger | `AuditLog` | Regulatory event logging (CREATE, UPDATE, DELETE, VERIFY, UPLOAD, APPROVE) |

---

## 4. Quick Start with Docker (Recommended)

To run the entire platform with PostgreSQL, Redis, MinIO S3, FastAPI backend, Celery worker, and Vite frontend:

```bash
# 1. Copy environment configurations
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Launch all services
docker compose up -d --build
```

### Accessing Endpoints:
- **Frontend Web Application**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Storage Console**: [http://localhost:9001](http://localhost:9001) (User: `minioadmin`, Pass: `minioadmin123`)
- **Backend Health Check**: [http://localhost:8000/health/ready](http://localhost:8000/health/ready)

---

## 4. Local Development Setup (Manual)

### Prerequisites:
- Python 3.10+ (tested up to 3.14)
- Node.js 18+ & npm 9+
- PostgreSQL 15+ & Redis 6+ (or run via Docker)

### 4.1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
python -m alembic upgrade head

# Seed initial turnkey database (Users, Sites, Materials, Listings, Directory)
python scripts/seed_db.py

# Run backend automated test suite
python -m pytest tests -v

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 4.2. Celery Worker (In a separate terminal)

```bash
cd backend
# With virtual environment activated:
celery -A app.workers.celery_app worker -l info -c 2
```

### 4.3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

---

## 5. AI Pipeline & Model Serving

The computer vision engine is strictly separated from the web backend:
- Interfaces are defined in `backend/ai_pipeline/contracts.py`.
- **Honest AI Architecture**: If fine-tuned weights (`ai_pipeline/weights/demolition_materials_yolov8.pt`) are not present, the system cleanly raises `ModelWeightsNotFoundError` rather than generating fake or deceptive pseudo-detections.
- See [`backend/ai_pipeline/README.md`](file:///backend/ai_pipeline/README.md) for training commands, Roboflow/TACO dataset preparations, and model export procedures.

---

## 6. Environment & Security Best Practices

1. **Direct Object Storage Uploads**: Survey images are never piped through the backend memory in production. Clients request S3 presigned PUT URLs (`/api/v1/surveys/{id}/presigned-url`) to stream directly to MinIO/S3.
2. **Access Control**: Passwords are encrypted with `bcrypt`. API routes enforce JWT token authentication with configurable expiration.
3. **Secret Isolation**: All credentials, database connection strings, S3 keys, and OpenAI API tokens reside in `.env` files which are excluded from Git version control.

---

## 7. Next Implementation Steps

1. **Model Training & Weights Acquisition**:
   - Collect and annotate 1,500+ demolition site drone frames across the 6 categories.
   - Train YOLOv8x/v11 on GPU and export weights to `backend/ai_pipeline/weights/`.
2. **LiDAR & RGB-D Photogrammetry Integration**:
   - Integrate stereoscopic depth map processing in `GeometricQuantityEstimator` for sub-centimeter volumetric precision.
3. **Contractor & Recycler Escrow Workflow**:
   - Add bidding, payment escrow, and logistics haulage tracking in the `/marketplace` module.
4. **Automated PDF Export**:
   - Implement WeasyPrint or ReportLab service to compile DMAR reports into official compliance PDFs with photo evidence.

