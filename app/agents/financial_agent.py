import os
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

# 1. Define Graph State Schema
class AgentState(TypedDict):
    document_text: str
    extracted_data: Dict[str, Any]
    compliance_issues: List[str]
    final_report: str

class FinancialMetrics(BaseModel):
    company_name: str = Field(description="Name of the company")
    revenue_growth: str = Field(description="Year over Year revenue growth rate")
    net_margin: str = Field(description="Net profit margin percentage")
    flagged_risks: List[str] = Field(description="Key operational or market risk factors mentioned")

def get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key or not key.strip():
        raise ValueError("Neither GEMINI_API_KEY nor GOOGLE_API_KEY environment variable is set.")
    return key.strip()

def get_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=get_api_key(),
        temperature=0,
        transport="rest",       # Forces HTTP REST transport to prevent gRPC streaming deadlocks
        request_timeout=30      # Fails fast at 30 seconds rather than hanging 120s
    )

# Node 1: Financial Extraction Agent
def extract_financials(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    structured_llm = llm.with_structured_output(FinancialMetrics)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert financial analyst. Extract key metrics and risk factors from the financial document."),
        ("human", "{document_text}")
    ])
    
    chain = prompt | structured_llm
    result: FinancialMetrics = chain.invoke({"document_text": state["document_text"]})
    return {"extracted_data": result.model_dump()}

# Node 2: Fast & Deterministic Compliance Auditor Agent
def audit_compliance(state: AgentState) -> Dict[str, Any]:
    extracted = state.get("extracted_data", {})
    issues = []
    
    # 1. Revenue growth check
    growth_str = str(extracted.get("revenue_growth", "0%")).replace("%", "").strip()
    try:
        growth_val = float(growth_str)
        if growth_val < 0:
            issues.append(f"Warning: Negative YoY revenue growth detected ({extracted.get('revenue_growth')}). Requires management audit note.")
    except ValueError:
        pass

    # 2. ESG compliance disclosure check
    risks = extracted.get("flagged_risks", [])
    risk_text = " ".join([str(r) for r in risks]).upper()
    if "ESG" not in risk_text and "ENVIRONMENTAL" not in risk_text and "CLIMATE" not in risk_text:
        issues.append("Compliance Risk: Missing mandatory ESG operational risk disclosure under SEC Item 1A.")
        
    return {"compliance_issues": issues}

# Node 3: Executive Report Generator Agent
# app/agents/financial_agent.py

def generate_report(state: AgentState) -> Dict[str, Any]:
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Synthesize financial data and compliance audit findings into a concise executive summary markdown report."),
        ("human", "Extracted Data: {extracted_data}\nCompliance Issues: {compliance_issues}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "extracted_data": state["extracted_data"],
        "compliance_issues": state["compliance_issues"]
    })
    
    # Extract clean text string from response object
    if isinstance(response.content, list):
        report_text = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content])
    else:
        report_text = str(response.content)

    return {"final_report": report_text}

# Build LangGraph workflow
workflow = StateGraph(AgentState)
workflow.add_node("extractor", extract_financials)
workflow.add_node("auditor", audit_compliance)
workflow.add_node("reporter", generate_report)

workflow.set_entry_point("extractor")
workflow.add_edge("extractor", "auditor")
workflow.add_edge("auditor", "reporter")
workflow.add_edge("reporter", END)

app_agent = workflow.compile()