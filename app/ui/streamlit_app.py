import os
import streamlit as st
import requests

st.set_page_config(
    page_title="FinAgent Ops - Compliance Portal",
    page_icon="📊",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://localhost:8002")

st.title("📊 Enterprise Financial Document Compliance Agent")
st.caption("Powered by FastAPI, LangGraph Multi-Agent Orchestration, and MLflow")

st.sidebar.header("System Status")
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    if health_resp.status_code == 200:
        st.sidebar.success("Backend API: Online")
    else:
        st.sidebar.error("Backend API: Error")
except Exception:
    st.sidebar.error("Backend API: Offline")

st.markdown("---")

doc_text = st.text_area(
    "Paste Financial Statement / SEC Filing Text below:",
    height=250,
    placeholder="Example: Acme Corp reports Q3 revenue growth of -2.5% YoY with a net margin of 8%. Primary risk factors include supply chain disruptions in APAC..."
)

if st.button("Run Multi-Agent Audit", type="primary"):
    if not doc_text.strip():
        st.warning("Please paste valid financial text to analyze.")
    else:
        with st.spinner("Executing extraction, audit, and reporting agents..."):
            try:
                response = requests.post(
                    f"{API_URL}/analyze",
                    json={"text": doc_text},
                    timeout=120
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Audit Complete in {data.get('execution_time_seconds')}s")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Structured Financial Data")
                        extracted = data.get("extracted_data", {})
                        
                        # High-visibility metric cards
                        m1, m2 = st.columns(2)
                        m1.metric("Company Name", extracted.get("company_name", "N/A"))
                        m2.metric("Revenue Growth", extracted.get("revenue_growth", "N/A"))
                        
                        st.metric("Net Profit Margin", extracted.get("net_margin", "N/A"))
                        
                        st.write("**Identified Risk Factors:**")
                        risks = extracted.get("flagged_risks", [])
                        if risks:
                            for risk in risks:
                                st.markdown(f"- {risk}")
                        else:
                            st.write("No specific risks extracted.")
                        
                    with col2:
                        st.subheader("⚠️ Regulatory Compliance Audit")
                        issues = data.get("compliance_issues", [])
                        if issues:
                            for issue in issues:
                                st.warning(issue)
                        else:
                            st.success("No critical compliance violations identified.")
                            
                    st.markdown("---")
                    st.markdown("### 📝 Executive Summary")
                    st.markdown(data.get("final_report", "No report generated."))
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Failed to communicate with API backend: {str(e)}")