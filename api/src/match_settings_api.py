"""
Match Settings API Module

Provides comprehensive endpoints for creating, editing, publishing, and managing match settings.
Includes ownership validation, test management, and code validation.
"""

from typing import List, Optional, Annotated
from fastapi import APIRouter, Query, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import MatchSetting, Test, TestScope, Teacher
from authentication.routes.auth_routes import get_current_user
from code_runner import compile_cpp, run_cpp_executable
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models
# ============================================================================

class TestItemResponse(BaseModel):
    test_id: int
    test_in: Optional[str] = None
    test_out: str
    scope: str
    
    class Config:
        from_attributes = True


class TestCreateRequest(BaseModel):
    test_in: Optional[str] = None
    test_out: str
    scope: str


class MatchSettingResponse(BaseModel):
    match_set_id: int = Field(..., description="Unique identifier for the match setting")
    title: str = Field(..., description="Title of the match setting")
    description: str = Field(..., description="Detailed description")
    is_ready: bool = Field(..., description="Readiness status: true=ready, false=draft")
    reference_solution: str = Field(..., description="Reference solution code")
    student_code: Optional[str] = Field(None, description="Template code for students")
    function_name: Optional[str] = Field(None, description="Function name")
    function_type: Optional[str] = Field(None, description="Function type (e.g., 'output')")
    function_inputs: Optional[str] = Field(None, description="JSON array of function inputs")
    language: str = Field(..., description="Programming language (e.g., 'cpp')")
    creator_id: int = Field(..., description="ID of the teacher who created this setting")
    tests: List[TestItemResponse] = Field(default=[], description="List of tests for this setting")

    class Config:
        from_attributes = True


class MatchSettingCreateRequest(BaseModel):
    title: str
    description: str
    reference_solution: str
    student_code: Optional[str] = None
    function_name: Optional[str] = None
    function_type: str = "output"
    function_inputs: Optional[str] = None
    language: str = "cpp"
    tests: List[TestCreateRequest] = []
    publish: bool = False


class MatchSettingUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reference_solution: Optional[str] = None
    student_code: Optional[str] = None
    function_name: Optional[str] = None
    function_type: Optional[str] = None
    function_inputs: Optional[str] = None
    language: Optional[str] = None
    tests: Optional[List[TestCreateRequest]] = None
    publish: bool = False


class TestResult(BaseModel):
    test_in: Optional[str]
    test_out: str
    actual_output: str
    passed: bool
    error: Optional[str] = None


class TryMatchSettingRequest(BaseModel):
    """Request model for trying/validating a match setting"""
    reference_solution: str
    language: str = "cpp"
    tests: List[TestCreateRequest]


class TryMatchSettingResponse(BaseModel):
    """Response model for try/validation results"""
    success: bool
    message: str
    test_results: List[TestResult] = []
    compilation_error: Optional[str] = None


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/api", tags=["match-settings"])


# ============================================================================
# Helper Functions
# ============================================================================


def get_teacher_id(current_user: dict, db: Session) -> int:
    """Extract teacher_id from current user"""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can manage match settings"
        )
    
    # JWT payload uses 'sub' for user ID (as string), while testing mode might provide 'id'
    user_id = current_user.get("id")
    if user_id is None:
        user_id = int(current_user["sub"])
    
    teacher = db.query(Teacher).filter(Teacher.user_id == user_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher record not found"
        )
    
    return teacher.teacher_id


def verify_ownership(match_setting: MatchSetting, teacher_id: int):
    """Verify that the current teacher owns the match setting"""
    if match_setting.creator_id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this match setting"
        )


def run_tests(code: str, language: str, tests: List[TestCreateRequest]) -> TryMatchSettingResponse:
    """
    Compile and run code against test cases
    """
    if language != "cpp":
        return TryMatchSettingResponse(
            success=False,
            message="Only C++ is currently supported",
            compilation_error="Unsupported language"
        )
    
    # Compile the code
    executable_path, compile_error = compile_cpp(code)
    
    if compile_error:
        return TryMatchSettingResponse(
            success=False,
            message="Compilation failed",
            compilation_error=compile_error
        )
    
    # Run tests
    test_results = []
    all_passed = True
    
    try:
        for test in tests:
            test_input = test.test_in if test.test_in else ""
            result = run_cpp_executable(executable_path, test_input)
            
            actual_output = result["stdout"].strip()
            expected_output = test.test_out.strip()
            passed = actual_output == expected_output
            
            if not passed:
                all_passed = False
            
            test_results.append(TestResult(
                test_in=test.test_in,
                test_out=test.test_out,
                actual_output=actual_output,
                passed=passed,
                error=result["stderr"] if result["stderr"] else None
            ))
    
    finally:
        # Clean up executable
        if executable_path and os.path.exists(executable_path):
            os.remove(executable_path)
    
    return TryMatchSettingResponse(
        success=all_passed,
        message="All tests passed" if all_passed else "Some tests failed",
        test_results=test_results
    )


def validate_match_setting_logic(
    function_name: Optional[str],
    function_type: Optional[str],
    reference_solution: str,
    language: str,
    tests: List[TestCreateRequest]
):
    """
    Validate match setting fields and run tests.
    Raises HTTPException if validation fails.
    """
    
    # Check if there are any tests defined
    if not tests or len(tests) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one test case is required to publish a match setting",
        )
    
    # Run tests
    validation_result = run_tests(
        reference_solution,
        language,
        tests
    )
    
    if not validation_result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {validation_result.message}",
        )


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/match-settings",
    response_model=List[MatchSettingResponse],
    summary="Browse all match settings",
    description="Retrieve all available match settings with optional filtering by readiness status.",
)
async def get_match_settings(
    is_ready: Optional[bool] = Query(
        None,
        description="Filter by readiness status: true=ready, false=draft, omit=all",
    ),
    db: Session = Depends(get_db),
) -> List[MatchSettingResponse]:
    """
    Browse all available match settings with optional filtering.
    """
    query = db.query(MatchSetting)

    if is_ready is not None:
        query = query.filter(MatchSetting.is_ready == is_ready)

    results = query.all()

    response = []
    for ms in results:
        response.append(MatchSettingResponse(
            match_set_id=ms.match_set_id,
            title=ms.title,
            description=ms.description,
            is_ready=ms.is_ready,
            reference_solution=ms.reference_solution,
            student_code=ms.student_code,
            function_name=ms.function_name,
            function_type=ms.function_type,
            function_inputs=ms.function_inputs,
            language=ms.language,
            creator_id=ms.creator_id,
            tests=[
                TestItemResponse(
                    test_id=t.test_id,
                    test_in=t.test_in,
                    test_out=t.test_out,
                    scope=t.scope.name if hasattr(t.scope, 'name') else str(t.scope)
                ) for t in ms.tests
            ]
        ))
    
    return response


@router.get(
    "/match-settings/{match_set_id}",
    response_model=MatchSettingResponse,
    summary="Get a specific match setting",
)
async def get_match_setting(
    match_set_id: int,
    db: Session = Depends(get_db),
) -> MatchSettingResponse:
    """
    Retrieve a specific match setting by ID.
    """
    ms = db.query(MatchSetting).filter(MatchSetting.match_set_id == match_set_id).first()
    
    if not ms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match setting not found"
        )
    
    return MatchSettingResponse(
        match_set_id=ms.match_set_id,
        title=ms.title,
        description=ms.description,
        is_ready=ms.is_ready,
        reference_solution=ms.reference_solution,
        student_code=ms.student_code,
        function_name=ms.function_name,
        function_type=ms.function_type,
        function_inputs=ms.function_inputs,
        language=ms.language,
        creator_id=ms.creator_id,
        tests=[
            TestItemResponse(
                test_id=t.test_id,
                test_in=t.test_in,
                test_out=t.test_out,
                scope=t.scope.name if hasattr(t.scope, 'name') else str(t.scope)
            ) for t in ms.tests
        ]
    )


@router.post(
    "/match-settings",
    response_model=MatchSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new match setting",
)
async def create_match_setting(
    data: MatchSettingCreateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MatchSettingResponse:
    """
    Create a new match setting (saved as draft by default).
    """
    teacher_id = get_teacher_id(current_user, db)
    
    try:
        # Create match setting
        new_setting = MatchSetting(
            title=data.title,
            description=data.description,
            is_ready=data.publish,  # Set based on publish flag
            reference_solution=data.reference_solution,
            student_code=data.student_code,
            function_name=data.function_name,
            function_type=data.function_type,
            function_inputs=data.function_inputs,
            language=data.language,
            creator_id=teacher_id
        )
        
        # Validate if publishing
        if data.publish:
            validate_match_setting_logic(
                data.function_name,
                data.function_type,
                data.reference_solution,
                data.language,
                data.tests
            )
        
        db.add(new_setting)
        db.flush()  # Get the ID
        
        # Add tests
        for test_data in data.tests:
            test = Test(
                test_in=test_data.test_in,
                test_out=test_data.test_out,
                scope=TestScope[test_data.scope],
                match_set_id=new_setting.match_set_id
            )
            db.add(test)
        
        db.commit()
        db.refresh(new_setting)
        
        return await get_match_setting(new_setting.match_set_id, db)
    
    except IntegrityError as e:
        db.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A match setting with this title already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error"
        )


@router.put(
    "/match-settings/{match_set_id}",
    response_model=MatchSettingResponse,
    summary="Update an existing match setting",
)
async def update_match_setting(
    match_set_id: int,
    data: MatchSettingUpdateRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MatchSettingResponse:
    """
    Update an existing match setting (owner only).
    """
    teacher_id = get_teacher_id(current_user, db)
    
    match_setting = db.query(MatchSetting).filter(MatchSetting.match_set_id == match_set_id).first()
    
    if not match_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match setting not found"
        )
    
    verify_ownership(match_setting, teacher_id)
    validation_result = run_tests(data.reference_solution, data.language, data.tests)
    if not validation_result.success:
        error_detail = getattr(validation_result, "message", "Reference solution failed validation")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    update_data = data.dict(exclude_unset=True)
    
    tests_update = update_data.pop('tests', None)
    
    for field, value in update_data.items():
        if field != 'publish':  # Ignore publish field for setting attributes
            setattr(match_setting, field, value)
    
    # Update tests if provided
    if tests_update is not None:
        # Clear existing tests (cascade should handle delete)
        match_setting.tests = []
        
        # Add new tests
        for test_data in data.tests:
            test = Test(
                test_in=test_data.test_in,
                test_out=test_data.test_out,
                scope=TestScope[test_data.scope],
                match_set_id=match_setting.match_set_id
            )
            db.add(test)
    
    # Validate if publishing
    if data.publish:
        # Determine tests to run
        tests_to_run = []
        if tests_update is not None:
            # Use the new tests provided in the request
            tests_to_run = data.tests
        else:
            # Use existing tests from the database
            tests_to_run = [
                TestCreateRequest(
                    test_in=t.test_in,
                    test_out=t.test_out,
                    scope=t.scope.name if hasattr(t.scope, 'name') else str(t.scope)
                ) for t in match_setting.tests
            ]

        validate_match_setting_logic(
            match_setting.function_name,
            match_setting.function_type,
            match_setting.reference_solution,
            match_setting.language,
            tests_to_run
        )
        match_setting.is_ready = True
    
    try:
        db.commit()
        db.refresh(match_setting)
        return await get_match_setting(match_set_id, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A match setting with this title already exists"
        )


@router.post(
    "/match-settings/{match_set_id}/publish",
    response_model=MatchSettingResponse,
    summary="Publish a match setting",
)
async def publish_match_setting(
    match_set_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MatchSettingResponse:
    """
    Validate and publish a match setting (owner only).
    Runs all tests to ensure the reference solution is correct.
    """
    teacher_id = get_teacher_id(current_user, db)
    
    match_setting = db.query(MatchSetting).filter(MatchSetting.match_set_id == match_set_id).first()
    
    if not match_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match setting not found"
        )
    
    verify_ownership(match_setting, teacher_id)
    
    # Validate required fields and run tests
    tests_requests = [
        TestCreateRequest(
            test_in=t.test_in,
            test_out=t.test_out,
            scope=t.scope.name if hasattr(t.scope, 'name') else str(t.scope)
        ) for t in match_setting.tests
    ]
    
    validate_match_setting_logic(
        match_setting.function_name,
        match_setting.function_type,
        match_setting.reference_solution,
        match_setting.language,
        tests_requests
    )
    
    # Publish
    match_setting.is_ready = True
    db.commit()
    db.refresh(match_setting)
    
    return await get_match_setting(match_set_id, db)


@router.post(
    "/match-settings/try",
    response_model=TryMatchSettingResponse,
    summary="Try/validate code against tests",
)
async def try_match_setting(
    data: TryMatchSettingRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> TryMatchSettingResponse:
    """
    Compile and run code against test cases without saving.
    """
    _ = get_teacher_id(current_user, db)  # Verify teacher role
    
    return run_tests(data.reference_solution, data.language, data.tests)


@router.post(
    "/match-settings/{match_set_id}/clone",
    response_model=MatchSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a match setting",
)
async def clone_match_setting(
    match_set_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> MatchSettingResponse:
    """
    Clone an existing match setting. The new owner is the current teacher.
    """
    teacher_id = get_teacher_id(current_user, db)
    
    original = db.query(MatchSetting).filter(MatchSetting.match_set_id == match_set_id).first()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match setting not found"
        )
    
    # Create clone with new title
    clone_title = f"{original.title} (Clone)"
    counter = 1
    while db.query(MatchSetting).filter(MatchSetting.title == clone_title).first():
        clone_title = f"{original.title} (Clone {counter})"
        counter += 1
    
    cloned_setting = MatchSetting(
        title=clone_title,
        description=original.description,
        is_ready=False,  # Clones start as drafts
        reference_solution=original.reference_solution,
        student_code=original.student_code,
        function_name=original.function_name,
        function_type=original.function_type,
        function_inputs=original.function_inputs,
        language=original.language,
        creator_id=teacher_id
    )
    
    db.add(cloned_setting)
    db.flush()
    
    # Clone tests
    for test in original.tests:
        cloned_test = Test(
            test_in=test.test_in,
            test_out=test.test_out,
            scope=test.scope,
            match_set_id=cloned_setting.match_set_id
        )
        db.add(cloned_test)
    
    db.commit()
    db.refresh(cloned_setting)
    
    return await get_match_setting(cloned_setting.match_set_id, db)


@router.delete(
    "/match-settings/{match_set_id}/tests/{test_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a test case",
)
async def delete_test(
    match_set_id: int,
    test_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Delete a test case from a match setting (owner only).
    """
    teacher_id = get_teacher_id(current_user, db)
    
    match_setting = db.query(MatchSetting).filter(MatchSetting.match_set_id == match_set_id).first()
    
    if not match_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match setting not found"
        )
    
    verify_ownership(match_setting, teacher_id)
    
    test = db.query(Test).filter(
        Test.test_id == test_id,
        Test.match_set_id == match_set_id
    ).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    db.delete(test)
    db.commit()
    
    return None


@router.delete(
    "/match-settings/{match_set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a match setting",
)
async def delete_match_setting(
    match_set_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Delete a match setting (owner only).
    """
    teacher_id = get_teacher_id(current_user, db)
    
    match_setting = db.query(MatchSetting).filter(MatchSetting.match_set_id == match_set_id).first()
    
    if not match_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match setting not found"
        )
    
    verify_ownership(match_setting, teacher_id)
    
    db.delete(match_setting)
    db.commit()
    
    return None
