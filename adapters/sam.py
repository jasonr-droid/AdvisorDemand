import requests
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os

class SAMAdapter:
    """Adapter for SAM.gov opportunities data"""
    
    def __init__(self):
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.api_key = os.getenv("SAM_API_KEY", "")
        self.rate_limit_delay = 1.0
        
    def fetch_opportunities(self, county_fips: str, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Fetch federal opportunities from SAM.gov"""
        if not self.api_key:
            print("SAM.gov API key not provided, skipping SAM data fetch")
            return []
        
        try:
            # Default keywords for financial advisor services
            if not keywords:
                keywords = [
                    "accounting", "bookkeeping", "audit", "CFO", "controller",
                    "financial advisor", "financial consulting", "tax preparation"
                ]
            
            results = []
            
            for keyword in keywords:
                params = {
                    'api_key': self.api_key,
                    'keyword': keyword,
                    'ptype': 'o',  # Opportunities
                    'limit': 100,
                    'postedFrom': (datetime.now() - timedelta(days=365)).strftime('%m/%d/%Y'),
                    'postedTo': datetime.now().strftime('%m/%d/%Y')
                }
                
                response = requests.get(self.base_url, params=params, timeout=30)
                time.sleep(self.rate_limit_delay)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for opp in data.get('opportunitiesData', []):
                        # Try to extract location information
                        place_of_performance = opp.get('placeOfPerformance', {})
                        county_match = self._match_county(place_of_performance, county_fips)
                        
                        record = {
                            'notice_id': opp.get('noticeId', ''),
                            'title': opp.get('title', ''),
                            'naics': ','.join([str(code) for code in opp.get('naicsCode', [])]),
                            'place_county_fips': county_fips if county_match else None,
                            'posted_date': opp.get('postedDate', ''),
                            'close_date': opp.get('responseDeadLine', ''),
                            'url': f"https://sam.gov/opp/{opp.get('noticeId', '')}",
                            'source_url': f"{self.base_url}?{requests.compat.urlencode(params)}",
                            'retrieved_at': datetime.now().isoformat(),
                            'license': 'Public Domain'
                        }
                        
                        if record['notice_id']:
                            results.append(record)
                
                time.sleep(self.rate_limit_delay)
            
            return results
            
        except Exception as e:
            print(f"Error fetching SAM opportunities: {str(e)}")
            return []
    
    def _match_county(self, place_of_performance: Dict, target_county_fips: str) -> bool:
        """Match place of performance to county FIPS"""
        try:
            # Extract state and county information
            state_code = place_of_performance.get('state', {}).get('code', '')
            county_name = place_of_performance.get('city', {}).get('name', '')
            
            # Simple matching - in production, you'd want a more sophisticated
            # county name to FIPS mapping
            target_state = target_county_fips[:2]
            
            if state_code and state_code == target_state:
                return True  # At least same state
            
            return False
            
        except Exception:
            return False
    
    def get_opportunities_by_naics(self, naics_codes: List[str]) -> List[Dict[str, Any]]:
        """Fetch opportunities by NAICS codes"""
        if not self.api_key:
            return []
        
        results = []
        
        for naics in naics_codes:
            params = {
                'api_key': self.api_key,
                'naics': naics,
                'ptype': 'o',
                'limit': 100,
                'postedFrom': (datetime.now() - timedelta(days=365)).strftime('%m/%d/%Y')
            }
            
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                time.sleep(self.rate_limit_delay)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for opp in data.get('opportunitiesData', []):
                        record = {
                            'notice_id': opp.get('noticeId', ''),
                            'title': opp.get('title', ''),
                            'naics': naics,
                            'place_county_fips': None,  # Would need geo parsing
                            'posted_date': opp.get('postedDate', ''),
                            'close_date': opp.get('responseDeadLine', ''),
                            'url': f"https://sam.gov/opp/{opp.get('noticeId', '')}",
                            'source_url': f"{self.base_url}?{requests.compat.urlencode(params)}",
                            'retrieved_at': datetime.now().isoformat(),
                            'license': 'Public Domain'
                        }
                        
                        if record['notice_id']:
                            results.append(record)
                            
            except Exception as e:
                print(f"Error fetching SAM opportunities for NAICS {naics}: {str(e)}")
                continue
        
        return results
