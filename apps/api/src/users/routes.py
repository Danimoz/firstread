from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db_session as get_db
from src.core.config import settings
from .utils import authenticate_user, create_access_token, create_user, create_user, get_user_by_email, get_current_user, JWTBearer
from .schema import UserCreate, Token, UserRegistrationResponse, SignoutResponse


router = APIRouter(
  prefix="/users",
  tags=["users"]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
  existing_user = await get_user_by_email(db, user.email)
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Email already registered"
    )
  
  # Create the user
  new_user = await create_user(db, user)
  
  # Generate access token for the new user
  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
    data={"sub": new_user.email}, 
    expires_delta=access_token_expires
  )
  
  return UserRegistrationResponse(
    user=new_user,
    access_token=access_token,
    token_type="bearer"
  )


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def login(user: UserCreate, db: AsyncSession = Depends(get_db)):
  existing_user = await authenticate_user(db, user.email, user.password)
  if not existing_user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid credentials",
      headers={"WWW-Authenticate": "Bearer"},
    )
  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(data={"sub": existing_user.email}, expires_delta=access_token_expires)
  return Token(access_token=access_token, token_type="bearer")


@router.post("/signout", response_model=SignoutResponse, status_code=status.HTTP_200_OK)
async def signout(token: str = Depends(JWTBearer()), db: AsyncSession = Depends(get_db)):
  """
  Sign out the current user.
  Note: JWT tokens are stateless, so the client should remove the token from storage.
  This endpoint validates the token and provides a confirmation response.
  """
  # Verify the token is valid and get the user
  current_user = await get_current_user(db, token)
  if not current_user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"},
    )
  
  # In a production system with token blacklisting, you would add the token to a blacklist here
  # For now, we just confirm the signout
  return SignoutResponse(message="Successfully signed out")



