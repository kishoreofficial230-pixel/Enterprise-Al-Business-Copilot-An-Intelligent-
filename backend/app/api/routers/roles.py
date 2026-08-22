from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user


router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


# =========================
# EMPLOYEE
# =========================

@router.get("/employee")
def employee_access(
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] not in ["Employee", "Manager", "Admin"]:
        raise HTTPException(
            status_code=403,
            detail="Employee access required"
        )

    return {
        "message": "Employee access granted",
        "user": current_user
    }


# =========================
# MANAGER
# =========================

@router.get("/manager")
def manager_access(
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] not in ["Manager", "Admin"]:
        raise HTTPException(
            status_code=403,
            detail="Manager or Admin access required"
        )

    return {
        "message": "Manager access granted",
        "user": current_user
    }


# =========================
# ADMIN
# =========================

@router.get("/admin")
def admin_access(
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return {
        "message": "Admin access granted",
        "user": current_user
    }