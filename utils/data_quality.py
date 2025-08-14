import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class DataQualityManager:
    """Manages data quality assessment, suppression, and provenance tracking"""
    
    def __init__(self):
        self.suppression_threshold = 3  # k-anonymity threshold
        self.quality_thresholds = {
            'excellent': 95,
            'good': 85, 
            'acceptable': 70,
            'poor': 50
        }
        
    def apply_small_cell_suppression(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], 
                                   count_fields: List[str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Apply small cell suppression to protect privacy"""
        if isinstance(data, dict):
            return self._suppress_single_record(data, count_fields)
        elif isinstance(data, list):
            return [self._suppress_single_record(record, count_fields) for record in data]
        else:
            return data
    
    def _suppress_single_record(self, record: Dict[str, Any], count_fields: List[str]) -> Dict[str, Any]:
        """Apply suppression to a single record"""
        suppressed_record = record.copy()
        suppression_applied = False
        
        for field in count_fields:
            value = record.get(field)
            
            if value is not None and isinstance(value, (int, float)):
                if 0 < value < self.suppression_threshold:
                    suppressed_record[field] = None
                    suppressed_record[f'{field}_suppressed'] = True
                    suppressed_record['suppression_reason'] = f'Value <{self.suppression_threshold}'
                    suppression_applied = True
                else:
                    suppressed_record[f'{field}_suppressed'] = False
        
        suppressed_record['has_suppression'] = suppression_applied
        return suppressed_record
    
    def assess_data_quality(self, data: Dict[str, Any], data_source: str = '') -> Dict[str, Any]:
        """Assess overall data quality for a dataset"""
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            return {
                'overall_score': 0,
                'grade': 'F',
                'completeness_score': 0,
                'freshness_score': 0,
                'consistency_score': 0,
                'issues': ['Invalid data format'],
                'recommendations': ['Check data structure'],
                'data_source': data_source
            }
        
        quality_score = 100
        issues = []
        recommendations = []
        
        # Check completeness
        completeness_score, completeness_issues = self._assess_completeness(data)
        quality_score = min(quality_score, completeness_score)
        issues.extend(completeness_issues)
        
        # Check freshness
        freshness_score, freshness_issues = self._assess_freshness(data)
        quality_score = min(quality_score, freshness_score)
        issues.extend(freshness_issues)
        
        # Check consistency
        consistency_score, consistency_issues = self._assess_consistency(data)
        quality_score = min(quality_score, consistency_score)
        issues.extend(consistency_issues)
        
        # Generate grade
        grade = self._calculate_grade(quality_score)
        
        # Generate recommendations
        if completeness_score < 85:
            recommendations.append('Consider refreshing data from source')
        if freshness_score < 70:
            recommendations.append('Data may be outdated - check for newer releases')
        if consistency_score < 80:
            recommendations.append('Review data validation rules')
        
        return {
            'overall_score': quality_score,
            'grade': grade,
            'completeness_score': completeness_score,
            'freshness_score': freshness_score,
            'consistency_score': consistency_score,
            'issues': issues,
            'recommendations': recommendations,
            'data_source': data_source,
            'assessed_at': datetime.now().isoformat()
        }
    
    def _assess_completeness(self, data: Dict[str, Any]) -> tuple:
        """Assess data completeness"""
        score = 100
        issues = []
        
        # Check for required fields
        required_fields = ['county_fips', 'source_url', 'retrieved_at']
        missing_required = [f for f in required_fields if not data.get(f)]
        
        if missing_required:
            score -= len(missing_required) * 20
            issues.append(f'Missing required fields: {", ".join(missing_required)}')
        
        # Check for empty values in key fields
        key_fields = ['naics', 'establishments', 'employment', 'amount']
        empty_key_fields = [f for f in key_fields if f in data and not data[f]]
        
        if empty_key_fields:
            score -= len(empty_key_fields) * 5
            issues.append(f'Empty key fields: {", ".join(empty_key_fields)}')
        
        # Check suppression rate
        suppressed_fields = [k for k, v in data.items() if k.endswith('_suppressed') and v]
        suppression_rate = len(suppressed_fields) / len(data) * 100
        
        if suppression_rate > 50:
            score -= 30
            issues.append(f'High suppression rate: {suppression_rate:.1f}%')
        elif suppression_rate > 25:
            score -= 15
            issues.append(f'Moderate suppression rate: {suppression_rate:.1f}%')
        
        return max(0, score), issues
    
    def _assess_freshness(self, data: Dict[str, Any]) -> tuple:
        """Assess data freshness"""
        score = 100
        issues = []
        
        retrieved_at = data.get('retrieved_at')
        if not retrieved_at:
            return 50, ['No retrieval timestamp available']
        
        try:
            retrieved_date = datetime.fromisoformat(retrieved_at.replace('Z', '+00:00'))
            age_days = (datetime.now() - retrieved_date).days
            
            if age_days <= 1:
                # Fresh data
                pass
            elif age_days <= 7:
                score -= 5
            elif age_days <= 30:
                score -= 15
                issues.append(f'Data is {age_days} days old')
            elif age_days <= 90:
                score -= 30
                issues.append(f'Data is {age_days} days old - consider refresh')
            else:
                score -= 50
                issues.append(f'Data is {age_days} days old - refresh recommended')
                
        except (ValueError, TypeError) as e:
            score -= 20
            issues.append('Invalid retrieval timestamp format')
        
        # Check data vintage (for annual data like CBP)
        data_year = data.get('year')
        if data_year:
            current_year = datetime.now().year
            year_lag = current_year - data_year
            
            if year_lag > 3:
                score -= 20
                issues.append(f'Data is {year_lag} years behind current year')
        
        return max(0, score), issues
    
    def _assess_consistency(self, data: Dict[str, Any]) -> tuple:
        """Assess data consistency"""
        score = 100
        issues = []
        
        # Check numeric consistency
        establishments = data.get('establishments')
        employment = data.get('employment')
        
        if establishments and employment:
            if isinstance(establishments, (int, float)) and isinstance(employment, (int, float)):
                avg_emp_per_est = employment / establishments
                
                # Flag unusual ratios
                if avg_emp_per_est > 500:
                    score -= 10
                    issues.append(f'Unusually high employment per establishment: {avg_emp_per_est:.1f}')
                elif avg_emp_per_est < 1:
                    score -= 15
                    issues.append(f'Employment less than establishments: {avg_emp_per_est:.1f}')
        
        # Check payroll consistency
        annual_payroll = data.get('annual_payroll')
        if annual_payroll and employment:
            if isinstance(annual_payroll, (int, float)) and isinstance(employment, (int, float)):
                avg_pay_per_emp = annual_payroll / employment
                
                # Flag unusual payroll levels (very rough bounds)
                if avg_pay_per_emp > 200000:
                    score -= 5
                    issues.append(f'Unusually high average pay: ${avg_pay_per_emp:,.0f}')
                elif avg_pay_per_emp < 15000:
                    score -= 5
                    issues.append(f'Unusually low average pay: ${avg_pay_per_emp:,.0f}')
        
        # Check NAICS code format
        naics = data.get('naics')
        if naics:
            naics_str = str(naics)
            if not naics_str.isdigit() or len(naics_str) not in [2, 3, 4, 5, 6]:
                score -= 10
                issues.append(f'Invalid NAICS code format: {naics}')
        
        # Check FIPS code format
        county_fips = data.get('county_fips')
        if county_fips:
            fips_str = str(county_fips)
            if not fips_str.isdigit() or len(fips_str) != 5:
                score -= 15
                issues.append(f'Invalid county FIPS format: {county_fips}')
        
        return max(0, score), issues
    
    def _calculate_grade(self, score: int) -> str:
        """Calculate letter grade from numeric score"""
        if score >= self.quality_thresholds['excellent']:
            return 'A'
        elif score >= self.quality_thresholds['good']:
            return 'B'
        elif score >= self.quality_thresholds['acceptable']:
            return 'C'
        elif score >= self.quality_thresholds['poor']:
            return 'D'
        else:
            return 'F'
    
    def create_provenance_record(self, data: Dict[str, Any], processing_steps: List[str] = None) -> Dict[str, Any]:
        """Create comprehensive provenance record"""
        provenance = {
            'source_url': data.get('source_url', ''),
            'source_license': data.get('license', ''),
            'retrieved_at': data.get('retrieved_at', ''),
            'county_fips': data.get('county_fips', ''),
            'naics_code': data.get('naics', ''),
            'data_vintage': data.get('year', ''),
            'processing_steps': processing_steps or [],
            'quality_assessment': self.assess_data_quality(data),
            'suppression_applied': data.get('has_suppression', False),
            'created_at': datetime.now().isoformat()
        }
        
        return provenance
    
    def validate_data_ranges(self, data: List[Dict[str, Any]], field: str, 
                           min_val: Optional[float] = None, max_val: Optional[float] = None) -> List[Dict[str, Any]]:
        """Validate data ranges and flag outliers"""
        if not data or not field:
            return []
        
        values = [d.get(field) for d in data if d.get(field) is not None]
        if not values:
            return []
        
        # Calculate statistics
        df = pd.DataFrame({field: values})
        stats = df[field].describe()
        
        # Define outlier bounds (using IQR method)
        q1 = stats['25%']
        q3 = stats['75%']
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Override with explicit bounds if provided
        if min_val is not None:
            lower_bound = min_val
        if max_val is not None:
            upper_bound = max_val
        
        # Flag outliers
        outliers = []
        for record in data:
            value = record.get(field)
            if value is not None:
                if value < lower_bound or value > upper_bound:
                    outlier_record = record.copy()
                    outlier_record['outlier_flag'] = True
                    outlier_record['outlier_reason'] = f'{field} value {value} outside normal range [{lower_bound:.0f}, {upper_bound:.0f}]'
                    outliers.append(outlier_record)
        
        return outliers
    
    def generate_data_quality_report(self, county_fips: str, all_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate comprehensive data quality report for county"""
        report = {
            'county_fips': county_fips,
            'report_generated_at': datetime.now().isoformat(),
            'data_sources': {},
            'overall_quality': {},
            'recommendations': []
        }
        
        all_scores = []
        all_issues = []
        
        # Assess each data source
        for source, records in all_data.items():
            if not records:
                continue
                
            source_scores = []
            source_issues = []
            
            for record in records[:10]:  # Sample first 10 records
                quality = self.assess_data_quality(record, source)
                source_scores.append(quality['overall_score'])
                source_issues.extend(quality['issues'])
            
            avg_score = sum(source_scores) / len(source_scores) if source_scores else 0
            
            report['data_sources'][source] = {
                'record_count': len(records),
                'avg_quality_score': avg_score,
                'grade': self._calculate_grade(avg_score),
                'common_issues': list(set(source_issues))
            }
            
            all_scores.append(avg_score)
            all_issues.extend(source_issues)
        
        # Overall quality
        if all_scores:
            overall_score = sum(all_scores) / len(all_scores)
            report['overall_quality'] = {
                'score': overall_score,
                'grade': self._calculate_grade(overall_score),
                'data_sources_count': len(all_data),
                'total_records': sum(len(records) for records in all_data.values())
            }
            
            # Generate recommendations
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            # Most common issues become recommendations
            common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for issue, count in common_issues:
                if 'outdated' in issue.lower() or 'refresh' in issue.lower():
                    report['recommendations'].append('Schedule more frequent data refreshes')
                elif 'missing' in issue.lower():
                    report['recommendations'].append('Improve data validation and completeness checks')
                elif 'suppression' in issue.lower():
                    report['recommendations'].append('High suppression rates may indicate data sparsity')
        
        return report
    
    def format_suppression_message(self, field_name: str, reason: str = None) -> str:
        """Format user-friendly suppression message"""
        base_message = f"{field_name.replace('_', ' ').title()}: —"
        
        if reason:
            return f"{base_message} ({reason})"
        else:
            return f"{base_message} (suppressed for privacy)"
    
    def get_data_quality_badge(self, quality_score: int) -> Dict[str, str]:
        """Get data quality badge information"""
        grade = self._calculate_grade(quality_score)
        
        badge_colors = {
            'A': {'color': '#28a745', 'bg_color': '#d4edda', 'text': 'Excellent'},
            'B': {'color': '#6f42c1', 'bg_color': '#e2d9f3', 'text': 'Good'},
            'C': {'color': '#fd7e14', 'bg_color': '#fff3cd', 'text': 'Acceptable'},
            'D': {'color': '#dc3545', 'bg_color': '#f8d7da', 'text': 'Poor'},
            'F': {'color': '#6c757d', 'bg_color': '#f8f9fa', 'text': 'Needs Review'}
        }
        
        return {
            'grade': grade,
            'score': quality_score,
            'label': f"Quality: {badge_colors[grade]['text']} ({grade})",
            'color': badge_colors[grade]['color'],
            'bg_color': badge_colors[grade]['bg_color']
        }
