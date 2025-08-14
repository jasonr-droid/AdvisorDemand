import requests
import time
from typing import List, Dict, Any
from datetime import datetime
import os

class OpenCorporatesAdapter:
    """Adapter for OpenCorporates firm data"""
    
    def __init__(self):
        self.base_url = "https://api.opencorporates.com/v0.4"
        self.api_key = os.getenv("OPENCORPORATES_API_KEY", "")
        self.rate_limit_delay = 2.0  # OpenCorporates has strict rate limits
        
    def fetch_firms(self, county_fips: str, jurisdiction: str = "us") -> List[Dict[str, Any]]:
        """Fetch firm data for a county"""
        try:
            # OpenCorporates doesn't directly search by county FIPS
            # We need to map county to jurisdiction and search
            state_code = self._fips_to_state(county_fips[:2])
            
            if not state_code:
                return []
            
            # Search companies in the state
            url = f"{self.base_url}/companies/search"
            params = {
                'q': f'jurisdiction_code:{jurisdiction}_{state_code.lower()}',
                'per_page': 100,
                'page': 1
            }
            
            if self.api_key:
                params['api_token'] = self.api_key
            
            results = []
            
            for page in range(1, 6):  # Limit to 5 pages
                params['page'] = page
                
                response = requests.get(url, params=params, timeout=30)
                time.sleep(self.rate_limit_delay)
                
                if response.status_code == 200:
                    data = response.json()
                    companies = data.get('results', {}).get('companies', [])
                    
                    if not companies:
                        break
                    
                    for company in companies:
                        company_data = company.get('company', {})
                        
                        record = {
                            'company_id': f"oc_{company_data.get('company_number', '')}",
                            'jurisdiction': company_data.get('jurisdiction_code', ''),
                            'company_number': company_data.get('company_number', ''),
                            'county_fips': county_fips,  # Assumed for county search
                            'incorporation_date': company_data.get('incorporation_date', ''),
                            'status': company_data.get('current_status', ''),
                            'source_url': f"{self.base_url}/companies/search?{requests.compat.urlencode(params)}",
                            'retrieved_at': datetime.now().isoformat(),
                            'license': 'OpenCorporates License'
                        }
                        
                        if record['company_number']:
                            results.append(record)
                
                else:
                    break
            
            return results
            
        except Exception as e:
            print(f"Error fetching OpenCorporates data for {county_fips}: {str(e)}")
            return []
    
    def calculate_age_distribution(self, firms_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate firm age distribution"""
        if not firms_data:
            return {
                'age_0_1': 0,
                'age_1_3': 0, 
                'age_3_5': 0,
                'age_5_plus': 0,
                'total_firms': 0,
                'match_rate': 0.0
            }
        
        age_buckets = {
            'age_0_1': 0,
            'age_1_3': 0,
            'age_3_5': 0, 
            'age_5_plus': 0
        }
        
        firms_with_dates = 0
        current_year = datetime.now().year
        
        for firm in firms_data:
            inc_date = firm.get('incorporation_date')
            if inc_date:
                try:
                    inc_year = datetime.fromisoformat(inc_date).year
                    age = current_year - inc_year
                    firms_with_dates += 1
                    
                    if age <= 1:
                        age_buckets['age_0_1'] += 1
                    elif age <= 3:
                        age_buckets['age_1_3'] += 1
                    elif age <= 5:
                        age_buckets['age_3_5'] += 1
                    else:
                        age_buckets['age_5_plus'] += 1
                        
                except (ValueError, TypeError):
                    continue
        
        total_firms = len(firms_data)
        match_rate = (firms_with_dates / total_firms * 100) if total_firms > 0 else 0
        
        return {
            **age_buckets,
            'total_firms': total_firms,
            'match_rate': match_rate
        }
    
    def _fips_to_state(self, state_fips: str) -> str:
        """Convert state FIPS to state code"""
        fips_to_state = {
            '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA',
            '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL',
            '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN',
            '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME',
            '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS',
            '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
            '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
            '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
            '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT',
            '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI',
            '56': 'WY'
        }
        
        return fips_to_state.get(state_fips, '')
