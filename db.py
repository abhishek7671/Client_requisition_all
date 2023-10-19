"""Data Craetion"""

from datetime import datetime
import datetime
from pydantic import BaseModel, EmailStr

class StudentCreate(BaseModel):
    lname: str
    fname: str
    email: str
    password:str

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str

class ChangePasswordSchema(BaseModel):
    email: str
    old_password:str
    new_password: str


class LoginRequest(BaseModel):
    email: str
    password: str

class TokenCreate(BaseModel):
    user_id:str
    access_token:str
    refresh_token:str
    status:bool
    created_date:datetime.datetime

# ----------------------------------------------
class ClientCreate(BaseModel):
    name: str
    email: str
    address: str

class TechStackCreate(BaseModel):
    technology: str

class RequiredPositionCreate(BaseModel):
    tech_stack_id: int
    experience: int
    position_required: bool


class Client_RequisitionCreate(BaseModel):
    client_id: int
    required_position_id: int
    reference_email: str
    jdstatus: bool = False
    requestby: str
    status: bool = True
    resource_provided: bool = False
    profile_shared_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    comments: str = None


class employee(BaseModel):
    emp_id:int
    associate_name:str
    practice:str
    department:str
    reporting_manager:str
    digital_lead:str
    tech_stack :str
    experience :int
    competency:str


 