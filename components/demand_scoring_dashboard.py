import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from services.demand_scoring import DemandScoringService, DemandWeights
from lib.utils import DataUtils

def render_demand_scoring_dashboard(data_service, county_fips: str):
    """Render demand scoring analytics dashboard"""
    data_utils = DataUtils()
    
    st.header("🎯 Demand Scoring Analytics")
    st.markdown("*Sophisticated demand analysis using weighted scoring across multiple market signals*")
    
    # Refresh option
    col1, col2 = st.columns([3, 1])
    with col2:
        refresh_data = st.button("🔄 Refresh Data", help="Refresh all data sources for updated scoring")
    
    with st.spinner("Computing demand scores..."):
        # Use facade method for efficient data loading
        dashboard_data = data_service.get_demand_dashboard(county_fips, refresh=refresh_data)
        
        industry_scores = dashboard_data["by_industry"]
        top_companies = dashboard_data["by_company"]
        size_breakdown = dashboard_data["industry_size"]
        spend_ranges = dashboard_data["spend_ranges"]
        
        if industry_scores.empty:
            st.warning("⚠️ Insufficient data for demand scoring analysis")
            st.info("Demand scoring requires CBP industry data, business formation records, and market signals.")
            return
        
        # Display scoring methodology
        with st.expander("📊 Scoring Methodology", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **Weighted Signal Components:**
                - Business Formation Growth (30%)
                - Licenses per 1K establishments (25%)
                - RFPs per 1K establishments (25%)
                - Employment Growth - QCEW (20%)
                """)
            
            with col2:
                st.markdown("""
                **Analysis Features:**
                - Z-score normalization across industries
                - Per-establishment rate calculations
                - Multi-year trend analysis
                - Spend band estimation by firm size
                """)
        
        # Top scoring industries
        st.subheader("🏆 High-Demand Industries")
        
        # Display top 10 industries by demand score
        top_industries = industry_scores.head(10)
        
        if not top_industries.empty:
            # Create demand score visualization
            fig = px.bar(
                top_industries,
                x='demand_score',
                y='naics',
                orientation='h',
                title="Demand Scores by Industry Sector (2-Digit NAICS)",
                labels={'demand_score': 'Demand Score (Z-Score)', 'naics': 'NAICS Code'},
                color='demand_score',
                color_continuous_scale='RdYlGn'
            )
            fig.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                top_score = industry_scores['demand_score'].max()
                st.metric(
                    f"{data_utils.get_data_badge('Calculated')} Top Score",
                    f"{top_score:.2f}"
                )
            
            with col2:
                high_demand_count = len(industry_scores[industry_scores['demand_score'] > 0])
                st.metric(
                    "High-Demand Sectors",
                    f"{high_demand_count}"
                )
            
            with col3:
                total_establishments = industry_scores['establishments'].sum()
                st.metric(
                    "Total Establishments",
                    f"{total_establishments:,}"
                )
            
            with col4:
                avg_spend = industry_scores[['spend_low', 'spend_high']].mean().mean()
                st.metric(
                    "Avg Spend Potential",
                    f"${avg_spend:,.0f}"
                )
        
        # Detailed industry breakdown
        st.subheader("📈 Industry Demand Analysis")
        
        # Show detailed table
        display_df = industry_scores.copy()
        display_df['demand_score'] = display_df['demand_score'].round(2)
        display_df['spend_range'] = display_df['spend_low'].astype(str) + ' - $' + display_df['spend_high'].astype(str)
        
        st.dataframe(
            display_df[['naics', 'establishments', 'demand_score', 'spend_range']].rename(columns={
                'naics': 'NAICS Code',
                'establishments': 'Establishments',
                'demand_score': 'Demand Score',
                'spend_range': 'Estimated Spend Range ($)'
            }),
            use_container_width=True,
            height=300
        )
        
        # Company targets analysis
        st.subheader("🎯 Target Company Analysis")
        
        if not top_companies.empty:
            st.markdown("*Companies with recent licensing activity indicating potential demand*")
            
            # Display top target companies
            display_cols = [col for col in ['company_name', 'naics', 'issued_date', 'signal', 'jurisdiction'] 
                           if col in top_companies.columns]
            
            if display_cols:
                company_display = top_companies[display_cols].rename(columns={
                    'company_name': 'Company',
                    'naics': 'NAICS',
                    'issued_date': 'Activity Date',
                    'signal': 'Signal Type',
                    'jurisdiction': 'Location'
                })
                
                st.dataframe(company_display, use_container_width=True, height=250)
            else:
                st.info("Company name data not available - showing license activity signals")
                st.dataframe(top_companies, use_container_width=True, height=250)
        else:
            st.info("No recent company licensing activity found for target identification")
        
        # Spend estimates
        st.subheader("💰 Market Spend Estimates")
        
        spend_data = spend_ranges
        
        if not spend_data.empty:
            # Calculate total market potential
            total_low = (spend_data['spend_low'] * industry_scores['establishments']).sum()
            total_high = (spend_data['spend_high'] * industry_scores['establishments']).sum()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    f"{data_utils.get_data_badge('Estimated')} Market Size (Low)",
                    f"${total_low/1000000:.1f}M"
                )
            
            with col2:
                st.metric(
                    f"{data_utils.get_data_badge('Estimated')} Market Size (High)",
                    f"${total_high/1000000:.1f}M"
                )
            
            with col3:
                avg_opportunity = ((total_low + total_high) / 2) / len(industry_scores)
                st.metric(
                    "Avg Sector Opportunity",
                    f"${avg_opportunity/1000:.0f}K"
                )
        
        # Methodology notes
        st.markdown("""
        ---
        **📝 Notes:**
        - Demand scores use z-score normalization for cross-sector comparison
        - Spend estimates based on establishment size proxies and industry benchmarks
        - Target companies identified through recent licensing and formation activity
        - Analysis combines multiple government data sources for comprehensive market intelligence
        """)