import requests
import pandas as pd
import time
from typing import List, Dict, Any
from datetime import datetime
import os

class CBPAdapter:
    """Adapter for Census Bureau County Business Patterns data"""
    
    def __init__(self):
        self.base_url = "https://api.census.gov/data"
        self.api_key = os.getenv("CENSUS_API_KEY", "")
        self.rate_limit_delay = 1.0  # seconds between requests
        
    def fetch_county_data(self, county_fips: str, year: int = 2022) -> List[Dict[str, Any]]:
        """Fetch CBP data for a specific county"""
        try:
            # Extract state FIPS from county FIPS
            state_fips = county_fips[:2]
            county_code = county_fips[2:]
            
            # CBP API endpoint
            url = f"{self.base_url}/{year}/cbp"
            
            params = {
                'get': 'NAICS2017,NAICS2017_LABEL,ESTAB,EMP,PAYANN',
                'for': f'county:{county_code}',
                'in': f'state:{state_fips}',
                'NAICS2017': '*'
            }
            
            if self.api_key:
                params['key'] = self.api_key
            
            response = requests.get(url, params=params, timeout=30)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1:  # Has header and data
                    header = data[0]
                    rows = data[1:]
                    
                    results = []
                    for row in rows:
                        # Create record
                        record = {
                            'county_fips': county_fips,
                            'naics': row[0] if row[0] != 'null' else '',
                            'year': year,
                            'establishments': int(row[2]) if row[2] not in ['null', 'D', 'S'] else None,
                            'employment': int(row[3]) if row[3] not in ['null', 'D', 'S'] else None,
                            'annual_payroll': float(row[4]) * 1000 if row[4] not in ['null', 'D', 'S'] else None,  # Convert to dollars
                            'suppressed': 1 if any(val in ['D', 'S'] for val in row[2:5]) else 0,
                            'source_url': f"{url}?{requests.compat.urlencode(params)}",
                            'retrieved_at': datetime.now().isoformat(),
                            'license': 'Public Domain'
                        }
                        
                        # Only include if we have valid NAICS and some data
                        if record['naics'] and (record['establishments'] or record['employment']):
                            results.append(record)
                    
                    return results
            
            return []
            
        except Exception as e:
            print(f"Error fetching CBP data for {county_fips}: {str(e)}")
            return []
    
    def fetch_multiple_counties(self, county_fips_list: List[str], year: int = 2022) -> List[Dict[str, Any]]:
        """Fetch CBP data for multiple counties"""
        all_results = []
        
        for county_fips in county_fips_list:
            results = self.fetch_county_data(county_fips, year)
            all_results.extend(results)
            time.sleep(self.rate_limit_delay)
        
        return all_results
    
    def get_available_years(self) -> List[int]:
        """Get list of available CBP years"""
        try:
            # Check what years are available
            response = requests.get("https://api.census.gov/data.json", timeout=30)
            if response.status_code == 200:
                data = response.json()
                cbp_years = []
                
                for dataset in data.get('dataset', []):
                    if 'cbp' in dataset.get('c_dataset', []):
                        vintage = dataset.get('c_vintage')
                        if vintage and vintage.isdigit():
                            cbp_years.append(int(vintage))
                
                return sorted(cbp_years, reverse=True)
            
            # Fallback to known available years
            return [2022, 2021, 2020, 2019, 2018]
            
        except Exception as e:
            print(f"Error getting available CBP years: {str(e)}")
            return [2022, 2021, 2020, 2019, 2018]
