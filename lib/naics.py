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
        
        # NAICS hierarchy
        self.naics_hierarchy = {
            '52': 'Finance and Insurance',
            '523': 'Securities, Commodity Contracts, and Other Financial Investments',
            '5239': 'Other Financial Investment Activities',
            '52393': 'Investment Advice',
            '523930': 'Investment Advice',
            '54': 'Professional, Scientific, and Technical Services',
            '541': 'Professional, Scientific, and Technical Services',
            '5412': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '54121': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '541211': 'Offices of Certified Public Accountants',
            '541213': 'Tax Preparation Services',
            '541214': 'Payroll Services',
            '541219': 'Other Accounting Services'
        }
    
    def get_description(self, naics_code: str) -> str:
        """Get description for NAICS code"""
        # Remove any non-numeric characters and handle different lengths
        clean_code = ''.join(filter(str.isdigit, naics_code))
        
        # Try exact match first
        if clean_code in self.naics_hierarchy:
            return self.naics_hierarchy[clean_code]
        
        # Try progressively shorter codes
        for length in range(len(clean_code) - 1, 0, -1):
            truncated = clean_code[:length]
            if truncated in self.naics_hierarchy:
                return self.naics_hierarchy[truncated]
        
        return f"NAICS {clean_code}"
    
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
