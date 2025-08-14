import streamlit as st
import pandas as pd
import plotly.express as px
from lib.naics import NAICSMapper
from lib.utils import DataUtils

def render_industry_table(data_service, county_fips: str):
    """Render industry analysis table"""
    naics_mapper = NAICSMapper()
    data_utils = DataUtils()
    
    # Get industry data
    with st.spinner("Loading industry data..."):
        industry_data = data_service.get_industry_data(county_fips)
    
    if industry_data.empty:
        st.warning("No industry data available for this county")
        return
    
    # NAICS level filter
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        naics_level = st.selectbox(
            "NAICS Detail Level",
            options=[2, 3, 4, 6],
            index=1,  # Default to 3-digit
            help="Choose level of industry detail"
        )
    
    with col2:
        show_financial_only = st.checkbox(
            "Financial Services Only",
            help="Show only financial advisor related industries"
        )
    
    with col3:
        min_establishments = st.number_input(
            "Min Establishments",
            min_value=0,
            value=5,
            help="Filter out industries with fewer establishments"
        )
    
    # Filter data
    filtered_data = industry_data.copy()
    
    # Filter by NAICS level
    filtered_data = filtered_data[
        filtered_data['naics'].str.len() == naics_level
    ]
    
    # Filter by financial services if requested
    if show_financial_only:
        financial_mask = filtered_data['naics'].apply(naics_mapper.is_financial_services)
        filtered_data = filtered_data[financial_mask]
    
    # Filter by minimum establishments
    if min_establishments > 0:
        filtered_data = filtered_data[
            (filtered_data['establishments'].fillna(0) >= min_establishments)
        ]
    
    if filtered_data.empty:
        st.warning("No industries match the selected filters")
        return
    
    # Prepare display data
    display_data = filtered_data.copy()
    
    # Add NAICS descriptions
    display_data['industry'] = display_data['naics'].apply(naics_mapper.get_description)
    
    # Format numeric columns
    numeric_columns = ['establishments', 'employment', 'annual_payroll', 'avg_weekly_wage']
    for col in numeric_columns:
        if col in display_data.columns:
            display_data[f'{col}_formatted'] = display_data[col].apply(
                lambda x: data_utils.format_number(x) if col != 'annual_payroll' 
                else data_utils.format_large_number(x)
            )
    
    # Suppress small cells
    suppression_columns = ['establishments', 'employment']
    display_data = data_utils.suppress_small_cells(display_data, suppression_columns)
    
    # Create display table
    table_columns = {
        'naics': 'NAICS',
        'industry': 'Industry',
        'establishments_formatted': f'{data_utils.get_data_badge("Observed")} Establishments',
        'employment_formatted': f'{data_utils.get_data_badge("Observed")} Employment',
        'annual_payroll_formatted': f'{data_utils.get_data_badge("Observed")} Annual Payroll',
        'avg_weekly_wage_formatted': f'{data_utils.get_data_badge("Observed")} Avg Weekly Wage'
    }
    
    # Filter columns that exist in data
    available_columns = {k: v for k, v in table_columns.items() if k in display_data.columns}
    
    st.subheader("📊 Industry Overview")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_establishments = display_data['establishments'].sum()
        st.metric("Total Establishments", data_utils.format_number(total_establishments))
    
    with col2:
        total_employment = display_data['employment'].sum()
        st.metric("Total Employment", data_utils.format_number(total_employment))
    
    with col3:
        total_payroll = display_data['annual_payroll'].sum()
        st.metric("Total Payroll", data_utils.format_large_number(total_payroll))
    
    with col4:
        avg_wage = display_data['avg_weekly_wage'].mean()
        st.metric("Avg Weekly Wage", f"${avg_wage:,.0f}" if pd.notna(avg_wage) else "—")
    
    # Industry table
    st.subheader("Industry Details")
    
    # Sort options
    sort_col1, sort_col2 = st.columns(2)
    
    with sort_col1:
        sort_by = st.selectbox(
            "Sort by",
            options=['establishments', 'employment', 'annual_payroll', 'avg_weekly_wage'],
            index=1  # Default to employment
        )
    
    with sort_col2:
        sort_ascending = st.checkbox("Ascending", value=False)
    
    # Sort data
    if sort_by in display_data.columns:
        display_data = display_data.sort_values(sort_by, ascending=sort_ascending)
    
    # Display table
    st.dataframe(
        display_data[list(available_columns.keys())].rename(columns=available_columns),
        use_container_width=True,
        hide_index=True
    )
    
    # Charts
    st.subheader("📈 Industry Visualization")
    
    chart_type = st.radio(
        "Chart Type",
        options=["Bar Chart", "Pie Chart", "Scatter Plot"],
        horizontal=True
    )
    
    if chart_type == "Bar Chart":
        # Top industries bar chart
        top_n = st.slider("Show top N industries", 5, 20, 10)
        top_industries = display_data.nlargest(top_n, sort_by)
        
        fig = px.bar(
            top_industries,
            x='industry',
            y=sort_by,
            title=f"Top {top_n} Industries by {sort_by.replace('_', ' ').title()}",
            labels={'industry': 'Industry', sort_by: sort_by.replace('_', ' ').title()}
        )
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Pie Chart":
        # Industry distribution pie chart
        top_industries = display_data.nlargest(8, sort_by)
        others_sum = display_data.iloc[8:][sort_by].sum() if len(display_data) > 8 else 0
        
        if others_sum > 0:
            # Add "Others" category
            others_row = pd.Series({
                'industry': 'Others',
                sort_by: others_sum
            })
            pie_data = pd.concat([top_industries[['industry', sort_by]], others_row.to_frame().T])
        else:
            pie_data = top_industries[['industry', sort_by]]
        
        fig = px.pie(
            pie_data,
            values=sort_by,
            names='industry',
            title=f"Industry Distribution by {sort_by.replace('_', ' ').title()}"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Scatter Plot":
        # Employment vs Payroll scatter
        if 'employment' in display_data.columns and 'annual_payroll' in display_data.columns:
            fig = px.scatter(
                display_data,
                x='employment',
                y='annual_payroll',
                hover_name='industry',
                title="Employment vs Annual Payroll",
                labels={
                    'employment': 'Employment',
                    'annual_payroll': 'Annual Payroll ($)'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Scatter plot requires both employment and payroll data")
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    if st.button("Generate CSV Export", key="industry_export"):
        csv_data = data_utils.export_to_csv(
            display_data[list(available_columns.keys())].rename(columns=available_columns),
            f"industry_analysis_{county_fips}.csv"
        )
        
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"industry_analysis_{county_fips}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
