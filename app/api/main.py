import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
from app.agents.financial_agent import app_agent

app = FastAPI(
    title="FinAgent-Ops API",
    description="Production API for Financial Document Analysis & Compliance Agent",
    version="1.0.0"
)

# Set MLflow tracking URI to custom port 5003
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5003")
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment("FinAgent_Compliance_Pipeline")

class AnalyzeRequest(BaseModel):
    text: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "finagent-api"}

@app.post("/analyze")
async def analyze_document(request: AnalyzeRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Document text cannot be empty.")
    
    start_time = time.time()
    
    with mlflow.start_run(run_name="LangGraph_Execution"):
        mlflow.log_param("document_char_length", len(request.text))
        
        try:
            result = app_agent.invoke({"document_text": request.text})
            execution_time = time.time() - start_time
            
            mlflow.log_metric("latency_seconds", execution_time)
            mlflow.log_metric("compliance_issues_count", len(result.get("compliance_issues", [])))
            
            return {
                "status": "success",
                "execution_time_seconds": round(execution_time, 3),
                "extracted_data": result.get("extracted_data"),
                "compliance_issues": result.get("compliance_issues"),
                "final_report": result.get("final_report")
            }
        except Exception as e:
            mlflow.log_param("error", str(e))
            raise HTTPException(status_code=500, detail=f"Agent Execution Failed: {str(e)}")