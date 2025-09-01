import jwt, logging
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.users.models import User
from src.users.schema import UserCreate
from src.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
  return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
  return pwd_context.hash(password)

async def create_user(db: AsyncSession, user: UserCreate):
  hashed_password = get_password_hash(user.password)
  db_user = User(email=user.email, password=hashed_password)
  db.add(db_user)
  await db.commit()
  await db.refresh(db_user)
  return db_user

async def get_user_by_email(db: AsyncSession, email: str):
  result = await db.execute(select(User).where(User.email == email))
  return result.scalar_one_or_none()

async def get_current_user(db: AsyncSession, token: str):
  """Get current user from JWT token"""
  try:
    decoded_token = decode_jwt(token)
    if not decoded_token:
      return None
    
    email = decoded_token.get("sub")
    if not email:
      return None
      
    user = await get_user_by_email(db, email)
    return user
  except Exception as e:
    logger.error(f"Failed to get current user: {e}")
    return None

async def authenticate_user(db: AsyncSession, email: str, password: str):
  user_in_db = await get_user_by_email(db, email)
  if not user_in_db:
    return False
  if not verify_password(password, user_in_db.password):
    return False
  return user_in_db

def create_access_token(data:dict, expires_delta: timedelta | None = None):
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.HASH_ALGORITHM)
  return encoded_jwt

def decode_jwt(token: str):
  try:
    decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.HASH_ALGORITHM])
    exp_timestamp = decoded_token.get("exp")
    if exp_timestamp:
      exp_datetime = datetime.fromtimestamp(exp_timestamp, timezone.utc)
      if datetime.now(timezone.utc) >= exp_datetime:
        raise jwt.ExpiredSignatureError
      return decoded_token
  except jwt.ExpiredSignatureError:
    logger.error("Token has expired")
    return None
  except jwt.InvalidTokenError:
    logger.error("Invalid Token")
    return None
  except Exception as e:
    logger.error(f"Failed to decode JWT: {e}")
    return None
  

class JWTBearer(HTTPBearer):
  def __init__(self, auto_error: bool = True):
    super(JWTBearer, self).__init__(auto_error=auto_error)

  async def __call__(self, request: Request):
    credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
    if credentials:
      if not credentials.scheme == "Bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
      if not self.verify_jwt(credentials.credentials):
        raise HTTPException(status_code=403, detail="Invalid token or expired token.")
      return credentials.credentials
    else:
      raise HTTPException(status_code=403, detail="Invalid authorization code.")

  def verify_jwt(self, token: str) -> bool:
    try:
      decoded_token = decode_jwt(token)
      if not decoded_token:
        return False
      return True
    except Exception as e:
      logger.error(f"Failed to verify JWT: {e}")
      return False
