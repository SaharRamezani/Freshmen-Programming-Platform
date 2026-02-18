from typing import Optional
from sqlalchemy.orm import Session
from authentication.models.user import User, UserRoleEnum


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            
        Returns:
            User object if found, None otherwise.
        """
        User_instance = db.query(User).filter(User.id == user_id).first()
        if User_instance:
            return User_instance
        return None

    @staticmethod
    def get_by_google_sub(db: Session, google_sub: str) -> Optional[User]:
        """
        Retrieve a user by their Google subject identifier.
        
        Args:
            db: Database session.
            google_sub: Google's unique user identifier.
            
        Returns:
            User object if found, None otherwise.
        """
        User_instance = db.query(User).filter(User.google_sub == google_sub).first()
        if User_instance:
            return User_instance
        return None

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            db: Database session.
            email: User's email address.
            
        Returns:
            User object if found, None otherwise.
        """
        User_instance = db.query(User).filter(User.email == email).first()
        if User_instance:
            return User_instance
        return None
    

    @staticmethod
    def create(db: Session, user_data: dict) -> User:
        """
        Create a new user in the database.
        
        Args:
            db: Database session.
            user_data: Dictionary containing user information:
                - google_sub: Google unique identifier
                - email: User email
                - first_name: User first name
                - last_name: User last name
                - profile_url: (optional) Profile picture URL
                - role: (optional) User role, defaults to 'student'
                
        Returns:
            Created User object.
        """
        if not user_data.get('google_sub') or not user_data.get('email') or not user_data.get('first_name') or not user_data.get('last_name'):
            raise ValueError("Missing required user fields")
        if db.query(User).filter(User.email == user_data['email']).first():
            raise ValueError("Email already in use")
        new_user = User(
            google_sub=user_data['google_sub'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            profile_url=user_data.get('profile_url'),
            role=user_data.get('role', 'student')
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_role(db: Session, user_id: int, new_role: UserRoleEnum) -> Optional[User]:
        """
        Update a user's role (e.g., promote student to teacher).
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            new_role: The new role to assign.
            
        Returns:
            Updated User object if found, None otherwise.
        """
        User_instance = db.query(User).filter(User.id == user_id).first()
        if User_instance:
            User_instance.role = new_role
            db.commit()
            db.refresh(User_instance)
            return User_instance
        return None

    @staticmethod
    def update_score(db: Session, user_id: int, score_delta: int) -> Optional[User]:
        """
        Update a user's score (add or subtract points).
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            score_delta: Points to add (positive) or subtract (negative).
            
        Returns:
            Updated User object if found, None otherwise.
        """
        User_instance = db.query(User).filter(User.id == user_id).first()
        if User_instance:
            new_score = User_instance.score + score_delta
            if new_score < 0:
                new_score = 0
            elif new_score > 2000000:
                new_score = 2000000
            User_instance.score = new_score
            db.commit()
            db.refresh(User_instance)
            return User_instance
        return None
    

    @staticmethod
    def update_profile(db: Session, user_id: int, profile_data: dict) -> Optional[User]:
        """
        Update user profile information.
        
        Args:
            db: Database session.
            user_id: User's unique identifier.
            profile_data: Dictionary containing profile fields to update:
                - email: (optional)
                - first_name: (optional)
                - last_name: (optional)
                - profile_url: (optional)
                
        Returns:
            Updated User object if found, None otherwise.
        """
        User_instance = db.query(User).filter(User.id == user_id).first()
        if User_instance:
            if 'email' in profile_data:
                User_instance.email = profile_data['email']
            if 'first_name' in profile_data:
                User_instance.first_name = profile_data['first_name']
            if 'last_name' in profile_data:
                User_instance.last_name = profile_data['last_name']
            if 'profile_url' in profile_data:
                User_instance.profile_url = profile_data['profile_url']
            if 'role' in profile_data:
                User_instance.role = profile_data['role']
            db.commit()
            db.refresh(User_instance)
            return User_instance
        return None

    @staticmethod
    def get_all_by_role(db: Session, role: UserRoleEnum) -> list[User]:
        """
        Retrieve all users with a specific role.
        
        Args:
            db: Database session.
            role: The role to filter by.
            
        Returns:
            List of User objects with the specified role.
        """
        return db.query(User).filter(User.role == role).all()
        
