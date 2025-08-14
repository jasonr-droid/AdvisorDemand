import logging
from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta, timezone
import calendar

logger = logging.getLogger(__name__)

class DateUtils:
    """Date utility functions for financial data analysis"""
    
    def __init__(self):
        self.common_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y', 
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%Y',
            '%Y-%m'
        ]
    
    def parse_date(self, date_str: Union[str, None]) -> Optional[datetime]:
        """Parse date string using common formats"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        for fmt in self.common_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def format_date(self, date_obj: datetime, format_type: str = 'display') -> str:
        """Format datetime object for display"""
        if not date_obj:
            return 'N/A'
        
        if format_type == 'display':
            return date_obj.strftime('%B %d, %Y')
        elif format_type == 'short':
            return date_obj.strftime('%m/%d/%Y')
        elif format_type == 'iso':
            return date_obj.strftime('%Y-%m-%d')
        elif format_type == 'year':
            return date_obj.strftime('%Y')
        elif format_type == 'quarter':
            quarter = (date_obj.month - 1) // 3 + 1
            return f"{date_obj.year}Q{quarter}"
        else:
            return date_obj.strftime('%Y-%m-%d')
    
    def get_fiscal_year(self, date_obj: datetime, fy_start_month: int = 10) -> int:
        """Get fiscal year from date (default: US federal FY starts Oct 1)"""
        if not date_obj:
            return datetime.now().year
        
        if date_obj.month >= fy_start_month:
            return date_obj.year + 1
        else:
            return date_obj.year
    
    def get_quarter_info(self, date_obj: datetime) -> Dict[str, Any]:
        """Get quarter information from date"""
        if not date_obj:
            return {}
        
        quarter = (date_obj.month - 1) // 3 + 1
        quarter_start_month = (quarter - 1) * 3 + 1
        quarter_end_month = quarter * 3
        
        return {
            'year': date_obj.year,
            'quarter': quarter,
            'quarter_name': f"Q{quarter}",
            'quarter_full': f"{date_obj.year}Q{quarter}",
            'start_month': quarter_start_month,
            'end_month': quarter_end_month,
            'start_date': datetime(date_obj.year, quarter_start_month, 1),
            'end_date': datetime(date_obj.year, quarter_end_month, 
                               calendar.monthrange(date_obj.year, quarter_end_month)[1])
        }
    
    def date_ago(self, days: int = 0, months: int = 0, years: int = 0) -> datetime:
        """Get date from specified time ago"""
        now = datetime.now()
        
        # Calculate years and months
        target_year = now.year - years
        target_month = now.month - months
        
        # Handle month underflow
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        # Handle month overflow
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        try:
            result = datetime(target_year, target_month, now.day, now.hour, now.minute, now.second)
        except ValueError:
            # Handle cases like Feb 31 -> Feb 28/29
            last_day = calendar.monthrange(target_year, target_month)[1]
            result = datetime(target_year, target_month, min(now.day, last_day), 
                            now.hour, now.minute, now.second)
        
        # Subtract days
        result = result - timedelta(days=days)
        
        return result
    
    def get_data_freshness_info(self, retrieved_at: str) -> Dict[str, Any]:
        """Get data freshness information"""
        if not retrieved_at:
            return {'status': 'unknown', 'message': 'No retrieval date available'}
        
        retrieved_date = self.parse_date(retrieved_at)
        if not retrieved_date:
            return {'status': 'unknown', 'message': 'Invalid retrieval date'}
        
        now = datetime.now()
        age = now - retrieved_date
        
        if age.days == 0:
            status = 'fresh'
            message = 'Updated today'
        elif age.days == 1:
            status = 'fresh'
            message = 'Updated yesterday'
        elif age.days <= 7:
            status = 'recent'
            message = f'Updated {age.days} days ago'
        elif age.days <= 30:
            status = 'acceptable'
            message = f'Updated {age.days} days ago'
        elif age.days <= 90:
            status = 'stale'
            message = f'Updated {age.days} days ago'
        else:
            status = 'very_stale'
            message = f'Updated {age.days} days ago'
        
        return {
            'status': status,
            'message': message,
            'days_old': age.days,
            'retrieved_date': retrieved_date,
            'formatted_date': self.format_date(retrieved_date, 'display')
        }
    
    def get_reporting_period_info(self, year: int, quarter: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a reporting period"""
        info = {
            'year': year,
            'period_type': 'annual' if not quarter else 'quarterly'
        }
        
        if quarter:
            q_num = int(quarter.replace('Q', ''))
            quarter_info = self.get_quarter_info(datetime(year, q_num * 3, 1))
            info.update(quarter_info)
            info['display_name'] = f"{year} Q{q_num}"
        else:
            info['display_name'] = str(year)
        
        # Determine if this is current, recent, or historical
        now = datetime.now()
        current_year = now.year
        current_quarter = (now.month - 1) // 3 + 1
        
        if quarter:
            if year == current_year and q_num == current_quarter:
                info['recency'] = 'current'
            elif year == current_year and q_num < current_quarter:
                info['recency'] = 'recent'
            elif year == current_year - 1:
                info['recency'] = 'recent'
            else:
                info['recency'] = 'historical'
        else:
            if year == current_year:
                info['recency'] = 'current'
            elif year == current_year - 1:
                info['recency'] = 'recent'
            else:
                info['recency'] = 'historical'
        
        return info
    
    def validate_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Validate and parse date range"""
        start_dt = self.parse_date(start_date)
        end_dt = self.parse_date(end_date)
        
        if not start_dt or not end_dt:
            return {'valid': False, 'error': 'Invalid date format'}
        
        if start_dt > end_dt:
            return {'valid': False, 'error': 'Start date must be before end date'}
        
        # Check if range is too large
        if (end_dt - start_dt).days > 2 * 365:  # 2 years
            return {'valid': False, 'error': 'Date range too large (max 2 years)'}
        
        return {
            'valid': True,
            'start_date': start_dt,
            'end_date': end_dt,
            'duration_days': (end_dt - start_dt).days,
            'formatted_range': f"{self.format_date(start_dt, 'short')} - {self.format_date(end_dt, 'short')}"
        }
    
    def get_as_of_date(self, data_source: str, data_year: Optional[int] = None, 
                      data_quarter: Optional[str] = None) -> str:
        """Generate 'as of' date string for data sources"""
        if data_source.upper() in ['CBP', 'COUNTY_BUSINESS_PATTERNS']:
            if data_year:
                return f"as of {data_year} (annual)"
            return "as of latest available year"
        
        elif data_source.upper() in ['QCEW', 'QUARTERLY_CENSUS']:
            if data_year and data_quarter:
                return f"as of {data_year} {data_quarter}"
            return "as of latest available quarter"
        
        elif data_source.upper() in ['SBA', 'SBA_LOANS']:
            return "as of latest available data"
        
        elif data_source.upper() in ['SAM', 'USASPENDING']:
            return "as of active opportunities"
        
        else:
            return "as of latest update"
    
    def get_time_series_gaps(self, dates: list) -> list:
        """Identify gaps in time series data"""
        if len(dates) < 2:
            return []
        
        # Parse and sort dates
        parsed_dates = []
        for date_str in dates:
            parsed = self.parse_date(date_str)
            if parsed:
                parsed_dates.append(parsed)
        
        parsed_dates.sort()
        gaps = []
        
        for i in range(1, len(parsed_dates)):
            prev_date = parsed_dates[i-1]
            curr_date = parsed_dates[i]
            gap_days = (curr_date - prev_date).days
            
            # Consider gaps > 40 days as significant
            if gap_days > 40:
                gaps.append({
                    'start': prev_date,
                    'end': curr_date,
                    'gap_days': gap_days,
                    'formatted': f"{self.format_date(prev_date, 'short')} to {self.format_date(curr_date, 'short')}"
                })
        
        return gaps
    
    def is_recent(self, date_str: str, threshold_days: int = 30) -> bool:
        """Check if date is within threshold of current date"""
        date_obj = self.parse_date(date_str)
        if not date_obj:
            return False
        
        age = datetime.now() - date_obj
        return age.days <= threshold_days

# Global instance
date_utils = DateUtils()
