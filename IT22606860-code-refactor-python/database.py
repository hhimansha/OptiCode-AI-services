"""
Database models for storing analytics and history
Uses SQLite for simplicity
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class RefactoringHistory(Base):
    __tablename__ = 'refactoring_history'
    
    id = Column(Integer, primary_key=True)
    original_code = Column(Text, nullable=False)
    refactored_code = Column(Text, nullable=False)
    model_used = Column(String(50))
    processing_time = Column(Float)
    quality_improvement = Column(Float)
    risk_reduction = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_rating = Column(Integer, default=0)
    
class CodeRisk(Base):
    __tablename__ = 'code_risks'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100))
    category = Column(String(50))
    severity = Column(String(20))
    line_number = Column(Integer)
    message = Column(Text)
    fixed = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    metadata = Column(Text)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = create_engine('sqlite:///refactoring_analytics.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def save_refactoring_history(original, refactored, model, time, quality, risks):
    """Save refactoring session to database"""
    session = get_session()
    try:
        history = RefactoringHistory(
            original_code=original,
            refactored_code=refactored,
            model_used=model,
            processing_time=time,
            quality_improvement=quality,
            risk_reduction=risks
        )
        session.add(history)
        session.commit()
        return history.id
    finally:
        session.close()

def save_code_risks(session_id, risks):
    """Save detected risks"""
    session = get_session()
    try:
        for risk in risks:
            risk_entry = CodeRisk(
                session_id=session_id,
                category=risk.get('category'),
                severity=risk.get('severity'),
                line_number=risk.get('line'),
                message=risk.get('message')
            )
            session.add(risk_entry)
        session.commit()
    finally:
        session.close()

def get_analytics_summary():
    """Get summary statistics"""
    session = get_session()
    try:
        total_refactorings = session.query(RefactoringHistory).count()
        avg_improvement = session.query(
            func.avg(RefactoringHistory.quality_improvement)
        ).scalar() or 0
        total_risks_fixed = session.query(CodeRisk).filter(
            CodeRisk.fixed == True
        ).count()
        
        return {
            'total_refactorings': total_refactorings,
            'avg_improvement': round(avg_improvement, 2),
            'total_risks_fixed': total_risks_fixed
        }
    finally:
        session.close()