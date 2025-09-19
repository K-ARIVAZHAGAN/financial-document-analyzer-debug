## Importing libraries and files
from crewai import Task
from agents import financial_analyst, document_verifier, investment_advisor, risk_assessor
from tools import search_tool, read_financial_document

## Document verification task
document_verification_task = Task(
    description="""Verify and validate the financial document at {file_path}.
    
    Your tasks:
    1. Confirm the document exists and is readable
    2. Validate it contains financial information
    3. Check document structure and completeness
    4. Identify the type of financial document (annual report, quarterly filing, etc.)
    5. Flag any data quality issues or inconsistencies
    
    User query context: {query}""",

    expected_output="""A verification report containing:
    - Document validation status (Valid/Invalid)
    - Document type identification
    - Content summary overview
    - Data quality assessment
    - Any issues or warnings identified
    - Recommendation for proceeding with analysis""",

    agent=document_verifier,
    tools=[read_financial_document],
    async_execution=False,
)

## Main financial analysis task
financial_analysis_task = Task(
    description="""Conduct comprehensive financial analysis of the verified document to address: {query}
    
    Your analysis should include:
    1. Key financial metrics and ratios analysis
    2. Revenue, profitability, and cash flow trends
    3. Balance sheet strength and liquidity position
    4. Operational efficiency indicators
    5. Year-over-year and quarter-over-quarter comparisons
    6. Industry context and competitive positioning
    
    Use the document at: {file_path}""",

    expected_output="""Comprehensive financial analysis report with:
    - Executive summary of financial health
    - Detailed financial metrics analysis
    - Revenue and profitability assessment
    - Cash flow and liquidity analysis
    - Key financial ratios and trends
    - Comparative analysis (historical/industry)
    - Strengths and weaknesses identification
    - Supporting data and calculations""",

    agent=financial_analyst,
    tools=[read_financial_document, search_tool],
    async_execution=False,
)

## Investment analysis task
investment_analysis_task = Task(
    description="""Based on the financial analysis, provide investment recommendations addressing: {query}
    
    Your investment analysis should cover:
    1. Investment thesis and rationale
    2. Valuation assessment and price targets
    3. Growth prospects and catalysts
    4. Competitive advantages and moats
    5. Market opportunity and positioning
    6. Investment timeline and strategy recommendations
    
    Reference the financial document analysis and market research.""",

    expected_output="""Investment recommendation report including:
    - Clear investment recommendation (Buy/Hold/Sell)
    - Investment thesis and supporting rationale
    - Valuation analysis and price targets
    - Growth drivers and catalysts
    - Investment risks and mitigating factors
    - Recommended investment strategy and timeline
    - Portfolio allocation suggestions
    - Key metrics to monitor""",

    agent=investment_advisor,
    tools=[search_tool],
    async_execution=False,
)

## Risk assessment task
risk_assessment_task = Task(
    description="""Conduct comprehensive risk assessment for investment decision regarding: {query}
    
    Analyze the following risk categories:
    1. Market and systematic risks
    2. Company-specific and operational risks
    3. Financial and credit risks
    4. Regulatory and compliance risks
    5. ESG and sustainability risks
    6. Liquidity and concentration risks
    
    Provide risk mitigation strategies and monitoring frameworks.""",

    expected_output="""Risk assessment report containing:
    - Overall risk rating and classification
    - Detailed risk factor analysis by category
    - Quantitative risk metrics where applicable
    - Risk probability and impact assessment
    - Risk mitigation strategies and recommendations
    - Key risk indicators for ongoing monitoring
    - Stress testing scenarios
    - Risk-adjusted return projections""",

    agent=risk_assessor,
    tools=[search_tool],
    async_execution=False,
)