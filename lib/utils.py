import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import streamlit as st

class DataUtils:
    """General data processing utilities"""
    
    @staticmethod
    def suppress_small_cells(data: Union[pd.DataFrame, List[Dict]], 
                           columns: List[str], 
                           threshold: int = 3) -> Union[pd.DataFrame, List[Dict]]:
        """Suppress small cells (k<3) for privacy compliance"""
        if isinstance(data, pd.DataFrame):
            df = data.copy()
            for col in columns:
                if col in df.columns:
                    mask = (df[col] > 0) & (df[col] < threshold)
                    df.loc[mask, col] = None
            return df
        
        elif isinstance(data, list):
            processed_data = []
            for item in data:
                processed_item = item.copy()
                for col in columns:
                    if col in processed_item:
                        value = processed_item[col]
                        if value is not None and 0 < value < threshold:
                            processed_item[col] = None
                processed_data.append(processed_item)
            return processed_data
        
        return data
    
    @staticmethod
    def standardize_currency(value: Union[str, float, int]) -> Optional[float]:
        """Standardize currency values"""
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, str):
            # Remove currency symbols and commas
            clean_value = value.replace('$', '').replace(',', '').strip()
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return float(value)
    
    @staticmethod
    def calculate_percentile_rank(values: List[float], target_value: float) -> float:
        """Calculate percentile rank of a value"""
        if not values or target_value is None:
            return 0.0
        
        values_array = np.array([v for v in values if v is not None])
        if len(values_array) == 0:
            return 0.0
        
        percentile = (np.sum(values_array <= target_value) / len(values_array)) * 100
        return round(percentile, 1)
    
    @staticmethod
    def format_large_number(value: Union[int, float], precision: int = 1) -> str:
        """Format large numbers with appropriate suffixes"""
        if pd.isna(value) or value is None:
            return "—"
        
        value = float(value)
        
        if abs(value) >= 1_000_000_000:
            return f"${value/1_000_000_000:.{precision}f}B"
        elif abs(value) >= 1_000_000:
            return f"${value/1_000_000:.{precision}f}M"
        elif abs(value) >= 1_000:
            return f"${value/1_000:.{precision}f}K"
        else:
            return f"${value:,.0f}"
    
    @staticmethod
    def format_number(value: Union[int, float], precision: int = 0) -> str:
        """Format numbers with commas"""
        if pd.isna(value) or value is None:
            return "—"
        
        if precision == 0:
            return f"{value:,.0f}"
        else:
            return f"{value:,.{precision}f}"
    
    @staticmethod
    def get_data_badge(label_type: str) -> str:
        """Get colored badge for data labels"""
        badge_colors = {
            'Observed': '🟢',
            'Proxy': '🟡', 
            'Estimated': '🟣'
        }
        
        return f"{badge_colors.get(label_type, '⚪')} {label_type}"
    
    @staticmethod
    def calculate_growth_rate(current_value: float, previous_value: float) -> Optional[float]:
        """Calculate growth rate between two values"""
        if pd.isna(current_value) or pd.isna(previous_value) or previous_value == 0:
            return None
        
        growth_rate = ((current_value - previous_value) / previous_value) * 100
        return round(growth_rate, 1)
    
    @staticmethod
    def get_as_of_date(retrieved_at: str) -> str:
        """Format 'as of' date from retrieved_at timestamp"""
        try:
            dt = datetime.fromisoformat(retrieved_at.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except (ValueError, AttributeError):
            return retrieved_at
    
    @staticmethod
    def merge_data_sources(datasets: List[pd.DataFrame], 
                          join_columns: List[str],
                          suffixes: List[str] = None) -> pd.DataFrame:
        """Merge multiple data sources on common columns"""
        if not datasets:
            return pd.DataFrame()
        
        result = datasets[0].copy()
        
        for i, df in enumerate(datasets[1:], 1):
            suffix = suffixes[i] if suffixes and i < len(suffixes) else f'_{i}'
            result = result.merge(df, on=join_columns, how='outer', suffixes=('', suffix))
        
        return result
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame, 
                            required_columns: List[str],
                            min_rows: int = 1) -> Dict[str, Any]:
        """Validate data quality and return summary"""
        quality_report = {
            'valid': True,
            'issues': [],
            'summary': {}
        }
        
        # Check if DataFrame exists and has minimum rows
        if df is None or df.empty:
            quality_report['valid'] = False
            quality_report['issues'].append('No data available')
            return quality_report
        
        if len(df) < min_rows:
            quality_report['valid'] = False
            quality_report['issues'].append(f'Insufficient data: {len(df)} rows (minimum {min_rows})')
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            quality_report['valid'] = False
            quality_report['issues'].append(f'Missing columns: {missing_columns}')
        
        # Data completeness
        for col in required_columns:
            if col in df.columns:
                completeness = (df[col].notna().sum() / len(df)) * 100
                quality_report['summary'][f'{col}_completeness'] = round(completeness, 1)
                
                if completeness < 50:
                    quality_report['issues'].append(f'Low completeness for {col}: {completeness:.1f}%')
        
        return quality_report
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, 
                     filename: str,
                     include_metadata: bool = True) -> str:
        """Export DataFrame to CSV with metadata"""
        if include_metadata:
            # Add metadata rows at the top
            metadata_rows = [
                ['# Financial Advisor Demand Analyzer Export'],
                ['# Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['# Source: Government data via official APIs'],
                ['# License: Public Domain / Open Data'],
                [''],  # Empty row before data
            ]
            
            # Create metadata DataFrame
            max_cols = len(df.columns)
            metadata_df = pd.DataFrame(metadata_rows)
            
            # Ensure metadata has same number of columns
            while len(metadata_df.columns) < max_cols:
                metadata_df[len(metadata_df.columns)] = ''
            
            # Combine metadata and data
            export_df = pd.concat([metadata_df, df], ignore_index=True)
        else:
            export_df = df
        
        return export_df.to_csv(index=False)
    
    @staticmethod
    def create_tooltip(metric_name: str, 
                      source: str, 
                      as_of_date: str,
                      calculation: str = None) -> str:
        """Create tooltip text for metrics"""
        tooltip_parts = [
            f"**{metric_name}**",
            f"Source: {source}",
            f"As of: {as_of_date}"
        ]
        
        if calculation:
            tooltip_parts.append(f"Calculation: {calculation}")
        
        return '\n'.join(tooltip_parts)
