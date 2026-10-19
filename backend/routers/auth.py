from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from ..core.database import hr_users
from ..utils.password_utils import hash_password, verify_password
# ❌ REMOVED: from ..core.auth_utils import create_jwt_token


router = APIRouter(prefix="/auth", tags=["Authentication"])

class SignupModel(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str

class LoginModel(BaseModel):
    email: str
    password: str


@router.post("/signup")
def signup(user: SignupModel):
    if hr_users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hr_users.insert_one({
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "password": hash_password(user.password)
    })

    return {"success": True, "message": "Account created successfully"}


@router.post("/login")
def login(login_data: LoginModel, response: Response):
    user = hr_users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    # ❌ REMOVED: token = create_jwt_token(user["email"])
    # ❌ REMOVED: response.set_cookie(...)

    return {
        "success": True,
        "message": "Login successful",
        "name": user["name"],
        "email": user["email"]
        # ❌ REMOVED: access_token and token_type
    }


@router.post("/logout")
def logout(response: Response):
    # ❌ Cookie removal is no longer needed, but kept safe
    response.delete_cookie("access_token")
    return {"success": True, "message": "Logged out successfully"}
