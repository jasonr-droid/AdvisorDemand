import requests
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os

class USASpendingAdapter:
    """Adapter for USAspending.gov awards data"""
    
    def __init__(self):
        self.base_url = "https://api.usaspending.gov/api/v2"
        self.rate_limit_delay = 1.0
        
    def fetch_awards(self, county_fips: str, fiscal_year: int = 2024) -> List[Dict[str, Any]]:
        """Fetch federal awards for a specific county"""
        try:
            # USAspending API endpoint for spending data
            url = f"{self.base_url}/search/spending_by_award/"
            
            # Request payload
            payload = {
                "filters": {
                    "time_period": [
                        {
                            "start_date": f"{fiscal_year-1}-10-01",
                            "end_date": f"{fiscal_year}-09-30"
                        }
                    ],
                    "place_of_performance_locations": [
                        {
                            "country": "USA",
                            "county": county_fips
                        }
                    ]
                },
                "fields": [
                    "Award ID",
                    "Award Type",
                    "Total Obligated Amount", 
                    "Description",
                    "Start Date",
                    "End Date",
                    "Awarding Agency",
                    "NAICS Code",
                    "NAICS Description",
                    "Place of Performance County Name",
                    "Place of Performance County Code"
                ],
                "page": 1,
                "limit": 100,
                "sort": "Total Obligated Amount",
                "order": "desc"
            }
            
            response = requests.post(url, json=payload, timeout=30)
            time.sleep(self.rate_limit_delay)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for award in data.get('results', []):
                    record = {
                        'award_id': award.get('Award ID', ''),
                        'naics': award.get('NAICS Code', ''),
                        'recipient_county_fips': county_fips,
                        'amount': float(award.get('Total Obligated Amount', 0)),
                        'action_date': award.get('Start Date', ''),
                        'agency': award.get('Awarding Agency', ''),
                        'url': f"https://www.usaspending.gov/award/{award.get('Award ID', '')}",
                        'source_url': url,
                        'retrieved_at': datetime.now().isoformat(),
                        'license': 'Public Domain'
                    }
                    
                    if record['award_id'] and record['amount'] > 0:
                        results.append(record)
                
                return results
                
            return []
            
        except Exception as e:
            print(f"Error fetching USAspending awards for {county_fips}: {str(e)}")
            return []
    
    def fetch_awards_by_naics(self, naics_codes: List[str], fiscal_year: int = 2024) -> List[Dict[str, Any]]:
        """Fetch awards by NAICS codes"""
        try:
            url = f"{self.base_url}/search/spending_by_award/"
            results = []
            
            for naics in naics_codes:
                payload = {
                    "filters": {
                        "time_period": [
                            {
                                "start_date": f"{fiscal_year-1}-10-01",
                                "end_date": f"{fiscal_year}-09-30"
                            }
                        ],
                        "naics_codes": [naics]
                    },
                    "fields": [
                        "Award ID",
                        "Total Obligated Amount",
                        "Start Date", 
                        "Awarding Agency",
                        "NAICS Code",
                        "Place of Performance County Code"
                    ],
                    "page": 1,
                    "limit": 100
                }
                
                response = requests.post(url, json=payload, timeout=30)
                time.sleep(self.rate_limit_delay)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for award in data.get('results', []):
                        record = {
                            'award_id': award.get('Award ID', ''),
                            'naics': naics,
                            'recipient_county_fips': award.get('Place of Performance County Code', ''),
                            'amount': float(award.get('Total Obligated Amount', 0)),
                            'action_date': award.get('Start Date', ''),
                            'agency': award.get('Awarding Agency', ''),
                            'url': f"https://www.usaspending.gov/award/{award.get('Award ID', '')}",
                            'source_url': url,
                            'retrieved_at': datetime.now().isoformat(),
                            'license': 'Public Domain'
                        }
                        
                        if record['award_id'] and record['amount'] > 0:
                            results.append(record)
            
            return results
            
        except Exception as e:
            print(f"Error fetching USAspending awards by NAICS: {str(e)}")
            return []
    
    def get_spending_summary(self, county_fips: str, fiscal_year: int = 2024) -> Dict[str, Any]:
        """Get spending summary for a county"""
        try:
            url = f"{self.base_url}/search/spending_by_geography/"
            
            payload = {
                "scope": "place_of_performance",
                "geo_layer": "county",
                "filters": {
                    "time_period": [
                        {
                            "start_date": f"{fiscal_year-1}-10-01",
                            "end_date": f"{fiscal_year}-09-30"
                        }
                    ]
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Find the specific county in results
                for result in data.get('results', []):
                    if result.get('shape_code') == county_fips:
                        return {
                            'total_obligations': result.get('aggregated_amount', 0),
                            'award_count': result.get('award_count', 0),
                            'county_fips': county_fips,
                            'fiscal_year': fiscal_year
                        }
            
            return {}
            
        except Exception as e:
            print(f"Error fetching spending summary for {county_fips}: {str(e)}")
            return {}
