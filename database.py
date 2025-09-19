# Database Models and Configuration
# This module handles all database operations for the Financial Document Analyzer

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()

class AnalysisResult(Base):
    """Database model for storing financial document analysis results"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True)  # Celery task ID
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    upload_time = Column(DateTime, default=datetime.utcnow)
    analysis_start_time = Column(DateTime)
    analysis_complete_time = Column(DateTime)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # Analysis Results (JSON stored as text)
    financial_summary = Column(Text)  # JSON string
    risk_assessment = Column(Text)    # JSON string
    investment_advice = Column(Text)  # JSON string
    regulatory_compliance = Column(Text)  # JSON string
    
    # Metrics
    processing_time_seconds = Column(Float)
    confidence_score = Column(Float)
    error_message = Column(Text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "analysis_start_time": self.analysis_start_time.isoformat() if self.analysis_start_time else None,
            "analysis_complete_time": self.analysis_complete_time.isoformat() if self.analysis_complete_time else None,
            "status": self.status,
            "financial_summary": json.loads(self.financial_summary) if self.financial_summary else None,
            "risk_assessment": json.loads(self.risk_assessment) if self.risk_assessment else None,
            "investment_advice": json.loads(self.investment_advice) if self.investment_advice else None,
            "regulatory_compliance": json.loads(self.regulatory_compliance) if self.regulatory_compliance else None,
            "processing_time_seconds": self.processing_time_seconds,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message
        }

class UserSession(Base):
    """Database model for tracking user sessions and activity"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_ip = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Analytics
    documents_processed = Column(Integer, default=0)
    total_processing_time = Column(Float, default=0.0)

# Database Configuration
DATABASE_URL = "sqlite:///./financial_analyzer.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Get database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Operations
class DatabaseManager:
    """Centralized database operations manager"""
    
    @staticmethod
    def create_analysis_record(
        task_id: str,
        filename: str,
        file_size: int,
        db: Session
    ) -> AnalysisResult:
        """Create a new analysis record"""
        analysis = AnalysisResult(
            task_id=task_id,
            filename=filename,
            file_size=file_size,
            status="pending"
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    
    @staticmethod
    def update_analysis_status(
        task_id: str,
        status: str,
        db: Session,
        error_message: Optional[str] = None
    ) -> Optional[AnalysisResult]:
        """Update analysis status"""
        analysis = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
        if analysis:
            analysis.status = status
            if status == "processing":
                analysis.analysis_start_time = datetime.utcnow()
            elif status in ["completed", "failed"]:
                analysis.analysis_complete_time = datetime.utcnow()
                if analysis.analysis_start_time:
                    analysis.processing_time_seconds = (
                        analysis.analysis_complete_time - analysis.analysis_start_time
                    ).total_seconds()
            
            if error_message:
                analysis.error_message = error_message
            
            db.commit()
            db.refresh(analysis)
        return analysis
    
    @staticmethod
    def save_analysis_results(
        task_id: str,
        results: Dict[str, Any],
        db: Session
    ) -> Optional[AnalysisResult]:
        """Save complete analysis results"""
        analysis = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
        if analysis:
            # Store each analysis component as JSON
            analysis.financial_summary = json.dumps(results.get("financial_summary", {}))
            analysis.risk_assessment = json.dumps(results.get("risk_assessment", {}))
            analysis.investment_advice = json.dumps(results.get("investment_advice", {}))
            analysis.regulatory_compliance = json.dumps(results.get("regulatory_compliance", {}))
            
            # Calculate confidence score (average of individual scores)
            scores = []
            for key in ["financial_summary", "risk_assessment", "investment_advice", "regulatory_compliance"]:
                if key in results and isinstance(results[key], dict):
                    score = results[key].get("confidence_score", 0.0)
                    if score > 0:
                        scores.append(score)
            
            analysis.confidence_score = sum(scores) / len(scores) if scores else 0.0
            analysis.status = "completed"
            
            db.commit()
            db.refresh(analysis)
        return analysis
    
    @staticmethod
    def get_analysis_by_task_id(task_id: str, db: Session) -> Optional[AnalysisResult]:
        """Get analysis by task ID"""
        return db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    
    @staticmethod
    def get_recent_analyses(limit: int = 10, db: Session = None) -> List[AnalysisResult]:
        """Get recent analysis results"""
        return db.query(AnalysisResult).order_by(AnalysisResult.upload_time.desc()).limit(limit).all()
    
    @staticmethod
    def get_analysis_statistics(db: Session) -> Dict[str, Any]:
        """Get overall analysis statistics"""
        total_analyses = db.query(AnalysisResult).count()
        completed_analyses = db.query(AnalysisResult).filter(AnalysisResult.status == "completed").count()
        failed_analyses = db.query(AnalysisResult).filter(AnalysisResult.status == "failed").count()
        
        avg_processing_time = db.query(AnalysisResult.processing_time_seconds).filter(
            AnalysisResult.processing_time_seconds.isnot(None)
        ).all()
        
        avg_time = sum(t[0] for t in avg_processing_time) / len(avg_processing_time) if avg_processing_time else 0
        
        return {
            "total_analyses": total_analyses,
            "completed_analyses": completed_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0,
            "average_processing_time": round(avg_time, 2)
        }