from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./engineermind.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("SimulationCase", back_populates="project", cascade="all, delete-orphan")
    decision_records = relationship("DecisionRecord", back_populates="project", cascade="all, delete-orphan")

class SimulationCase(Base):
    __tablename__ = "simulation_cases"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String, index=True)
    velocity_ms = Column(Float, default=40.0)
    chord_m = Column(Float, default=1.8)
    target_y_plus = Column(Float, default=1.0)
    solver = Column(String, default="OpenFOAM")
    regime = Column(String, default="external_aerodynamics")
    status = Column(String, default="INITIALIZED")  # INITIALIZED, RUNNING, PASSED, ANOMALY, FAILED, BLOCKED_DEPENDENCY_MISSING
    pipeline_step = Column(String, default="IDLE")  # IDLE, BLOCKMESH, SURFACEFEATURES, SNAPPY, SOLVING, CONVERGED, FAILED
    physics_json = Column(JSON, default=dict)
    diagnostics_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="cases")

class DecisionRecord(Base):
    __tablename__ = "decision_records"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    actor = Column(String, default="Copilot")
    summary = Column(String)
    details = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="decision_records")

Base.metadata.create_all(bind=engine)
