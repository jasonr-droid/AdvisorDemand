import requests
import pandas as pd
import time
from typing import List, Dict, Any
from datetime import datetime
import os

class BFSAdapter:
    """Adapter for Bureau of Formation Statistics data"""
    
    def __init__(self):
        self.base_url = "https://www.census.gov/econ/bfs/csv"
        self.rate_limit_delay = 1.0
        
    def fetch_county_formations(self, county_fips: str, year: int = 2023) -> List[Dict[str, Any]]:
        """Fetch business formation data for a county"""
        try:
            # BFS provides county-level data files
            file_url = f"{self.base_url}/bfs{year}co.csv"
            
            response = requests.get(file_url, timeout=60)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                from io import StringIO
                df = pd.read_csv(StringIO(response.text))
                
                # Filter for specific county
                # BFS uses FIPS codes in 'fipscty' column
                county_data = df[df['fipscty'].astype(str).str.zfill(5) == county_fips]
                
                results = []
                for _, row in county_data.iterrows():
                    record = {
                        'county_fips': county_fips,
                        'year': year,
                        'applications_total': int(row.get('ba_ba', 0)) if pd.notna(row.get('ba_ba')) else 0,
                        'high_propensity_apps': int(row.get('ba_hba', 0)) if pd.notna(row.get('ba_hba')) else 0,
                        'source_url': file_url,
                        'retrieved_at': datetime.now().isoformat(),
                        'license': 'Public Domain'
                    }
                    
                    if record['applications_total'] > 0:
                        results.append(record)
                
                return results
            
            return []
            
        except Exception as e:
            print(f"Error fetching BFS data for {county_fips}: {str(e)}")
            return []
    
    def fetch_multiple_years(self, county_fips: str, years: List[int]) -> List[Dict[str, Any]]:
        """Fetch BFS data for multiple years"""
        all_results = []
        
        for year in years:
            results = self.fetch_county_formations(county_fips, year)
            all_results.extend(results)
            time.sleep(self.rate_limit_delay)
        
        return all_results
    
    def get_available_years(self) -> List[int]:
        """Get available BFS data years"""
        # BFS typically releases data with a 1-2 year lag
        current_year = datetime.now().year
        return list(range(current_year - 3, current_year))
    
    def calculate_formation_trends(self, formations_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate formation trends and metrics"""
        if not formations_data:
            return {
                'total_applications': 0,
                'avg_annual_applications': 0,
                'high_propensity_rate': 0.0,
                'trend': 'unknown'
            }
        
        df = pd.DataFrame(formations_data)
        
        total_apps = df['applications_total'].sum()
        total_high_prop = df['high_propensity_apps'].sum()
        avg_annual = df['applications_total'].mean()
        
        # Calculate high propensity rate
        high_prop_rate = (total_high_prop / total_apps * 100) if total_apps > 0 else 0
        
        # Calculate trend
        trend = 'stable'
        if len(df) > 1:
            df_sorted = df.sort_values('year')
            recent_avg = df_sorted.tail(2)['applications_total'].mean()
            earlier_avg = df_sorted.head(2)['applications_total'].mean()
            
            if recent_avg > earlier_avg * 1.1:
                trend = 'increasing'
            elif recent_avg < earlier_avg * 0.9:
                trend = 'decreasing'
        
        return {
            'total_applications': int(total_apps),
            'avg_annual_applications': int(avg_annual),
            'high_propensity_rate': round(high_prop_rate, 1),
            'trend': trend,
            'years_available': len(df)
        }
