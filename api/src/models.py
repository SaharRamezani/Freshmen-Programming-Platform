"""
This file defines Python classes (ORM) that map to database tables,
and Pydantic models for API request/response schemas.
"""

import enum
from datetime import datetime as dt
from typing import List

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, Enum, DateTime, Numeric
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy import UniqueConstraint



from database import Base

SCHEMA_NAME = "capstone_app"

class TestScope(enum.Enum):
    private = "private"
    public = "public"

class Teacher(Base):
    __tablename__ = "teacher"
    __table_args__ = {'schema': SCHEMA_NAME}

    teacher_id = Column(Integer, primary_key=True)
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    email = Column(String(150), unique=True, nullable=False) 
    user_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.users.id"), nullable=False) 

    match_settings = relationship("MatchSetting", back_populates="creator")
    matches = relationship("Match", back_populates="creator")
    game_sessions = relationship("GameSession", back_populates="creator")


class MatchSetting(Base):
    __tablename__ = "match_setting"
    __table_args__ = {'schema': SCHEMA_NAME}

    match_set_id = Column(Integer, primary_key=True)
    title = Column(String(150), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    is_ready = Column(Boolean, nullable=False, default=False)
    reference_solution = Column(Text, nullable=False)
    student_code = Column(Text, nullable=True)  # Template code for students
    function_name = Column(String(100), nullable=True)
    function_type = Column(String(50), nullable=True, default="output")
    function_inputs = Column(Text, nullable=True)  # JSON array
    language = Column(String(20), nullable=False, default="cpp")
    total_points = Column(Integer, nullable=False, default=100)
    creator_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.teacher.teacher_id"))
    
    # Relationship: This setting belongs to one teacher
    creator = relationship("Teacher", back_populates="match_settings")
    matches = relationship("Match", back_populates="match_setting")
    tests = relationship("Test", back_populates="match_setting", cascade="all, delete-orphan")

class Test(Base):
    __tablename__ = "tests"
    __table_args__ = {'schema': SCHEMA_NAME}

    test_id = Column(Integer, primary_key=True)
    test_in = Column(String(500), nullable=True)
    test_out = Column(String(500), nullable=True)
    scope = Column(Enum(TestScope, name='test_scope', schema=SCHEMA_NAME), nullable=False)
    match_set_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.match_setting.match_set_id"), nullable=False)

    match_setting = relationship("MatchSetting", back_populates="tests")


class StudentTest(Base):
    """
    SQLAlchemy model for the 'student_tests' table (student-created tests).
    """
    __tablename__ = "student_tests"
    __table_args__ = {'schema': SCHEMA_NAME}

    test_id = Column(Integer, primary_key=True)
    test_in = Column(String(500), nullable=True)
    test_out = Column(String(500), nullable=True)
    match_for_game_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.matches_for_game.match_for_game_id"), nullable=False)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student.student_id"), nullable=False)
    reviewer_comment = Column(String(500), nullable=True)


class StudentSolution(Base):
    """
    SQLAlchemy model for the 'student_solutions' table.
    """
    __tablename__ = "student_solutions"
    __table_args__ = {'schema': SCHEMA_NAME}

    solution_id = Column(Integer, primary_key=True)
    code = Column(Text, nullable=False)
    has_passed = Column(Boolean, nullable=False, default=False)
    passed_test = Column(Integer, default=0)
    match_for_game_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.matches_for_game.match_for_game_id"), nullable=False)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student.student_id"), nullable=False)
    

class StudentSolutionTest(Base):
    """
    SQLAlchemy model for the 'student_solution_tests' table.
    Tracks test results for student solutions.
    """
    __tablename__ = "student_solution_tests"
    __table_args__ = (
        {'schema': SCHEMA_NAME}
    )

    student_solution_test_id = Column(Integer, primary_key=True, autoincrement=True)
    solution_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student_solutions.solution_id"), nullable=False)
    teacher_test_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.tests.test_id"), nullable=True)
    student_test_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student_tests.test_id"), nullable=True)
    test_output = Column(Text, nullable=False)


class Match(Base):
    """
    SQLAlchemy model for the 'match' table.

    """
    __tablename__ = "match"
    __table_args__ = {'schema': SCHEMA_NAME}

    match_id = Column(Integer, primary_key=True)

    title = Column(String(150), nullable=False) 

    match_set_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.match_setting.match_set_id"))
    creator_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.teacher.teacher_id"))
    difficulty_level = Column(Integer, nullable=False)
    review_number = Column(Integer, nullable=False)
    duration_phase1 = Column(Integer, nullable=False, default=0)  # in minutes
    duration_phase2 = Column(Integer, nullable=False, default=0)  # in minutes
    
    # Relationships
    creator = relationship("Teacher", back_populates="matches")
    match_setting = relationship("MatchSetting", back_populates="matches")


class MatchesForGame(Base):
    __tablename__ = "matches_for_game"
    __table_args__ = {'schema': SCHEMA_NAME}

    match_for_game_id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.match.match_id"))
    game_id  = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.game_session.game_id"))


class Student(Base):
    __tablename__ = "student"
    __table_args__ = {'schema': SCHEMA_NAME}

    student_id      = Column(Integer    , primary_key=True)
    email           = Column(String(150), nullable=False)
    first_name      = Column(String(100), nullable=False)
    last_name       = Column(String(100), nullable=False)
    score           = Column(Integer    , default=0, nullable=False)
    user_id         = Column(Integer    , nullable=False)

class Login(Base):
    __tablename__   = "login"
    __table_args__  = {'schema': SCHEMA_NAME}

    login_id        =   Column(Integer    , primary_key=True)
    sub             =   Column(String(255), nullable=False)
    auth_provider   =   Column(String(50), nullable=False)

class StudentJoinGame(Base):
    __tablename__   = "student_join_game"
    __table_args__  = {'schema': SCHEMA_NAME}

    student_join_game_id = Column(Integer    , primary_key=True)
    student_id    = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student.student_id"))        
    game_id       = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.game_session.game_id"))

    assigned_match_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.match.match_id"), nullable=True)
    session_score = Column(Numeric(10, 2), nullable=True)  # Score for this game session (calculated after Phase 2)

class MatchJoinGame(Base):
    __tablename__ = "match_for_game"
    __table_args__ = {'schema': SCHEMA_NAME}


    match_for_game_id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.match.match_id"))
    game_id  = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.game_session.game_id"))



class GameSession(Base):
    __tablename__ = "game_session"
    __table_args__ = {'schema': SCHEMA_NAME}

    game_id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    creator_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.teacher.teacher_id"))
    creator = relationship("Teacher", back_populates="game_sessions")
    duration_phase1 = Column(Integer, nullable=False)
    duration_phase2 = Column(Integer, nullable=False)
    actual_start_date = Column(DateTime(timezone=True), nullable=True)


class VoteType(enum.Enum):
    correct = "correct"
    incorrect = "incorrect"
    skip = "skip"


class StudentAssignedReview(Base):
    """
    SQLAlchemy model for the 'student_assigned_review' table.
    Represents the assignment of a student to review another student's solution.
    """
    __tablename__ = "student_assigned_review"
    __table_args__ = (
        UniqueConstraint("student_id", "assigned_solution_id", name="uq_student_assigned_review_pair"),
        {'schema': SCHEMA_NAME}
    )

    student_assigned_review_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student.student_id"), nullable=False)
    assigned_solution_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student_solutions.solution_id"), nullable=False)

    # Relationships
    student = relationship("Student")
    assigned_solution = relationship("StudentSolution")


class StudentReviewVote(Base):
    """
    SQLAlchemy model for the 'student_review_vote' table.
    Stores the vote submitted by a student for an assigned review.
    """
    __tablename__ = "student_review_vote"
    __table_args__ = {'schema': SCHEMA_NAME}

    review_vote_id = Column(Integer, primary_key=True)
    student_assigned_review_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student_assigned_review.student_assigned_review_id"), nullable=False)
    vote = Column(Enum(VoteType, name='vote', schema=SCHEMA_NAME), nullable=False)
    proof_test_in = Column(String(500), nullable=True)
    proof_test_out = Column(String(500), nullable=True)
    valid = Column(Boolean, nullable=True)
    note = Column(String(500), nullable=True)

    # Relationship
    assigned_review = relationship("StudentAssignedReview")


class Badge(Base):
    """
    SQLAlchemy model for the 'badge' table.
    """
    __tablename__ = "badge"
    __table_args__ = {'schema': SCHEMA_NAME}

    badge_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    icon_path = Column(String(255), nullable=True)
    criteria_type = Column(String(50), nullable=False)

    
class StudentBadge(Base):
    """
    SQLAlchemy model for the 'student_badge' table.
    """
    __tablename__ = "student_badge"
    __table_args__ = (
        UniqueConstraint("student_id", "badge_id", name="uq_student_badge_unique"),
        {'schema': SCHEMA_NAME}
    )

    student_badge_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.student.student_id"), nullable=False)
    badge_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.badge.badge_id"), nullable=False)
    earned_at = Column(DateTime(timezone=True), default=dt.now)
    game_session_id = Column(Integer, ForeignKey(f"{SCHEMA_NAME}.game_session.game_id"), nullable=True)

    # Relationships
    badge = relationship("Badge")
    student = relationship("Student")


# ============================================================================
# Pydantic Models for Game Session Management API (User Story 3)
# ============================================================================

class StudentResponse(BaseModel):
    """
    Response model for individual student information.
    """
    student_id: int = Field(..., description="Unique identifier of the student")
    first_name: str = Field(..., description="First name of the student")
    last_name: str = Field(..., description="Last name of the student")
    email: str = Field(..., description="Email address of the student")


class GameSessionStudentsResponse(BaseModel):
    """
    Response model for listing all students joined to a game session.
    """
    game_id: int = Field(..., description="ID of the game session")
    total_students: int = Field(..., description="Total number of students joined")
    students: List[StudentResponse] = Field(..., description="List of joined students")


class MatchInfoResponse(BaseModel):
    """
    Response model for match information within a game session.
    """
    match_id: int = Field(..., description="Unique identifier of the match")
    title: str = Field(..., description="Title of the match")
    difficulty_level: int = Field(..., description="Difficulty level of the match")


class GameSessionFullDetailResponse(BaseModel):
    """
    Response model for full game session details including students and matches.
    """
    game_id: int = Field(..., description="ID of the game session")
    name: str = Field(..., description="Name of the game session")
    start_date: dt = Field(..., description="Start date of the game session")
    actual_start_date: Optional[dt] = Field(..., description="Actual start date of the game session")
    creator_id: int = Field(..., description="ID of the teacher who created the session")
    total_students: int = Field(..., description="Total number of students joined")
    students: List[StudentResponse] = Field(..., description="List of joined students")
    matches: List[MatchInfoResponse] = Field(..., description="List of matches in the session")
    duration_phase1: int = Field(..., description="First Phase Duration")
    duration_phase2: int = Field(..., description="Second Phase Duration")
   

class StudentMatchAssignment(BaseModel):
    """
    Response model for individual student-to-match assignment.
    """
    student_id: int = Field(..., description="ID of the student")
    student_name: str = Field(..., description="Full name of the student")
    assigned_match_id: int = Field(..., description="ID of the assigned match")
    assigned_match_title: str = Field(..., description="Title of the assigned match")


class GameSessionStartResponse(BaseModel):
    """
    Response model after starting a game session.
    """
    game_id: int = Field(..., description="ID of the game session")
    message: str = Field(..., description="Success message")
    total_students_assigned: int = Field(..., description="Number of students assigned to matches")
    assignments: List[StudentMatchAssignment] = Field(..., description="List of student-to-match assignments")
    duration_phase1: int = Field(..., description="First Phase Duration")
    duration_phase2: int = Field(..., description="Second Phase Duration")
    actual_start_date: Optional[dt] = Field(..., description="Actual start date of the game session")
    
class MatchJoinGameResponse(BaseModel):
    """
    Response model for matches joined to a game session.
    """
    match_for_game_id: int = Field(..., description="ID of the match-for-game record")
    match_id: int = Field(..., description="ID of the match")
    game_id: int = Field(..., description="ID of the game session")


