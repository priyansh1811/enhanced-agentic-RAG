"""Specialist tools for the Archon agent."""

import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.tools.tavily_search import TavilySearchResults

from ..data.storage import VectorStore
from ..config import get_settings


class LibrarianTool:
    """Multi-step RAG tool for document retrieval and analysis."""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.settings = get_settings()
    
    @tool
    def librarian_tool(self, query: str) -> str:
        """
        Use this tool to search through financial documents and SEC filings.
        It can find specific information, quotes, or data points from Microsoft's reports.
        Best for questions about specific facts, quotes, or information contained in documents.
        """
        print(f"\n-- Librarian Tool Called with query: '{query}' --")
        
        # Step 1: Initial retrieval
        print("  - Step 1: Initial retrieval")
        initial_results = self.vector_store.search(query, limit=10)
        
        if not initial_results:
            return "No relevant documents found for your query."
        
        # Step 2: Re-ranking with cross-encoder
        print("  - Step 2: Re-ranking results")
        reranked_results = sorted(initial_results, key=lambda x: x['cross_score'], reverse=True)
        
        # Step 3: Select top results
        print("  - Step 3: Selecting top 5 results")
        top_results = reranked_results[:5]
        
        # Format results
        formatted_results = []
        for i, result in enumerate(top_results, 1):
            formatted_result = {
                "rank": i,
                "content": result["content"][:500] + "..." if len(result["content"]) > 500 else result["content"],
                "source": result["source_file"],
                "relevance_score": round(result["final_score"], 3),
                "summary": result["enriched_metadata"]["summary"],
                "keywords": result["enriched_metadata"]["keywords"]
            }
            formatted_results.append(formatted_result)
        
        return f"Found {len(formatted_results)} relevant documents:\n" + \
               "\n".join([f"{r['rank']}. {r['summary']} (Score: {r['relevance_score']})" 
                         for r in formatted_results])


class AnalystSQLTool:
    """SQL-based tool for querying structured financial data."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0,
            api_key=self.settings.openai_api_key
        )
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        self.agent_executor = create_sql_agent(
            llm=self.llm, 
            db=self.db, 
            agent_type="openai-tools", 
            verbose=True
        )
    
    @tool
    def analyst_sql_tool(self, query: str) -> str:
        """
        This tool is an expert financial analyst that can query a database with Microsoft's revenue and net income data.
        Use it for questions about specific financial numbers for a single time period (e.g., 'What was the revenue in Q4 2023?').
        For trends over time, use the analyst_trend_tool.
        The input should be a clear, specific question about financial data.
        """
        print(f"\n-- Analyst SQL Tool Called with query: '{query}' --")
        result = self.agent_executor.invoke({"input": query})
        return result['output']


class AnalystTrendTool:
    """Advanced tool for trend analysis over multiple time periods."""
    
    def __init__(self, db_path: str, table_name: str = "revenue_summary"):
        self.db_path = db_path
        self.table_name = table_name
    
    @tool
    def analyst_trend_tool(self, query: str) -> str:
        """
        Use this tool to analyze financial data over multiple time periods to identify trends, growth rates, and patterns.
        It is best for questions like 'Analyze revenue trend over the last 8 quarters' or 'Show me the net income growth YoY'.
        It provides a narrative summary of trends, not just raw numbers.
        """
        print(f"\n-- Analyst Trend Tool Called with query: '{query}' --")
        
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            df_trends = pd.read_sql_query(
                f"SELECT * FROM {self.table_name} ORDER BY year, quarter", 
                conn
            )
            conn.close()
            
            if df_trends.empty:
                return "No data available for trend analysis."
            
            # Create period index
            df_trends['period'] = df_trends['year'].astype(str) + '-' + df_trends['quarter']
            df_trends.set_index('period', inplace=True)
            
            # Analyze revenue trends
            metric = 'revenue_usd_billions'
            df_trends['QoQ_Growth'] = df_trends[metric].pct_change()
            df_trends['YoY_Growth'] = df_trends[metric].pct_change(4)  # 4 quarters in a year
            
            latest_period = df_trends.index[-1]
            start_period = df_trends.index[0]
            latest_val = df_trends.loc[latest_period, metric]
            start_val = df_trends.loc[start_period, metric]
            latest_qoq = df_trends.loc[latest_period, 'QoQ_Growth']
            latest_yoy = df_trends.loc[latest_period, 'YoY_Growth']
            
            # Calculate overall growth
            total_growth = ((latest_val - start_val) / start_val) * 100
            
            # Generate trend summary
            trend_summary = f"""
            Revenue Trend Analysis ({start_period} to {latest_period}):
            
            • Starting Value: ${start_val:.1f}B ({start_period})
            • Latest Value: ${latest_val:.1f}B ({latest_period})
            • Total Growth: {total_growth:.1f}%
            
            Recent Performance:
            • Quarter-over-Quarter Growth: {latest_qoq*100:.1f}%
            • Year-over-Year Growth: {latest_yoy*100:.1f}%
            
            Trend Analysis:
            """
            
            # Add trend interpretation
            if latest_qoq > 0.05:
                trend_summary += "• Strong quarterly growth momentum\n"
            elif latest_qoq > 0:
                trend_summary += "• Moderate quarterly growth\n"
            else:
                trend_summary += "• Quarterly decline detected\n"
            
            if latest_yoy > 0.1:
                trend_summary += "• Strong year-over-year growth\n"
            elif latest_yoy > 0:
                trend_summary += "• Positive year-over-year growth\n"
            else:
                trend_summary += "• Year-over-year decline\n"
            
            return trend_summary.strip()
            
        except Exception as e:
            return f"Error analyzing trends: {str(e)}"


class ScoutTool:
    """Tool for live web data and news retrieval."""
    
    def __init__(self):
        self.settings = get_settings()
        self.tavily_search = TavilySearchResults(
            api_key=self.settings.tavily_api_key,
            max_results=5
        )
    
    @tool
    def scout_tool(self, query: str) -> str:
        """
        Use this tool to search for recent news, market updates, or live information about Microsoft.
        It searches the web for current information that might not be in the document database.
        Best for questions about recent events, news, or current market conditions.
        """
        print(f"\n-- Scout Tool Called with query: '{query}' --")
        
        try:
            results = self.tavily_search.invoke(query)
            
            if not results:
                return "No recent information found for your query."
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_result = {
                    "title": result.get("title", "No title"),
                    "url": result.get("url", "No URL"),
                    "content": result.get("content", "No content")[:300] + "...",
                    "published_date": result.get("published_date", "Unknown date")
                }
                formatted_results.append(formatted_result)
            
            return f"Found {len(formatted_results)} recent results:\n" + \
                   "\n".join([f"{i}. {r['title']} - {r['published_date']}\n   {r['content']}" 
                             for i, r in enumerate(formatted_results, 1)])
            
        except Exception as e:
            return f"Error searching for recent information: {str(e)}"
