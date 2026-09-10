"""Database models: Users, Customers, Policies, Recommendations,
RiskAssessments, AuditLogs."""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from backend.app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    role = Column(String(50), default="agent")  # agent | admin
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    crm_id = Column(String(64), unique=True, index=True)  # e.g. CUST-0001
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), default="")
    email = Column(String(255), default="")
    phone = Column(String(50), default="")
    age = Column(Integer, nullable=False)
    gender = Column(String(20), default="")
    location = Column(String(120), default="")
    occupation = Column(String(120), default="")
    annual_income = Column(Float, default=0)
    marital_status = Column(String(30), default="")
    health_conditions = Column(Text, default="")  # comma separated
    smoker = Column(String(10), default="no")
    insurance_needs = Column(Text, default="")  # comma separated
    budget = Column(Float, default=0)
    consent_given = Column(Integer, default=0)
    status = Column(String(30), default="onboarding")  # onboarding|completed|blocked
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Policy(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), unique=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50))  # health | life | auto | home
    premium = Column(Float)
    coverage = Column(Text)
    eligibility = Column(JSON)   # dict of rules
    risk_appetite = Column(JSON)  # dict e.g. {"min_score":0,"max_score":100}
    summary = Column(Text)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    run_id = Column(String(64), index=True)
    risk_score = Column(Float)
    category = Column(String(20))
    confidence = Column(Float)
    factors = Column(JSON)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    run_id = Column(String(64), index=True)
    ranking = Column(Integer)
    policy_name = Column(String(150))
    product_id = Column(String(50))
    match_score = Column(Float)
    premium = Column(Float)
    coverage_summary = Column(Text)
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), index=True)
    agent = Column(String(50))
    event = Column(String(255))
    level = Column(String(20), default="INFO")  # INFO|WARN|ERROR
    detail = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkflowRun(Base):
    """Stores full workflow state for the dashboard/trace."""
    __tablename__ = "workflow_runs"
    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(Integer, index=True)
    status = Column(String(30), default="running")  # running|completed|blocked|failed
    final_state = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)