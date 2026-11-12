"""Add quantity estimation, dimensions, uncertainty, and verified weighbridge columns

Revision ID: 002_quantity_condition_module
Revises: 001_initial_schema
Create Date: 2026-11-11 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_quantity_condition_module'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 3D Physical Dimensions
    op.add_column('material_items', sa.Column('dimension_length_m', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('dimension_width_m', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('dimension_height_m', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('surface_area_m2', sa.Float(), nullable=True))

    # Uncertainty boundaries
    op.add_column('material_items', sa.Column('min_volume_m3', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('max_volume_m3', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('min_weight_tonnes', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('max_weight_tonnes', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('uncertainty_percentage', sa.Float(), nullable=False, server_default='20.0'))

    # Assumptions applied
    op.add_column('material_items', sa.Column('assumed_density_t_per_m3', sa.Float(), nullable=False, server_default='2.40'))
    op.add_column('material_items', sa.Column('reference_measurement_notes', sa.String(length=255), nullable=True))

    # Condition & Safety Hazards
    op.add_column('material_items', sa.Column('damage_severity_pct', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('material_items', sa.Column('damage_type', sa.String(length=100), nullable=True))
    op.add_column('material_items', sa.Column('requires_specialist_abatement', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('material_items', sa.Column('hazard_inspection_warning', sa.Text(), nullable=True))

    # Recoverability & Circular Economy
    op.add_column('material_items', sa.Column('recommended_recovery_route', sa.String(length=100), nullable=False, server_default='CLOSED_LOOP_RECYCLING'))
    op.add_column('material_items', sa.Column('recoverability_percentage', sa.Float(), nullable=False, server_default='85.0'))

    # Separate Verified Quantities (e.g., Weighbridge Measurements)
    op.add_column('material_items', sa.Column('verified_weight_tonnes', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('verified_volume_m3', sa.Float(), nullable=True))
    op.add_column('material_items', sa.Column('weighbridge_ticket_number', sa.String(length=100), nullable=True))
    op.add_column('material_items', sa.Column('weighbridge_scale_id', sa.String(length=100), nullable=True))
    op.add_column('material_items', sa.Column('weighbridge_timestamp', sa.DateTime(timezone=True), nullable=True))
    op.add_column('material_items', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    columns = [
        'dimension_length_m',
        'dimension_width_m',
        'dimension_height_m',
        'surface_area_m2',
        'min_volume_m3',
        'max_volume_m3',
        'min_weight_tonnes',
        'max_weight_tonnes',
        'uncertainty_percentage',
        'assumed_density_t_per_m3',
        'reference_measurement_notes',
        'damage_severity_pct',
        'damage_type',
        'requires_specialist_abatement',
        'hazard_inspection_warning',
        'recommended_recovery_route',
        'recoverability_percentage',
        'verified_weight_tonnes',
        'verified_volume_m3',
        'weighbridge_ticket_number',
        'weighbridge_scale_id',
        'weighbridge_timestamp',
        'verified_at',
    ]
    for col in columns:
        op.drop_column('material_items', col)

