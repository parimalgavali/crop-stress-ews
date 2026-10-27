from alembic import context
from sqlalchemy import create_engine

from cropews.api.db import database_url
from cropews.api.models import Base

connectable = create_engine(context.config.get_main_option("sqlalchemy.url") or database_url())
with connectable.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
