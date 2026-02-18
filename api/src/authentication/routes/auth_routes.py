import logging
import os
from datetime import timedelta
import httpx
from authentication.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from authentication.schema.token_schema import TokenResponse, RefreshTokenRequest, TokenRevocationRequest, TokenValidationResponse
from authentication.schema.user_schema import UserRead
from authentication.services.auth_service import AuthService
from authentication.exceptions import (
    InvalidTokenError,
    InvalidStateError,
    TokenExpiredError,
    TokenRevokedError,
    UserNotFoundError,
    OAuthProviderError,
    DatabaseError,
    AuthenticationError,
    ConfigurationError
)
from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# Initialize Authlib
from authlib.integrations.starlette_client import OAuth
from authentication.config import (
    GOOGLE_OAUTH_CLIENT_ID, 
    GOOGLE_OAUTH_CLIENT_SECRET, 
    GOOGLE_OAUTH_REDIRECT_URI,
    GOOGLE_OAUTH_DISCOVERY_URL
)

oauth = OAuth()

# Register OAuth client only if configuration is available
# This prevents errors during module import if env vars are not set
if GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET and GOOGLE_OAUTH_REDIRECT_URI:
    oauth.register(
        name='google',
        client_id=GOOGLE_OAUTH_CLIENT_ID,
        client_secret=GOOGLE_OAUTH_CLIENT_SECRET,
        server_metadata_url=GOOGLE_OAUTH_DISCOVERY_URL,
        client_kwargs={
            'scope': 'openid email profile',
            'timeout': 10.0  # 10 second timeout for OAuth requests
        }
    )
else:
    logger.warning("Google OAuth client not registered - missing configuration")


@router.get(
    "/initiate",
    status_code=status.HTTP_200_OK,
    summary="Initiate Google OAuth flow",
    description="Redirects user to Google for authentication"
)
async def initiate_oauth(request: Request):
    try:
        if not GOOGLE_OAUTH_CLIENT_ID:
            logger.error("GOOGLE_OAUTH_CLIENT_ID is not set")
            raise ConfigurationError("Google OAuth client ID is not configured")
        if not GOOGLE_OAUTH_CLIENT_SECRET:
            logger.error("GOOGLE_OAUTH_CLIENT_SECRET is not set")
            raise ConfigurationError("Google OAuth client secret is not configured")
        if not GOOGLE_OAUTH_REDIRECT_URI:
            logger.error("GOOGLE_OAUTH_REDIRECT_URI is not set")
            raise ConfigurationError("Google OAuth redirect URI is not configured")
        
        redirect_uri = GOOGLE_OAUTH_REDIRECT_URI
        
        try:
            google_client = oauth.google
        except AttributeError:
            logger.error("Google OAuth client is not registered")
            raise ConfigurationError("Google OAuth client is not properly configured")
        
        return await google_client.authorize_redirect(request, redirect_uri)
    
    except ConfigurationError as e:
        logger.error(f"Configuration error during OAuth initiation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth configuration error. Please contact the administrator."
        )
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError, httpx.ConnectTimeout) as e:
        logger.error(f"Network error connecting to OAuth provider: {e}", exc_info=True)
        
        # Check if we're in development mode
        is_dev = os.getenv("ENVIRONMENT", "development") == "development"
        
        if is_dev:
            error_detail = (
                "Unable to connect to Google OAuth service. This is common in development environments. "\
                "Please use the 'Dev Login' buttons on the login page instead, or check your network connection."
            )
        else:
            error_detail = "Unable to connect to authentication service. Please check your network connection and try again."
        
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_detail
        )
    except OAuthProviderError as e:
        logger.error(f"OAuth provider error during initiation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Authentication service error. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error during OAuth initiation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth flow. Please try again later."
        )


from fastapi.responses import JSONResponse, RedirectResponse

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:3000")

@router.get(
    "/callback",
    status_code=status.HTTP_200_OK,
    summary="Google OAuth callback",    
    description="Handles Google OAuth callback and issues tokens",
)
async def google_oauth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Exchange the authorization code from Google for user information,
    find or create the user, issue application access/refresh tokens,
    and redirect to frontend.
    """
    try:
        # Authlib handles the exchange of code for token and user info parsing
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
             user_info = await oauth.google.userinfo(token=token)

        # Authenticate with Google user info
        user, access_token, refresh_token = await AuthService.authenticate_with_google(dict(user_info), db)
        
        logger.info(f"User authenticated successfully: {user.email}")
        
        # Prepare redirect to frontend
        # Pass access_token in URL fragment or query param so frontend can read it
        # Fragment is safer as it's not sent to server on reload, but query param is standard for this flow
        redirect_url = f"{SERVER_URL}/?access_token={access_token}"
        response = RedirectResponse(url=redirect_url)

        # Set refresh token in httpOnly cookie
        refresh_token_max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_token_max_age,
            httponly=True,
            secure=is_production,
            samesite="lax",
            path="/auth"
        )
        
        return response

    except OAuthProviderError as e:
        logger.error(f"OAuth provider error: {e}", exc_info=True)
        # Redirect to frontend login with error
        return RedirectResponse(url=f"{SERVER_URL}/?error=oauth_error")
    except DatabaseError as e:
        logger.error(f"Database error during OAuth callback: {e}", exc_info=True)
        return RedirectResponse(url=f"{SERVER_URL}/?error=server_error")
    except AuthenticationError as e:
        logger.warning(f"Authentication error: {e}")
        return RedirectResponse(url=f"{SERVER_URL}/?error=auth_failed")
    except Exception as e:
        logger.error(f"Unexpected error during OAuth callback: {e}", exc_info=True)
        return RedirectResponse(url=f"{SERVER_URL}/?error=unexpected_error")

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",    
    description="Issues a new access token using a valid refresh token from cookie",
)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Refresh the access token using a valid refresh token from httpOnly cookie.
    Implements refresh token rotation.
    """
    # Read refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found in cookie")
    
    try:
        # Refresh token rotation: old token revoked, new token issued
        new_access_token, new_refresh_token = AuthService.refresh_access_token(refresh_token, db)
        
        logger.info("Access token refreshed successfully")
        
        # Set new refresh token in cookie (rotation)
        refresh_token_max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            max_age=refresh_token_max_age,
            httponly=True,
            secure=is_production,
            samesite="lax",
            path="/auth"
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=None,  # Not in body, sent via cookie
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 15 minutes
        )
    except (InvalidTokenError, TokenExpiredError, TokenRevokedError) as e:
        logger.warning(f"Invalid refresh token: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    except UserNotFoundError as e:
        logger.error(f"User not found during token refresh: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except DatabaseError as e:
        logger.error(f"Database error during token refresh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke refresh token (logout)",    
    description="Revokes the refresh token from cookie to log out the user",
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Revoke the refresh token from cookie to log out the user.
    Clears the refresh token cookie.
    """
    # Read refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if refresh_token:
        try:
            revoked = AuthService.revoke_refresh_token(refresh_token, db)
            if revoked:
                logger.info("Refresh token revoked successfully")
            else:
                # Token not found - idempotent success (already logged out or invalid token)
                logger.debug("Token not found during logout (idempotent)")
        except DatabaseError as e:
            logger.error(f"Database error during logout: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
        except Exception as e:
            logger.error(f"Unexpected error during logout: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")
    
    # Clear refresh token cookie regardless of revocation result
    response.delete_cookie(
        key="refresh_token",
        path="/auth",
        samesite="lax"
    )
    
    return {"message": "Successfully logged out"}


from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

# Testing mode flag - when enabled, authentication is bypassed for automated tests
# SECURITY: This should NEVER be enabled in production environments
# NOTE: This flag is evaluated once at module load time. Changes to the environment
# variable after application startup will not take effect until the application restarts.
API_TESTING_MODE = os.getenv("API_TESTING_MODE", "false").lower() == "true"

# Log testing mode status once at module load time to avoid log spam
if API_TESTING_MODE:
    logger.warning("⚠️ API_TESTING_MODE enabled - authentication will be bypassed for all requests")

async def get_current_user(token: Annotated[str | None, Depends(oauth2_scheme)]):
    """
    Dependency to validate access token and return user info.
    In testing mode, returns a mock user to bypass authentication.
    """
    # Testing mode bypass - only for automated tests
    if API_TESTING_MODE:
        return {
            "sub": "dev_teacher_sub_456",  # Mock user ID
            "id": 42,     # Database ID for Dev Teacher (40 initial + 2 dev users)
            "email": "dev.teacher@test.com",
            "role": "teacher"
        }
    
    # Normal authentication flow
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = AuthService.validate_access_token(token)
        return payload
    except (InvalidTokenError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_teacher(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """
    Dependency that ensures the current user is a teacher.
    Raises 403 Forbidden if the user is not a teacher.
    """
    role = current_user.get("role", "")
    if role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can perform this action"
        )
    return current_user


@router.get(
    "/validate",
    response_model=TokenValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate access token",
    description="Validates an access token and returns user information and role"
)
async def validate_token(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> TokenValidationResponse:
    """
    Validate an access token.
    Uses get_current_user dependency which handles token extraction and validation.
    """
    user_id = int(current_user["sub"])
    role = current_user.get("role", "unknown")
    email = current_user.get("email", "")
    
    return TokenValidationResponse(
        is_valid=True,
        user_id=user_id,
        role=role,
        message=f"Token is valid for user {email}"
    )


@router.post(
    "/role-change-check",
    status_code=status.HTTP_200_OK,
    summary="Check if user's role has changed",
    description="Checks if the user's role in the database differs from the role in their current access token"
)
async def check_role_change(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """
    Check if user's role has changed since the access token was issued.
    """
    user_id = int(current_user["sub"])
    token_role = current_user.get("role", "unknown")
    
    try:
        # Check if role has changed in database
        role_changed = AuthService.check_role_change(user_id, token_role, db)
        
        if role_changed:
            from authentication.repositories.user_repository import UserRepository
            user = UserRepository.get_by_id(db, user_id)
            current_role = user.role.value if user else token_role
            
            logger.info(f"Role change detected for user {user_id}: {token_role} -> {current_role}")
            return {
                "role_changed": True,
                "current_role": current_role,
                "token_role": token_role,
                "message": f"Role has changed from {token_role} to {current_role}. Please refresh your token."
            }
        else:
            return {
                "role_changed": False,
                "current_role": token_role,
                "token_role": token_role,
                "message": "Role has not changed"
            }
    except Exception as e:
        logger.error(f"Unexpected error during role change check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/dev-login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Dev mode login (TESTING ONLY)",
    description="Login as a test user without OAuth. Only works in development mode."
)
async def dev_mode_login(
    role: str,
    response: Response,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Dev mode login endpoint for testing.
    Allows quick login as student or teacher without OAuth flow.
    
    SECURITY: This endpoint should only be enabled in development!
    """
    # Check if we're in development mode
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    if not is_dev:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev mode login is only available in development environment"
        )
    
    # Validate role
    if role not in ["student", "student2", "teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'student', 'student2', 'teacher', or 'admin'"
        )
    
    try:
        # Get the dev user from database
        from authentication.repositories.user_repository import UserRepository
        
        email = f"dev.{role}@test.com"
        user = UserRepository.get_by_email(db, email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dev {role} user not found in database"
            )
        
        # Issue tokens
        access_token = AuthService.issue_access_token(user)
        refresh_token, _ = AuthService.issue_refresh_token(user.id, db)
        
        logger.info(f"Dev mode login: {role} ({user.email})")
        
        # Set refresh token in cookie
        refresh_token_max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_token_max_age,
            httponly=True,
            secure=False,  # Dev mode
            samesite="lax",
            path="/auth"
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=None,  # Sent via cookie
            token_type="Bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during dev mode login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dev mode login failed"
        )

