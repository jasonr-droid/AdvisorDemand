import logging
from typing import Dict, List, Optional, Tuple
import csv
import io

logger = logging.getLogger(__name__)

class FIPSHelper:
    """Utility class for FIPS code operations and county lookups"""
    
    def __init__(self):
        # Basic FIPS to state mapping
        self.state_fips_to_code = {
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
        
        self.state_code_to_fips = {v: k for k, v in self.state_fips_to_code.items()}
        
        self.state_fips_to_name = {
            '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas', '06': 'California',
            '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware', '11': 'District of Columbia', '12': 'Florida',
            '13': 'Georgia', '15': 'Hawaii', '16': 'Idaho', '17': 'Illinois', '18': 'Indiana',
            '19': 'Iowa', '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
            '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota', '28': 'Mississippi',
            '29': 'Missouri', '30': 'Montana', '31': 'Nebraska', '32': 'Nevada', '33': 'New Hampshire',
            '34': 'New Jersey', '35': 'New Mexico', '36': 'New York', '37': 'North Carolina', '38': 'North Dakota',
            '39': 'Ohio', '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
            '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas', '49': 'Utah',
            '50': 'Vermont', '51': 'Virginia', '53': 'Washington', '54': 'West Virginia', '55': 'Wisconsin',
            '56': 'Wyoming'
        }
        
        # Major counties for common searches
        self.major_counties = {
            '06037': {'name': 'Los Angeles County', 'state': 'CA', 'state_name': 'California'},
            '06073': {'name': 'San Diego County', 'state': 'CA', 'state_name': 'California'},
            '06075': {'name': 'San Francisco County', 'state': 'CA', 'state_name': 'California'},
            '06001': {'name': 'Alameda County', 'state': 'CA', 'state_name': 'California'},
            '06085': {'name': 'Santa Clara County', 'state': 'CA', 'state_name': 'California'},
            '36061': {'name': 'New York County', 'state': 'NY', 'state_name': 'New York'},
            '36047': {'name': 'Kings County', 'state': 'NY', 'state_name': 'New York'},
            '36081': {'name': 'Queens County', 'state': 'NY', 'state_name': 'New York'},
            '17031': {'name': 'Cook County', 'state': 'IL', 'state_name': 'Illinois'},
            '48201': {'name': 'Harris County', 'state': 'TX', 'state_name': 'Texas'},
            '04013': {'name': 'Maricopa County', 'state': 'AZ', 'state_name': 'Arizona'},
            '12086': {'name': 'Miami-Dade County', 'state': 'FL', 'state_name': 'Florida'},
            '53033': {'name': 'King County', 'state': 'WA', 'state_name': 'Washington'},
            '25025': {'name': 'Suffolk County', 'state': 'MA', 'state_name': 'Massachusetts'},
            '51059': {'name': 'Fairfax County', 'state': 'VA', 'state_name': 'Virginia'}
        }
    
    def validate_fips(self, fips_code: str) -> bool:
        """Validate FIPS code format"""
        if not fips_code or not isinstance(fips_code, str):
            return False
        
        # Remove any whitespace
        fips_code = fips_code.strip()
        
        # Should be 5 digits for county FIPS
        if len(fips_code) != 5:
            return False
        
        # Should be all digits
        if not fips_code.isdigit():
            return False
        
        # State FIPS should be valid
        state_fips = fips_code[:2]
        if state_fips not in self.state_fips_to_code:
            return False
        
        return True
    
    def parse_fips(self, fips_code: str) -> Optional[Tuple[str, str]]:
        """Parse FIPS code into state and county components"""
        if not self.validate_fips(fips_code):
            return None
        
        state_fips = fips_code[:2]
        county_fips = fips_code[2:]
        
        return state_fips, county_fips
    
    def get_state_info(self, fips_code: str) -> Optional[Dict[str, str]]:
        """Get state information from FIPS code"""
        parsed = self.parse_fips(fips_code)
        if not parsed:
            return None
        
        state_fips, _ = parsed
        
        return {
            'fips': state_fips,
            'code': self.state_fips_to_code.get(state_fips, ''),
            'name': self.state_fips_to_name.get(state_fips, '')
        }
    
    def get_county_info(self, fips_code: str) -> Optional[Dict[str, str]]:
        """Get county information from FIPS code"""
        if not self.validate_fips(fips_code):
            return None
        
        # Check if it's a major county we have data for
        if fips_code in self.major_counties:
            county_info = self.major_counties[fips_code].copy()
            county_info['fips'] = fips_code
            county_info['display_name'] = f"{county_info['name']}, {county_info['state']}"
            return county_info
        
        # For other counties, provide basic info
        state_info = self.get_state_info(fips_code)
        if not state_info:
            return None
        
        return {
            'fips': fips_code,
            'name': f"County {fips_code[2:]}",
            'state': state_info['code'],
            'state_name': state_info['name'],
            'display_name': f"County {fips_code[2:]}, {state_info['code']}"
        }
    
    def search_counties(self, search_term: str) -> List[Dict[str, str]]:
        """Search for counties by name or FIPS"""
        search_term = search_term.lower().strip()
        results = []
        
        # If it looks like a FIPS code, validate and return
        if search_term.isdigit() and len(search_term) == 5:
            county_info = self.get_county_info(search_term)
            if county_info:
                results.append(county_info)
            return results
        
        # Search in major counties
        for fips, info in self.major_counties.items():
            county_name = info['name'].lower()
            state_code = info['state'].lower()
            state_name = info['state_name'].lower()
            
            if (search_term in county_name or 
                search_term in state_code or 
                search_term in state_name or
                search_term in f"{county_name}, {state_code}"):
                
                result_info = info.copy()
                result_info['fips'] = fips
                result_info['display_name'] = f"{info['name']}, {info['state']}"
                results.append(result_info)
        
        return results
    
    def get_neighboring_counties(self, fips_code: str) -> List[str]:
        """Get neighboring counties (simplified - returns same state counties)"""
        if not self.validate_fips(fips_code):
            return []
        
        state_fips = fips_code[:2]
        
        # Return other major counties in the same state
        same_state_counties = [
            fips for fips, info in self.major_counties.items()
            if fips.startswith(state_fips) and fips != fips_code
        ]
        
        return same_state_counties
    
    def format_county_name(self, fips_code: str) -> str:
        """Format county name for display"""
        county_info = self.get_county_info(fips_code)
        if county_info:
            return county_info['display_name']
        return f"County {fips_code}"
    
    def get_all_states(self) -> List[Dict[str, str]]:
        """Get list of all states"""
        states = []
        for fips, code in self.state_fips_to_code.items():
            states.append({
                'fips': fips,
                'code': code,
                'name': self.state_fips_to_name[fips]
            })
        
        return sorted(states, key=lambda x: x['name'])
    
    def get_state_counties(self, state_fips: str) -> List[Dict[str, str]]:
        """Get counties for a specific state"""
        if state_fips not in self.state_fips_to_code:
            return []
        
        state_counties = []
        for fips, info in self.major_counties.items():
            if fips.startswith(state_fips):
                county_info = info.copy()
                county_info['fips'] = fips
                county_info['display_name'] = f"{info['name']}, {info['state']}"
                state_counties.append(county_info)
        
        return sorted(state_counties, key=lambda x: x['name'])
    
    def is_valid_state_fips(self, state_fips: str) -> bool:
        """Check if state FIPS is valid"""
        return state_fips in self.state_fips_to_code
    
    def state_code_to_fips_code(self, state_code: str) -> Optional[str]:
        """Convert state code (e.g., 'CA') to FIPS code"""
        return self.state_code_to_fips.get(state_code.upper())
    
    def fips_to_state_code(self, state_fips: str) -> Optional[str]:
        """Convert state FIPS to state code"""
        return self.state_fips_to_code.get(state_fips)

# Global instance
fips_helper = FIPSHelper()
