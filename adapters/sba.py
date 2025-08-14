import requests
import pandas as pd
import time
from typing import List, Dict, Any
from datetime import datetime
import os

class SBAAdapter:
    """Adapter for SBA loan data"""
    
    def __init__(self):
        self.base_url = "https://www.sba.gov/sites/default/files/data_files"
        self.api_key = os.getenv("SBA_API_KEY", "")
        self.rate_limit_delay = 1.0
        
    def fetch_loan_data(self, county_fips: str, fiscal_year: int = 2024) -> List[Dict[str, Any]]:
        """Fetch SBA loan data for a specific county"""
        try:
            # SBA provides CSV files with loan data
            # Try different file patterns that SBA uses
            file_patterns = [
                f"FOIA_-_7a_FY{fiscal_year}_asof_*.csv",
                f"FOIA_-_504_FY{fiscal_year}_asof_*.csv"
            ]
            
            results = []
            
            for pattern in file_patterns:
                try:
                    # Use a known file URL format for SBA data
                    if "7a" in pattern:
                        url = f"https://www.sba.gov/sites/default/files/data_files/FOIA_-_7a_FY{fiscal_year}_asof_123123.csv"
                        program = "7(a)"
                    else:
                        url = f"https://www.sba.gov/sites/default/files/data_files/FOIA_-_504_FY{fiscal_year}_asof_123123.csv"
                        program = "504"
                    
                    response = requests.get(url, timeout=60)
                    time.sleep(self.rate_limit_delay)
                    
                    if response.status_code == 200:
                        # Parse CSV
                        from io import StringIO
                        df = pd.read_csv(StringIO(response.text), low_memory=False)
                        
                        # Filter for the specific county
                        # SBA data usually has state and county fields
                        county_data = df[
                            (df.get('BorrCounty', '').str.contains(county_fips[-3:], na=False)) |
                            (df.get('ProjectCounty', '').str.contains(county_fips[-3:], na=False))
                        ]
                        
                        for _, row in county_data.iterrows():
                            record = {
                                'loan_id': f"{program}_{row.get('LoanNumber', '')}{row.get('SBALoanNumber', '')}",
                                'county_fips': county_fips,
                                'fy': fiscal_year,
                                'program': program,
                                'amount': float(row.get('GrossApproval', 0)) if pd.notna(row.get('GrossApproval')) else 0,
                                'lender': str(row.get('Lender', '')),
                                'naics': str(row.get('NAICSCode', '')),
                                'approval_date': str(row.get('ApprovalDate', '')),
                                'source_url': url,
                                'retrieved_at': datetime.now().isoformat(),
                                'license': 'Public Domain'
                            }
                            
                            if record['amount'] > 0:
                                results.append(record)
                
                except Exception as e:
                    print(f"Error processing SBA file pattern {pattern}: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error fetching SBA data for {county_fips}: {str(e)}")
            return []
    
    def fetch_multiple_years(self, county_fips: str, years: List[int]) -> List[Dict[str, Any]]:
        """Fetch SBA data for multiple fiscal years"""
        all_results = []
        
        for year in years:
            results = self.fetch_loan_data(county_fips, year)
            all_results.extend(results)
            time.sleep(self.rate_limit_delay)
        
        return all_results
    
    def calculate_metrics(self, loan_data: List[Dict[str, Any]], establishments_count: int) -> Dict[str, float]:
        """Calculate SBA metrics per 1K firms"""
        if not loan_data or establishments_count == 0:
            return {
                'loans_per_1k_firms': 0.0,
                'amount_per_1k_firms': 0.0,
                'avg_amount': 0.0
            }
        
        total_loans = len(loan_data)
        total_amount = sum(loan['amount'] for loan in loan_data)
        
        return {
            'loans_per_1k_firms': (total_loans / establishments_count) * 1000,
            'amount_per_1k_firms': (total_amount / establishments_count) * 1000,
            'avg_amount': total_amount / total_loans if total_loans > 0 else 0.0
        }
