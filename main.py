from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
import uuid
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

# Original imports
from crewai import Crew, Process
from agents import financial_analyst, document_verifier, investment_advisor, risk_assessor
from task import financial_analysis_task, document_verification_task, investment_analysis_task, risk_assessment_task

# New imports for queue and database
from database import get_db, create_tables, DatabaseManager, AnalysisResult
from worker_tasks import analyze_document, get_task_status
from celery_config import celery_app

app = FastAPI(
    title="Financial Document Analyzer", 
    version="2.0.0",
    description="Advanced Financial Document Analysis with Queue Processing and Database Storage"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables and check connections"""
    try:
        create_tables()
        print("✅ Database tables created successfully")
        
        # Check Redis connection
        celery_app.control.ping(timeout=1)
        print("✅ Redis/Celery connection successful")
    except Exception as e:
        print(f"⚠️ Startup warning: {e}")

def execute_financial_analysis(query: str, file_path: str = "data/TSLA-Q2-2025-Update.pdf"):
    """Execute the complete financial analysis workflow using CrewAI"""
    try:
        financial_crew = Crew(
            agents=[document_verifier, financial_analyst, investment_advisor, risk_assessor],
            tasks=[document_verification_task, financial_analysis_task, investment_analysis_task, risk_assessment_task],
            process=Process.sequential,
            verbose=True
        )
        
        inputs = {
            'query': query,
            'file_path': file_path
        }
        
        result = financial_crew.kickoff(inputs=inputs)
        return result
    
    except Exception as e:
        raise Exception(f"Crew execution failed: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial Document Analyzer API is running",
        "version": "2.0.0",
        "status": "healthy",
        "features": ["Queue Processing", "Database Storage", "Background Analysis"]
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    try:
        # Check database
        stats = DatabaseManager.get_analysis_statistics(db)
        
        # Check Celery
        celery_stats = celery_app.control.inspect().stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "queue_system": "active" if celery_stats else "inactive",
            "analysis_statistics": stats
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/analyze")
async def analyze_document_async(
    file: UploadFile = File(...),
    query: str = Form(default="Provide a comprehensive financial analysis with investment insights and risk assessment"),
    db: Session = Depends(get_db)
):
    """Analyze financial document using background queue processing"""
    
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create database record
        analysis_record = DatabaseManager.create_analysis_record(
            task_id=task_id,
            filename=file.filename,
            file_size=file_size,
            db=db
        )
        
        # Submit to queue
        task = analyze_document.delay(task_id, file_content, file.filename, file_size)
        
        return {
            "status": "accepted",
            "message": "Document submitted for analysis",
            "task_id": task_id,
            "filename": file.filename,
            "file_size": file_size,
            "estimated_completion": "2-5 minutes",
            "check_status_url": f"/status/{task_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")

@app.get("/status/{task_id}")
async def get_analysis_status(task_id: str, db: Session = Depends(get_db)):
    """Get the status of an analysis task"""
    
    analysis = DatabaseManager.get_analysis_by_task_id(task_id, db)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get Celery task status
    celery_task = celery_app.AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": analysis.status,
        "filename": analysis.filename,
        "upload_time": analysis.upload_time.isoformat() if analysis.upload_time else None,
        "celery_status": celery_task.status
    }
    
    if analysis.status == "completed":
        response["results"] = analysis.to_dict()
        response["download_url"] = f"/results/{task_id}"
    elif analysis.status == "failed":
        response["error"] = analysis.error_message
    elif analysis.status == "processing":
        if analysis.analysis_start_time:
            processing_time = (datetime.utcnow() - analysis.analysis_start_time).total_seconds()
            response["processing_time_seconds"] = round(processing_time, 1)
        response["progress"] = "Analysis in progress..."
    
    return response

@app.get("/results/{task_id}")
async def get_analysis_results(task_id: str, db: Session = Depends(get_db)):
    """Get complete analysis results"""
    
    analysis = DatabaseManager.get_analysis_by_task_id(task_id, db)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    if analysis.status != "completed":
        raise HTTPException(status_code=400, detail=f"Analysis not completed. Current status: {analysis.status}")
    
    return analysis.to_dict()

@app.get("/history")
async def get_analysis_history(
    limit: int = 10,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get analysis history"""
    
    query = db.query(AnalysisResult)
    
    if status:
        query = query.filter(AnalysisResult.status == status)
    
    analyses = query.order_by(AnalysisResult.upload_time.desc()).limit(limit).all()
    
    return {
        "total": len(analyses),
        "limit": limit,
        "status_filter": status,
        "analyses": [
            {
                "task_id": a.task_id,
                "filename": a.filename,
                "status": a.status,
                "upload_time": a.upload_time.isoformat() if a.upload_time else None,
                "processing_time_seconds": a.processing_time_seconds,
                "confidence_score": a.confidence_score
            }
            for a in analyses
        ]
    }

@app.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """Get system statistics"""
    
    stats = DatabaseManager.get_analysis_statistics(db)
    
    # Add queue statistics
    try:
        celery_inspect = celery_app.control.inspect()
        active_tasks = celery_inspect.active()
        scheduled_tasks = celery_inspect.scheduled()
        
        queue_stats = {
            "active_tasks": sum(len(tasks) for tasks in (active_tasks or {}).values()),
            "scheduled_tasks": sum(len(tasks) for tasks in (scheduled_tasks or {}).values()),
            "workers_online": len(active_tasks) if active_tasks else 0
        }
    except Exception:
        queue_stats = {
            "active_tasks": 0,
            "scheduled_tasks": 0,
            "workers_online": 0,
            "error": "Could not connect to queue system"
        }
    
    return {
        "database_statistics": stats,
        "queue_statistics": queue_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

# Legacy synchronous endpoint (kept for backward compatibility)
@app.post("/analyze-sync")
async def analyze_document_sync(
    file: UploadFile = File(...),
    query: str = Form(default="Provide a comprehensive financial analysis with investment insights and risk assessment")
):
    """Synchronous analysis endpoint (legacy - use /analyze for better performance)"""
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = f"data/uploaded_{file_id}.pdf"
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Validate and sanitize query
        if not query or query.strip() == "":
            query = "Provide a comprehensive financial analysis with investment insights and risk assessment"
        
        query = query.strip()[:500]  # Limit query length
        
        # Execute financial analysis
        result = execute_financial_analysis(query=query, file_path=file_path)
        
        return {
            "status": "success",
            "query": query,
            "analysis": str(result),
            "file_processed": file.filename,
            "file_id": file_id,
            "warning": "This is a synchronous endpoint. Use /analyze for better performance with queue processing."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignore cleanup errors

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)