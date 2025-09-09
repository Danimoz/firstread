# Desc: Load all models to be used in the application, so Alembic can pick them for migrations
from src.core.database import Base
from src.users.models import User
from src.contract.models import Contract
