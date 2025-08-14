from typing import Dict, List, Optional

class NAICSMapper:
    """NAICS code mapping and utilities"""
    
    def __init__(self):
        # Financial advisor related NAICS codes
        self.financial_naics = {
            '523': 'Securities, Commodity Contracts, and Other Financial Investments',
            '5239': 'Other Financial Investment Activities',
            '52393': 'Investment Advice',
            '523930': 'Investment Advice',
            '541': 'Professional, Scientific, and Technical Services',
            '5412': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '54121': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '541211': 'Offices of Certified Public Accountants',
            '541213': 'Tax Preparation Services',
            '541214': 'Payroll Services',
            '541219': 'Other Accounting Services',
            '5413': 'Architectural, Engineering, and Related Services',
            '54131': 'Architectural Services',
            '541330': 'Engineering Services'
        }
        
        # NAICS hierarchy - comprehensive mapping for all major sectors
        self.naics_hierarchy = {
            # 2-digit sectors
            '11': 'Agriculture, Forestry, Fishing and Hunting',
            '21': 'Mining, Quarrying, and Oil and Gas Extraction',
            '22': 'Utilities',
            '23': 'Construction',
            '31': 'Manufacturing',
            '32': 'Manufacturing',
            '33': 'Manufacturing',
            '42': 'Wholesale Trade',
            '44': 'Retail Trade',
            '45': 'Retail Trade',
            '48': 'Transportation and Warehousing',
            '49': 'Transportation and Warehousing',
            '51': 'Information',
            '52': 'Finance and Insurance',
            '53': 'Real Estate and Rental and Leasing',
            '54': 'Professional, Scientific, and Technical Services',
            '55': 'Management of Companies and Enterprises',
            '56': 'Administrative and Support and Waste Management Services',
            '61': 'Educational Services',
            '62': 'Health Care and Social Assistance',
            '71': 'Arts, Entertainment, and Recreation',
            '72': 'Accommodation and Food Services',
            '81': 'Other Services (except Public Administration)',
            '92': 'Public Administration',
            
            # 3-digit subsectors (commonly seen in data)
            '236': 'Construction of Buildings',
            '238': 'Specialty Trade Contractors',
            '311': 'Food Manufacturing',
            '312': 'Beverage and Tobacco Product Manufacturing',
            '441': 'Motor Vehicle and Parts Dealers',
            '445': 'Food and Beverage Stores',
            '446': 'Health and Personal Care Stores',
            '447': 'Gasoline Stations',
            '448': 'Clothing and Clothing Accessories Stores',
            '451': 'Sporting Goods, Hobby, Musical Instrument, and Book Stores',
            '452': 'General Merchandise Stores',
            '453': 'Miscellaneous Store Retailers',
            '454': 'Nonstore Retailers',
            '511': 'Publishing Industries (except Internet)',
            '512': 'Motion Picture and Sound Recording Industries',
            '515': 'Broadcasting (except Internet)',
            '517': 'Telecommunications',
            '518': 'Data Processing, Hosting, and Related Services',
            '519': 'Other Information Services',
            '522': 'Credit Intermediation and Related Activities',
            '523': 'Securities, Commodity Contracts, and Other Financial Investments',
            '524': 'Insurance Carriers and Related Activities',
            '525': 'Funds, Trusts, and Other Financial Vehicles',
            '531': 'Real Estate',
            '532': 'Rental and Leasing Services',
            '533': 'Lessors of Nonfinancial Intangible Assets',
            '541': 'Professional, Scientific, and Technical Services',
            '551': 'Management of Companies and Enterprises',
            '561': 'Administrative and Support Services',
            '562': 'Waste Management and Remediation Services',
            '611': 'Educational Services',
            '621': 'Ambulatory Health Care Services',
            '622': 'Hospitals',
            '623': 'Nursing and Residential Care Facilities',
            '624': 'Social Assistance',
            '711': 'Performing Arts, Spectator Sports, and Related Industries',
            '712': 'Museums, Historical Sites, and Similar Institutions',
            '713': 'Amusement, Gambling, and Recreation Industries',
            '721': 'Accommodation',
            '722': 'Food Services and Drinking Places',
            '811': 'Repair and Maintenance',
            '812': 'Personal and Laundry Services',
            '813': 'Religious, Grantmaking, Civic, Professional, and Similar Organizations',
            '814': 'Private Households',
            '921': 'Executive, Legislative, and Other General Government Support',
            '922': 'Justice, Public Order, and Safety Activities',
            '923': 'Administration of Human Resource Programs',
            '924': 'Administration of Environmental Quality Programs',
            '925': 'Administration of Housing Programs, Urban Planning, and Community Development',
            '926': 'Administration of Economic Programs',
            '927': 'Space Research and Technology',
            '928': 'National Security and International Affairs',
            
            # Financial advisor specific codes
            '5239': 'Other Financial Investment Activities',
            '52393': 'Investment Advice',
            '523930': 'Investment Advice',
            '5412': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '54121': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '541211': 'Offices of Certified Public Accountants',
            '541213': 'Tax Preparation Services',
            '541214': 'Payroll Services',
            '541219': 'Other Accounting Services'
        }
    
    def get_description(self, naics_code: str) -> str:
        """Get description for NAICS code with fallback to shorter codes"""
        # Handle None/empty input
        if not naics_code:
            return "Unknown Industry"
            
        # Remove any non-numeric characters and handle different lengths
        clean_code = ''.join(filter(str.isdigit, str(naics_code)))
        
        # Try exact match first
        if clean_code in self.naics_hierarchy:
            return self.naics_hierarchy[clean_code]
        
        # Try progressively shorter codes for hierarchical fallback
        for length in range(len(clean_code) - 1, 1, -1):
            truncated = clean_code[:length]
            if truncated in self.naics_hierarchy:
                return self.naics_hierarchy[truncated]
        
        # Final fallback for 2-digit sectors
        if len(clean_code) >= 2:
            sector = clean_code[:2]
            if sector in self.naics_hierarchy:
                return self.naics_hierarchy[sector]
        
        return f"Industry Code {clean_code}"
    
    def get_short_description(self, naics_code: str) -> str:
        """Get shortened description for charts and compact displays"""
        full_desc = self.get_description(naics_code)
        
        # Shorten common long names for better chart display
        shortened_map = {
            'Professional, Scientific, and Technical Services': 'Professional Services',
            'Administrative and Support and Waste Management Services': 'Admin & Support Services',
            'Health Care and Social Assistance': 'Healthcare',
            'Accommodation and Food Services': 'Hospitality',
            'Transportation and Warehousing': 'Transportation',
            'Real Estate and Rental and Leasing': 'Real Estate',
            'Finance and Insurance': 'Financial Services',
            'Arts, Entertainment, and Recreation': 'Entertainment',
            'Other Services (except Public Administration)': 'Other Services',
            'Educational Services': 'Education',
            'Information': 'Information/Tech',
            'Administrative and Support Services': 'Admin Services',
            'Securities, Commodity Contracts, and Other Financial Investments': 'Securities & Investments'
        }
        
        return shortened_map.get(full_desc, full_desc)
    
    def is_financial_services(self, naics_code: str) -> bool:
        """Check if NAICS code is related to financial services"""
        clean_code = ''.join(filter(str.isdigit, naics_code))
        
        # Check if code starts with financial service prefixes
        financial_prefixes = ['52', '523', '5239', '541211', '541213', '541214', '541219']
        
        for prefix in financial_prefixes:
            if clean_code.startswith(prefix):
                return True
        
        return False
    
    def get_financial_naics_codes(self) -> List[str]:
        """Get list of financial advisor related NAICS codes"""
        return list(self.financial_naics.keys())
    
    def filter_by_length(self, naics_codes: List[str], length: int) -> List[str]:
        """Filter NAICS codes by digit length"""
        return [code for code in naics_codes if len(''.join(filter(str.isdigit, code))) == length]
    
    def group_by_level(self, naics_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Group NAICS data by hierarchy level"""
        grouped = {
            '2-digit': [],
            '3-digit': [],
            '4-digit': [],
            '5-digit': [],
            '6-digit': []
        }
        
        for item in naics_data:
            naics = item.get('naics', '')
            clean_code = ''.join(filter(str.isdigit, naics))
            
            if len(clean_code) == 2:
                grouped['2-digit'].append(item)
            elif len(clean_code) == 3:
                grouped['3-digit'].append(item)
            elif len(clean_code) == 4:
                grouped['4-digit'].append(item)
            elif len(clean_code) == 5:
                grouped['5-digit'].append(item)
            elif len(clean_code) == 6:
                grouped['6-digit'].append(item)
        
        return grouped
    
    def get_parent_code(self, naics_code: str) -> Optional[str]:
        """Get parent NAICS code"""
        clean_code = ''.join(filter(str.isdigit, naics_code))
        
        if len(clean_code) > 2:
            return clean_code[:-1]
        
        return None
    
    def get_children_codes(self, parent_code: str, all_codes: List[str]) -> List[str]:
        """Get child NAICS codes"""
        clean_parent = ''.join(filter(str.isdigit, parent_code))
        children = []
        
        for code in all_codes:
            clean_code = ''.join(filter(str.isdigit, code))
            if clean_code.startswith(clean_parent) and len(clean_code) == len(clean_parent) + 1:
                children.append(clean_code)
        
        return children
