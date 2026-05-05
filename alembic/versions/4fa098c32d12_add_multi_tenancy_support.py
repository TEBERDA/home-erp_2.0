"""Add multi-tenancy support

Revision ID: 4fa098c32d12
Revises: 38ddffe6f04e
Create Date: 2026-05-04 23:02:15.456239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4fa098c32d12'
down_revision: Union[str, Sequence[str], None] = '38ddffe6f04e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create households table
    op.create_table('households',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('invite_code', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_households_id'), 'households', ['id'], unique=False)
    op.create_index(op.f('ix_households_invite_code'), 'households', ['invite_code'], unique=True)
    
    # 2. Insert Default Household
    op.execute("INSERT INTO households (id, name, invite_code) VALUES (1, 'Default Household', 'default-invite-code')")
    # Sync sequence after manual ID insert
    op.execute("SELECT setval('households_id_seq', (SELECT MAX(id) FROM households))")

    # 3. Create users table
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=True),
    sa.Column('household_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['household_id'], ['households.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 4. Add household_id to all tables with server_default=1
    tables_to_update = [
        'batteries', 'chore_logs', 'chores', 'equipment', 'equipment_documents',
        'locations', 'maintenance_tasks', 'products', 'recipe_ingredients',
        'recipes', 'shopping_list_items', 'stock_entries', 'stores', 'unit_conversions'
    ]
    
    for table in tables_to_update:
        op.add_column(table, sa.Column('household_id', sa.Integer(), nullable=False, server_default='1'))
        op.create_index(op.f(f'ix_{table}_household_id'), table, ['household_id'], unique=False)
        op.create_foreign_key(None, table, 'households', ['household_id'], ['id'])
        # Remove server default after setting it
        op.alter_column(table, 'household_id', server_default=None)

    # 5. Handle special index changes (uniqueness)
    op.drop_index('ix_locations_name', table_name='locations')
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    
    op.drop_index('ix_products_barcode', table_name='products')
    op.create_index(op.f('ix_products_barcode'), 'products', ['barcode'], unique=False)
    
    op.drop_index('ix_stores_name', table_name='stores')
    op.create_index(op.f('ix_stores_name'), 'stores', ['name'], unique=False)
    
    op.add_column('units', sa.Column('household_id', sa.Integer(), nullable=True))
    op.drop_index('ix_units_name', table_name='units')
    op.create_index(op.f('ix_units_name'), 'units', ['name'], unique=False)
    op.create_foreign_key(None, 'units', 'households', ['household_id'], ['id'])


def downgrade() -> None:
    # Reverse special index changes
    op.drop_constraint(None, 'units', type_='foreignkey')
    op.drop_index(op.f('ix_units_name'), table_name='units')
    op.create_index('ix_units_name', 'units', ['name'], unique=True)
    op.drop_column('units', 'household_id')

    tables_to_update = [
        'batteries', 'chore_logs', 'chores', 'equipment', 'equipment_documents',
        'locations', 'maintenance_tasks', 'products', 'recipe_ingredients',
        'recipes', 'shopping_list_items', 'stock_entries', 'stores', 'unit_conversions'
    ]
    
    for table in tables_to_update:
        op.drop_constraint(None, table, type_='foreignkey')
        op.drop_index(op.f(f'ix_{table}_household_id'), table_name=table)
        op.drop_column(table, 'household_id')

    # Restore uniqueness
    op.drop_index('ix_locations_name', table_name='locations')
    op.create_index('ix_locations_name', 'locations', ['name'], unique=True)
    
    op.drop_index('ix_products_barcode', table_name='products')
    op.create_index('ix_products_barcode', 'products', ['barcode'], unique=True)
    
    op.drop_index('ix_stores_name', table_name='stores')
    op.create_index('ix_stores_name', 'stores', ['name'], unique=True)

    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_households_invite_code'), table_name='households')
    op.drop_index(op.f('ix_households_id'), table_name='households')
    op.drop_table('households')
