from typing import List, Optional, Annotated
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import os
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import (
    StudentAssignedReview,
    StudentReviewVote,
    StudentSolution,
    VoteType,
    MatchesForGame,
    Match,
    MatchSetting,
    Test,
    StudentTest,
    StudentSolutionTest,
    GameSession,
)
from authentication.routes.auth_routes import get_current_user
from code_runner import compile_cpp, run_cpp_executable

router = APIRouter(prefix="/api/phase-two", tags=["phase-two"])

class ExistingVoteResponse(BaseModel):
    vote: str
    valid: Optional[bool] = None
    proof_test_in: Optional[str] = None
    proof_test_out: Optional[str] = None
    note: Optional[str] = None


class AssignedSolutionResponse(BaseModel):
    student_assigned_review_id: int
    assigned_solution_id: int
    code: str
    pseudonym: str

    class Config:
        orm_mode = True


class VoteRequest(BaseModel):
    """Request model for submitting a vote."""
    student_assigned_review_id: int = Field(..., description="ID of the assigned review")
    vote: str = Field(..., description="Vote type: 'correct', 'incorrect', or 'skip'")
    proof_test_in: Optional[str] = Field(None, description="Test input (required for 'incorrect' vote)")
    proof_test_out: Optional[str] = Field(None, description="Expected test output (required for 'incorrect' vote)")
    note: Optional[str] = Field(None, description="Optional note about the review")


class VoteResponse(BaseModel):
    """Response model for a submitted vote."""
    review_vote_id: int
    message: str
    valid: Optional[bool] = None


class PhaseTwoTimingResponse(BaseModel):
    """Response model for phase 2 timing info."""
    duration_phase2: int = Field(..., description="Duration of phase 2 in minutes")
    phase2_start_time: Optional[datetime] = Field(None, description="When phase 2 started (actual_start_date + duration_phase1)")
    remaining_seconds: int = Field(..., description="Seconds remaining in phase 2")


@router.get("/timing", response_model=PhaseTwoTimingResponse)
def get_phase_two_timing(
    game_id: int = Query(..., description="ID of the game session"),
    db: Session = Depends(get_db),
):
    """
    Get timing information for phase 2 of a game session.
    Returns the duration and remaining time for the review phase.
    """
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    
    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if not game_session.actual_start_date:
        raise HTTPException(status_code=400, detail="Game session has not started yet")
    
    # Calculate when phase 2 starts (after phase 1 ends)
    phase1_duration_seconds = (game_session.duration_phase1 or 0) * 60
    phase2_duration_seconds = (game_session.duration_phase2 or 0) * 60
    
    phase2_start_time = game_session.actual_start_date.timestamp() + phase1_duration_seconds
    phase2_end_time = phase2_start_time + phase2_duration_seconds
    
    now = datetime.now(timezone.utc).timestamp()
    remaining_seconds = max(0, int(phase2_end_time - now))
    
    return PhaseTwoTimingResponse(
        duration_phase2=game_session.duration_phase2 or 0,
        phase2_start_time=datetime.fromtimestamp(phase2_start_time, tz=timezone.utc),
        remaining_seconds=remaining_seconds
    )


class AssignReviewsResponse(BaseModel):
    """Response model for review assignment."""
    message: str
    total_assignments: int
    assignments_per_student: dict


def _ensure_reviews_assigned(game_id: int, db: Session) -> int:
    """
    Helper function to ensure reviews are assigned for a game session.
    Returns the number of new assignments created (0 if already assigned).
    
    Rules:
    1. Students only review solutions from the SAME match_for_game_id (same problem)
    2. Students CANNOT review their own solution
    3. Each student reviews up to `review_number` solutions (from Match settings)
    4. If there are fewer students than review_number, students review all available solutions
    """
    # Check if reviews have already been assigned for this game
    existing_assignments = (
        db.query(StudentAssignedReview)
        .join(StudentSolution, StudentAssignedReview.assigned_solution_id == StudentSolution.solution_id)
        .join(MatchesForGame, StudentSolution.match_for_game_id == MatchesForGame.match_for_game_id)
        .filter(MatchesForGame.game_id == game_id)
        .first()
    )
    
    if existing_assignments:
        return 0  # Already assigned
    
    # Get all matches in this game session with their review_number
    matches_for_game = (
        db.query(MatchesForGame, Match)
        .join(Match, MatchesForGame.match_id == Match.match_id)
        .filter(MatchesForGame.game_id == game_id)
        .all()
    )
    
    if not matches_for_game:
        return 0
    
    total_assignments = 0
    
    # Process each match_for_game separately (students only review same problem)
    for mfg, match in matches_for_game:
        review_number = match.review_number or 3  # default to 3 if not set
        
        # Get all solutions for this match_for_game
        solutions = (
            db.query(StudentSolution)
            .filter(
                StudentSolution.match_for_game_id == mfg.match_for_game_id,
                StudentSolution.has_passed.is_(True)
            )
            .all()
        )
        
        if len(solutions) < 2:
            # Need at least 2 students to do reviews
            continue
        
        student_ids = [sol.student_id for sol in solutions]
        
        # For each student, assign them solutions to review
        for student_id in student_ids:
            # Get other students' solutions (exclude own)
            other_solutions = [sol for sol in solutions if sol.student_id != student_id]
            
            # Limit to review_number, but take all if fewer available
            solutions_to_review = other_solutions[:min(review_number, len(other_solutions))]
            
            for solution in solutions_to_review:
                # Create the review assignment
                assignment = StudentAssignedReview(
                    student_id=student_id,
                    assigned_solution_id=solution.solution_id
                )
                db.add(assignment)
                total_assignments += 1
    
    if total_assignments > 0:
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return 0

    
    return total_assignments


@router.post("/assign_reviews", response_model=AssignReviewsResponse)
def assign_reviews_for_game(
    game_id: int = Query(..., description="ID of the game session"),
    db: Session = Depends(get_db),
):
    """
    Assign solutions for review to students in a game session.
    
    Rules:
    1. Students only review solutions from the SAME match_for_game_id (same problem)
    2. Students CANNOT review their own solution
    3. Each student reviews up to `review_number` solutions (from Match settings)
    4. If there are fewer students than review_number, students review all available solutions
    
    This endpoint can be called manually or is auto-triggered when students request their assignments.
    """
    # Verify game session exists and has started
    game_session = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if not game_session:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if not game_session.actual_start_date:
        raise HTTPException(status_code=400, detail="Game session has not started yet")
    
    total_assignments = _ensure_reviews_assigned(game_id, db)
    
    if total_assignments == 0:
        return AssignReviewsResponse(
            message="Reviews were already assigned for this game session",
            total_assignments=0,
            assignments_per_student={}
        )
    
    return AssignReviewsResponse(
        message=f"Successfully assigned {total_assignments} reviews for game session {game_id}",
        total_assignments=total_assignments,
        assignments_per_student={}
    )


@router.get("/assigned_solutions", response_model=List[AssignedSolutionResponse])
def get_assigned_solutions(
    current_user: Annotated[dict, Depends(get_current_user)],
    game_id: int = Query(..., description="ID of the game session"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all solutions assigned to the authenticated student for review.
    Automatically assigns reviews if not already done (lazy initialization).
    """
    student_id = int(current_user["sub"])
    
    # Ensure reviews are assigned (will do nothing if already assigned)
    _ensure_reviews_assigned(game_id, db)

    assigned_reviews = (
        db.query(StudentAssignedReview)
        .join(StudentSolution, StudentAssignedReview.assigned_solution_id == StudentSolution.solution_id)
        .join(MatchesForGame, StudentSolution.match_for_game_id == MatchesForGame.match_for_game_id)
        .filter(
            StudentAssignedReview.student_id == student_id,
            MatchesForGame.game_id == game_id
        )
        .all()
    )

    result = []
    for review in assigned_reviews:
        solution = review.assigned_solution
        
        pseudonym = f"Candidate #{solution.solution_id}"
        
        result.append(AssignedSolutionResponse(
            student_assigned_review_id=review.student_assigned_review_id,
            assigned_solution_id=solution.solution_id,
            code=solution.code,
            pseudonym=pseudonym,
        ))

    return result


@router.post("/vote", response_model=VoteResponse)
def submit_vote(
    current_user: Annotated[dict, Depends(get_current_user)],
    request: VoteRequest,
    db: Session = Depends(get_db),
):
    """
    Submit a vote for an assigned solution review.
    """
    student_id = int(current_user["sub"])

    assigned_review = (
        db.query(StudentAssignedReview)
        .filter(StudentAssignedReview.student_assigned_review_id == request.student_assigned_review_id)
        .first()
    )

    if not assigned_review:
        raise HTTPException(status_code=404, detail="Assigned review not found")

    if assigned_review.student_id != student_id:
        raise HTTPException(status_code=403, detail="Not authorized to vote on this review")

    existing_vote = (
        db.query(StudentReviewVote)
        .filter(StudentReviewVote.student_assigned_review_id == request.student_assigned_review_id)
        .first()
    )


    vote_type_str = request.vote.lower()
    if vote_type_str not in ["correct", "incorrect", "skip"]:
        raise HTTPException(status_code=400, detail="Invalid vote type. Must be 'correct', 'incorrect', or 'skip'")

    if vote_type_str == "incorrect":
        if not request.proof_test_in or not request.proof_test_out:
            raise HTTPException(status_code=400, detail="Proof test input and output are required for 'incorrect' vote")

    solution = assigned_review.assigned_solution
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    # Get match info to access reference solution and tests
    match_for_game = (
        db.query(MatchesForGame)
        .filter(MatchesForGame.match_for_game_id == solution.match_for_game_id)
        .first()
    )

    if not match_for_game:
        raise HTTPException(status_code=404, detail="Match for game not found")

    match = (
        db.query(Match)
        .filter(Match.match_id == match_for_game.match_id)
        .first()
    )

    if not match or not match.match_set_id:
        raise HTTPException(status_code=404, detail="Match or match setting not found")

    match_setting = (
        db.query(MatchSetting)
        .filter(MatchSetting.match_set_id == match.match_set_id)
        .first()
    )

    if not match_setting:
        raise HTTPException(status_code=404, detail="Match setting not found")

    valid = None

    if vote_type_str == "incorrect":
        valid, student_actual_output = _validate_incorrect_vote(
            student_code=solution.code,
            reference_code=match_setting.reference_solution,
            test_in=request.proof_test_in,
            test_out=request.proof_test_out
        )
    elif vote_type_str == "correct":
        valid = _validate_correct_vote(
            solution=solution,
            match_set_id=match.match_set_id,
            db=db
        )
  
    vote_enum = VoteType(vote_type_str)

  
    if existing_vote:
        # Update existing vote (edit)
        existing_vote.vote = vote_enum
        existing_vote.proof_test_in = request.proof_test_in if vote_type_str == "incorrect" else None
        existing_vote.proof_test_out = request.proof_test_out if vote_type_str == "incorrect" else None
        existing_vote.valid = valid
        existing_vote.note = request.note
        db.commit()
        db.refresh(existing_vote)
        
        # If valid incorrect vote, ensure test is persisted
        if vote_type_str == "incorrect" and valid:
             _persist_proof_test(
                 db=db,
                 student_id=student_id,
                 solution=solution,
                 test_in=request.proof_test_in,
                 test_out=request.proof_test_out,
                 actual_output=student_actual_output,
                 note=request.note
             )

        return VoteResponse(
            review_vote_id=existing_vote.review_vote_id,
            message="Vote updated successfully",
            valid=valid
        )
    else:
        # Create new vote (first time)
        new_vote = StudentReviewVote(
            student_assigned_review_id=request.student_assigned_review_id,
            vote=vote_enum,
            proof_test_in=request.proof_test_in if vote_type_str == "incorrect" else None,
            proof_test_out=request.proof_test_out if vote_type_str == "incorrect" else None,
            valid=valid,
            note=request.note
        )
        db.add(new_vote)
        db.commit()
        db.refresh(new_vote)

        # If valid incorrect vote, persist test
        if vote_type_str == "incorrect" and valid:
             _persist_proof_test(
                 db=db,
                 student_id=student_id,
                 solution=solution,
                 test_in=request.proof_test_in,
                 test_out=request.proof_test_out,
                 actual_output=student_actual_output,
                 note=request.note
             )

        return VoteResponse(
            review_vote_id=new_vote.review_vote_id,
            message="Vote submitted successfully",
            valid=valid
        )


def _persist_proof_test(
    db: Session, 
    student_id: int, 
    solution: StudentSolution, 
    test_in: str, 
    test_out: str, 
    actual_output: str,
    note: Optional[str] = None
):
    """
    Persist the proof test as a StudentTest and record the result in StudentSolutionTest.
    This makes it visible in the solution results.
    
    Args:
        db: Database session
        student_id: ID of the student who created the proof test (reviewer)
        solution: The student solution being reviewed
        test_in: Input for the proof test
        test_out: Expected output for the proof test
        actual_output: Actual output generated by the solution
        note: Optional comment from the reviewer explaining the issue
    """
    #  Create StudentTest (linked to the reviewer)
    new_test = StudentTest(
        test_in=test_in,
        test_out=test_out,
        match_for_game_id=solution.match_for_game_id,
        student_id=student_id,
        reviewer_comment=note  # Store reviewer's comment
    )
    db.add(new_test)
    db.flush() # Get test_id
    
    sol_test = StudentSolutionTest(
        solution_id=solution.solution_id,
        teacher_test_id=None,
        student_test_id=new_test.test_id,
        test_output=actual_output
    )
    db.add(sol_test)
    db.commit()


def _validate_incorrect_vote(
    student_code: str,
    reference_code: str,
    test_in: str,
    test_out: str
) -> tuple[bool, str]:
    """
    Validate an 'incorrect' vote by running the proof test on both solutions.
    
    Returns (True, actual_output) if:
    - The test FAILS on the student's solution (returns student's actual output), AND
    - The test PASSES on the reference solution
    
    This proves the student's code has a bug that the reference solution doesn't have.
    """
    # Compile and run test on student solution
    student_exe, student_compile_error = compile_cpp(student_code)
    student_actual_output = ""
    
    if student_exe is None:
        # Student code doesn't compile - test fails on student code
        student_test_passes = False
        student_actual_output = f"Compilation Error: {student_compile_error}"
    else:
        try:
            student_result = run_cpp_executable(student_exe, test_in)
            student_output = (student_result.get("stdout") or "").strip()
            student_actual_output = student_output
            expected_output = test_out.strip()
            
            if student_result["status"] != "success":
                student_test_passes = False
                student_actual_output = student_result.get("stderr") or "Runtime Error"
            else:
                student_test_passes = (student_output == expected_output)
        finally:
            if os.path.exists(student_exe):
                try:
                    os.remove(student_exe)
                except:
                    pass

    # Compile and run test on reference solution
    ref_exe, ref_compile_error = compile_cpp(reference_code)
    if ref_exe is None:
        # Reference code doesn't compile - something is wrong with reference
        return False, ""
    
    try:
        ref_result = run_cpp_executable(ref_exe, test_in)
        ref_output = (ref_result.get("stdout") or "").strip()
        expected_output = test_out.strip()
        ref_test_passes = (ref_result["status"] == "success" and ref_output == expected_output)
    finally:
        if os.path.exists(ref_exe):
            try:
                os.remove(ref_exe)
            except:
                pass

    is_valid = (not student_test_passes) and ref_test_passes
    return is_valid, student_actual_output


def _validate_correct_vote(
    solution: StudentSolution,
    match_set_id: int,
    db: Session
) -> bool:
    """
    Validate a 'correct' vote by checking if the solution passed all tests.
    
    Uses the pre-computed passed_test count from Phase 1 instead of re-running tests.
    
    Returns True if passed_test == total_tests
    """
    total_tests = (
        db.query(Test)
        .filter(Test.match_set_id == match_set_id)
        .count()
    )

    passed_tests = solution.passed_test or 0

    return passed_tests == total_tests
