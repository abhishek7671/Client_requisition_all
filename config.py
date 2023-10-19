"""Database Configuration"""

import datetime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String ,DateTime,Boolean,ForeignKey

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:root@localhost:5432/client_tracker"
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345678@host.docker.internal/new_fastapi" #database configuration for docker


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    """Database table creation for users"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    lname = Column(String)
    fname = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

class TokenTable(Base):
    """Database table creation for tokens"""
    __tablename__ = "token"
    user_id = Column(Integer)
    access_toke = Column(String(450), primary_key=True)
    refresh_toke = Column(String(450),nullable=False)
    status = Column(Boolean)
    created_date = Column(DateTime, default=datetime.datetime.now)

# ---------------------------------------------------

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    address = Column(String)

class TechStack(Base):
    __tablename__ = "tech_stacks"
    id = Column(Integer, primary_key=True, index=True)
    technology = Column(String)


# class RequiredPosition(Base):
#     __tablename__ = "required_positions"
#     id = Column(Integer, primary_key=True, index=True)
#     tech_stack_id = Column(Integer, ForeignKey("tech_stacks.id"))
#     tech_stack_name = Column(String)
#     experience = Column(Integer, default=None)
#     position_required = Column(Boolean, default=None)



class Client_Requisition(Base):
    __tablename__ = "client_requisitions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"))
    # required_position_id = Column(Integer, ForeignKey("required_positions.id", ondelete="CASCADE"))
    tech_stack_str = Column(String)
    jdstatus = Column(Boolean)
    position_request = Column(String)
    reference_email = Column(String)
    requestby = Column(String)
    status = Column(String)
    resource_provided = Column(Boolean)
    profile_shared_count = Column(Integer, default=0, )
    accepted_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    comments = Column(String)
    delete_status = Column(String, default="activate")


class employeedata(Base):

    __tablename__ = "employee"
    id=Column(Integer,primary_key=True)
    emp_id=Column(Integer)
    associate_name=Column(String)
    department=Column(String)
    reporting_manager=Column(String)
    digital_lead=Column(String)
    tech_stack = Column(String)
    experience = Column(Integer)
    competency = Column(String)