from sqlalchemy import NullPool, exc
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from src.core.config import settings

print(settings.async_database_url)

engine = create_async_engine(
  settings.async_database_url,
  echo=True,
  # poolclass=NullPool,
  connect_args={
    "ssl": True,
    # "sslmode": "require"
  }
)



AsyncSessionLocal = async_sessionmaker(
  autoflush=False,
  autocommit=False,
  bind=engine,
  expire_on_commit=False
)

async def get_db_session():
  async with AsyncSessionLocal() as session:
    try:
      yield session
      await session.commit()
    except exc.SQLAlchemyError as error:
      await session.rollback()
      raise error
    finally:
      await session.close()

Base = declarative_base()