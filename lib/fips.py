from typing import Dict, List, Optional, Tuple

class FIPSHelper:
    """FIPS code utilities and county mapping"""
    
    def __init__(self):
        # State FIPS to state mapping
        self.state_fips = {
            '01': 'Alabama', '02': 'Alaska', '04': 'Arizona', '05': 'Arkansas',
            '06': 'California', '08': 'Colorado', '09': 'Connecticut', '10': 'Delaware',
            '11': 'District of Columbia', '12': 'Florida', '13': 'Georgia', '15': 'Hawaii',
            '16': 'Idaho', '17': 'Illinois', '18': 'Indiana', '19': 'Iowa',
            '20': 'Kansas', '21': 'Kentucky', '22': 'Louisiana', '23': 'Maine',
            '24': 'Maryland', '25': 'Massachusetts', '26': 'Michigan', '27': 'Minnesota',
            '28': 'Mississippi', '29': 'Missouri', '30': 'Montana', '31': 'Nebraska',
            '32': 'Nevada', '33': 'New Hampshire', '34': 'New Jersey', '35': 'New Mexico',
            '36': 'New York', '37': 'North Carolina', '38': 'North Dakota', '39': 'Ohio',
            '40': 'Oklahoma', '41': 'Oregon', '42': 'Pennsylvania', '44': 'Rhode Island',
            '45': 'South Carolina', '46': 'South Dakota', '47': 'Tennessee', '48': 'Texas',
            '49': 'Utah', '50': 'Vermont', '51': 'Virginia', '53': 'Washington',
            '54': 'West Virginia', '55': 'Wisconsin', '56': 'Wyoming'
        }
        
        # Major counties for testing and examples
        self.sample_counties = {
            '06037': {'name': 'Los Angeles County', 'state': 'CA'},
            '06073': {'name': 'San Diego County', 'state': 'CA'},
            '06075': {'name': 'San Francisco County', 'state': 'CA'},
            '48201': {'name': 'Harris County', 'state': 'TX'},
            '17031': {'name': 'Cook County', 'state': 'IL'},
            '36061': {'name': 'New York County', 'state': 'NY'},
            '04013': {'name': 'Maricopa County', 'state': 'AZ'},
            '32003': {'name': 'Clark County', 'state': 'NV'},
            '12086': {'name': 'Miami-Dade County', 'state': 'FL'},
            '53033': {'name': 'King County', 'state': 'WA'}
        }
    
    def validate_fips(self, fips_code: str) -> bool:
        """Validate FIPS code format"""
        if not fips_code or not isinstance(fips_code, str):
            return False
        
        # Remove any non-numeric characters
        clean_fips = ''.join(filter(str.isdigit, fips_code))
        
        # Check length (should be 5 digits for county FIPS)
        if len(clean_fips) != 5:
            return False
        
        # Check if state part is valid
        state_part = clean_fips[:2]
        return state_part in self.state_fips
    
    def format_fips(self, fips_code: str) -> str:
        """Format FIPS code to standard 5-digit format"""
        clean_fips = ''.join(filter(str.isdigit, fips_code))
        return clean_fips.zfill(5)
    
    def get_state_from_fips(self, fips_code: str) -> Optional[str]:
        """Get state name from FIPS code"""
        if not self.validate_fips(fips_code):
            return None
        
        state_fips = fips_code[:2]
        return self.state_fips.get(state_fips)
    
    def get_state_abbrev_from_fips(self, fips_code: str) -> Optional[str]:
        """Get state abbreviation from FIPS code"""
        state_name = self.get_state_from_fips(fips_code)
        if not state_name:
            return None
        
        # State name to abbreviation mapping
        state_abbrevs = {
            'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
            'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
            'District of Columbia': 'DC', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI',
            'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
            'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME',
            'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
            'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
            'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
            'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
            'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI',
            'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',
            'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
            'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
        }
        
        return state_abbrevs.get(state_name)
    
    def parse_county_search(self, search_term: str) -> Optional[str]:
        """Parse county search term and return FIPS code if found"""
        search_lower = search_term.lower().strip()
        
        # Check if it's already a FIPS code
        if search_term.isdigit() and len(search_term) == 5:
            if self.validate_fips(search_term):
                return search_term
        
        # Search in sample counties
        for fips, info in self.sample_counties.items():
            county_name = info['name'].lower()
            state_abbrev = info['state'].lower()
            
            if (search_lower in county_name or 
                county_name in search_lower or
                search_lower == fips or
                search_lower == f"{county_name}, {state_abbrev}"):
                return fips
        
        return None
    
    def get_county_info(self, fips_code: str) -> Optional[Dict[str, str]]:
        """Get county information from FIPS code"""
        if not self.validate_fips(fips_code):
            return None
        
        formatted_fips = self.format_fips(fips_code)
        
        # Check sample counties first
        if formatted_fips in self.sample_counties:
            return {
                'fips': formatted_fips,
                'name': self.sample_counties[formatted_fips]['name'],
                'state': self.sample_counties[formatted_fips]['state'],
                'state_name': self.get_state_from_fips(formatted_fips)
            }
        
        # For other counties, provide basic info
        state_name = self.get_state_from_fips(formatted_fips)
        state_abbrev = self.get_state_abbrev_from_fips(formatted_fips)
        
        if state_name and state_abbrev:
            return {
                'fips': formatted_fips,
                'name': f"County {formatted_fips[2:]}",  # Generic name
                'state': state_abbrev,
                'state_name': state_name
            }
        
        return None
    
    def get_sample_counties(self) -> List[Dict[str, str]]:
        """Get list of sample counties for dropdown"""
        counties = []
        for fips, info in self.sample_counties.items():
            counties.append({
                'fips': fips,
                'name': info['name'],
                'state': info['state'],
                'display_name': f"{info['name']}, {info['state']} ({fips})"
            })
        
        return sorted(counties, key=lambda x: x['display_name'])
    
    def split_fips(self, fips_code: str) -> Tuple[Optional[str], Optional[str]]:
        """Split FIPS code into state and county parts"""
        if not self.validate_fips(fips_code):
            return None, None
        
        formatted_fips = self.format_fips(fips_code)
        return formatted_fips[:2], formatted_fips[2:]
