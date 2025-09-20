import os
import uuid

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from crewai import Crew, Process
from agents import financial_analyst, document_verifier, investment_advisor, risk_assessor
from task import financial_analysis_task, document_verification_task, investment_analysis_task, risk_assessment_task

app = FastAPI(title="Financial Document Analyzer", version="1.0.0")


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
        "version": "1.0.0",
        "status": "healthy"
    }


@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(default="Provide a comprehensive financial analysis with investment insights and risk assessment")
):
    """Analyze financial document and provide comprehensive investment recommendations"""

    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
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
            "file_id": file_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Clean up uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                # Log the error instead of silently ignoring
                print(f"Warning: Could not remove temporary file {file_path}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
