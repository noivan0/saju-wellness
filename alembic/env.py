from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

config = context.config
fileConfig(config.config_file_name)

# DB URL 환경변수에서 로드
DB_URL = (
    f"postgresql://{os.getenv('DB_USER', 'saju')}:"
    f"{os.getenv('DB_PASSWORD', 'changeme')}@"
    f"{os.getenv('DB_HOST', 'db')}:{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'saju_db')}"
)
config.set_main_option("sqlalchemy.url", DB_URL)

# target_metadata: SQLAlchemy 모델 Base 연결 (자동 마이그레이션 지원)
try:
    from src.api.models.user import Base
    target_metadata = Base.metadata
except ImportError:
    target_metadata = None


def run_migrations_offline():
    context.configure(url=DB_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
