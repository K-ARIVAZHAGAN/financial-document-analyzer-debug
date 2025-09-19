# Celery Worker Tasks for Financial Document Analysis
# This module contains all background tasks that can be executed by Celery workers

import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import Celery
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from celery_config import celery_app
from database import DatabaseManager, SessionLocal, AnalysisResult
from agents import FinancialAnalysisCrew
from tools import PDFExtractorTool

# Configure logging
logger = get_task_logger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_document(self, task_id: str, file_content: bytes, filename: str, file_size: int) -> Dict[str, Any]:
    """
    Background task to analyze financial documents
    
    Args:
        task_id: Unique task identifier
        file_content: PDF file content as bytes
        filename: Original filename
        file_size: File size in bytes
    
    Returns:
        Dict containing analysis results
    """
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Starting analysis for task {task_id}, file: {filename}")
        
        # Update status to processing
        DatabaseManager.update_analysis_status(task_id, "processing", db)
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize tools and crew
            pdf_tool = PDFExtractorTool()
            crew = FinancialAnalysisCrew()
            
            logger.info(f"Extracting text from PDF: {filename}")
            
            # Extract text from PDF
            extracted_text = pdf_tool.extract_text(temp_file_path)
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                raise ValueError("Insufficient text extracted from PDF. Document may be corrupted or contain mostly images.")
            
            logger.info(f"Successfully extracted {len(extracted_text)} characters from {filename}")
            
            # Run financial analysis
            logger.info(f"Starting financial analysis for task {task_id}")
            analysis_results = crew.analyze_document(extracted_text)
            
            if not analysis_results:
                raise ValueError("Financial analysis returned empty results")
            
            # Parse and structure results
            structured_results = _structure_analysis_results(analysis_results)
            
            # Save results to database
            DatabaseManager.save_analysis_results(task_id, structured_results, db)
            
            logger.info(f"Successfully completed analysis for task {task_id}")
            
            return {
                "status": "completed",
                "task_id": task_id,
                "filename": filename,
                "results": structured_results,
                "processing_time": (datetime.utcnow() - 
                    db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first().analysis_start_time
                ).total_seconds()
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as exc:
        logger.error(f"Analysis failed for task {task_id}: {str(exc)}")
        
        # Update status to failed
        DatabaseManager.update_analysis_status(task_id, "failed", db, error_message=str(exc))
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        
        return {
            "status": "failed",
            "task_id": task_id,
            "filename": filename,
            "error": str(exc),
            "retries": self.request.retries
        }
    
    finally:
        db.close()

@celery_app.task
def cleanup_old_results() -> Dict[str, Any]:
    """
    Periodic task to clean up old analysis results
    Removes results older than 7 days to keep database size manageable
    """
    db: Session = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        # Find old records
        old_records = db.query(AnalysisResult).filter(
            AnalysisResult.upload_time < cutoff_date
        ).all()
        
        deleted_count = len(old_records)
        
        # Delete old records
        for record in old_records:
            db.delete(record)
        
        db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old analysis results")
        
        return {
            "status": "completed",
            "deleted_records": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        db.rollback()
        return {
            "status": "failed",
            "error": str(exc)
        }
    
    finally:
        db.close()

@celery_app.task
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the current status of a task
    
    Args:
        task_id: Celery task ID
    
    Returns:
        Dict containing task status and results if available
    """
    db: Session = SessionLocal()
    
    try:
        # Get from database
        analysis = DatabaseManager.get_analysis_by_task_id(task_id, db)
        
        if not analysis:
            return {
                "status": "not_found",
                "task_id": task_id,
                "message": "Task not found in database"
            }
        
        # Get Celery task info
        celery_task = celery_app.AsyncResult(task_id)
        
        result = {
            "status": analysis.status,
            "task_id": task_id,
            "filename": analysis.filename,
            "upload_time": analysis.upload_time.isoformat() if analysis.upload_time else None,
            "celery_status": celery_task.status,
        }
        
        if analysis.status == "completed":
            result["results"] = analysis.to_dict()
        elif analysis.status == "failed":
            result["error"] = analysis.error_message
        elif analysis.status == "processing":
            result["progress"] = "Analysis in progress..."
        
        return result
    
    except Exception as exc:
        logger.error(f"Error getting task status for {task_id}: {str(exc)}")
        return {
            "status": "error",
            "task_id": task_id,
            "error": str(exc)
        }
    
    finally:
        db.close()

def _structure_analysis_results(raw_results: str) -> Dict[str, Any]:
    """
    Structure the raw analysis results into organized components
    
    Args:
        raw_results: Raw text results from CrewAI analysis
    
    Returns:
        Structured dictionary with analysis components
    """
    try:
        # Parse the results (assuming they come back as structured text)
        # This is a simplified parser - you may need to adjust based on actual output format
        
        structured = {
            "financial_summary": {
                "content": raw_results.get("financial_summary", ""),
                "confidence_score": 0.85,
                "timestamp": datetime.utcnow().isoformat()
            },
            "risk_assessment": {
                "content": raw_results.get("risk_assessment", ""),
                "confidence_score": 0.80,
                "timestamp": datetime.utcnow().isoformat()
            },
            "investment_advice": {
                "content": raw_results.get("investment_advice", ""),
                "confidence_score": 0.75,
                "timestamp": datetime.utcnow().isoformat()
            },
            "regulatory_compliance": {
                "content": raw_results.get("regulatory_compliance", ""),
                "confidence_score": 0.90,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        # If raw_results is a string, try to extract sections
        if isinstance(raw_results, str):
            # Simple section extraction based on keywords
            sections = {
                "financial_summary": _extract_section(raw_results, ["financial summary", "summary", "overview"]),
                "risk_assessment": _extract_section(raw_results, ["risk", "risks", "risk assessment"]),
                "investment_advice": _extract_section(raw_results, ["investment", "recommendation", "advice"]),
                "regulatory_compliance": _extract_section(raw_results, ["regulatory", "compliance", "legal"])
            }
            
            for key, content in sections.items():
                if content:
                    structured[key]["content"] = content
        
        return structured
    
    except Exception as exc:
        logger.error(f"Error structuring results: {str(exc)}")
        # Return basic structure with raw content
        return {
            "financial_summary": {
                "content": str(raw_results),
                "confidence_score": 0.5,
                "timestamp": datetime.utcnow().isoformat()
            },
            "risk_assessment": {"content": "", "confidence_score": 0.0, "timestamp": datetime.utcnow().isoformat()},
            "investment_advice": {"content": "", "confidence_score": 0.0, "timestamp": datetime.utcnow().isoformat()},
            "regulatory_compliance": {"content": "", "confidence_score": 0.0, "timestamp": datetime.utcnow().isoformat()}
        }

def _extract_section(text: str, keywords: list) -> str:
    """Extract section content based on keywords"""
    text_lower = text.lower()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        start_idx = text_lower.find(keyword_lower)
        
        if start_idx != -1:
            # Find the end of the section (next major heading or end of text)
            remaining_text = text[start_idx:]
            
            # Simple section extraction - take next 500 characters
            return remaining_text[:500].strip()
    
    return ""