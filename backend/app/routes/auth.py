"""
Authentication API Routes for Administrator Access.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from database.db_manager import DatabaseManager
from backend.app.schemas.schemas import LoginRequest, LoginResponse, ChangePasswordRequest
from backend.app.auth.security import create_access_token, get_current_admin

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
db = DatabaseManager()


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest):
    """
    Authenticate administrator credentials and return an HMAC-SHA256 bearer token.
    Default initial credentials: username 'admin', password 'admin123'.
    """
    admin = db.verify_admin_password(credentials.username, credentials.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(admin)
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": admin,
    }


@router.get("/me")
def get_current_user_profile(admin=Depends(get_current_admin)):
    """Return currently authenticated administrator profile."""
    return {"admin": admin}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, admin=Depends(get_current_admin)):
    """Change password for current administrator."""
    username = admin["username"]
    success, msg = db.change_admin_password(username, req.old_password, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/logout")
def logout(admin=Depends(get_current_admin)):
    """Stateless logout confirmation."""
    return {"message": "Logged out successfully."}

