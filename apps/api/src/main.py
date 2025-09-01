import logging
from fastapi import FastAPI
from .users import routes as users_routes
from .contract import routes as contract_routes

# Configure logging
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
  title="FirstRead Assessment API",
  description="API for the FirstRead assessment",
  version="1.0.0"
)

app.include_router(users_routes.router)
app.include_router(contract_routes.router)

@app.get("/")
def root():
  logger.info("Root endpoint accessed")
  return {"Hello": "World"}

@app.get("/health")
def health_check():
  logger.info("Health check endpoint accessed")
  return {"status": "healthy"}
