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
        rfp_signals = signals_data[signals_data['signal_type'] == 'rfp_count'] if not signals_data.empty else pd.DataFrame()
    
    if rfp_signals.empty:
        st.info("No federal RFP opportunities found for this county in the past year")
        return
    
    # Summary metrics from cached signals data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rfp_count = rfp_signals['value'].iloc[0] if not rfp_signals.empty else 0
        st.metric(
            f"{data_utils.get_data_badge('Observed')} Total RFPs",
            data_utils.format_number(rfp_count)
        )
    
    with col2:
        # Show year of data
        data_year = rfp_signals['year'].iloc[0] if not rfp_signals.empty else 2024
        st.metric(
            "Data Year",
            data_year
        )
    
    with col3:
        # Show data source
        source = rfp_signals['source'].iloc[0] if not rfp_signals.empty else "SAM.gov"
        st.metric(
            "Source",
            source
        )
    
    # RFP trends chart
    if len(rfp_data) > 1:
        rfp_data['posted_month'] = pd.to_datetime(rfp_data['posted_date'], errors='coerce').dt.to_period('M')
        monthly_counts = rfp_data.groupby('posted_month').size().reset_index(name='count')
        monthly_counts['month'] = monthly_counts['posted_month'].astype(str)
        
        fig = px.line(
            monthly_counts,
            x='month',
            y='count',
            title="RFP Postings Over Time",
            labels={'count': 'Number of RFPs', 'month': 'Month'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # RFP details table
    st.subheader("RFP Details")
    
    display_columns = {
        'title': 'Title',
        'naics': 'NAICS',
        'posted_date': 'Posted Date',
        'close_date': 'Close Date',
        'url': 'Link'
    }
    
    # Filter columns that exist
    available_columns = {k: v for k, v in display_columns.items() if k in rfp_data.columns}
    
    if available_columns:
        display_data = rfp_data[list(available_columns.keys())].copy()
        
        # Format dates
        date_columns = ['posted_date', 'close_date']
        for col in date_columns:
            if col in display_data.columns:
                display_data[col] = pd.to_datetime(display_data[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Format URLs as clickable links
        if 'url' in display_data.columns:
            display_data['url'] = display_data['url'].apply(
                lambda x: f"[View RFP]({x})" if pd.notna(x) else ""
            )
        
        st.dataframe(
            display_data.rename(columns=available_columns),
            use_container_width=True,
            hide_index=True
        )

def render_awards_signals(data_service, county_fips: str, data_utils):
    """Render federal awards signals"""
    st.subheader("Federal Contract Awards")
    
    with st.spinner("Loading awards data..."):
        # Get all signals data and filter for awards data
        signals_data = data_service.get_demand_signals(county_fips)
        award_signals = signals_data[signals_data['signal_type'] == 'award_count'] if not signals_data.empty else pd.DataFrame()
    
    if award_signals.empty:
        st.info("No federal contract awards found for this county")
        return
    
    # Summary metrics from cached signals data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        award_count = award_signals['value'].iloc[0] if not award_signals.empty else 0
        st.metric(
            f"{data_utils.get_data_badge('Observed')} Total Awards",
            data_utils.format_number(award_count)
        )
    
    with col2:
        # Show year of data
        data_year = award_signals['year'].iloc[0] if not award_signals.empty else 2024
        st.metric(
            "Data Year",
            data_year
        )
    
    with col3:
        # Show data source  
        source = award_signals['source'].iloc[0] if not award_signals.empty else "USAspending.gov"
        st.metric(
            "Source",
            source
        )
    
    # Awards by agency
    if 'agency' in awards_data.columns:
        agency_summary = awards_data.groupby('agency').agg({
            'amount': ['count', 'sum']
        }).round(0)
        agency_summary.columns = ['Count', 'Total Value']
        agency_summary = agency_summary.sort_values('Total Value', ascending=False).head(10)
        
        st.subheader("Top Awarding Agencies")
        st.dataframe(agency_summary, use_container_width=True)
    
    # Awards timeline
    if len(awards_data) > 1 and 'action_date' in awards_data.columns:
        awards_data['award_month'] = pd.to_datetime(awards_data['action_date'], errors='coerce').dt.to_period('M')
        monthly_awards = awards_data.groupby('award_month').agg({
            'amount': ['count', 'sum']
        }).reset_index()
        monthly_awards.columns = ['month', 'count', 'total_value']
        monthly_awards['month'] = monthly_awards['month'].astype(str)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_awards['month'],
            y=monthly_awards['count'],
            mode='lines+markers',
            name='Number of Awards',
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            x=monthly_awards['month'],
            y=monthly_awards['total_value'],
            mode='lines+markers',
            name='Total Value ($)',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Federal Awards Over Time",
            xaxis_title="Month",
            yaxis=dict(title="Number of Awards", side="left"),
            yaxis2=dict(title="Total Value ($)", side="right", overlaying="y"),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_license_signals(data_service, county_fips: str, data_utils):
    """Render business license signals"""
    st.subheader("Business License Activity")
    
    with st.spinner("Loading license data..."):
        license_data = data_service.get_license_data(county_fips)
    
    if (isinstance(license_data, list) and len(license_data) == 0) or (hasattr(license_data, 'empty') and license_data.empty):
        st.info("No business license data available for this county")
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
        sba_signals = signals_data[signals_data['signal_type'] == 'sba_loans'] if not signals_data.empty else pd.DataFrame()
    
    if sba_signals.empty:
        st.info("No SBA loan data available for this county")
        return
    
    # Summary metrics from cached SBA loan data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sba_loan_count = sba_signals['value'].iloc[0] if not sba_signals.empty else 0
        st.metric(
            f"{data_utils.get_data_badge('Observed')} SBA Loans",
            data_utils.format_number(sba_loan_count)
        )
    
    with col2:
        # Show year of data
        data_year = sba_signals['year'].iloc[0] if not sba_signals.empty else 2024
        st.metric(
            "Data Year",
            data_year
        )
    
    with col3:
        # Show data source  
        source = sba_signals['source'].iloc[0] if not sba_signals.empty else "SBA"
        st.metric(
            "Source",
            source
        )
    
    # SBA loan information
    if not sba_signals.empty:
        description = sba_signals['description'].iloc[0]
        st.info(f"💡 **Capital Demand Indicator**: {description}")
        
        st.markdown("""
        **SBA loans indicate businesses requiring capital access**, which creates demand for:
        - Financial advisory services
        - Business loan consulting  
        - Cash flow management advice
        - Growth planning services
        """)
