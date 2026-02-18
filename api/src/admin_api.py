from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from pydantic import BaseModel

from database import get_db
from authentication.routes.auth_routes import get_current_user
from authentication.models.user import User, UserRoleEnum
from models import Student, Teacher

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

class AdminUserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str

class RoleChangeRequest(BaseModel):
    user_id: int

async def require_admin(current_user: Annotated[dict, Depends(get_current_user)]):
    role = current_user.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/users", response_model=List[AdminUserResponse])
async def get_all_users(
    current_user: Annotated[dict, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id).all()
    return [
        AdminUserResponse(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role.value if hasattr(u.role, 'value') else u.role
        ) for u in users
    ]

@router.post("/promote/teacher")
async def promote_to_teacher(
    request: RoleChangeRequest,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRoleEnum.teacher:
        return {"message": "User is already a teacher"}
        
    user.role = UserRoleEnum.teacher
    
    teacher = db.query(Teacher).filter(Teacher.email == user.email).first()
    if not teacher:
        new_teacher = Teacher(
            teacher_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            user_id=user.id
        )
        db.add(new_teacher)
    else:
        if hasattr(teacher, 'user_id') and not teacher.user_id:
            teacher.user_id = user.id
            
    db.commit()
    return {"message": f"User {user.email} promoted to Teacher"}

@router.post("/demote/student")
async def demote_to_student(
    request: RoleChangeRequest,
    current_user: Annotated[dict, Depends(require_admin)],
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.role == UserRoleEnum.student:
        return {"message": "User is already a student"}
        
    user.role = UserRoleEnum.student
    
    student = db.query(Student).filter(Student.email == user.email).first()
    if not student:
        new_student = Student(
            student_id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            score=0,
            user_id=user.id
        )
        db.add(new_student)
    else:
        if hasattr(student, 'user_id') and not student.user_id:
            student.user_id = user.id
            
    db.commit()
    return {"message": f"User {user.email} demoted to Student"}
