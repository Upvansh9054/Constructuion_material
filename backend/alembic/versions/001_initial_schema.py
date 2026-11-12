"""Initial complete schema across all 15 Demolition Intelligence modules

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-11 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users Table (Module 1, 2)
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)

    # 2. Demolition Sites Table (Module 3, 4)
    op.create_table(
        'demolition_sites',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('site_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False, default='USA'),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('estimated_demolition_date', sa.Date(), nullable=True),
        sa.Column('actual_demolition_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='PLANNING'),
        sa.Column('contractor_id', sa.String(length=36), nullable=False),
        sa.Column('building_type', sa.String(length=100), nullable=True),
        sa.Column('building_length_m', sa.Float(), nullable=True),
        sa.Column('building_width_m', sa.Float(), nullable=True),
        sa.Column('building_height_m', sa.Float(), nullable=True),
        sa.Column('number_of_floors', sa.Integer(), nullable=True),
        sa.Column('total_building_volume_m3', sa.Float(), nullable=True),
        sa.Column('footprint_sqm', sa.Float(), nullable=True),
        sa.Column('structural_type', sa.String(length=100), nullable=True),
        sa.Column('has_asbestos_risk', sa.Boolean(), nullable=False, default=False),
        sa.Column('has_lead_paint', sa.Boolean(), nullable=False, default=False),
        sa.Column('hazard_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['contractor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_demolition_sites_id'), 'demolition_sites', ['id'], unique=False)
    op.create_index(op.f('ix_demolition_sites_site_code'), 'demolition_sites', ['site_code'], unique=True)
    op.create_index(op.f('ix_demolition_sites_status'), 'demolition_sites', ['status'], unique=False)
    op.create_index(op.f('ix_demolition_sites_contractor_id'), 'demolition_sites', ['contractor_id'], unique=False)

    # 3. Site Surveys Table (Module 5)
    op.create_table(
        'site_surveys',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('site_id', sa.String(length=36), nullable=False),
        sa.Column('surveyor_id', sa.String(length=36), nullable=True),
        sa.Column('survey_date', sa.Date(), nullable=False),
        sa.Column('assessment_name', sa.String(length=255), nullable=True),
        sa.Column('assessment_type', sa.String(length=100), nullable=False, default='PRE_DEMOLITION'),
        sa.Column('weather_condition', sa.String(length=100), nullable=True),
        sa.Column('survey_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='PENDING'),
        sa.Column('processing_status', sa.String(length=50), nullable=False, default='IDLE'),
        sa.Column('total_images_count', sa.Integer(), nullable=False, default=0),
        sa.Column('processed_images_count', sa.Integer(), nullable=False, default=0),
        sa.Column('extracted_frames_count', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['site_id'], ['demolition_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['surveyor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_site_surveys_id'), 'site_surveys', ['id'], unique=False)
    op.create_index(op.f('ix_site_surveys_site_id'), 'site_surveys', ['site_id'], unique=False)
    op.create_index(op.f('ix_site_surveys_status'), 'site_surveys', ['status'], unique=False)

    # 4. Survey Images / Media Table (Module 5)
    op.create_table(
        'survey_images',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('survey_id', sa.String(length=36), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('media_type', sa.String(length=50), nullable=False, default='IMAGE'),
        sa.Column('original_s3_key', sa.String(length=500), nullable=False),
        sa.Column('annotated_s3_key', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_s3_key', sa.String(length=500), nullable=True),
        sa.Column('cv_preprocessed_s3_key', sa.String(length=500), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('is_extracted_frame', sa.Boolean(), nullable=False, default=False),
        sa.Column('parent_video_id', sa.String(length=36), nullable=True),
        sa.Column('frame_index', sa.Integer(), nullable=True),
        sa.Column('timestamp_seconds', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('codec', sa.String(length=50), nullable=True),
        sa.Column('processing_status', sa.String(length=50), nullable=False, default='PROCESSED'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('camera_altitude_m', sa.Float(), nullable=True),
        sa.Column('focal_length_mm', sa.Float(), nullable=True),
        sa.Column('sensor_width_mm', sa.Float(), nullable=True),
        sa.Column('gsd_cm_per_px', sa.Float(), nullable=True),
        sa.Column('gps_latitude', sa.Float(), nullable=True),
        sa.Column('gps_longitude', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['survey_id'], ['site_surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_survey_images_id'), 'survey_images', ['id'], unique=False)
    op.create_index(op.f('ix_survey_images_survey_id'), 'survey_images', ['survey_id'], unique=False)

    # 5. Analysis Jobs Table (Module 6)
    op.create_table(
        'analysis_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('survey_id', sa.String(length=36), nullable=False),
        sa.Column('celery_task_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='QUEUED'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_duration_seconds', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['survey_id'], ['site_surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_analysis_jobs_id'), 'analysis_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_analysis_jobs_survey_id'), 'analysis_jobs', ['survey_id'], unique=False)
    op.create_index(op.f('ix_analysis_jobs_status'), 'analysis_jobs', ['status'], unique=False)

    # 6. Material Category Definitions Table (Module 7)
    op.create_table(
        'material_category_definitions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('standard_density_t_per_m3', sa.Float(), nullable=False),
        sa.Column('carbon_offset_factor_kg_per_t', sa.Float(), nullable=False),
        sa.Column('default_price_per_t_usd', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_material_category_definitions_id'), 'material_category_definitions', ['id'], unique=False)
    op.create_index(op.f('ix_material_category_definitions_category'), 'material_category_definitions', ['category'], unique=True)

    # 7. Material Items Table (Module 8, 9, 10)
    op.create_table(
        'material_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('survey_id', sa.String(length=36), nullable=False),
        sa.Column('source_image_id', sa.String(length=36), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition_grade', sa.String(length=50), nullable=False, default='RECYCLABLE'),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('bounding_box', sa.JSON(), nullable=True),
        sa.Column('estimated_volume_m3', sa.Float(), nullable=False, default=0.0),
        sa.Column('estimated_weight_tonnes', sa.Float(), nullable=False, default=0.0),
        sa.Column('unit_count', sa.Integer(), nullable=True),
        sa.Column('packing_factor', sa.Float(), nullable=False, default=0.85),
        sa.Column('calculation_method', sa.String(length=100), nullable=False, default='calibrated_gsd_photogrammetry'),
        sa.Column('contamination_risk', sa.String(length=255), nullable=True),
        sa.Column('estimated_market_value_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('embodied_carbon_offset_kg', sa.Float(), nullable=False, default=0.0),
        sa.Column('is_verified_by_surveyor', sa.Boolean(), nullable=False, default=False),
        sa.Column('surveyor_adjustment_notes', sa.Text(), nullable=True),
        sa.Column('verified_by_user_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['source_image_id'], ['survey_images.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['survey_id'], ['site_surveys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['verified_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_material_items_id'), 'material_items', ['id'], unique=False)
    op.create_index(op.f('ix_material_items_survey_id'), 'material_items', ['survey_id'], unique=False)
    op.create_index(op.f('ix_material_items_category'), 'material_items', ['category'], unique=False)
    op.create_index(op.f('ix_material_items_condition_grade'), 'material_items', ['condition_grade'], unique=False)

    # 8. Buyer and Recycler Profiles Table (Module 11)
    op.create_table(
        'buyer_recycler_profiles',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('company_type', sa.String(length=50), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False, default=25.0),
        sa.Column('accepted_categories', sa.JSON(), nullable=False),
        sa.Column('certified_standards', sa.JSON(), nullable=False),
        sa.Column('contact_person', sa.String(length=150), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=False),
        sa.Column('contact_phone', sa.String(length=50), nullable=False),
        sa.Column('total_purchased_tonnes', sa.Float(), nullable=False, default=0.0),
        sa.Column('active_bids_count', sa.Integer(), nullable=False, default=0),
        sa.Column('rating', sa.Float(), nullable=False, default=4.8),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_buyer_recycler_profiles_id'), 'buyer_recycler_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_buyer_recycler_profiles_user_id'), 'buyer_recycler_profiles', ['user_id'], unique=True)
    op.create_index(op.f('ix_buyer_recycler_profiles_company_type'), 'buyer_recycler_profiles', ['company_type'], unique=False)
    op.create_index(op.f('ix_buyer_recycler_profiles_city'), 'buyer_recycler_profiles', ['city'], unique=False)

    # 9. Marketplace Listings Table (Module 12)
    op.create_table(
        'marketplace_listings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('material_item_id', sa.String(length=36), nullable=False),
        sa.Column('seller_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('available_tonnes', sa.Float(), nullable=False),
        sa.Column('min_order_tonnes', sa.Float(), nullable=False, default=1.0),
        sa.Column('price_per_tonne_usd', sa.Float(), nullable=False),
        sa.Column('total_price_usd', sa.Float(), nullable=False),
        sa.Column('pickup_address', sa.String(length=500), nullable=False),
        sa.Column('pickup_city', sa.String(length=100), nullable=False),
        sa.Column('logistics_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='ACTIVE'),
        sa.Column('listed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sold_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['material_item_id'], ['material_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_marketplace_listings_id'), 'marketplace_listings', ['id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_material_item_id'), 'marketplace_listings', ['material_item_id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_seller_id'), 'marketplace_listings', ['seller_id'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_status'), 'marketplace_listings', ['status'], unique=False)
    op.create_index(op.f('ix_marketplace_listings_pickup_city'), 'marketplace_listings', ['pickup_city'], unique=False)

    # 10. Enquiry Transactions Table (Module 13)
    op.create_table(
        'enquiry_transactions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('listing_id', sa.String(length=36), nullable=False),
        sa.Column('buyer_id', sa.String(length=36), nullable=False),
        sa.Column('requested_tonnes', sa.Float(), nullable=False),
        sa.Column('bid_price_per_tonne_usd', sa.Float(), nullable=False),
        sa.Column('total_offer_usd', sa.Float(), nullable=False),
        sa.Column('haulage_type', sa.String(length=100), nullable=False, default='FLATBED_TRAILER'),
        sa.Column('status', sa.String(length=50), nullable=False, default='PENDING'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_enquiry_transactions_id'), 'enquiry_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_enquiry_transactions_listing_id'), 'enquiry_transactions', ['listing_id'], unique=False)
    op.create_index(op.f('ix_enquiry_transactions_buyer_id'), 'enquiry_transactions', ['buyer_id'], unique=False)
    op.create_index(op.f('ix_enquiry_transactions_status'), 'enquiry_transactions', ['status'], unique=False)

    # 11. Demolition Audit Reports Table (Module 14)
    op.create_table(
        'demolition_audit_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('site_id', sa.String(length=36), nullable=False),
        sa.Column('survey_id', sa.String(length=36), nullable=False),
        sa.Column('report_title', sa.String(length=255), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('regulatory_compliance_notes', sa.Text(), nullable=True),
        sa.Column('buyer_matching_insights', sa.Text(), nullable=True),
        sa.Column('total_recoverable_tonnes', sa.Float(), nullable=False, default=0.0),
        sa.Column('total_estimated_value_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('total_carbon_offset_kg_co2e', sa.Float(), nullable=False, default=0.0),
        sa.Column('detailed_breakdown_json', sa.JSON(), nullable=False),
        sa.Column('pdf_report_s3_key', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['demolition_sites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['survey_id'], ['site_surveys.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_demolition_audit_reports_id'), 'demolition_audit_reports', ['id'], unique=False)
    op.create_index(op.f('ix_demolition_audit_reports_site_id'), 'demolition_audit_reports', ['site_id'], unique=False)
    op.create_index(op.f('ix_demolition_audit_reports_survey_id'), 'demolition_audit_reports', ['survey_id'], unique=False)

    # 12. Audit Logs Table (Module 15)
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=64), nullable=True),
        sa.Column('change_details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('demolition_audit_reports')
    op.drop_table('enquiry_transactions')
    op.drop_table('marketplace_listings')
    op.drop_table('buyer_recycler_profiles')
    op.drop_table('material_items')
    op.drop_table('material_category_definitions')
    op.drop_table('analysis_jobs')
    op.drop_table('survey_images')
    op.drop_table('site_surveys')
    op.drop_table('demolition_sites')
    op.drop_table('users')
