import logging
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

class NAICSMapper:
    """NAICS code mapping and hierarchy management"""
    
    def __init__(self):
        # Financial services NAICS codes with descriptions
        self.financial_naics = {
            # Finance and Insurance
            '52': 'Finance and Insurance',
            '521': 'Monetary Authorities-Central Bank',
            '522': 'Credit Intermediation and Related Activities',
            '5221': 'Depository Credit Intermediation',
            '5222': 'Nondepository Credit Intermediation', 
            '5223': 'Activities Related to Credit Intermediation',
            '523': 'Securities, Commodity Contracts, and Other Financial Investments and Related Activities',
            '5231': 'Securities and Commodity Contracts Intermediation and Brokerage',
            '5232': 'Securities and Commodity Exchanges',
            '5239': 'Other Financial Investment Activities',
            '52391': 'Miscellaneous Intermediation',
            '52392': 'Portfolio Management',
            '52393': 'Investment Advice',
            '523930': 'Investment Advice',
            '524': 'Insurance Carriers and Related Activities',
            '5241': 'Insurance Carriers',
            '5242': 'Agencies, Brokerages, and Other Insurance Related Activities',
            '525': 'Funds, Trusts, and Other Financial Vehicles',
            '5251': 'Insurance and Employee Benefit Funds',
            '5259': 'Other Investment Pools and Funds',
            
            # Professional Services (Accounting/Financial)
            '541': 'Professional, Scientific, and Technical Services',
            '5412': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '54121': 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services',
            '541211': 'Offices of Certified Public Accountants',
            '541212': 'Offices of Other Accounting Services',
            '541213': 'Tax Preparation Services',
            '541214': 'Payroll Services',
            '541219': 'Other Accounting Services'
        }
        
        # NAICS hierarchy levels
        self.naics_levels = {
            2: 'Sector',
            3: 'Subsector', 
            4: 'Industry Group',
            5: 'NAICS Industry',
            6: 'National Industry'
        }
        
        # Core financial advisor related codes
        self.financial_advisor_codes = {
            '523930': 'Investment Advice',
            '52393': 'Investment Advice',
            '541211': 'Offices of Certified Public Accountants',
            '541213': 'Tax Preparation Services',
            '541214': 'Payroll Services',
            '52392': 'Portfolio Management'
        }
    
    def get_naics_title(self, naics_code: str) -> str:
        """Get title for NAICS code"""
        if not naics_code:
            return 'Unknown'
        
        # Clean the code
        naics_code = str(naics_code).strip()
        
        # Check our financial services mapping first
        if naics_code in self.financial_naics:
            return self.financial_naics[naics_code]
        
        # For codes not in our mapping, generate a generic title
        level = len(naics_code)
        level_name = self.naics_levels.get(level, 'Industry')
        return f"{level_name} {naics_code}"
    
    def get_naics_level(self, naics_code: str) -> int:
        """Get the hierarchy level of a NAICS code"""
        if not naics_code:
            return 0
        return len(str(naics_code).strip())
    
    def get_parent_naics(self, naics_code: str) -> Optional[str]:
        """Get parent NAICS code"""
        if not naics_code or len(naics_code) <= 2:
            return None
        
        return naics_code[:-1]
    
    def get_child_naics_pattern(self, naics_code: str) -> str:
        """Get SQL LIKE pattern for child NAICS codes"""
        if not naics_code:
            return '%'
        
        return f"{naics_code}%"
    
    def is_financial_services(self, naics_code: str) -> bool:
        """Check if NAICS code is related to financial services"""
        if not naics_code:
            return False
        
        naics_code = str(naics_code).strip()
        
        # Direct match
        if naics_code in self.financial_naics:
            return True
        
        # Check if it's a child of a financial services code
        for fs_code in self.financial_naics.keys():
            if naics_code.startswith(fs_code) and len(naics_code) > len(fs_code):
                return True
        
        return False
    
    def is_core_financial_advisor(self, naics_code: str) -> bool:
        """Check if NAICS code is core financial advisor business"""
        if not naics_code:
            return False
        
        naics_code = str(naics_code).strip()
        return naics_code in self.financial_advisor_codes
    
    def get_financial_services_codes(self, level: Optional[int] = None) -> List[str]:
        """Get all financial services NAICS codes at specified level"""
        if level is None:
            return list(self.financial_naics.keys())
        
        return [code for code in self.financial_naics.keys() if len(code) == level]
    
    def get_code_hierarchy(self, naics_code: str) -> List[Dict[str, str]]:
        """Get the full hierarchy for a NAICS code"""
        if not naics_code:
            return []
        
        hierarchy = []
        code = str(naics_code).strip()
        
        # Build hierarchy from sector down to current level
        for i in range(2, len(code) + 1):
            parent_code = code[:i]
            hierarchy.append({
                'code': parent_code,
                'title': self.get_naics_title(parent_code),
                'level': i,
                'level_name': self.naics_levels.get(i, 'Industry')
            })
        
        return hierarchy
    
    def filter_by_level(self, naics_codes: List[str], level: int) -> List[str]:
        """Filter NAICS codes by hierarchy level"""
        return [code for code in naics_codes if len(str(code).strip()) == level]
    
    def aggregate_to_level(self, naics_codes: List[str], target_level: int) -> Set[str]:
        """Aggregate NAICS codes to a higher level"""
        aggregated = set()
        
        for code in naics_codes:
            code = str(code).strip()
            if len(code) >= target_level:
                parent_code = code[:target_level]
                aggregated.add(parent_code)
        
        return aggregated
    
    def get_search_terms(self, naics_code: str) -> List[str]:
        """Get search terms associated with a NAICS code"""
        naics_code = str(naics_code).strip()
        
        search_terms = []
        title = self.get_naics_title(naics_code)
        
        # Add the title words
        search_terms.extend(title.lower().split())
        
        # Add specific terms based on code
        if naics_code.startswith('523'):
            search_terms.extend(['investment', 'securities', 'brokerage', 'financial advisor'])
        elif naics_code.startswith('5412'):
            search_terms.extend(['accounting', 'CPA', 'bookkeeping', 'tax', 'audit'])
        elif naics_code == '523930':
            search_terms.extend(['investment advice', 'financial planning', 'wealth management'])
        elif naics_code == '541211':
            search_terms.extend(['CPA', 'certified public accountant', 'audit'])
        elif naics_code == '541213':
            search_terms.extend(['tax preparation', 'tax services', 'IRS'])
        elif naics_code == '541214':
            search_terms.extend(['payroll', 'payroll services', 'HR'])
        
        return list(set(search_terms))  # Remove duplicates
    
    def validate_naics_code(self, naics_code: str) -> bool:
        """Validate NAICS code format"""
        if not naics_code:
            return False
        
        code = str(naics_code).strip()
        
        # Must be numeric
        if not code.isdigit():
            return False
        
        # Must be between 2-6 digits
        if len(code) < 2 or len(code) > 6:
            return False
        
        return True
    
    def get_industry_group_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of industry groups to specific codes"""
        mapping = {}
        
        # Group financial services codes
        mapping['Investment Services'] = ['523', '52393', '523930', '52392']
        mapping['Banking & Credit'] = ['521', '522', '5221', '5222', '5223']
        mapping['Insurance'] = ['524', '5241', '5242']
        mapping['Accounting Services'] = ['5412', '54121', '541211', '541212', '541219']
        mapping['Tax & Payroll'] = ['541213', '541214']
        mapping['Other Financial'] = ['525', '5251', '5259', '52391']
        
        return mapping
    
    def get_competitive_codes(self, naics_code: str) -> List[str]:
        """Get NAICS codes that represent competitive services"""
        naics_code = str(naics_code).strip()
        
        # Define competitive relationships
        competitive_mapping = {
            '523930': ['52392', '541211', '52393'],  # Investment advice competes with portfolio mgmt, CPAs
            '541211': ['541212', '541219', '523930'],  # CPAs compete with other accounting, investment advice
            '541213': ['541211', '541214'],  # Tax prep competes with CPAs, payroll
            '541214': ['541213', '541211'],  # Payroll competes with tax prep, CPAs
            '52392': ['523930', '52393'],  # Portfolio mgmt competes with investment advice
        }
        
        return competitive_mapping.get(naics_code, [])

# Global instance
naics_mapper = NAICSMapper()
