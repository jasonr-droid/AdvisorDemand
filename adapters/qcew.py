import requests
import pandas as pd
import time
from typing import List, Dict, Any
from datetime import datetime
import os

class QCEWAdapter:
    """Adapter for Bureau of Labor Statistics QCEW data"""
    
    def __init__(self):
        self.base_url = "https://data.bls.gov/cew/data/api"
        self.api_key = os.getenv("BLS_API_KEY", "")
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def fetch_county_data(self, county_fips: str, year: int = 2024, quarter: str = "1") -> List[Dict[str, Any]]:
        """Fetch QCEW data for a specific county"""
        try:
            # QCEW uses area codes that combine state and county FIPS
            area_code = county_fips
            
            # QCEW API endpoint for county data
            url = f"{self.base_url}/{year}/{quarter}/area/{area_code}.csv"
            
            response = requests.get(url, timeout=30)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                # Parse CSV response
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                results = []
                for _, row in df.iterrows():
                    # Filter for relevant ownership codes and industry levels
                    if (row.get('own_code') == '0' and  # All ownership
                        row.get('agglvl_code') in ['78', '79']):  # County level
                        
                        record = {
                            'county_fips': county_fips,
                            'naics': str(row.get('industry_code', '')),
                            'year': year,
                            'quarter': f"{year}Q{quarter}",
                            'employment': int(row.get('month3_emplvl', 0)) if pd.notna(row.get('month3_emplvl')) else None,
                            'avg_weekly_wage': float(row.get('avg_wkly_wage', 0)) if pd.notna(row.get('avg_wkly_wage')) else None,
                            'source_url': url,
                            'retrieved_at': datetime.now().isoformat(),
                            'license': 'Public Domain'
                        }
                        
                        # Only include if we have valid data
                        if record['naics'] and (record['employment'] or record['avg_weekly_wage']):
                            results.append(record)
                
                return results
            
            return []
            
        except Exception as e:
            print(f"Error fetching QCEW data for {county_fips}: {str(e)}")
            return []
    
    def fetch_latest_quarter_data(self, county_fips: str) -> List[Dict[str, Any]]:
        """Fetch the most recent quarter of QCEW data"""
        # Try current year quarters in reverse order
        current_year = datetime.now().year
        quarters = ['4', '3', '2', '1']
        
        for year in [current_year, current_year - 1]:
            for quarter in quarters:
                data = self.fetch_county_data(county_fips, year, quarter)
                if data:
                    return data
        
        return []
    
    def get_available_quarters(self, year: int) -> List[str]:
        """Get available quarters for a given year"""
        try:
            # BLS typically has data with a lag, so check what's available
            quarters = []
            for q in ['1', '2', '3', '4']:
                test_url = f"{self.base_url}/{year}/{q}/area"
                response = requests.head(test_url, timeout=10)
                if response.status_code == 200:
                    quarters.append(q)
            
            return quarters
            
        except Exception as e:
            print(f"Error checking available quarters for {year}: {str(e)}")
            return ['1', '2', '3', '4']  # Fallback
