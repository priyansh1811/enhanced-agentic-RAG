"""Specialist agents for different analytical tasks."""

from typing import List, Dict, Any
from .tools import LibrarianTool, AnalystSQLTool, AnalystTrendTool, ScoutTool
from .reasoning_engine import ReasoningEngine
from ..data.storage import VectorStore
from ..config import get_settings


class SpecialistAgents:
    """Collection of specialist agents for different analytical tasks."""
    
    def __init__(self, vector_store: VectorStore, db_path: str):
        self.settings = get_settings()
        self.vector_store = vector_store
        
        # Initialize specialist tools
        self.librarian = LibrarianTool(vector_store)
        self.analyst_sql = AnalystSQLTool(db_path)
        self.analyst_trend = AnalystTrendTool(db_path)
        self.scout = ScoutTool()
        
        # Create reasoning engine with all tools
        self.tools = [
            self.librarian.librarian_tool,
            self.analyst_sql.analyst_sql_tool,
            self.analyst_trend.analyst_trend_tool,
            self.scout.scout_tool
        ]
        
        self.reasoning_engine = ReasoningEngine(self.tools)
    
    def analyze_request(self, request: str) -> Dict[str, Any]:
        """
        Analyze a user request using the complete specialist agent system.
        
        Args:
            request: User's analytical request
            
        Returns:
            Complete analysis result with response and metadata
        """
        print(f"\n=== Archon Analysis: {request} ===")
        
        # Process through reasoning engine
        result = self.reasoning_engine.process_request(request)
        
        # Add metadata about the analysis
        result["analysis_metadata"] = {
            "tools_used": [step["tool"] for step in result.get("execution_steps", [])],
            "total_steps": len(result.get("execution_steps", [])),
            "verification_passed": all(
                v["confidence_score"] >= 3 
                for v in result.get("verification_history", [])
            ),
            "needs_clarification": result.get("clarification_question") is not None
        }
        
        return result
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get information about available specialist tools."""
        return [
            {
                "name": "librarian_tool",
                "description": "Search through financial documents and SEC filings",
                "best_for": "Specific facts, quotes, or information from documents"
            },
            {
                "name": "analyst_sql_tool", 
                "description": "Query structured financial data for specific numbers",
                "best_for": "Specific financial metrics for single time periods"
            },
            {
                "name": "analyst_trend_tool",
                "description": "Analyze trends and patterns over multiple time periods",
                "best_for": "Growth rates, trend analysis, and comparative metrics"
            },
            {
                "name": "scout_tool",
                "description": "Search for recent news and live information",
                "best_for": "Current events, recent news, and market updates"
            }
        ]
    
    def test_tools(self) -> Dict[str, Any]:
        """Test all specialist tools with sample queries."""
        test_queries = {
            "librarian_tool": "What are the main risks mentioned in Microsoft's annual report?",
            "analyst_sql_tool": "What was Microsoft's revenue in Q4 2023?",
            "analyst_trend_tool": "Analyze Microsoft's revenue growth over the last 8 quarters",
            "scout_tool": "What are the latest news about Microsoft's AI investments?"
        }
        
        results = {}
        for tool_name, query in test_queries.items():
            try:
                print(f"\n--- Testing {tool_name} ---")
                tool = next(tool for tool in self.tools if tool.name == tool_name)
                result = tool.invoke(query)
                results[tool_name] = {
                    "status": "success",
                    "query": query,
                    "result": result[:200] + "..." if len(result) > 200 else result
                }
            except Exception as e:
                results[tool_name] = {
                    "status": "error",
                    "query": query,
                    "error": str(e)
                }
        
        return results
