# Database Architecture & Entity-Relationship (ER) Diagram

The persistence layer for **Demolition Intelligence & Material Recovery** is implemented on PostgreSQL 16 utilizing SQLAlchemy 2.0 with asynchronous connection pooling (`asyncpg`) and transactional integrity.

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ DEMOLITION_SITES : "contracts / owns"
    USERS ||--o{ SITE_SURVEYS : "conducts"
    USERS ||--o{ MARKETPLACE_LISTINGS : "sells"
    
    DEMOLITION_SITES ||--o{ SITE_SURVEYS : "has"
    DEMOLITION_SITES ||--o{ DEMOLITION_AUDIT_REPORTS : "receives"
    
    SITE_SURVEYS ||--o{ SURVEY_IMAGES : "contains"
    SITE_SURVEYS ||--o{ MATERIAL_ITEMS : "logs"
    SITE_SURVEYS ||--o{ ANALYSIS_JOBS : "triggers"
    SITE_SURVEYS ||--o{ DEMOLITION_AUDIT_REPORTS : "synthesizes"
    
    SURVEY_IMAGES ||--o{ MATERIAL_ITEMS : "localizes_in"
    MATERIAL_ITEMS ||--o{ MARKETPLACE_LISTINGS : "offers_on"

    USERS {
        string id PK "UUID"
        string email UK "Indexed"
        string hashed_password
        string full_name
        string role "ADMIN, CONTRACTOR, SURVEYOR, BUYER, RECYCLER"
        string company_name
        string phone_number
        boolean is_active
        boolean is_superuser
        timestamp created_at
        timestamp updated_at
    }

    DEMOLITION_SITES {
        string id PK "UUID"
        string name "Indexed"
        string site_code UK "Indexed"
        text description
        string address
        string city "Indexed"
        string postal_code
        string country
        float latitude
        float longitude
        string status "PLANNING, ACTIVE_DEMOLITION, COMPLETED"
        date estimated_demolition_date
        date actual_demolition_date
        string contractor_id FK
        timestamp created_at
        timestamp updated_at
    }

    SITE_SURVEYS {
        string id PK "UUID"
        string site_id FK "Indexed"
        string surveyor_id FK
        date survey_date
        string weather_condition
        text survey_notes
        string status "PENDING, PROCESSING, ANALYSIS_COMPLETED, FAILED"
        int total_images_count
        timestamp created_at
        timestamp updated_at
    }

    SURVEY_IMAGES {
        string id PK "UUID"
        string survey_id FK "Indexed"
        string file_name
        string original_s3_key
        string annotated_s3_key
        string thumbnail_s3_key
        bigint file_size_bytes
        string mime_type
        int width
        int height
        float gps_latitude
        float gps_longitude
        timestamp created_at
    }

    MATERIAL_ITEMS {
        string id PK "UUID"
        string survey_id FK "Indexed"
        string source_image_id FK "Indexed"
        string category "CONCRETE, BRICKS, STEEL, TIMBER, GLASS, MIXED_DEBRIS"
        string subcategory
        text description
        string condition_grade "REUSABLE_EXCELLENT, REUSABLE_GOOD, RECYCLABLE, DOWN_CYCLE_ONLY, HAZARDOUS_CONTAMINATED"
        float estimated_volume_m3
        float estimated_weight_tonnes
        int unit_count
        string contamination_risk
        float confidence_score
        json bounding_box
        json segmentation_polygon
        float estimated_market_value_usd
        float embodied_carbon_offset_kg
        boolean is_verified_by_surveyor
        text surveyor_adjustment_notes
        timestamp created_at
        timestamp updated_at
    }

    ANALYSIS_JOBS {
        string id PK "UUID"
        string survey_id FK "Indexed"
        string celery_task_id UK "Indexed"
        string status "QUEUED, IN_PROGRESS, SUCCESS, FAILED"
        int progress_percentage
        int processed_images_count
        int total_images_count
        text error_message
        json execution_metrics
        timestamp started_at
        timestamp completed_at
        timestamp created_at
    }

    MARKETPLACE_LISTINGS {
        string id PK "UUID"
        string material_item_id FK "Indexed"
        string seller_id FK "Indexed"
        string title
        text description
        float available_tonnes
        float min_order_tonnes
        float price_per_tonne_usd
        float total_price_usd
        string pickup_address
        string pickup_city "Indexed"
        text logistics_notes
        string status "DRAFT, ACTIVE, RESERVED, SOLD, CANCELLED"
        timestamp listed_at
        timestamp sold_at
        timestamp created_at
        timestamp updated_at
    }

    DEMOLITION_AUDIT_REPORTS {
        string id PK "UUID"
        string site_id FK "Indexed"
        string survey_id FK "Indexed"
        string report_title
        text executive_summary
        text regulatory_compliance_notes
        text buyer_matching_insights
        float total_recoverable_tonnes
        float total_estimated_value_usd
        float total_carbon_offset_kg_co2e
        json detailed_breakdown_json
        string pdf_report_s3_key
        timestamp created_at
    }
```

---

## 2. Table Specifications & Cardinality Rules

| Parent Entity | Child Entity | Cardinality | Cascade Action | Rationale |
| :--- | :--- | :---: | :--- | :--- |
| `users` | `demolition_sites` | $1 : N$ | `CASCADE` | Sites belong to the primary contractor/creator account. |
| `demolition_sites` | `site_surveys` | $1 : N$ | `CASCADE` | Surveys represent chronological inspection sessions for a site. |
| `site_surveys` | `survey_images` | $1 : N$ | `CASCADE` | Image records are scoped strictly to the inspection survey. |
| `site_surveys` | `material_items` | $1 : N$ | `CASCADE` | Material items belong to the survey session where detected. |
| `survey_images` | `material_items` | $1 : N$ | `SET NULL` | Deleting an image leaves the logged material item intact with historical metadata. |
| `site_surveys` | `analysis_jobs` | $1 : N$ | `CASCADE` | Background jobs track asynchronous processing for the survey. |
| `material_items`| `marketplace_listings` | $1 : N$ | `CASCADE` | Marketplace offers depend on verified material items. |
| `site_surveys` | `demolition_audit_reports` | $1 : N$ | `CASCADE` | Audit reports synthesize the survey's aggregated data. |

---

## 3. Database Indexing Strategy
- **Primary Keys**: High-entropy UUID v4 strings for distributed ID generation and horizontal partitioning compatibility.
- **Foreign Keys**: Every foreign key is explicitly indexed to avoid full table scans during joins and cascade deletions.
- **Geographic & Search Indexes**: `city` and `site_code` are indexed for fast contractor filtering and logistics queries.
- **Enum Indexes**: Status fields (`JobStatus`, `SurveyStatus`, `ListingStatus`) are indexed to optimize dashboard queries and polling workers.

