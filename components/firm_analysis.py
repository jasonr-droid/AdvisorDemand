import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.data_service import DataService
from utils.data_quality import DataQualityManager
from lib.date_utils import date_utils

logger = logging.getLogger(__name__)

class FirmAnalysis:
    """Firm demographics and formation analysis component"""
    
    def __init__(self, data_service: DataService, quality_manager: DataQualityManager):
        self.data_service = data_service
        self.quality_manager = quality_manager
    
    def render(self, county_fips: str):
        """Render complete firm analysis dashboard"""
        st.header("🏢 Firm Demographics")
        st.markdown("*Analyze firm age distribution, formation trends, and business applications*")
        
        # Get firm demographics data
        with st.spinner("Loading firm demographics data..."):
            firm_data = self.data_service.get_firm_demographics(county_fips)
        
        if not any(firm_data.values()):
            st.warning("No firm demographics data available for this county.")
            return
        
        # Summary metrics
        self._render_summary_metrics(firm_data)
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Age Distribution", 
            "📈 Formation Trends", 
            "📋 Business Applications",
            "🔍 Analysis"
        ])
        
        with tab1:
            self._render_age_distribution(firm_data.get('age_distribution', {}))
        
        with tab2:
            self._render_formation_trends(firm_data.get('formation_trends', []))
        
        with tab3:
            self._render_business_applications(firm_data.get('business_applications', {}))
        
        with tab4:
            self._render_detailed_analysis(firm_data, county_fips)
    
    def _render_summary_metrics(self, firm_data: Dict[str, Any]):
        """Render summary metrics cards"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Age distribution data
        age_dist = firm_data.get('age_distribution', {})
        age_buckets = age_dist.get('age_buckets', {})
        total_firms = age_dist.get('total_firms', 0)
        match_rate = age_dist.get('match_rate', 0)
        
        with col1:
            st.metric(
                "Tracked Firms",
                f"{total_firms:,}",
                help="Firms with incorporation date data"
            )
        
        with col2:
            young_firms = age_buckets.get('0-1', 0) + age_buckets.get('1-3', 0)
            young_pct = (young_firms / total_firms * 100) if total_firms > 0 else 0
            st.metric(
                "Young Firms (<3y)",
                f"{young_firms:,}",
                delta=f"{young_pct:.1f}%",
                help="Firms less than 3 years old"
            )
        
        with col3:
            st.metric(
                "Data Match Rate",
                f"{match_rate:.1f}%",
                help="Percentage of firms with complete data"
            )
        
        # Business applications data
        bfs_data = firm_data.get('business_applications', {})
        with col4:
            latest_apps = bfs_data.get('total_applications', 0)
            st.metric(
                "New Applications",
                f"{latest_apps:,}",
                help="Business applications (latest year)"
            )
    
    def _render_age_distribution(self, age_data: Dict[str, Any]):
        """Render firm age distribution analysis"""
        st.subheader("📊 Firm Age Distribution")
        
        age_buckets = age_data.get('age_buckets', {})
        total_firms = age_data.get('total_firms', 0)
        match_rate = age_data.get('match_rate', 0)
        
        if not age_buckets or total_firms == 0:
            st.info("No firm age distribution data available.")
            return
        
        # Data quality info
        with st.expander("ℹ️ Data Quality Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Firms Analyzed", f"{total_firms:,}")
                st.metric("Match Rate", f"{match_rate:.1f}%")
            
            with col2:
                quality_badge = self.quality_manager.get_data_quality_badge(int(match_rate))
                st.write(f"**Quality Grade:** {quality_badge['grade']}")
                st.write("**Source:** OpenCorporates incorporation data")
        
        # Age distribution visualization
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create age distribution chart
            age_df = pd.DataFrame([
                {'Age_Group': age_group, 'Count': count, 'Percentage': count/total_firms*100}
                for age_group, count in age_buckets.items()
            ])
            
            # Sort by logical age order
            age_order = ['0-1', '1-3', '3-5', '5+']
            age_df['Age_Group'] = pd.Categorical(age_df['Age_Group'], categories=age_order, ordered=True)
            age_df = age_df.sort_values('Age_Group')
            
            fig = px.bar(
                age_df,
                x='Age_Group',
                y='Count',
                title="Firm Age Distribution",
                labels={'Age_Group': 'Age Group (Years)', 'Count': 'Number of Firms'},
                text='Count'
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart for percentages
            fig_pie = px.pie(
                age_df,
                names='Age_Group',
                values='Count',
                title="Age Distribution (%)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Age group analysis
        st.subheader("🔍 Age Group Analysis")
        
        # Calculate insights
        startup_firms = age_buckets.get('0-1', 0)
        emerging_firms = age_buckets.get('1-3', 0) 
        established_firms = age_buckets.get('3-5', 0)
        mature_firms = age_buckets.get('5+', 0)
        
        startup_pct = (startup_firms / total_firms * 100) if total_firms > 0 else 0
        emerging_pct = (emerging_firms / total_firms * 100) if total_firms > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Startups (0-1y)",
                f"{startup_firms:,}",
                delta=f"{startup_pct:.1f}%"
            )
            if startup_pct > 15:
                st.success("High startup activity")
            elif startup_pct > 8:
                st.info("Moderate startup activity")
            else:
                st.warning("Low startup activity")
        
        with col2:
            st.metric(
                "Emerging (1-3y)",
                f"{emerging_firms:,}",
                delta=f"{emerging_pct:.1f}%"
            )
            if emerging_pct > 20:
                st.success("Strong growth phase")
            elif emerging_pct > 12:
                st.info("Moderate growth")
            else:
                st.warning("Limited growth activity")
        
        with col3:
            st.metric(
                "Established (3-5y)",
                f"{established_firms:,}",
                delta=f"{(established_firms/total_firms*100):.1f}%"
            )
        
        with col4:
            st.metric(
                "Mature (5+y)",
                f"{mature_firms:,}",
                delta=f"{(mature_firms/total_firms*100):.1f}%"
            )
        
        # Business lifecycle insights
        st.subheader("💡 Business Lifecycle Insights")
        
        insights = []
        
        if startup_pct > 15:
            insights.append("🟢 High startup formation rate indicates dynamic business environment")
        elif startup_pct < 5:
            insights.append("🟡 Low startup rate may indicate market saturation or barriers to entry")
        
        if emerging_pct > 20:
            insights.append("🟢 Strong emerging business segment suggests healthy growth pipeline")
        
        survival_rate = ((emerging_firms + established_firms + mature_firms) / 
                        (startup_firms + emerging_firms + established_firms + mature_firms) * 100) if total_firms > 0 else 0
        
        if survival_rate > 85:
            insights.append("🟢 High business survival rate indicates favorable market conditions")
        elif survival_rate < 70:
            insights.append("🟡 Lower survival rate may indicate competitive challenges")
        
        if insights:
            for insight in insights:
                st.write(f"• {insight}")
        else:
            st.info("Analysis requires more comprehensive firm data.")
    
    def _render_formation_trends(self, formation_data: List[Dict[str, Any]]):
        """Render business formation trends"""
        st.subheader("📈 Business Formation Trends")
        
        if not formation_data:
            st.info("No business formation trend data available.")
            return
        
        # Convert to DataFrame for analysis
        trends_df = pd.DataFrame(formation_data)
        trends_df = trends_df.sort_values('year')
        
        # Summary metrics for latest year
        if not trends_df.empty:
            latest_data = trends_df.iloc[-1]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Latest Year",
                    f"{latest_data['year']}"
                )
            
            with col2:
                total_apps = latest_data.get('applications_total', 0)
                st.metric(
                    "Total Applications",
                    f"{total_apps:,}"
                )
            
            with col3:
                hp_apps = latest_data.get('high_propensity_apps', 0)
                hp_rate = (hp_apps / total_apps * 100) if total_apps > 0 else 0
                st.metric(
                    "High Propensity Rate",
                    f"{hp_rate:.1f}%",
                    help="Percentage of applications likely to create jobs"
                )
        
        # Formation trends chart
        if len(trends_df) > 1:
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Total Applications Over Time', 'High Propensity Applications'),
                specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
            )
            
            # Total applications trend
            fig.add_trace(
                go.Scatter(
                    x=trends_df['year'],
                    y=trends_df['applications_total'],
                    mode='lines+markers',
                    name='Total Applications',
                    line=dict(color='#1f77b4', width=3)
                ),
                row=1, col=1
            )
            
            # High propensity applications
            fig.add_trace(
                go.Scatter(
                    x=trends_df['year'],
                    y=trends_df['high_propensity_apps'],
                    mode='lines+markers',
                    name='High Propensity Apps',
                    line=dict(color='#ff7f0e', width=3)
                ),
                row=2, col=1
            )
            
            fig.update_layout(height=500, showlegend=True)
            fig.update_xaxes(title_text="Year", row=2, col=1)
            fig.update_yaxes(title_text="Applications", row=1, col=1)
            fig.update_yaxes(title_text="High Propensity Apps", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Year-over-year analysis
            st.subheader("📊 Year-over-Year Changes")
            
            if len(trends_df) >= 2:
                latest = trends_df.iloc[-1]
                previous = trends_df.iloc[-2]
                
                total_change = ((latest['applications_total'] - previous['applications_total']) / 
                               previous['applications_total'] * 100) if previous['applications_total'] > 0 else 0
                
                hp_change = ((latest['high_propensity_apps'] - previous['high_propensity_apps']) / 
                            previous['high_propensity_apps'] * 100) if previous['high_propensity_apps'] > 0 else 0
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        f"Total Applications Change ({previous['year']} → {latest['year']})",
                        f"{total_change:+.1f}%",
                        delta=f"{int(latest['applications_total'] - previous['applications_total']):+,} applications"
                    )
                
                with col2:
                    st.metric(
                        f"High Propensity Change ({previous['year']} → {latest['year']})",
                        f"{hp_change:+.1f}%",
                        delta=f"{int(latest['high_propensity_apps'] - previous['high_propensity_apps']):+,} applications"
                    )
        
        # Formation data table
        st.subheader("📋 Historical Data")
        
        # Format data for display
        display_df = trends_df.copy()
        display_df['HP_Rate'] = (display_df['high_propensity_apps'] / display_df['applications_total'] * 100).round(1)
        
        # Rename columns for display
        display_columns = {
            'year': 'Year',
            'applications_total': 'Total Applications',
            'high_propensity_apps': 'High Propensity Apps',
            'HP_Rate': 'HP Rate (%)',
            'applications_with_planned_wages': 'With Planned Wages',
            'applications_with_first_day_wages': 'With First Day Wages'
        }
        
        available_columns = {k: v for k, v in display_columns.items() if k in display_df.columns}
        display_df = display_df[list(available_columns.keys())].rename(columns=available_columns)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    
    def _render_business_applications(self, bfs_data: Dict[str, Any]):
        """Render BFS business applications data"""
        st.subheader("📋 Business Applications (BFS)")
        
        if not bfs_data:
            st.info("No Bureau of Formation Statistics data available.")
            return
        
        # Latest year metrics
        latest_year = bfs_data.get('latest_year')
        total_apps = bfs_data.get('total_applications', 0)
        hp_apps = bfs_data.get('high_propensity_applications', 0)
        hp_rate = bfs_data.get('high_propensity_rate', 0)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Data Year",
                f"{latest_year}" if latest_year else "N/A"
            )
        
        with col2:
            st.metric(
                "Total Applications",
                f"{total_apps:,}"
            )
        
        with col3:
            st.metric(
                "High Propensity Apps",
                f"{hp_apps:,}"
            )
        
        with col4:
            st.metric(
                "HP Rate",
                f"{hp_rate:.1f}%",
                help="Percentage likely to create jobs within 8 quarters"
            )
        
        # Year-over-year changes
        yoy_total_change = bfs_data.get('yoy_total_change_pct', 0)
        yoy_hp_change = bfs_data.get('yoy_hp_change_pct', 0)
        
        if yoy_total_change != 0 or yoy_hp_change != 0:
            st.subheader("📈 Year-over-Year Changes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                direction = "📈" if yoy_total_change > 0 else "📉" if yoy_total_change < 0 else "➡️"
                st.metric(
                    f"{direction} Total Applications Change",
                    f"{yoy_total_change:+.1f}%"
                )
            
            with col2:
                direction = "📈" if yoy_hp_change > 0 else "📉" if yoy_hp_change < 0 else "➡️"
                st.metric(
                    f"{direction} High Propensity Change",
                    f"{yoy_hp_change:+.1f}%"
                )
        
        # Multi-year trend data
        trend_data = bfs_data.get('trend_data', [])
        if len(trend_data) > 1:
            st.subheader("📊 Multi-Year Trends")
            
            trend_df = pd.DataFrame(trend_data)
            trend_df = trend_df.sort_values('year')
            
            # Calculate high propensity rates
            trend_df['hp_rate'] = (trend_df['high_propensity_apps'] / trend_df['applications_total'] * 100).round(1)
            
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Application Volumes', 'High Propensity Rate'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Volume chart
            fig.add_trace(
                go.Bar(
                    x=trend_df['year'],
                    y=trend_df['applications_total'],
                    name='Total Applications',
                    marker_color='lightblue'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=trend_df['year'],
                    y=trend_df['high_propensity_apps'],
                    name='High Propensity',
                    marker_color='orange'
                ),
                row=1, col=1
            )
            
            # Rate chart
            fig.add_trace(
                go.Scatter(
                    x=trend_df['year'],
                    y=trend_df['hp_rate'],
                    mode='lines+markers',
                    name='HP Rate (%)',
                    line=dict(color='green', width=3)
                ),
                row=1, col=2
            )
            
            fig.update_layout(height=400)
            fig.update_xaxes(title_text="Year")
            fig.update_yaxes(title_text="Applications", row=1, col=1)
            fig.update_yaxes(title_text="HP Rate (%)", row=1, col=2)
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Data source information
        with st.expander("ℹ️ About Business Formation Statistics", expanded=False):
            st.write("""
            **Business Formation Statistics (BFS)** from the U.S. Census Bureau track new business applications:
            
            - **Total Applications**: All Employer Identification Number (EIN) applications
            - **High Propensity Applications**: Applications with high likelihood of creating payroll jobs
            - **Data Frequency**: Annual
            - **Geographic Level**: County
            - **Source**: U.S. Census Bureau Business Formation Statistics
            
            High propensity applications are identified using machine learning models that predict 
            which applications are likely to result in job creation within 8 quarters.
            """)
    
    def _render_detailed_analysis(self, firm_data: Dict[str, Any], county_fips: str):
        """Render detailed firm analysis and insights"""
        st.subheader("🔍 Detailed Analysis")
        
        # Market dynamics assessment
        age_data = firm_data.get('age_distribution', {})
        bfs_data = firm_data.get('business_applications', {})
        formation_trends = firm_data.get('formation_trends', [])
        
        # Calculate key metrics
        age_buckets = age_data.get('age_buckets', {})
        total_firms = age_data.get('total_firms', 0)
        
        if total_firms > 0:
            young_firm_rate = ((age_buckets.get('0-1', 0) + age_buckets.get('1-3', 0)) / total_firms * 100)
            startup_rate = (age_buckets.get('0-1', 0) / total_firms * 100)
        else:
            young_firm_rate = startup_rate = 0
        
        # Market dynamism assessment
        st.subheader("🎯 Market Dynamism Assessment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Dynamism score calculation
            dynamism_score = 0
            
            # Young firm rate (0-30 points)
            dynamism_score += min(young_firm_rate * 0.5, 30)
            
            # BFS high propensity rate (0-25 points)
            hp_rate = bfs_data.get('high_propensity_rate', 0)
            dynamism_score += min(hp_rate * 0.5, 25)
            
            # YoY growth (0-25 points)
            yoy_change = bfs_data.get('yoy_total_change_pct', 0)
            if yoy_change > 0:
                dynamism_score += min(yoy_change * 0.5, 25)
            
            # Formation consistency (0-20 points)
            if len(formation_trends) >= 3:
                recent_years = formation_trends[-3:]
                avg_apps = sum(t.get('applications_total', 0) for t in recent_years) / len(recent_years)
                if avg_apps > 100:  # Consistent formation activity
                    dynamism_score += 20
            
            dynamism_score = min(dynamism_score, 100)
            
            st.metric(
                "Market Dynamism Score",
                f"{dynamism_score:.1f}/100",
                help="Composite score based on firm formation and age distribution"
            )
            
            # Dynamism interpretation
            if dynamism_score > 70:
                st.success("🟢 Highly Dynamic Market")
                dynamism_level = "High"
            elif dynamism_score > 50:
                st.info("🟡 Moderately Dynamic Market")
                dynamism_level = "Moderate"
            else:
                st.warning("🔴 Less Dynamic Market")
                dynamism_level = "Low"
        
        with col2:
            # Business lifecycle health
            if total_firms > 0:
                lifecycle_health = {
                    'Startups (0-1y)': age_buckets.get('0-1', 0),
                    'Growth (1-3y)': age_buckets.get('1-3', 0),
                    'Established (3-5y)': age_buckets.get('3-5', 0),
                    'Mature (5+y)': age_buckets.get('5+', 0)
                }
                
                fig = px.pie(
                    values=list(lifecycle_health.values()),
                    names=list(lifecycle_health.keys()),
                    title="Business Lifecycle Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Strategic insights
        st.subheader("💡 Strategic Insights")
        
        insights = []
        
        # Market entry timing insights
        if startup_rate > 12:
            insights.append("🟢 High startup formation rate suggests market accepts new entrants")
        elif startup_rate < 5:
            insights.append("🟡 Low startup rate may indicate market maturity or high barriers")
        
        # Competition landscape
        mature_rate = (age_buckets.get('5+', 0) / total_firms * 100) if total_firms > 0 else 0
        if mature_rate > 60:
            insights.append("🟡 Market dominated by mature firms - differentiation important")
        elif mature_rate < 30:
            insights.append("🟢 Market has room for established players")
        
        # Growth trajectory
        if yoy_change > 10:
            insights.append("🟢 Strong growth trajectory in business formation")
        elif yoy_change < -10:
            insights.append("🔴 Declining business formation trend")
        
        # High propensity insights
        if hp_rate > 70:
            insights.append("🟢 High job creation potential from new businesses")
        elif hp_rate < 50:
            insights.append("🟡 Moderate job creation potential")
        
        if insights:
            for insight in insights:
                st.write(f"• {insight}")
        
        # Opportunity assessment
        st.subheader("🎯 Opportunity Assessment")
        
        opportunity_factors = []
        
        # Market timing
        if dynamism_level == "High":
            opportunity_factors.append(("Market Timing", "Excellent", "🟢"))
        elif dynamism_level == "Moderate":
            opportunity_factors.append(("Market Timing", "Good", "🟡"))
        else:
            opportunity_factors.append(("Market Timing", "Challenging", "🔴"))
        
        # Competition level
        if young_firm_rate > 25:
            opportunity_factors.append(("Competition", "High (many new entrants)", "🟡"))
        elif young_firm_rate > 15:
            opportunity_factors.append(("Competition", "Moderate", "🟢"))
        else:
            opportunity_factors.append(("Competition", "Low (established market)", "🟢"))
        
        # Growth potential
        if yoy_change > 5:
            opportunity_factors.append(("Growth Potential", "High", "🟢"))
        elif yoy_change > -5:
            opportunity_factors.append(("Growth Potential", "Stable", "🟡"))
        else:
            opportunity_factors.append(("Growth Potential", "Declining", "🔴"))
        
        # Display opportunity matrix
        for factor, assessment, icon in opportunity_factors:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{factor}:**")
            with col2:
                st.write(assessment)
            with col3:
                st.write(icon)
        
        # Data quality and limitations
        with st.expander("⚠️ Data Quality & Limitations", expanded=False):
            match_rate = age_data.get('match_rate', 0)
            
            st.write("**Data Coverage:**")
            if match_rate > 80:
                st.success(f"✅ High data quality ({match_rate:.1f}% match rate)")
            elif match_rate > 60:
                st.warning(f"⚠️ Moderate data quality ({match_rate:.1f}% match rate)")
            else:
                st.error(f"❌ Limited data quality ({match_rate:.1f}% match rate)")
            
            st.write("""
            **Limitations:**
            - Firm age data depends on incorporation records availability
            - BFS data has ~1 year lag from Census Bureau
            - High propensity rates are model-based predictions
            - Small firms may be underrepresented in official data
            
            **Recommendations:**
            - Supplement with local business association data
            - Consider field research for recent market changes
            - Monitor quarterly BFS updates for trend changes
            """)
