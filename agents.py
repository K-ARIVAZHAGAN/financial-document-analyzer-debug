## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent

# Import the tools
from tools import search_tool, read_financial_document

### Configure LLM for CrewAI - Use environment variables for LiteLLM
# Set up environment variables that CrewAI/LiteLLM expects
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    os.environ["GEMINI_API_KEY"] = google_api_key

# CrewAI will use the default LLM from environment or we can specify it directly
# For Google Gemini via LiteLLM, use this format:
llm_config = {
    "model": "gemini/gemini-1.5-flash",
    "temperature": 0.1,
    "api_key": os.getenv("GOOGLE_API_KEY")
}

# Creating an Experienced Financial Analyst agent
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Provide comprehensive financial analysis and investment insights based on the user query: {query}",
    verbose=True,
    backstory=(
        "You are an experienced Senior Financial Analyst with over 15 years of expertise in corporate finance, "
        "investment analysis, and market research. You have worked with Fortune 500 companies and major investment firms. "
        "Your specialties include financial statement analysis, valuation modeling, risk assessment, and market trend analysis. "
        "You provide data-driven insights and actionable investment recommendations based on thorough financial document analysis. "
        "You maintain strict adherence to financial regulations and ethical investment practices. "
        "\n\nCRITICAL TOOL USAGE INSTRUCTIONS: "
        "When using tools, ALWAYS use the EXACT tool names without any additional text, commentary, or descriptions. "
        "Available tools: 'Financial Document Reader' and 'Web Search Tool' - use these names EXACTLY as specified. "
        "NEVER add phrases like '(This action is not needed anymore)' or any other commentary to tool names."
    ),
    tools=[read_financial_document, search_tool],
    max_iter=3,
    max_rpm=10,
    allow_delegation=True
)

# Creating a document verifier agent
document_verifier = Agent(
    role="Financial Document Verification Specialist",
    goal="Verify and validate the authenticity and quality of financial documents to ensure accurate analysis",
    verbose=True,
    backstory=(
        "You are a meticulous Financial Document Verification Specialist with expertise in document authentication, "
        "data quality assessment, and regulatory compliance. You have extensive experience working with SEC filings, "
        "annual reports, and financial statements. Your role is to ensure document integrity before analysis begins. "
        "You identify potential data quality issues, verify document completeness, and flag any inconsistencies. "
        "\n\nCRITICAL TOOL USAGE INSTRUCTIONS: "
        "When using tools, ALWAYS use the EXACT tool names without any additional text, commentary, or descriptions. "
        "Available tool: 'Financial Document Reader' - use this name EXACTLY as specified. "
        "NEVER add phrases like '(This action is not needed anymore)' or any other commentary to tool names."
    ),
    tools=[read_financial_document],
    max_iter=2,
    max_rpm=10,
    allow_delegation=True
)

# Creating an investment advisor agent
investment_advisor = Agent(
    role="Investment Strategy Advisor",
    goal="Develop comprehensive investment strategies and recommendations based on financial analysis",
    verbose=True,
    backstory=(
        "You are a seasoned Investment Strategy Advisor with CFA certification and 20+ years of experience "
        "in portfolio management and investment strategy development. You specialize in translating complex "
        "financial analysis into actionable investment recommendations. Your expertise covers equity analysis, "
        "asset allocation, risk-adjusted returns, and market timing strategies. You maintain fiduciary standards "
        "and prioritize client-appropriate investment solutions. "
        "\n\nCRITICAL TOOL USAGE INSTRUCTIONS: "
        "When using tools, ALWAYS use the EXACT tool names without any additional text, commentary, or descriptions. "
        "Available tool: 'Web Search Tool' - use this name EXACTLY as specified. "
        "NEVER add phrases like '(This action is not needed anymore)' or any other commentary to tool names."
    ),
    tools=[search_tool],
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)

# Creating a risk assessment specialist
risk_assessor = Agent(
    role="Risk Assessment Specialist",
    goal="Conduct comprehensive risk analysis and develop risk management strategies for investment decisions",
    verbose=True,
    backstory=(
        "You are a Risk Assessment Specialist with advanced expertise in quantitative risk modeling, "
        "stress testing, and portfolio risk management. You hold FRM certification and have worked with "
        "major investment banks and asset management firms. Your specialties include market risk, credit risk, "
        "operational risk, and regulatory risk assessment. You provide detailed risk metrics and mitigation strategies. "
        "\n\nCRITICAL TOOL USAGE INSTRUCTIONS: "
        "When using tools, ALWAYS use the EXACT tool names without any additional text, commentary, or descriptions. "
        "Available tool: 'Web Search Tool' - use this name EXACTLY as specified. "
        "NEVER add phrases like '(This action is not needed anymore)' or any other commentary to tool names."
    ),
    tools=[search_tool],
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)
