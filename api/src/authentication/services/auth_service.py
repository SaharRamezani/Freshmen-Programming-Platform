import os
import hashlib
import secrets
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict
import jwt
import httpx
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from authentication.models.user import User, UserRoleEnum
from authentication.models.refresh_token import RefreshToken
from authentication.repositories.user_repository import UserRepository
from authentication.repositories.refresh_token_repository import RefreshTokenRepository
from authentication.schema.user_schema import UserCreateFromGoogle
from authentication.schema.token_schema import TokenResponse, AccessTokenPayload
from authentication.exceptions import (
    InvalidTokenError,
    InvalidStateError,
    TokenExpiredError,
    TokenRevokedError,
    UserNotFoundError,
    OAuthProviderError,
    DatabaseError,
    ConfigurationError
)
from models import Student

logger = logging.getLogger(__name__)

from authentication.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_TIMEDELTA,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    TOKEN_HASH_ALGORITHM,
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI,
    GOOGLE_OAUTH_DISCOVERY_URL,
)


class AuthService:
    @staticmethod
    async def authenticate_with_google(user_info: dict, db: Session) -> Tuple[User, str, str]:
        google_sub = user_info.get("sub")
        email = user_info.get("email")
        fullname = user_info.get("name", "")
        picture = user_info.get("picture", "")
        
        if not google_sub or not email:
            raise InvalidTokenError("Missing required user information from Google")
            
        name_parts = fullname.split(" ", 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = UserRepository.get_by_google_sub(db, google_sub)
        if not user:
            user_data = UserCreateFromGoogle(
                google_sub=google_sub,
                email=email,
                first_name=first_name,
                last_name=last_name,
                profile_url=picture,
                role="student" 
            )
            user = UserRepository.create(db, user_data.dict())
            
            # Also create a Student record with matching ID for legacy API compatibility
            # Also create a Student record with matching ID for legacy API compatibility
            if user.role == UserRoleEnum.student:
                # Check if student record already exists (e.g. created by DB trigger)
                existing_student = db.query(Student).filter(Student.student_id == user.id).first()
                
                if not existing_student:
                    student = Student(
                        student_id=user.id,
                        email=user.email,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        score=0,
                        user_id=user.id
                    )
                    db.add(student)
                    db.commit()
                    logger.info(f"Created Student record for user {user.id}")
                else:
                    logger.info(f"Student record for user {user.id} already exists (likely via DB trigger)")

        access_token = AuthService.issue_access_token(user)
        refresh_token, _ = AuthService.issue_refresh_token(user.id, db)

        return user, access_token, refresh_token


    @staticmethod
    def refresh_access_token(refresh_token: str, db: Session) -> Tuple[str, str]:
        """
        Refresh access token using a valid refresh token.
        Implements refresh token rotation: revokes old token and issues new one.
        
        Args:
            refresh_token: The refresh token to use
            db: Database session
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            Exception: If refresh token is invalid, expired, or already revoked
        """
        hashed_token = AuthService.hash_token(refresh_token)

        try:
            token_record = RefreshTokenRepository.get_by_token_hash(db, hashed_token)
            if not token_record:
                logger.warning("Refresh token not found")
                raise InvalidTokenError("Invalid refresh token")
            
            if not token_record.is_valid():
                if token_record.revoked_at:
                    logger.warning("Refresh token has been revoked")
                    raise TokenRevokedError("Refresh token has been revoked")
                else:
                    logger.warning("Refresh token has expired")
                    raise TokenExpiredError("Refresh token has expired")

            user = UserRepository.get_by_id(db, token_record.user_id)
            if not user:
                logger.error(f"User not found for refresh token: {token_record.user_id}")
                raise UserNotFoundError("User not found")
            
            token_record.revoked_at = datetime.utcnow()
            db.commit()
        except (InvalidTokenError, TokenRevokedError, TokenExpiredError, UserNotFoundError):
            raise 
        except SQLAlchemyError as e:
            logger.error("Database error during token refresh", exc_info=True)
            db.rollback()
            raise DatabaseError("Database error during token refresh") from e
        
        new_access_token = AuthService.issue_access_token(user)
        
        new_refresh_token, _ = AuthService.issue_refresh_token(user.id, db)

        return new_access_token, new_refresh_token

    ## SUPER IMPORTANT FUNCTION THAT MUST BE COLED BEFORE VERY RESCTRICED API CALL BECAUSE IT VERIFY IF YOU HAVE THE RIGHT TO MAKE THE API CALL
    @staticmethod
    def validate_access_token(access_token: str) -> dict:
        """
        Validate access token JWT.
        Relies on PyJWT's built-in expiration verification (verify_exp=True by default).
        
        Args:
            access_token: JWT access token string
            
        Returns:
            Decoded token payload
            
        Raises:
            Exception: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                access_token, 
                JWT_SECRET_KEY, 
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True, "verify_signature": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("Access token has expired")
            raise TokenExpiredError("Access token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            raise InvalidTokenError(f"Invalid access token: {str(e)}")


    @staticmethod
    def revoke_refresh_token(refresh_token_raw: str, db: Session) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token_raw: The raw refresh token to revoke
            db: Database session
            
        Returns:
            True if token was revoked, False if token not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            hashed_token = AuthService.hash_token(refresh_token_raw)
            token_record = RefreshTokenRepository.get_by_token_hash(db, hashed_token)
            if not token_record:
                return False
            token_record.revoked_at = datetime.utcnow()
            db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error("Database error revoking refresh token", exc_info=True)
            db.rollback()
            raise DatabaseError("Database error revoking refresh token") from e


    @staticmethod
    def revoke_all_user_tokens(user_id: int, db: Session) -> int:
        revoked_count = RefreshTokenRepository.revoke_all_for_user(db, user_id)
        return revoked_count


    @staticmethod
    def hash_token(token: str) -> str:
        hasher = hashlib.new(TOKEN_HASH_ALGORITHM)
        hasher.update(token.encode('utf-8'))
        return hasher.hexdigest()
    
    @staticmethod
    def issue_access_token(user: User) -> str:
        """
        Generates a short-lived JWT access token.
        
        Args:
            user: User object to generate token for
            
        Returns:
            JWT access token string
        """
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt


    @staticmethod
    def issue_refresh_token(user_id: int, db: Session) -> Tuple[str, RefreshToken]:
        """
        Generates a long-lived refresh token and stores it in the database.
        
        Args:
            user_id: ID of the user
            db: Database session
            
        Returns:
            Tuple of (raw_token_string, RefreshToken_object)
        """
        # Generate raw token
        raw_token = AuthService.generate_random_token()
        hashed_token = AuthService.hash_token(raw_token)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + REFRESH_TOKEN_EXPIRE_TIMEDELTA
        
        # Store in DB
        try:
            refresh_token_obj = RefreshTokenRepository.create(
                db=db,
                user_id=user_id,
                token_hash=hashed_token,
                expires_at=expires_at
            )
            return raw_token, refresh_token_obj
        except SQLAlchemyError as e:
            logger.error("Database error creating refresh token", exc_info=True)
            raise DatabaseError("Failed to create refresh token") from e
    @staticmethod
    def generate_random_token(length: int = 64) -> str:
        return secrets.token_urlsafe(length)


    @staticmethod
    def check_role_change(user_id: int, old_role: str, db: Session) -> bool:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise Exception("User not found")
        return user.role != old_role
