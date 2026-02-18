from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from authentication.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    def get_by_id(db: Session, token_id: int) -> Optional[RefreshToken]:
        """
        Retrieve a refresh token by its ID.
        
        Args:
            db: Database session.
            token_id: Refresh token's unique identifier.
            
        Returns:
            RefreshToken object if found, None otherwise.
        """
        token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
        if token and token.is_valid():
            return token
        return None

    @staticmethod
    def get_by_token_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
        """
        Retrieve a refresh token by its hash.
        
        Args:
            db: Database session.
            token_hash: The hashed refresh token.
            
        Returns:
            RefreshToken object if found, None otherwise.
        """
        token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if token and token.is_valid():
            return token
        return None

    @staticmethod
    def create(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        """
        Create a new refresh token in the database.
        
        Args:
            db: Database session.
            user_id: Associated user ID.
            token_hash: Hashed refresh token (never store raw token).
            expires_at: Token expiration timestamp.
            
        Returns:
            Created RefreshToken object.
        """
        new_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        return new_token

    @staticmethod
    def revoke(db: Session, token_id: int) -> Optional[RefreshToken]:
        """
        Revoke a refresh token (mark as revoked for immediate logout).
        
        Args:
            db: Database session.
            token_id: Refresh token's unique identifier.
            
        Returns:
            Updated RefreshToken object if found, None otherwise.
        """
        token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
        if token:
            token.revoked_at = datetime.utcnow()
            db.commit()
            db.refresh(token)
            return token
        return None

    @staticmethod
    def revoke_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
        """
        Revoke a refresh token by its hash.
        
        Args:
            db: Database session.
            token_hash: The hashed refresh token.
            
        Returns:
            Updated RefreshToken object if found, None otherwise.
        """
        token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if token:
            token.revoked_at = datetime.utcnow()
            db.commit()
            db.refresh(token)
            return token
        return None

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: int) -> int:
        """
        Revoke all refresh tokens for a specific user (logout all sessions).
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            
        Returns:
            Number of tokens revoked.
        """
        count = 0

        tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
        for token in tokens:
            if token.revoked_at is None: #token.is_valid() could be used as well
                token.revoked_at = datetime.utcnow()
                count += 1
        db.commit()
        
        return count

    @staticmethod
    def is_valid(db: Session, token_hash: str) -> bool:
        """
        Check if a refresh token is valid (not revoked and not expired).
        
        Args:
            db: Database session.
            token_hash: The hashed refresh token.
            
        Returns:
            True if token is valid, False otherwise.
        """
        token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if token:
            return token.revoked_at is None and token.expires_at > datetime.utcnow()
        return False
    

    @staticmethod
    def get_valid_for_user(db: Session, user_id: int) -> list[RefreshToken]:
        """
        Retrieve all valid (non-revoked, non-expired) tokens for a user.
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            
        Returns:
            List of valid RefreshToken objects.
        """
        Alltokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
        valid_tokens = []
        for token in Alltokens:
            if token.is_valid():
                valid_tokens.append(token)
        return valid_tokens

    @staticmethod
    def cleanup_expired(db: Session) -> int:
        """
        Remove or mark as expired all refresh tokens that have expired.
        
        This can be called periodically to clean up the database.
        
        Args:
            db: Database session.
            
        Returns:
            Number of expired tokens cleaned up.
        """
        expired_tokens = db.query(RefreshToken).filter(RefreshToken.expires_at <= datetime.utcnow()).all()
        count = len(expired_tokens)
        for token in expired_tokens:
            db.delete(token)
        db.commit()
        return count

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> list[RefreshToken]:
        """
        Retrieve all refresh tokens (revoked and active) for a user.
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            
        Returns:
            List of all RefreshToken objects for the user.
        """
        return db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
