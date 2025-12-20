"""Create user and user_hotel relationship with roles

Revision ID: a9924596f2fc
Revises: 5d53d85191e5
Create Date: 2025-12-18 18:07:31.685195

"""
from typing import Sequence, Union
from sqlalchemy.dialects.postgresql import ENUM

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9924596f2fc'
down_revision: Union[str, Sequence[str], None] = '5d53d85191e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    system_role_enum = ENUM(
        'user', 'admin', 'support',
        name='system_role',
        create_type=False,
    )
    user_role_enum = ENUM(
        'owner', 'manager', 'viewer',
        name='user_role',
        create_type=False,
    )

    bind = op.get_bind()

    system_role_enum.create(bind, checkfirst=True)
    user_role_enum.create(bind, checkfirst=True)

    op.create_table('user',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('surname', sa.String(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('hashed_password', sa.String(), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=False),
                    sa.Column('system_role', system_role_enum, server_default='user', nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                              nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email')
                    )
    op.create_table('user_hotel',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('hotel_id', sa.Integer(), nullable=False),
                    sa.Column('role', user_role_enum, server_default='viewer', nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'),
                              nullable=False),
                    sa.ForeignKeyConstraint(['hotel_id'], ['hotel.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('user_id', 'hotel_id', name='uq_user_hotel')
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_hotel')
    op.drop_table('user')

    bind = op.get_bind()

    ENUM(name='user_role').drop(bind, checkfirst=True)
    ENUM(name='system_role').drop(bind, checkfirst=True)
