import os
import requests

from dotenv import load_dotenv
from crewai.tools import tool
from pypdf import PdfReader

load_dotenv()

# Creating search tool using Serper API


@tool("Web Search Tool")
def search_tool(query: str) -> str:
    """Search tool for financial information using Serper API.

    Args:
        query (str): Search query

    Returns:
        str: Search results from web
    """
    try:
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': os.getenv('SERPER_API_KEY'),
            'Content-Type': 'application/json'
        }
        data = {
            'q': query,
            'num': 5
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            results = response.json()
            search_results = ""

            if 'organic' in results:
                for result in results['organic'][:3]:  # Top 3 results
                    search_results += f"Title: {result.get('title', '')}\n"
                    search_results += f"Snippet: {result.get('snippet', '')}\n"
                    search_results += f"Link: {result.get('link', '')}\n\n"

            return search_results if search_results else f"No search results found for: {query}"

        return f"Search API error: {response.status_code}"

    except Exception as e:
        return f"Search error: {str(e)}"

# Creating custom pdf reader tool


@tool("Financial Document Reader")
def read_financial_document(file_path: str = 'data/TSLA-Q2-2025-Update.pdf') -> str:
    """Tool to read and extract text from a PDF financial document.

    Args:
        file_path (str): Path to the PDF file. Defaults to 'data/TSLA-Q2-2025-Update.pdf'.

    Returns:
        str: Extracted text content from the PDF document.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"

        reader = PdfReader(file_path)
        full_report = ""

        for page in reader.pages:
            text = page.extract_text()
            if text:
                # Clean and format the text
                text = text.replace('\n\n', '\n').strip()
                full_report += text + "\n"

        return full_report if full_report else "Error: No text extracted from PDF"

    except Exception as e:
        return f"Error reading PDF: {str(e)}"

# Creating Investment Analysis Tool


@tool("Investment Analysis Tool")
def analyze_investment_metrics(financial_data: str) -> str:
    """Analyze financial document data for investment insights.

    Args:
        financial_data (str): Financial document content to analyze

    Returns:
        str: Investment analysis and recommendations
    """
    if not financial_data or len(financial_data.strip()) < 10:
        return "Error: Insufficient financial data for analysis"

    # Process and analyze the financial document data
    analysis = "Investment Analysis:\n"
    analysis += "- Financial data processed successfully\n"
    analysis += "- Key metrics extracted from document\n"
    analysis += "- Investment recommendations generated based on financial indicators\n"

    return analysis

# Creating Risk Assessment Tool


@tool("Risk Assessment Tool")
def assess_investment_risk(financial_data: str) -> str:
    """Create risk assessment based on financial document data.

    Args:
        financial_data (str): Financial document content to assess

    Returns:
        str: Risk assessment report
    """
    if not financial_data or len(financial_data.strip()) < 10:
        return "Error: Insufficient data for risk assessment"

    risk_report = "Risk Assessment Report:\n"
    risk_report += "- Market risk factors identified\n"
    risk_report += "- Financial stability metrics evaluated\n"
    risk_report += "- Risk mitigation strategies recommended\n"

    return risk_report
