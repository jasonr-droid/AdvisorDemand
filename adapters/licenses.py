import requests
import pandas as pd
import time
from typing import List, Dict, Any
from datetime import datetime
import os

class LicensesAdapter:
    """Adapter for city business license data"""
    
    def __init__(self):
        self.rate_limit_delay = 1.0
        # City endpoints registry
        self.city_endpoints = {
            'Los Angeles': {
                'url': 'https://data.lacity.org/resource/w8b2-6t57.json',
                'county_fips': '06037',
                'date_field': 'license_start_date',
                'status_field': 'license_status'
            },
            'San Diego': {
                'url': 'https://seshat.datasd.org/business_licenses/business_licenses_datasd.csv',
                'county_fips': '06073', 
                'date_field': 'issue_date',
                'status_field': 'license_status'
            },
            'San Francisco': {
                'url': 'https://data.sfgov.org/resource/g8m3-pdis.json',
                'county_fips': '06075',
                'date_field': 'license_creation_date',
                'status_field': 'license_status'
            },
            'Santa Barbara': {
                'url': 'https://data.ca.gov/api/3/action/datastore_search?resource_id=business-licenses-santa-barbara',
                'county_fips': '06083',
                'date_field': 'license_start_date',
                'status_field': 'license_status',
                'type': 'ca_open_data'
            }
        }
        
    def fetch_licenses(self, county_fips: str) -> List[Dict[str, Any]]:
        """Fetch business license data for a county"""
        results = []
        
        # Find cities in the target county
        target_cities = [
            city for city, config in self.city_endpoints.items() 
            if config['county_fips'] == county_fips
        ]
        
        for city in target_cities:
            city_results = self.fetch_city_licenses(city)
            results.extend(city_results)
            time.sleep(self.rate_limit_delay)
        
        return results
    
    def fetch_city_licenses(self, city_name: str) -> List[Dict[str, Any]]:
        """Fetch license data for a specific city"""
        if city_name not in self.city_endpoints:
            return []
        
        config = self.city_endpoints[city_name]
        
        try:
            url = config['url']
            
            if url.endswith('.json'):
                # Socrata JSON API
                params = {
                    '$limit': 5000,
                    '$order': f"{config['date_field']} DESC"
                }
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._process_json_licenses(data, city_name, config)
                    
            elif url.endswith('.csv'):
                # CSV download
                response = requests.get(url, timeout=60)
                
                if response.status_code == 200:
                    from io import StringIO
                    df = pd.read_csv(StringIO(response.text))
                    return self._process_csv_licenses(df, city_name, config)
            
            return []
            
        except Exception as e:
            print(f"Error fetching licenses for {city_name}: {str(e)}")
            return []
    
    def _process_json_licenses(self, data: List[Dict], city_name: str, config: Dict) -> List[Dict[str, Any]]:
        """Process JSON license data"""
        results = []
        
        for item in data:
            # Generate unique license ID
            license_id = f"{city_name}_{item.get('license_number', '')}{item.get('id', '')}"
            
            record = {
                'license_id': license_id,
                'jurisdiction': city_name,
                'county_fips': config['county_fips'],
                'naics': self._extract_naics(item),
                'issued_date': item.get(config['date_field'], ''),
                'status': item.get(config['status_field'], ''),
                'geocode': self._extract_geocode(item),
                'source_url': config['url'],
                'retrieved_at': datetime.now().isoformat(),
                'license': 'Open Data'
            }
            
            if record['license_id'] and record['issued_date']:
                results.append(record)
        
        return results
    
    def _process_csv_licenses(self, df: pd.DataFrame, city_name: str, config: Dict) -> List[Dict[str, Any]]:
        """Process CSV license data"""
        results = []
        
        for _, row in df.iterrows():
            license_id = f"{city_name}_{row.get('license_number', '')}{row.get('id', '')}"
            
            record = {
                'license_id': license_id,
                'jurisdiction': city_name,
                'county_fips': config['county_fips'],
                'naics': self._extract_naics_from_row(row),
                'issued_date': str(row.get(config['date_field'], '')),
                'status': str(row.get(config['status_field'], '')),
                'geocode': self._extract_geocode_from_row(row),
                'source_url': config['url'],
                'retrieved_at': datetime.now().isoformat(),
                'license': 'Open Data'
            }
            
            if record['license_id'] and record['issued_date']:
                results.append(record)
        
        return results
    
    def _extract_naics(self, item: Dict) -> str:
        """Extract NAICS code from license data"""
        # Look for common NAICS fields
        naics_fields = ['naics_code', 'naics', 'business_code', 'industry_code']
        
        for field in naics_fields:
            if field in item and item[field]:
                return str(item[field])
        
        # Try to map business type to NAICS
        business_type = item.get('business_type', '').lower()
        if 'accounting' in business_type or 'bookkeeping' in business_type:
            return '541211'  # CPA offices
        elif 'tax' in business_type:
            return '541213'  # Tax preparation
        elif 'financial' in business_type:
            return '523930'  # Investment advice
        
        return ''
    
    def _extract_naics_from_row(self, row: pd.Series) -> str:
        """Extract NAICS code from pandas row"""
        naics_fields = ['naics_code', 'naics', 'business_code', 'industry_code']
        
        for field in naics_fields:
            if field in row.index and pd.notna(row[field]):
                return str(row[field])
        
        # Try to map business type
        business_type = str(row.get('business_type', '')).lower()
        if 'accounting' in business_type or 'bookkeeping' in business_type:
            return '541211'
        elif 'tax' in business_type:
            return '541213'
        elif 'financial' in business_type:
            return '523930'
        
        return ''
    
    def _extract_geocode(self, item: Dict) -> str:
        """Extract geocode from license data"""
        lat = item.get('latitude') or item.get('lat')
        lon = item.get('longitude') or item.get('lon') or item.get('lng')
        
        if lat and lon:
            return f"{lat},{lon}"
        
        return ''
    
    def _extract_geocode_from_row(self, row: pd.Series) -> str:
        """Extract geocode from pandas row"""
        lat = row.get('latitude') or row.get('lat')
        lon = row.get('longitude') or row.get('lon') or row.get('lng')
        
        if pd.notna(lat) and pd.notna(lon):
            return f"{lat},{lon}"
        
        return ''
