"""kvs_refactor_and_identity_schema

Revision ID: 1eb28e1c0aea
Revises: 4f5c885debb4
Create Date: 2026-05-20 14:55:19.856665

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1eb28e1c0aea'
down_revision: Union[str, Sequence[str], None] = '4f5c885debb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # --- PART 1: SYSTEM SETTINGS REFACTOR ---
    # 1. Inspect existing columns
    sys_cols_info = inspector.get_columns('system_settings')
    old_sys_cols = [col['name'] for col in sys_cols_info if col['name'] not in ('id', 'key', 'value')]
    
    row_data = None
    if old_sys_cols:
        cols_str = ", ".join(f'"{col}"' for col in old_sys_cols)
        try:
            res = connection.execute(sa.text(f"SELECT {cols_str} FROM system_settings")).fetchone()
            if res:
                row_data = dict(zip(old_sys_cols, res))
        except Exception as e:
            print(f"Error reading system settings: {e}")

    kvs_data = []
    if row_data:
        for k, v in row_data.items():
            if v is not None:
                if isinstance(v, bool):
                    v_str = "true" if v else "false"
                else:
                    v_str = str(v)
                kvs_data.append({"key": k, "value": v_str})
                
    # Drop all indices on system_settings key first (if any)
    try:
        op.drop_index('ix_system_settings_key', table_name='system_settings')
    except Exception:
        pass
        
    with op.batch_alter_table('system_settings') as batch_op:
        # Add key/value columns
        batch_op.add_column(sa.Column('key', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('value', sa.String(), nullable=True))
        
    # Clear old settings
    connection.execute(sa.text("DELETE FROM system_settings"))
    
    # Insert new KVS rows
    if kvs_data:
        for item in kvs_data:
            connection.execute(
                sa.text("INSERT INTO system_settings (key, value) VALUES (:key, :value)"),
                {"key": item["key"], "value": item["value"]}
            )
            
    with op.batch_alter_table('system_settings') as batch_op:
        for col_name in old_sys_cols:
            batch_op.drop_column(col_name)
        batch_op.alter_column('key', nullable=False, existing_type=sa.String())
        batch_op.alter_column('value', nullable=False, existing_type=sa.String())
        batch_op.create_unique_constraint('uq_system_settings_key', ['key'])
        batch_op.create_index('ix_system_settings_key', ['key'], unique=True)
        
    # --- PART 2: USER SCHEMA UPDATE ---
    user_cols_info = inspector.get_columns('users')
    old_user_cols = [col['name'] for col in user_cols_info]
    
    users_data = []
    # Identify which of the old columns are present
    select_cols = [col for col in ['id', 'email', 'hashed_password', 'role'] if col in old_user_cols]
    if 'email' in old_user_cols and 'hashed_password' in old_user_cols:
        cols_str = ", ".join(f'"{col}"' for col in select_cols)
        try:
            res = connection.execute(sa.text(f"SELECT {cols_str} FROM users")).fetchall()
            for row in res:
                # Map row columns to dict
                row_dict = dict(zip(select_cols, row))
                role = row_dict.get('role', 'user')
                perms = ["system:write", "triage:approve"] if role == 'admin' else []
                users_data.append({
                    "id": row_dict["id"],
                    "email": row_dict["email"],
                    "hashed_password": row_dict["hashed_password"],
                    "is_local_disabled": False,
                    "permissions": perms,
                    "allowed_ips": []
                })
        except Exception as e:
            print(f"Error migrating users: {e}")
            
    # Drop indices
    try:
        op.drop_index('ix_users_username', table_name='users')
    except Exception:
        pass
    try:
        op.drop_index('ix_users_email', table_name='users')
    except Exception:
        pass
        
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('is_local_disabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('permissions', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('allowed_ips', sa.JSON(), nullable=True))
        
    # Clear users
    connection.execute(sa.text("DELETE FROM users"))
    
    # Insert new users
    for u in users_data:
        connection.execute(
            sa.text("""
                INSERT INTO users (id, email, hashed_password, is_local_disabled, permissions, allowed_ips)
                VALUES (:id, :email, :hashed_password, :is_local_disabled, :permissions, :allowed_ips)
            """),
            {
                "id": u["id"],
                "email": u["email"],
                "hashed_password": u["hashed_password"],
                "is_local_disabled": u["is_local_disabled"],
                "permissions": json.dumps(u["permissions"]),
                "allowed_ips": json.dumps(u["allowed_ips"])
            }
        )
        
    with op.batch_alter_table('users') as batch_op:
        for col_name in old_user_cols:
            if col_name not in ('id', 'email', 'hashed_password'):
                batch_op.drop_column(col_name)
        batch_op.alter_column('is_local_disabled', nullable=False, existing_type=sa.Boolean(), server_default='0')
        batch_op.alter_column('permissions', nullable=False, existing_type=sa.JSON())
        batch_op.alter_column('allowed_ips', nullable=False, existing_type=sa.JSON())
        batch_op.create_index('ix_users_email', ['email'], unique=True)
        
    # --- PART 3: API KEY TABLE ---
    # Create api_keys table if not exists
    if 'api_keys' not in inspector.get_table_names():
        op.create_table(
            'api_keys',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('key_prefix', sa.String(), nullable=False),
            sa.Column('hashed_key', sa.String(), nullable=False),
            sa.Column('permissions', sa.JSON(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    # 1. Drop api_keys
    op.drop_table('api_keys')
    
    # 2. Revert User columns
    res = connection.execute(sa.text("SELECT id, email, hashed_password, permissions FROM users")).fetchall()
    users_data = []
    for row in res:
        try:
            perms = json.loads(row[3]) if isinstance(row[3], str) else row[3]
        except Exception:
            perms = []
        role = 'admin' if 'system:write' in perms else 'user'
        email = row[1]
        username = email.split('@')[0]
        users_data.append({
            "id": row[0],
            "username": username,
            "email": email,
            "hashed_password": row[2],
            "role": role,
            "is_pro": 'system:write' in perms
        })
        
    try:
        op.drop_index('ix_users_email', table_name='users')
    except Exception:
        pass
        
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('role', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('license_key', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('is_pro', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('paddle_customer_id', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('paddle_subscription_id', sa.String(), nullable=True))
        
    connection.execute(sa.text("DELETE FROM users"))
    for u in users_data:
        connection.execute(
            sa.text("""
                INSERT INTO users (id, username, email, hashed_password, role, is_pro)
                VALUES (:id, :username, :email, :hashed_password, :role, :is_pro)
            """),
            {
                "id": u["id"],
                "username": u["username"],
                "email": u["email"],
                "hashed_password": u["hashed_password"],
                "role": u["role"],
                "is_pro": 1 if u["is_pro"] else 0
            }
        )
        
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('is_local_disabled')
        batch_op.drop_column('permissions')
        batch_op.drop_column('allowed_ips')
        batch_op.alter_column('username', nullable=False, existing_type=sa.String())
        batch_op.alter_column('role', nullable=False, existing_type=sa.String(), server_default='user')
        batch_op.alter_column('is_pro', nullable=False, existing_type=sa.Boolean(), server_default='0')
        batch_op.create_index('ix_users_username', ['username'], unique=True)
        batch_op.create_index('ix_users_email', ['email'], unique=True)
        
    # 3. Revert System Settings
    res_sys = connection.execute(sa.text("SELECT key, value FROM system_settings")).fetchall()
    kvs = {row[0]: row[1] for row in res_sys}
    
    with op.batch_alter_table('system_settings') as batch_op:
        batch_op.add_column(sa.Column('discord_webhook_url', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('ntfy_topic_url', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('consensus_threshold', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('cloud_credits', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('maintenance_start', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('maintenance_end', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('monitored_directory', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('triage_directory', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('scan_intensity', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('is_setup_complete', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('max_workers', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('auto_restore', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('auto_restore_cloud', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('auto_restore_ai', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('ai_use_kintsugi_cloud', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('retention_days', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('snapshot_mount_path', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('enable_3rd_party_plugins', sa.Boolean(), nullable=True))
        
    connection.execute(sa.text("DELETE FROM system_settings"))
    if kvs:
        def to_bool(val):
            return val.lower() == 'true' if val else False
        def to_int(val):
            return int(val) if val else 0
        connection.execute(
            sa.text("""
                INSERT INTO system_settings (
                    id, discord_webhook_url, ntfy_topic_url, consensus_threshold, cloud_credits,
                    maintenance_start, maintenance_end, monitored_directory, triage_directory,
                    scan_intensity, is_setup_complete, max_workers, auto_restore, auto_restore_cloud,
                    auto_restore_ai, ai_use_kintsugi_cloud, retention_days,
                    snapshot_mount_path, enable_3rd_party_plugins
                ) VALUES (
                    1, :discord_webhook_url, :ntfy_topic_url, :consensus_threshold, :cloud_credits,
                    :maintenance_start, :maintenance_end, :monitored_directory, :triage_directory,
                    :scan_intensity, :is_setup_complete, :max_workers, :auto_restore, :auto_restore_cloud,
                    :auto_restore_ai, :ai_use_kintsugi_cloud, :retention_days,
                    :snapshot_mount_path, :enable_3rd_party_plugins
                )
            """),
            {
                "discord_webhook_url": kvs.get("discord_webhook_url"),
                "ntfy_topic_url": kvs.get("ntfy_topic_url"),
                "consensus_threshold": to_int(kvs.get("consensus_threshold")),
                "cloud_credits": to_int(kvs.get("cloud_credits")),
                "maintenance_start": kvs.get("maintenance_start", "01:00"),
                "maintenance_end": kvs.get("maintenance_end", "05:00"),
                "monitored_directory": kvs.get("monitored_directory", "/media"),
                "triage_directory": kvs.get("triage_directory", "/app/data/triage"),
                "scan_intensity": kvs.get("scan_intensity", "eco"),
                "is_setup_complete": to_bool(kvs.get("is_setup_complete")),
                "max_workers": to_int(kvs.get("max_workers")),
                "auto_restore": to_bool(kvs.get("auto_restore")),
                "auto_restore_cloud": to_bool(kvs.get("auto_restore_cloud")),
                "auto_restore_ai": to_bool(kvs.get("auto_restore_ai")),
                "ai_use_kintsugi_cloud": to_bool(kvs.get("ai_use_kintsugi_cloud")),
                "retention_days": to_int(kvs.get("retention_days")),
                "snapshot_mount_path": kvs.get("snapshot_mount_path", "/snapshots"),
                "enable_3rd_party_plugins": to_bool(kvs.get("enable_3rd_party_plugins")),
            }
        )
        
    with op.batch_alter_table('system_settings') as batch_op:
        try:
            batch_op.drop_index('ix_system_settings_key')
        except Exception:
            pass
        batch_op.drop_column('key')
        batch_op.drop_column('value')
