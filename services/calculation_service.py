import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from lib.utils import DataUtils

class CalculationService:
    """Service for calculations, scoring, and derived metrics"""
    
    def __init__(self):
        self.data_utils = DataUtils()
        self.logger = logging.getLogger(__name__)
    
    def calculate_capital_access_index(self, 
                                     sba_data: pd.DataFrame,
                                     establishments_count: int,
                                     amount_weight: float = 0.6,
                                     count_weight: float = 0.4) -> Dict[str, Any]:
        """Calculate Capital Access Index from SBA data"""
        try:
            if sba_data.empty or establishments_count == 0:
                return {
                    'index_score': 0.0,
                    'loans_per_1k_firms': 0.0,
                    'amount_per_1k_firms': 0.0,
                    'raw_metrics': {},
                    'normalized_metrics': {},
                    'methodology': 'Insufficient data for calculation'
                }
            
            # Calculate raw metrics
            total_loans = len(sba_data)
            total_amount = sba_data['amount'].sum()
            
            loans_per_1k = (total_loans / establishments_count) * 1000
            amount_per_1k = (total_amount / establishments_count) * 1000
            
            raw_metrics = {
                'loans_per_1k_firms': loans_per_1k,
                'amount_per_1k_firms': amount_per_1k,
                'total_loans': total_loans,
                'total_amount': total_amount,
                'establishments': establishments_count
            }
            
            # For normalization, we need reference values (could be from historical data or benchmarks)
            # Using reasonable ranges for financial services counties
            loans_per_1k_range = (0, 50)  # 0-50 loans per 1k firms
            amount_per_1k_range = (0, 5000000)  # $0-5M per 1k firms
            
            # Min-max normalization to 0-100 scale
            normalized_loans = self._min_max_normalize(loans_per_1k, loans_per_1k_range[0], loans_per_1k_range[1]) * 100
            normalized_amount = self._min_max_normalize(amount_per_1k, amount_per_1k_range[0], amount_per_1k_range[1]) * 100
            
            normalized_metrics = {
                'normalized_loans_per_1k': normalized_loans,
                'normalized_amount_per_1k': normalized_amount
            }
            
            # Calculate weighted index
            index_score = (normalized_amount * amount_weight) + (normalized_loans * count_weight)
            
            # Ensure score is between 0-100
            index_score = max(0, min(100, index_score))
            
            methodology = f"Weighted average: amount_per_1k ({amount_weight}) + count_per_1k ({count_weight}), min-max normalized 0-100"
            
            return {
                'index_score': round(index_score, 1),
                'loans_per_1k_firms': round(loans_per_1k, 1),
                'amount_per_1k_firms': round(amount_per_1k, 0),
                'raw_metrics': raw_metrics,
                'normalized_metrics': normalized_metrics,
                'methodology': methodology
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating capital access index: {str(e)}")
            return {
                'index_score': 0.0,
                'loans_per_1k_firms': 0.0,
                'amount_per_1k_firms': 0.0,
                'raw_metrics': {},
                'normalized_metrics': {},
                'methodology': f'Calculation error: {str(e)}'
            }
    
    def calculate_opportunity_score(self, 
                                  industry_data: pd.DataFrame,
                                  rfp_data: pd.DataFrame, 
                                  awards_data: pd.DataFrame,
                                  license_data: pd.DataFrame,
                                  formation_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall opportunity score from multiple signals"""
        try:
            signals = {}
            score_components = []
            
            # Industry growth signal (from employment trends)
            if not industry_data.empty and len(industry_data) > 1:
                employment_growth = self._calculate_employment_growth(industry_data)
                signals['employment_growth'] = employment_growth
                score_components.append(('employment_growth', employment_growth, 0.3))
            
            # Demand signals from RFPs
            if not rfp_data.empty:
                rfp_signal = self._calculate_rfp_signal(rfp_data)
                signals['rfp_activity'] = rfp_signal
                score_components.append(('rfp_activity', rfp_signal, 0.25))
            
            # Award activity signal
            if not awards_data.empty:
                award_signal = self._calculate_award_signal(awards_data)
                signals['award_activity'] = award_signal
                score_components.append(('award_activity', award_signal, 0.2))
            
            # Business formation signal
            if not formation_data.empty:
                formation_signal = self._calculate_formation_signal(formation_data)
                signals['formation_activity'] = formation_signal
                score_components.append(('formation_activity', formation_signal, 0.15))
            
            # License activity signal
            if not license_data.empty:
                license_signal = self._calculate_license_signal(license_data)
                signals['license_activity'] = license_signal
                score_components.append(('license_activity', license_signal, 0.1))
            
            # Calculate weighted opportunity score only if we have at least 2 signals
            if len(score_components) >= 2:
                total_weight = sum(weight for _, _, weight in score_components)
                weighted_score = sum(signal * weight for _, signal, weight in score_components)
                opportunity_score = (weighted_score / total_weight) * 100
                
                methodology = f"Weighted average of {len(score_components)} signals"
            else:
                opportunity_score = None
                methodology = "Insufficient signals for composite score (minimum 2 required)"
            
            return {
                'opportunity_score': round(opportunity_score, 1) if opportunity_score else None,
                'signals': signals,
                'components': score_components,
                'methodology': methodology,
                'signals_count': len(score_components)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating opportunity score: {str(e)}")
            return {
                'opportunity_score': None,
                'signals': {},
                'components': [],
                'methodology': f'Calculation error: {str(e)}',
                'signals_count': 0
            }
    
    def calculate_market_concentration(self, industry_data: pd.DataFrame, metric: str = 'employment') -> Dict[str, Any]:
        """Calculate market concentration metrics (HHI, etc.)"""
        try:
            if industry_data.empty or metric not in industry_data.columns:
                return {
                    'hhi': 0,
                    'top_4_concentration': 0,
                    'effective_competitors': 0,
                    'market_structure': 'Unknown'
                }
            
            # Filter out missing values and calculate market shares
            valid_data = industry_data[industry_data[metric].notna() & (industry_data[metric] > 0)]
            
            if valid_data.empty:
                return {
                    'hhi': 0,
                    'top_4_concentration': 0,
                    'effective_competitors': 0,
                    'market_structure': 'No data'
                }
            
            total = valid_data[metric].sum()
            market_shares = valid_data[metric] / total
            
            # Herfindahl-Hirschman Index
            hhi = (market_shares ** 2).sum() * 10000  # Scale to 0-10000
            
            # Top 4 concentration ratio
            top_4_shares = market_shares.nlargest(4).sum()
            top_4_concentration = top_4_shares * 100
            
            # Effective number of competitors (1/HHI)
            effective_competitors = 1 / (hhi / 10000) if hhi > 0 else len(valid_data)
            
            # Market structure classification
            if hhi < 1500:
                market_structure = 'Competitive'
            elif hhi < 2500:
                market_structure = 'Moderately Concentrated'
            else:
                market_structure = 'Highly Concentrated'
            
            return {
                'hhi': round(hhi, 0),
                'top_4_concentration': round(top_4_concentration, 1),
                'effective_competitors': round(effective_competitors, 1),
                'market_structure': market_structure,
                'total_firms': len(valid_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating market concentration: {str(e)}")
            return {
                'hhi': 0,
                'top_4_concentration': 0,
                'effective_competitors': 0,
                'market_structure': 'Error'
            }
    
    def calculate_growth_metrics(self, time_series_data: pd.DataFrame, 
                               value_column: str, 
                               time_column: str) -> Dict[str, Any]:
        """Calculate growth metrics from time series data"""
        try:
            if time_series_data.empty or len(time_series_data) < 2:
                return {
                    'cagr': None,
                    'recent_growth': None,
                    'trend': 'Insufficient data',
                    'volatility': None
                }
            
            # Sort by time
            sorted_data = time_series_data.sort_values(time_column)
            values = sorted_data[value_column].dropna()
            
            if len(values) < 2:
                return {
                    'cagr': None,
                    'recent_growth': None,
                    'trend': 'Insufficient data',
                    'volatility': None
                }
            
            # Calculate CAGR (Compound Annual Growth Rate)
            first_value = values.iloc[0]
            last_value = values.iloc[-1]
            years = len(values) - 1
            
            if first_value > 0 and years > 0:
                cagr = ((last_value / first_value) ** (1/years) - 1) * 100
            else:
                cagr = None
            
            # Recent growth (last period vs previous)
            if len(values) >= 2:
                recent_growth = ((values.iloc[-1] / values.iloc[-2]) - 1) * 100
            else:
                recent_growth = None
            
            # Trend analysis
            if cagr is not None:
                if cagr > 5:
                    trend = 'Strong Growth'
                elif cagr > 0:
                    trend = 'Moderate Growth'
                elif cagr > -5:
                    trend = 'Stable/Slight Decline'
                else:
                    trend = 'Declining'
            else:
                trend = 'Unknown'
            
            # Volatility (coefficient of variation)
            volatility = (values.std() / values.mean()) * 100 if values.mean() > 0 else None
            
            return {
                'cagr': round(cagr, 1) if cagr is not None else None,
                'recent_growth': round(recent_growth, 1) if recent_growth is not None else None,
                'trend': trend,
                'volatility': round(volatility, 1) if volatility is not None else None,
                'periods': len(values)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating growth metrics: {str(e)}")
            return {
                'cagr': None,
                'recent_growth': None,
                'trend': 'Error',
                'volatility': None
            }
    
    def calculate_benchmarks(self, county_data: Dict[str, Any], 
                           benchmark_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate percentile rankings against benchmark counties"""
        try:
            if not benchmark_data or not county_data:
                return {
                    'percentile_rankings': {},
                    'peer_comparison': 'No benchmark data available'
                }
            
            percentile_rankings = {}
            benchmark_df = pd.DataFrame(benchmark_data)
            
            # Calculate percentiles for key metrics
            metrics_to_compare = [
                'establishments', 'employment', 'annual_payroll',
                'sba_loans_per_1k', 'sba_amount_per_1k'
            ]
            
            for metric in metrics_to_compare:
                if metric in county_data and metric in benchmark_df.columns:
                    county_value = county_data[metric]
                    benchmark_values = benchmark_df[metric].dropna()
                    
                    if len(benchmark_values) > 0 and county_value is not None:
                        percentile = self.data_utils.calculate_percentile_rank(
                            benchmark_values.tolist(), county_value
                        )
                        percentile_rankings[metric] = percentile
            
            # Overall peer comparison
            if percentile_rankings:
                avg_percentile = np.mean(list(percentile_rankings.values()))
                
                if avg_percentile >= 75:
                    peer_comparison = 'Top Quartile'
                elif avg_percentile >= 50:
                    peer_comparison = 'Above Average'
                elif avg_percentile >= 25:
                    peer_comparison = 'Below Average'
                else:
                    peer_comparison = 'Bottom Quartile'
            else:
                peer_comparison = 'No comparable metrics'
            
            return {
                'percentile_rankings': percentile_rankings,
                'peer_comparison': peer_comparison,
                'benchmark_counties': len(benchmark_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating benchmarks: {str(e)}")
            return {
                'percentile_rankings': {},
                'peer_comparison': 'Error in calculation'
            }
    
    # Private helper methods
    def _min_max_normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Min-max normalization to 0-1 scale"""
        if max_val == min_val:
            return 0.5
        return max(0, min(1, (value - min_val) / (max_val - min_val)))
    
    def _calculate_employment_growth(self, industry_data: pd.DataFrame) -> float:
        """Calculate employment growth signal from industry data"""
        try:
            if 'employment' not in industry_data.columns or 'year' not in industry_data.columns:
                return 50  # Neutral score
            
            # Group by year and sum employment
            yearly_employment = industry_data.groupby('year')['employment'].sum().sort_index()
            
            if len(yearly_employment) < 2:
                return 50
            
            # Calculate growth rate
            recent_employment = yearly_employment.iloc[-1]
            previous_employment = yearly_employment.iloc[-2]
            
            if previous_employment > 0:
                growth_rate = ((recent_employment / previous_employment) - 1) * 100
                
                # Convert to 0-100 signal (50 = no growth)
                # Positive growth increases signal, negative decreases
                signal = 50 + (growth_rate * 2)  # 1% growth = 2 point increase
                return max(0, min(100, signal))
            
            return 50
            
        except Exception as e:
            self.logger.error(f"Error calculating employment growth: {str(e)}")
            return 50
    
    def _calculate_rfp_signal(self, rfp_data: pd.DataFrame) -> float:
        """Calculate RFP activity signal"""
        try:
            # Recent RFP activity (last 90 days) vs historical
            recent_cutoff = datetime.now() - pd.Timedelta(days=90)
            
            if 'posted_date' in rfp_data.columns:
                rfp_data['posted_date'] = pd.to_datetime(rfp_data['posted_date'], errors='coerce')
                recent_rfps = rfp_data[rfp_data['posted_date'] >= recent_cutoff]
                total_rfps = len(rfp_data)
                recent_count = len(recent_rfps)
                
                if total_rfps > 0:
                    # Higher recent activity relative to total suggests increasing demand
                    recent_ratio = (recent_count / total_rfps) * 100
                    
                    # Convert to signal (more recent activity = higher signal)
                    # Assume 25% recent activity = 50 (neutral), scale accordingly
                    signal = (recent_ratio / 25) * 50
                    return max(0, min(100, signal))
            
            # Fallback: total RFP count relative to typical range
            total_rfps = len(rfp_data)
            # Assume 0-20 RFPs is typical range for a county
            signal = (total_rfps / 20) * 100
            return max(0, min(100, signal))
            
        except Exception as e:
            self.logger.error(f"Error calculating RFP signal: {str(e)}")
            return 50
    
    def _calculate_award_signal(self, awards_data: pd.DataFrame) -> float:
        """Calculate federal awards activity signal"""
        try:
            if 'amount' in awards_data.columns:
                total_amount = awards_data['amount'].sum()
                award_count = len(awards_data)
                
                # Normalize based on typical county award amounts
                # Assume $0-10M is typical range
                amount_signal = (total_amount / 10_000_000) * 50
                
                # Normalize based on award count (0-50 awards typical)
                count_signal = (award_count / 50) * 50
                
                # Combined signal
                signal = (amount_signal + count_signal) / 2
                return max(0, min(100, signal))
            
            return 50
            
        except Exception as e:
            self.logger.error(f"Error calculating award signal: {str(e)}")
            return 50
    
    def _calculate_formation_signal(self, formation_data: pd.DataFrame) -> float:
        """Calculate business formation signal"""
        try:
            if 'applications_total' in formation_data.columns and len(formation_data) >= 2:
                # Sort by year and calculate trend
                sorted_data = formation_data.sort_values('year')
                recent_apps = sorted_data['applications_total'].iloc[-1]
                previous_apps = sorted_data['applications_total'].iloc[-2]
                
                if previous_apps > 0:
                    growth_rate = ((recent_apps / previous_apps) - 1) * 100
                    
                    # Convert growth rate to signal (0% growth = 50)
                    signal = 50 + (growth_rate * 2)
                    return max(0, min(100, signal))
            
            return 50
            
        except Exception as e:
            self.logger.error(f"Error calculating formation signal: {str(e)}")
            return 50
    
    def _calculate_license_signal(self, license_data: pd.DataFrame) -> float:
        """Calculate business license activity signal"""
        try:
            if 'issued_date' in license_data.columns:
                # Recent license activity
                recent_cutoff = datetime.now() - pd.Timedelta(days=90)
                license_data['issued_date'] = pd.to_datetime(license_data['issued_date'], errors='coerce')
                
                recent_licenses = license_data[license_data['issued_date'] >= recent_cutoff]
                total_licenses = len(license_data)
                recent_count = len(recent_licenses)
                
                # Normalize based on typical license counts (0-100 licenses)
                signal = (recent_count / 25) * 100  # 25 recent licenses = 100 signal
                return max(0, min(100, signal))
            
            return 50
            
        except Exception as e:
            self.logger.error(f"Error calculating license signal: {str(e)}")
            return 50
