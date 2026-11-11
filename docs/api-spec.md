# Demolition Intelligence & Material Recovery: REST API Specification

- **Base URL**: `/api/v1`
- **Specification Format**: OpenAPI 3.1 compatible
- **Authentication**: Bearer JWT Token (`Authorization: Bearer <token>`)
- **Interactive Documentation**: Swagger UI at `/docs`, ReDoc at `/redoc`

---

## 1. Global Conventions & Error Schema

### 1.1. Standard Error Envelope
All client errors (4xx) and server errors (5xx) adhere to a consistent JSON response:
```json
{
  "detail": "Descriptive human-readable error explanation."
}
```

### 1.2. Standard Pagination Envelope
```json
{
  "items": [],
  "total": 128,
  "page": 1,
  "page_size": 20,
  "total_pages": 7
}
```

---

## 2. Core Endpoints Summary

### 2.1. Authentication & Accounts (`/auth`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/auth/register` | Register a new user (Contractor, Surveyor, Buyer, Recycler) | No |
| `POST` | `/auth/login` | OAuth2 password credentials exchange for access token | No |
| `GET` | `/auth/me` | Retrieve profile of the currently authenticated user | Yes |

#### Sample Token Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "7f9e8a71-6c2e-4b44-9387-9b2f2118f673",
    "email": "surveyor@demolitioncorp.com",
    "full_name": "Marcus Vance",
    "role": "SURVEYOR",
    "company_name": "Apex Demolition Group",
    "phone_number": "+1-555-019-2834",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2026-11-11T09:00:00Z",
    "updated_at": "2026-11-11T09:00:00Z"
  }
}
```

---

### 2.2. Demolition Sites (`/sites`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/sites/` | Register a new demolition site project | Yes |
| `GET` | `/sites/` | List demolition sites with pagination and search (`search`, `city`) | Yes |
| `GET` | `/sites/{site_id}` | Retrieve comprehensive site details | Yes |
| `PATCH` | `/sites/{site_id}` | Update site metadata, status, or demolition milestone dates | Yes |

---

### 2.3. Site Surveys & Image Evidence (`/surveys`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/surveys/` | Create a new inspection survey session | Yes |
| `GET` | `/surveys/{survey_id}` | Retrieve survey data with image links and presigned URLs | Yes |
| `POST` | `/surveys/{survey_id}/presigned-url` | Generate S3 presigned upload URL for direct client upload | Yes |
| `POST` | `/surveys/{survey_id}/upload-direct` | Multipart direct upload (local development mode) | Yes |

---

### 2.4. Materials & Valuation (`/materials`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/materials/` | Filter material inventory by `survey_id`, `category`, `condition` | Yes |
| `GET` | `/materials/summary/{survey_id}` | Financial valuation and carbon offset breakdown by category | Yes |
| `PATCH` | `/materials/{material_id}` | Review, adjust quantity/condition, and verify material item | Yes |

---

### 2.5. AI Analysis & Audit Reports (`/analysis`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/analysis/trigger` | Queue asynchronous computer vision and LLM report tasks | Yes |
| `GET` | `/analysis/jobs/{job_id}` | Poll background analysis progress and telemetry | Yes |
| `GET` | `/analysis/reports/{survey_id}` | Retrieve synthesized Demolition Material Audit Report (DMAR) | Yes |

#### Sample DMAR Audit Report Response
```json
{
  "id": "e4b2d312-32a4-4a25-9f5b-11c750b2b801",
  "site_id": "site-89a1",
  "survey_id": "srv-001",
  "report_title": "Demolition Material Audit Report - Metro Logistics Center",
  "executive_summary": "Pre-demolition visual audit completed for Metro Logistics Center...",
  "regulatory_compliance_notes": "EPA 70% diversion standard satisfied. No asbestos risk detected in mezzanine.",
  "buyer_matching_insights": "Direct salvage recommended for 98.1t structural steel columns to regional precast fabricators.",
  "total_recoverable_tonnes": 1124.3,
  "total_estimated_value_usd": 59194.10,
  "total_carbon_offset_kg_co2e": 289033.5,
  "detailed_breakdown_json": [
    {
      "category": "STEEL",
      "count": 24,
      "total_tonnes": 98.1,
      "total_volume_m3": 12.5,
      "estimated_value_usd": 31392.0,
      "carbon_offset_kg": 176580.0
    }
  ],
  "pdf_report_s3_key": "reports/srv-001/audit_report.pdf",
  "created_at": "2026-11-11T10:15:00Z"
}
```

---

### 2.6. Secondary Material Marketplace (`/marketplace`)
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/marketplace/` | Publish a material lot for buyers and recyclers | Yes |
| `GET` | `/marketplace/` | Browse active material listings with city/status filters | Yes |
| `PATCH` | `/marketplace/{listing_id}` | Update listing details or transition status (`SOLD`, `RESERVED`) | Yes |

---

### 2.7. Health & Infrastructure Probes
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `GET` | `/health/live` | Container liveness check | No |
| `GET` | `/health/ready` | Readiness check verifying database, Redis, and storage configs | No |
