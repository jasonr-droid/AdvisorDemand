import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lib.utils import DataUtils

def render_firm_age_chart(data_service, county_fips: str):
    """Render firm age distribution analysis"""
    data_utils = DataUtils()
    
    st.subheader("🏢 Firm Age Distribution")
    
    with st.spinner("Loading firm age data..."):
        firm_age_data = data_service.get_firm_age_data(county_fips)
    
    if not firm_age_data or firm_age_data.get('total_firms', 0) == 0:
        st.warning("No firm age data available for this county")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            f"{data_utils.get_data_badge('Observed')} Total Firms",
            data_utils.format_number(firm_age_data['total_firms'])
        )
    
    with col2:
        st.metric(
            "Match Rate",
            f"{firm_age_data['match_rate']:.1f}%",
            help="Percentage of firms with incorporation date data"
        )
    
    with col3:
        young_firms = firm_age_data['age_0_1'] + firm_age_data['age_1_3']
        st.metric(
            "Young Firms (0-3 years)",
            data_utils.format_number(young_firms)
        )
    
    with col4:
        established_firms = firm_age_data['age_3_5'] + firm_age_data['age_5_plus']
        st.metric(
            "Established Firms (3+ years)",
            data_utils.format_number(established_firms)
        )
    
    # Age distribution chart
    age_categories = ['0-1 years', '1-3 years', '3-5 years', '5+ years']
    age_counts = [
        firm_age_data['age_0_1'],
        firm_age_data['age_1_3'],
        firm_age_data['age_3_5'],
        firm_age_data['age_5_plus']
    ]
    
    # Create DataFrame for plotting
    age_df = pd.DataFrame({
        'Age Category': age_categories,
        'Number of Firms': age_counts,
        'Percentage': [count / sum(age_counts) * 100 if sum(age_counts) > 0 else 0 for count in age_counts]
    })
    
    # Chart type selection
    chart_type = st.radio(
        "Chart Type",
        options=["Bar Chart", "Pie Chart", "Donut Chart"],
        horizontal=True
    )
    
    if chart_type == "Bar Chart":
        fig = px.bar(
            age_df,
            x='Age Category',
            y='Number of Firms',
            title="Firm Age Distribution",
            color='Age Category',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        # Add percentage labels
        fig.update_traces(
            text=[f"{count}<br>({pct:.1f}%)" for count, pct in zip(age_df['Number of Firms'], age_df['Percentage'])],
            textposition='outside'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Pie Chart":
        fig = px.pie(
            age_df,
            values='Number of Firms',
            names='Age Category',
            title="Firm Age Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Donut Chart":
        fig = go.Figure(data=[go.Pie(
            labels=age_df['Age Category'],
            values=age_df['Number of Firms'],
            hole=0.4,
            textinfo='label+percent',
            textposition='auto'
        )])
        
        fig.update_layout(
            title="Firm Age Distribution",
            annotations=[dict(text='Firm Age', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Age distribution table
    st.subheader("Age Distribution Details")
    
    # Add cumulative percentages
    age_df['Cumulative Count'] = age_df['Number of Firms'].cumsum()
    age_df['Cumulative Percentage'] = age_df['Cumulative Count'] / age_df['Number of Firms'].sum() * 100
    
    # Format the display table
    display_df = age_df.copy()
    display_df['Number of Firms'] = display_df['Number of Firms'].apply(data_utils.format_number)
    display_df['Percentage'] = display_df['Percentage'].apply(lambda x: f"{x:.1f}%")
    display_df['Cumulative Count'] = display_df['Cumulative Count'].apply(data_utils.format_number)
    display_df['Cumulative Percentage'] = display_df['Cumulative Percentage'].apply(lambda x: f"{x:.1f}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Insights and analysis
    st.subheader("📊 Analysis Insights")
    
    total_firms_with_data = sum(age_counts)
    if total_firms_with_data > 0:
        # Calculate key insights
        young_firm_pct = (firm_age_data['age_0_1'] + firm_age_data['age_1_3']) / total_firms_with_data * 100
        newest_firm_pct = firm_age_data['age_0_1'] / total_firms_with_data * 100
        established_pct = (firm_age_data['age_3_5'] + firm_age_data['age_5_plus']) / total_firms_with_data * 100
        
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            st.info(f"""
            **Market Dynamics:**
            - {young_firm_pct:.1f}% of firms are 3 years old or newer
            - {newest_firm_pct:.1f}% are in their first year
            - {established_pct:.1f}% are established (3+ years)
            """)
        
        with insight_col2:
            # Determine market characteristics
            if young_firm_pct > 40:
                market_type = "High Growth/Emerging"
                market_desc = "High rate of new firm formation suggests growing market opportunity"
            elif young_firm_pct > 25:
                market_type = "Moderate Growth"
                market_desc = "Balanced mix of new and established firms"
            else:
                market_type = "Mature/Stable"
                market_desc = "Dominated by established firms with lower formation rates"
            
            st.success(f"""
            **Market Characterization:**
            - Market Type: {market_type}
            - Assessment: {market_desc}
            """)
    
    # Data quality indicator
    match_rate = firm_age_data['match_rate']
    if match_rate < 50:
        st.warning(f"""
        ⚠️ **Data Quality Note:** 
        Only {match_rate:.1f}% of firms have incorporation date data available. 
        Results may not be fully representative of the total firm population.
        """)
    elif match_rate < 75:
        st.info(f"""
        ℹ️ **Data Coverage:** 
        {match_rate:.1f}% of firms have incorporation date data. 
        Results provide a good representation of firm age distribution.
        """)
    else:
        st.success(f"""
        ✅ **High Data Quality:** 
        {match_rate:.1f}% of firms have incorporation date data. 
        Results are highly representative.
        """)
    
    # Export functionality
    if st.button("Export Firm Age Data", key="firm_age_export"):
        csv_data = data_utils.export_to_csv(
            age_df,
            f"firm_age_analysis_{county_fips}.csv"
        )
        
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"firm_age_analysis_{county_fips}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
