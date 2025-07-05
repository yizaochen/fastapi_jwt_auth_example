from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from .auth_utils import verify_jwt, verify_roles, ROLES
from db import get_db
from models import Employee

router = APIRouter()

# Pydantic models for request/response
class EmployeeCreate(BaseModel):
    firstname: str
    lastname: str

class EmployeeUpdate(BaseModel):
    id: int
    firstname: Optional[str] = None
    lastname: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    firstname: str
    lastname: str

    class Config:
        from_attributes = True

# GET /employees - Get all employees (requires authentication)
@router.get("/", response_model=list[EmployeeResponse])
async def get_all_employees(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt)
):
    """
    Get all employees.
    Equivalent to getAllEmployees in Express.js.
    """
    employees = db.query(Employee).all()
    
    if not employees:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="No employees found."
        )
    
    return employees

# POST /employees - Create new employee (requires Admin or Editor role)
@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_roles(ROLES["Admin"], ROLES["Editor"]))
):
    """
    Create a new employee.
    Equivalent to createNewEmployee in Express.js.
    Requires Admin or Editor role.
    """
    try:
        new_employee = Employee(
            firstname=employee_data.firstname,
            lastname=employee_data.lastname
        )
        
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        
        return new_employee
        
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee"
        )

# PUT /employees - Update employee (requires Admin or Editor role)
@router.put("/", response_model=EmployeeResponse)
async def update_employee(
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_roles(ROLES["Admin"], ROLES["Editor"]))
):
    """
    Update an existing employee.
    Equivalent to updateEmployee in Express.js.
    Requires Admin or Editor role.
    """
    employee = db.query(Employee).filter(Employee.id == employee_data.id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"No employee matches ID {employee_data.id}."
        )
    
    # Update fields if provided
    if employee_data.firstname is not None:
        employee.firstname = employee_data.firstname
    if employee_data.lastname is not None:
        employee.lastname = employee_data.lastname
    
    try:
        db.commit()
        db.refresh(employee)
        return employee
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee"
        )

# DELETE /employees - Delete employee (requires Admin role only)
@router.delete("/")
async def delete_employee(
    employee_data: EmployeeUpdate,  # Reusing EmployeeUpdate model, only ID is required
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_roles(ROLES["Admin"]))
):
    """
    Delete an employee.
    Equivalent to deleteEmployee in Express.js.
    Requires Admin role only.
    """
    employee = db.query(Employee).filter(Employee.id == employee_data.id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"No employee matches ID {employee_data.id}."
        )
    
    try:
        db.delete(employee)
        db.commit()
        return {"message": f"Employee with ID {employee_data.id} has been deleted"}
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete employee"
        )

# GET /employees/{id} - Get specific employee (requires authentication)
@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_jwt)
):
    """
    Get a specific employee by ID.
    Equivalent to getEmployee in Express.js.
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=f"No employee matches ID {employee_id}."
        )
    
    return employee
