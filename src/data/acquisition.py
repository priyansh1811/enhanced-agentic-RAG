"""Data acquisition module for downloading SEC filings."""

import os
from typing import List, Dict, Any
from sec_edgar_downloader import Downloader
from ..config import get_settings


class DataAcquisition:
    """Handles downloading of SEC filings and other financial documents."""
    
    def __init__(self):
        self.settings = get_settings()
        self.downloader = Downloader(
            self.settings.company_name,
            self.settings.company_email
        )
    
    def download_sec_filings(
        self, 
        ticker: str = None,
        filing_types: List[str] = None,
        limits: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Download SEC filings for a given ticker.
        
        Args:
            ticker: Company ticker symbol (defaults to settings)
            filing_types: List of filing types to download
            limits: Dictionary mapping filing types to download limits
            
        Returns:
            Dictionary with download results and file paths
        """
        if ticker is None:
            ticker = self.settings.company_ticker
            
        if filing_types is None:
            filing_types = ["10-K", "10-Q", "8-K", "DEF 14A"]
            
        if limits is None:
            limits = {"10-K": 1, "10-Q": 4, "8-K": 1, "DEF 14A": 1}
        
        results = {
            "ticker": ticker,
            "downloads": {},
            "file_paths": []
        }
        
        for filing_type in filing_types:
            try:
                limit = limits.get(filing_type, 1)
                print(f"Downloading {filing_type} filings for {ticker} (limit: {limit})")
                
                # Download filings
                self.downloader.get(filing_type, ticker, limit=limit)
                
                # Get the download directory
                download_dir = f"sec-edgar-filings/{ticker}/{filing_type}"
                
                if os.path.exists(download_dir):
                    # Find all HTML files in the directory
                    html_files = []
                    for root, dirs, files in os.walk(download_dir):
                        for file in files:
                            if file.endswith('.html'):
                                html_files.append(os.path.join(root, file))
                    
                    results["downloads"][filing_type] = {
                        "count": len(html_files),
                        "files": html_files
                    }
                    results["file_paths"].extend(html_files)
                    
                    print(f"  - Downloaded {len(html_files)} {filing_type} files")
                else:
                    print(f"  - No {filing_type} files found")
                    
            except Exception as e:
                print(f"Error downloading {filing_type}: {e}")
                results["downloads"][filing_type] = {"error": str(e)}
        
        return results
    
    def create_sample_dataset(self) -> str:
        """
        Create a sample financial dataset for testing.
        
        Returns:
            Path to the created CSV file
        """
        import pandas as pd
        
        # Sample financial data
        data = {
            "metric": [
                "Revenue", "Operating Income", "Net Income", "Total Assets",
                "Total Liabilities", "Shareholders Equity", "Cash and Equivalents",
                "Research and Development", "Sales and Marketing", "General and Administrative"
            ],
            "2021": [168.1, 69.9, 61.3, 333.8, 191.8, 142.0, 14.2, 20.7, 20.0, 4.8],
            "2022": [198.3, 83.4, 72.7, 364.8, 191.8, 173.0, 14.4, 24.5, 22.1, 5.2],
            "2023": [211.9, 88.5, 83.4, 411.9, 205.1, 206.8, 15.0, 28.9, 24.1, 5.8]
        }
        
        df = pd.DataFrame(data)
        csv_path = "data/raw/sample_financial_data.csv"
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
        
        print(f"Created sample dataset at {csv_path}")
        return csv_path
