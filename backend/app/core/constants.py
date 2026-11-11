import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CONTRACTOR = "CONTRACTOR"
    DEMOLITION_CONTRACTOR = "DEMOLITION_CONTRACTOR"
    SURVEYOR = "SURVEYOR"
    RECYCLER = "RECYCLER"
    BUYER = "BUYER"
    MATERIAL_BUYER = "MATERIAL_BUYER"


class SiteStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    PRE_DEMOLITION_SURVEY = "PRE_DEMOLITION_SURVEY"
    ACTIVE_DEMOLITION = "ACTIVE_DEMOLITION"
    MATERIAL_SORTING = "MATERIAL_SORTING"
    COMPLETED = "COMPLETED"


class SurveyStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    FAILED = "FAILED"


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class MediaType(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    ORTHOMOSAIC = "ORTHOMOSAIC"
    SCAN_360 = "SCAN_360"


class MaterialCategory(str, enum.Enum):
    CONCRETE = "CONCRETE"
    BRICKS = "BRICKS"
    STEEL = "STEEL"
    TIMBER = "TIMBER"
    GLASS = "GLASS"
    MIXED_DEBRIS = "MIXED_DEBRIS"


class ConditionGrade(str, enum.Enum):
    REUSABLE_EXCELLENT = "REUSABLE_EXCELLENT"  # Prime condition, direct structural or architectural reuse
    REUSABLE_GOOD = "REUSABLE_GOOD"            # Minor cleaning/refurbishment required
    RECYCLABLE = "RECYCLABLE"                  # Suitable for crushing/melting/reprocessing
    DOWN_CYCLE_ONLY = "DOWN_CYCLE_ONLY"        # Aggregate, backfill, low-grade road sub-base
    HAZARDOUS_CONTAMINATED = "HAZARDOUS_CONTAMINATED"  # Contains asbestos, heavy lead, hazardous adhesives


class ListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    CANCELLED = "CANCELLED"


class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VERIFY = "VERIFY"
    ANALYZE = "ANALYZE"
    BID = "BID"
    EXPORT = "EXPORT"
    UPLOAD = "UPLOAD"
    APPROVE = "APPROVE"


class BuyerCompanyType(str, enum.Enum):
    STEEL_MILL = "STEEL_MILL"
    AGGREGATE_CRUSHER = "AGGREGATE_CRUSHER"
    ARCHITECTURAL_SALVAGE = "ARCHITECTURAL_SALVAGE"
    TIMBER_RECLAIMER = "TIMBER_RECLAIMER"
    GLASS_RECYCLER = "GLASS_RECYCLER"


# Industry standard volumetric mass densities (Metric Tonnes / m^3)
# Based on CIRIA & EPA Construction and Demolition waste characterization guidelines
MATERIAL_DENSITIES_TONNES_PER_M3 = {
    MaterialCategory.CONCRETE: 2.40,
    MaterialCategory.BRICKS: 1.80,
    MaterialCategory.STEEL: 7.85,
    MaterialCategory.TIMBER: 0.65,
    MaterialCategory.GLASS: 2.50,
    MaterialCategory.MIXED_DEBRIS: 1.50,
}

# Embodied carbon emission offset factors when recovered/reused instead of virgin materials
# Measured in kg CO2 equivalent saved per metric tonne (kg CO2e / tonne)
# Source benchmark: ICE (Inventory of Carbon & Energy) database
CARBON_OFFSET_SAVINGS_PER_TONNE = {
    MaterialCategory.CONCRETE: 130.0,   # Crushed recycled aggregate vs virgin quarried crushed stone
    MaterialCategory.BRICKS: 240.0,     # Reclaimed architectural bricks vs virgin kiln-fired clay bricks
    MaterialCategory.STEEL: 1800.0,     # Electric Arc Furnace / structural reuse vs virgin Blast Furnace steel
    MaterialCategory.TIMBER: 450.0,     # Reclaimed timber beams vs virgin milled timber
    MaterialCategory.GLASS: 350.0,      # Recycled architectural cullet vs float glass production
    MaterialCategory.MIXED_DEBRIS: 50.0 # Diverted landfill emissions
}

# Baseline secondary market unit pricing estimate (USD per metric tonne)
# Real-world dynamic prices will calibrate based on condition grade and market indices
DEFAULT_BASELINE_PRICE_PER_TONNE = {
    MaterialCategory.CONCRETE: 18.0,    # Crushed concrete aggregate base
    MaterialCategory.BRICKS: 110.0,     # Reclaimed decorative/structural bricks
    MaterialCategory.STEEL: 320.0,      # Heavy structural scrap / reusable I-beams
    MaterialCategory.TIMBER: 190.0,     # Reclaimed structural lumber / hardwood
    MaterialCategory.GLASS: 45.0,       # Cullet / architectural pane stock
    MaterialCategory.MIXED_DEBRIS: 8.0, # Sorting required aggregate
}
