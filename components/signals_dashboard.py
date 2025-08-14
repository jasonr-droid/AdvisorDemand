import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from lib.utils import DataUtils

def render_signals_dashboard(data_service, county_fips: str):
    """Render demand signals dashboard"""
    data_utils = DataUtils()
    
    # Create tabs for different signal types
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 RFPs", "🏆 Awards", "📋 Licenses", "🏭 Formations"])
    
    with tab1:
        render_rfp_signals(data_service, county_fips, data_utils)
    
    with tab2:
        render_awards_signals(data_service, county_fips, data_utils)
    
    with tab3:
        render_license_signals(data_service, county_fips, data_utils)
    
    with tab4:
        render_formation_signals(data_service, county_fips, data_utils)

def render_rfp_signals(data_service, county_fips: str, data_utils):
    """Render RFP opportunities signals"""
    st.subheader("Federal RFP Opportunities")
    
    with st.spinner("Loading RFP data..."):
        # Get all signals data and filter for RFP data
        signals_data = data_service.get_demand_signals(county_fips)
        rfp_signals = signals_data[signals_data['signal_type'] == 'Federal RFP Opportunities'] if not signals_data.empty else pd.DataFrame()
    
    if rfp_signals.empty:
        st.info("No federal RFP opportunities found for this county in the past year")
        return
    
    # Summary metrics from cached signals data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rfp_count = rfp_signals['count'].iloc[0] if not rfp_signals.empty else 0
        st.metric(
            f"{data_utils.get_data_badge('Observed')} Total RFPs",
            data_utils.format_number(rfp_count)
        )
    
    with col2:
        # Show recent activity
        recent_count = rfp_signals['recent_count'].iloc[0] if not rfp_signals.empty else 0
        st.metric(
            "Recent Activity",
            data_utils.format_number(recent_count)
        )
    
    with col3:
        # Show data source
        source = rfp_signals['source'].iloc[0] if not rfp_signals.empty else "SAM.gov"
        st.metric(
            "Source",
            source
        )
    
    # Display detailed information about the RFP signals
    if not rfp_signals.empty:
        st.subheader("RFP Signal Details")
        
        # Show trend analysis
        trend = rfp_signals['trend'].iloc[0] if 'trend' in rfp_signals.columns else 'stable'
        trend_color = "🟢" if trend == 'increasing' else "🟡" if trend == 'stable' else "🔴"
        
        st.info(f"📊 **Market Intelligence**: Federal RFP opportunities show {trend_color} **{trend}** trend")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Federal Contracting Opportunities**")
            st.write("• Government agencies seeking financial advisory services")
            st.write("• Indicates public sector demand for financial consulting")
            st.write("• Creates opportunities for advisory service providers")
        
        with col2:
            st.markdown("**Data Source Information**")
            st.write(f"• Source: {rfp_signals['source'].iloc[0]}")
            st.write(f"• Trend: {trend_color} {trend.title()}")
            if 'recent_count' in rfp_signals.columns:
                st.write(f"• Recent Activity: {rfp_signals['recent_count'].iloc[0]} opportunities")
        
        st.markdown("🔗 **Data Source**: [SAM.gov](https://sam.gov)")

def render_awards_signals(data_service, county_fips: str, data_utils):
    """Render federal awards signals"""
    st.subheader("Federal Contract Awards")
    
    with st.spinner("Loading awards data..."):
        # Get all signals data and filter for awards data
        signals_data = data_service.get_demand_signals(county_fips)
        award_signals = signals_data[signals_data['signal_type'] == 'Federal Awards'] if not signals_data.empty else pd.DataFrame()
    
    if award_signals.empty:
        st.info("No federal contract awards found for this county")
        return
    
    # Summary metrics from cached signals data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        award_count = award_signals['count'].iloc[0] if not award_signals.empty else 0
        st.metric(
            f"{data_utils.get_data_badge('Observed')} Total Awards",
            data_utils.format_number(award_count)
        )
    
    with col2:
        # Show award value if available
        award_value = award_signals['value'].iloc[0] if not award_signals.empty and 'value' in award_signals.columns else 0
        if award_value > 0:
            st.metric(
                "Award Value",
                f"${data_utils.format_number(award_value/1000000)}M"
            )
        else:
            st.metric(
                "Trend",
                award_signals['trend'].iloc[0].title() if not award_signals.empty else "Stable"
            )
    
    with col3:
        # Show data source  
        source = award_signals['source'].iloc[0] if not award_signals.empty else "USAspending.gov"
        st.metric(
            "Source",
            source
        )
    
    # Display detailed information about the awards signals
    if not award_signals.empty:
        st.subheader("Awards Signal Details")
        
        # Show trend analysis
        trend = award_signals['trend'].iloc[0] if 'trend' in award_signals.columns else 'stable'
        trend_color = "🟢" if trend == 'increasing' else "🟡" if trend == 'stable' else "🔴"
        
        st.info(f"📊 **Market Intelligence**: Federal contract awards show {trend_color} **{trend}** trend")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Federal Contract Awards**")
            st.write("• Government contracts awarded to financial service providers")
            st.write("• Demonstrates successful government partnerships")  
            st.write("• Shows market validation of financial advisory services")
        
        with col2:
            st.markdown("**Data Source Information**")
            st.write(f"• Source: {award_signals['source'].iloc[0]}")
            st.write(f"• Trend: {trend_color} {trend.title()}")
            if 'value' in award_signals.columns and award_signals['value'].iloc[0] > 0:
                st.write(f"• Total Value: ${award_signals['value'].iloc[0]/1000000:.1f}M")
        
        st.markdown("🔗 **Data Source**: [USAspending.gov](https://usaspending.gov)")

def render_license_signals(data_service, county_fips: str, data_utils):
    """Render business license signals"""
    st.subheader("Business License Activity")
    
    with st.spinner("Loading license data..."):
        license_data = data_service.get_license_data(county_fips)
    
    if (isinstance(license_data, list) and len(license_data) == 0) or (hasattr(license_data, 'empty') and license_data.empty):
        # Provide information about data availability and alternative sources
        st.info("📋 Municipal license data access varies by jurisdiction")
        
        # County-specific guidance
        if county_fips == '06083':  # Santa Barbara County
            st.markdown("""
            **Santa Barbara County License Data Sources:**
            - **City of Santa Barbara**: Monthly Excel reports with active business licenses
            - **Data Fields**: Business name, address, activity type, ownership
            - **Update Schedule**: Monthly (by 10th business day)
            - **Access**: [City Business Tax Information](https://santabarbaraca.gov/business/business-taxes-assessments/business-tax-certificate-information)
            """)
        else:
            st.markdown("""
            **Alternative Data Collection Methods:**
            - Municipal business license portals
            - County assessor databases  
            - Chamber of commerce directories
            - State business registration records
            """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                f"{data_utils.get_data_badge('Data Source')} Coverage Status", 
                "Limited"
            )
        with col2:
            st.metric(
                "Available Sources",
                "Municipal Portals"
            )
        return
    
    # Convert list to DataFrame if needed
    if isinstance(license_data, list):
        if len(license_data) == 0:
            st.info("No business license data available for this county")
            return
        license_data = pd.DataFrame(license_data)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_licenses = len(license_data)
        st.metric(
            f"{data_utils.get_data_badge('Observed')} Total Licenses",
            data_utils.format_number(total_licenses)
        )
    
    with col2:
        # Recent licenses (last 90 days)
        recent_cutoff = datetime.now() - timedelta(days=90)
        recent_licenses = license_data[
            pd.to_datetime(license_data['issued_date'], errors='coerce') >= recent_cutoff
        ]
        st.metric(
            "Recent Licenses (90 days)",
            data_utils.format_number(len(recent_licenses))
        )
    
    with col3:
        # Unique jurisdictions
        jurisdictions = license_data['jurisdiction'].nunique()
        st.metric(
            "Cities Covered",
            data_utils.format_number(jurisdictions)
        )
    
    # License trends by jurisdiction
    if 'jurisdiction' in license_data.columns:
        jurisdiction_summary = license_data.groupby('jurisdiction').size().reset_index(name='count')
        
        fig = px.bar(
            jurisdiction_summary,
            x='jurisdiction',
            y='count',
            title="Licenses by City/Jurisdiction"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Monthly license trends
    if len(license_data) > 1:
        license_data['issued_month'] = pd.to_datetime(license_data['issued_date'], errors='coerce').dt.to_period('M')
        monthly_licenses = license_data.groupby('issued_month').size().reset_index(name='count')
        monthly_licenses['month'] = monthly_licenses['issued_month'].astype(str)
        
        fig = px.line(
            monthly_licenses,
            x='month',
            y='count',
            title="License Issuances Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

def render_formation_signals(data_service, county_fips: str, data_utils):
    """Render business formation signals - showing SBA loan data as capital demand indicator"""
    st.subheader("Capital Demand Activity (SBA Loans)")
    
    with st.spinner("Loading SBA loan data..."):
        # Get all signals data and filter for SBA loan data  
        signals_data = data_service.get_demand_signals(county_fips)
        sba_signals = signals_data[signals_data['signal_type'] == 'New Business Applications'] if not signals_data.empty else pd.DataFrame()
    
    if sba_signals.empty:
        st.info("No SBA loan data available for this county")
        return
    
    # Summary metrics from cached business formation data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        formation_count = sba_signals['count'].iloc[0] if not sba_signals.empty else 0
        st.metric(
            f"{data_utils.get_data_badge('Observed')} New Applications",
            data_utils.format_number(formation_count)
        )
    
    with col2:
        # Show recent activity
        recent_count = sba_signals['recent_count'].iloc[0] if not sba_signals.empty and 'recent_count' in sba_signals.columns else 0
        st.metric(
            "Recent Activity",
            data_utils.format_number(recent_count) if recent_count > 0 else "N/A"
        )
    
    with col3:
        # Show data source  
        source = sba_signals['source'].iloc[0] if not sba_signals.empty else "Census BFS"
        st.metric(
            "Source",
            source
        )
    
    # Business formation information
    if not sba_signals.empty:
        # Show trend analysis
        trend = sba_signals['trend'].iloc[0] if 'trend' in sba_signals.columns else 'stable'
        trend_color = "🟢" if trend == 'increasing' else "🟡" if trend == 'stable' else "🔴"
        
        st.info(f"💡 **Market Growth Indicator**: New business applications show {trend_color} **{trend}** trend")
        
        st.markdown("""
        **New business applications indicate entrepreneurial activity**, which creates demand for:
        - Business planning and financial consulting
        - Startup advisory services  
        - Capital access and funding guidance
        - Tax planning and compliance services
        """)
