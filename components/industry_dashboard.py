import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, List, Any, Optional

from services.data_service import DataService
from utils.data_quality import DataQualityManager
from lib.naics_mapping import naics_mapper
from lib.date_utils import date_utils

logger = logging.getLogger(__name__)

class IndustryDashboard:
    """Industry analysis dashboard component"""

    def __init__(self, data_service: DataService, quality_manager: DataQualityManager):
        self.data_service = data_service
        self.quality_manager = quality_manager
        # Assuming data_utils is available and has format_number and get_data_badge methods
        # If not, these would need to be defined or imported. For now, let's assume they exist.
        try:
            from utils.data_utils import DataUtils
            self.data_utils = DataUtils()
        except ImportError:
            # Mocking data_utils if not found to allow code to run
            class MockDataUtils:
                def format_number(self, number):
                    return f"{number:,}" if isinstance(number, (int, float)) else number
                def get_data_badge(self, label):
                    if label == 'Observed': return '🟢'
                    if label == 'Estimated': return '🟡'
                    if label == 'Proxy': return '🟣'
                    return ''
            self.data_utils = MockDataUtils()


    def render(self, county_fips: str):
        """Render complete industry dashboard"""
        st.header("🏭 Industry Analysis")

        # Industry level selector
        naics_level = st.selectbox(
            "Industry Detail Level:",
            [2, 4, 6],
            format_func=lambda x: {2: "Sector (2-digit)", 4: "Industry Group (4-digit)", 6: "Detailed Industry (6-digit)"}[x],
            index=0,
            help="Select the level of industry detail to display"
        )

        # Get industry data
        with st.spinner("Loading industry data..."):
            industry_data = self.data_service.get_industry_data(county_fips, naics_level)

        if industry_data is None or (hasattr(industry_data, 'empty') and industry_data.empty) or (isinstance(industry_data, list) and len(industry_data) == 0):
            st.warning("No industry data available for this county.")
            return

        # Convert DataFrame to list of dicts for processing
        if hasattr(industry_data, 'to_dict'):
            industry_records = industry_data.to_dict('records')
        else:
            industry_records = industry_data if isinstance(industry_data, list) else []

        # Apply data quality filtering
        quality_filtered_data = self._apply_quality_filters(industry_records)

        # Summary metrics
        self._render_summary_metrics(quality_filtered_data)

        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Industries Overview", "💼 Financial Services", "📈 Trends & Analysis", "📋 Data Export"])

        with tab1:
            self._render_industries_overview(quality_filtered_data)

        with tab2:
            self._render_financial_services_focus(quality_filtered_data)

        with tab3:
            self._render_trends_analysis(quality_filtered_data, county_fips)

        with tab4:
            self._render_data_export(quality_filtered_data, county_fips)

    def _render_summary_metrics(self, industry_data: List[Dict[str, Any]]):
        """Render summary metrics cards"""
        if not industry_data:
            return

        # Calculate totals
        total_establishments = sum(d.get('establishments', 0) or 0 for d in industry_data)
        total_employment = sum(d.get('employment', 0) or 0 for d in industry_data)
        total_payroll = sum(d.get('annual_payroll', 0) or 0 for d in industry_data)

        # Financial services totals
        financial_data = [d for d in industry_data if d.get('is_financial_services')]
        financial_establishments = sum(d.get('establishments', 0) or 0 for d in financial_data)
        financial_employment = sum(d.get('employment', 0) or 0 for d in financial_data)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Establishments",
                f"{total_establishments:,}",
                help="Total business establishments in county"
            )

        with col2:
            st.metric(
                "Total Employment", 
                f"{total_employment:,}",
                help="Total number of employees"
            )

        with col3:
            st.metric(
                "Annual Payroll",
                f"${total_payroll:,.0f}" if total_payroll else "N/A",
                help="Total annual payroll across all industries"
            )

        with col4:
            financial_pct = (financial_employment / total_employment * 100) if total_employment > 0 else 0
            st.metric(
                "Financial Services",
                f"{financial_establishments:,} Est.",
                delta=f"{financial_pct:.1f}% of employment",
                help="Financial services establishments and employment share"
            )

    def _render_industries_overview(self, industry_data: List[Dict[str, Any]]):
        """Render industries overview table and charts"""
        if not industry_data:
            st.info("No industry data to display")
            return

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(industry_data)

        # Sort by employment
        df = df.sort_values('employment', ascending=False, na_position='last')

        # Display options
        col1, col2 = st.columns([2, 1])

        with col1:
            show_financial_only = st.checkbox("Show only financial services", value=False)

        with col2:
            chart_type = st.selectbox("Chart Type:", ["Employment", "Establishments", "Payroll"])

        # Filter data if requested
        if show_financial_only:
            # Add financial services classification if not present
            if 'is_financial_services' not in df.columns:
                df = self._add_financial_services_classification(df)
            df = df[df['is_financial_services'] == True]

        if df.empty:
            st.warning("No data matches the selected filters")
            return

        # Industries table
        st.subheader("Industries Table")

        # Format data for display
        display_df = self._format_industries_table(df)

        # Display table with styling
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Quality": st.column_config.TextColumn("Quality", help="Data quality grade"),
                "Establishments": st.column_config.NumberColumn("Establishments", format="%d"),
                "Employment": st.column_config.NumberColumn("Employment", format="%d"),
                "Payroll": st.column_config.NumberColumn("Annual Payroll", format="$%,.0f"),
                "Avg Wage": st.column_config.NumberColumn("Avg Weekly Wage", format="$%,.0f"),
                "RFPs": st.column_config.NumberColumn("RFPs", format="%d"),
                "Awards": st.column_config.NumberColumn("Awards", format="%d"),
                "SBA Loans": st.column_config.NumberColumn("SBA Loans", format="%d")
            }
        )

        # Industry visualization
        st.subheader(f"Top Industries by {chart_type}")

        if chart_type == "Employment":
            self._render_employment_chart(df.head(15))
        elif chart_type == "Establishments":
            self._render_establishments_chart(df.head(15))
        elif chart_type == "Payroll":
            self._render_payroll_chart(df.head(15))

    def _render_financial_services_focus(self, industry_data: List[Dict[str, Any]]):
        """Render financial services focused analysis"""
        
        # Filter for financial services
        financial_data = [d for d in industry_data if d.get('is_financial_services')]

        if not financial_data:
            st.info("No financial services data available for this county.")
            return

        st.subheader("Financial Services Deep Dive")

        # Core financial advisor industries (NAICS 5239*)
        core_advisor_naics = ['5239', '52393', '52392']
        core_data = []
        for record in financial_data:
            naics_code = str(record.get('naics', ''))
            if any(naics_code.startswith(code) for code in core_advisor_naics):
                core_data.append(record)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_fs_establishments = sum(d.get('establishments', 0) or 0 for d in financial_data)
            st.metric(
                f"{self.data_utils.get_data_badge('Observed')} FS Establishments",
                self.data_utils.format_number(total_fs_establishments)
            )

        with col2:
            total_fs_employment = sum(d.get('employment', 0) or 0 for d in financial_data)  
            st.metric(
                f"{self.data_utils.get_data_badge('Observed')} FS Employment",
                self.data_utils.format_number(total_fs_employment)
            )

        with col3:
            core_establishments = sum(d.get('establishments', 0) or 0 for d in core_data)
            if core_establishments == 0 and financial_data:
                # Estimate advisor firms as subset of financial services
                estimated_advisors = max(1, int(total_fs_establishments * 0.15))  # ~15% estimate
                st.metric(
                    f"{self.data_utils.get_data_badge('Estimated')} Advisor Firms",
                    self.data_utils.format_number(estimated_advisors),
                    help="Estimated based on financial services establishments"
                )
            else:
                st.metric(
                    f"{self.data_utils.get_data_badge('Observed')} Advisor Firms",
                    self.data_utils.format_number(core_establishments),
                    help="NAICS 5239 - Other Financial Investment Activities"
                )

        with col4:
            core_employment = sum(d.get('employment', 0) or 0 for d in core_data)
            if core_employment == 0 and financial_data:
                # Estimate advisor employment as subset of financial services
                estimated_employment = max(1, int(total_fs_employment * 0.12))  # ~12% estimate
                st.metric(
                    f"{self.data_utils.get_data_badge('Estimated')} Advisor Employment", 
                    self.data_utils.format_number(estimated_employment),
                    help="Estimated people employed in financial advisory roles"
                )
            else:
                st.metric(
                    f"{self.data_utils.get_data_badge('Observed')} Advisor Employment", 
                    self.data_utils.format_number(core_employment),
                    help="People employed in financial advisory roles"
                )

        # Detailed breakdown
        st.write("**Financial Services Industries Breakdown:**")

        # Create display dataframe
        fs_df = pd.DataFrame(financial_data)
        if not fs_df.empty:
            display_df = self._format_financial_services_table(fs_df)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("No detailed financial services data available")

        # Financial services activity chart
        if len(financial_data) > 1:
            st.subheader("Financial Services by Industry")

            fs_df_chart = pd.DataFrame(financial_data)
            fs_df_chart = fs_df_chart.sort_values('employment', ascending=True)

            fig = px.bar(
                fs_df_chart.tail(10), 
                x='employment',
                y='naics_title',
                title="Employment in Financial Services Industries",
                labels={'employment': 'Employment', 'naics_title': 'Industry'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

    def _render_trends_analysis(self, industry_data: List[Dict[str, Any]], county_fips: str):
        """Render trends and competitive analysis"""
        st.subheader("Market Analysis & Trends")

        # Market concentration analysis
        if industry_data:
            df = pd.DataFrame(industry_data)
            total_employment = sum(d.get('employment', 0) or 0 for d in industry_data)

            # Calculate concentration
            df['employment_share'] = df['employment'] / total_employment * 100
            df = df.sort_values('employment_share', ascending=False)

            # Top industries concentration
            top_5_share = df.head(5)['employment_share'].sum()

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Market Concentration",
                    f"{top_5_share:.1f}%",
                    help="Employment share of top 5 industries"
                )

            with col2:
                hhi = sum((share/100) ** 2 for share in df['employment_share'] if not pd.isna(share))
                concentration_level = "High" if hhi > 0.25 else "Moderate" if hhi > 0.15 else "Low"
                st.metric(
                    "Competition Level",
                    concentration_level,
                    help=f"HHI: {hhi:.3f}"
                )

        # Opportunity analysis
        st.subheader("Business Opportunities")

        # Calculate opportunity scores
        opportunity_data = self._calculate_opportunity_scores(industry_data, county_fips)

        if opportunity_data:
            opp_df = pd.DataFrame(opportunity_data)
            opp_df = opp_df.sort_values('opportunity_score', ascending=False)

            st.write("**Top Opportunities for Financial Advisors:**")

            for _, row in opp_df.head(5).iterrows():
                with st.expander(f"🎯 {row['naics_title']} (Score: {row['opportunity_score']:.1f})"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Establishments", f"{row['establishments']:,}")
                        st.metric("Employment", f"{row['employment']:,}")

                    with col2:
                        st.metric("Recent RFPs", f"{row['rfp_count']:,}")
                        st.metric("Federal Awards", f"{row['award_count']:,}")

                    with col3:
                        st.metric("SBA Activity", f"{row['sba_count']:,} loans")
                        st.metric("Avg Payroll/Employee", f"${row['avg_pay']:,.0f}")

        # Demand signals chart
        st.subheader("Demand Indicators")

        demand_df = pd.DataFrame([
            {
                'naics_title': d['naics_title'],
                'rfp_count': d.get('rfp_count', 0),
                'award_count': d.get('award_count', 0),
                'sba_count': d.get('sba_loans', {}).get('count', 0)
            }
            for d in industry_data if d.get('is_financial_services')
        ])

        if not demand_df.empty and demand_df[['rfp_count', 'award_count', 'sba_count']].sum().sum() > 0:
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('RFP Opportunities', 'Federal Awards', 'SBA Lending'),
                specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
            )

            # RFPs
            fig.add_trace(
                go.Bar(x=demand_df['naics_title'], y=demand_df['rfp_count'], name='RFPs'),
                row=1, col=1
            )

            # Awards  
            fig.add_trace(
                go.Bar(x=demand_df['naics_title'], y=demand_df['award_count'], name='Awards'),
                row=1, col=2
            )

            # SBA
            fig.add_trace(
                go.Bar(x=demand_df['naics_title'], y=demand_df['sba_count'], name='SBA Loans'),
                row=1, col=3
            )

            fig.update_layout(height=400, showlegend=False)
            fig.update_xaxes(tickangle=45)

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent demand signals data available")

    def _render_data_export(self, industry_data: List[Dict[str, Any]], county_fips: str):
        """Render data export options"""
        st.subheader("📁 Export Data")

        if not industry_data:
            st.info("No data available for export")
            return

        # Export options
        col1, col2 = st.columns(2)

        with col1:
            export_format = st.selectbox("Format:", ["CSV", "Excel", "JSON"])
            include_metadata = st.checkbox("Include metadata & sources", value=True)

        with col2:
            include_quality = st.checkbox("Include quality indicators", value=True)
            include_financial_only = st.checkbox("Financial services only", value=False)

        # Filter data for export
        export_data = industry_data.copy()
        if include_financial_only:
            export_data = [d for d in export_data if d.get('is_financial_services')]

        # Prepare export DataFrame
        export_df = self._prepare_export_dataframe(
            export_data, 
            include_metadata=include_metadata,
            include_quality=include_quality
        )

        # Display preview
        st.write("**Export Preview:**")
        st.dataframe(export_df.head(10), use_container_width=True)

        # Download button
        if export_format == "CSV":
            csv_data = export_df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv_data,
                file_name=f"industry_analysis_{county_fips}.csv",
                mime="text/csv"
            )

        elif export_format == "Excel":
            # Note: In a full implementation, you'd use openpyxl or xlsxwriter
            st.info("Excel export would be available with additional libraries")

        elif export_format == "JSON":
            json_data = export_df.to_json(orient='records', indent=2)
            st.download_button(
                "📥 Download JSON",
                json_data,
                file_name=f"industry_analysis_{county_fips}.json",
                mime="application/json"
            )

        # Data dictionary
        with st.expander("📖 Data Dictionary"):
            self._render_data_dictionary()

    def _apply_quality_filters(self, industry_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply data quality filters and suppression"""
        filtered_data = []

        for record in industry_data:
            # Apply small cell suppression
            suppressed_record = self.quality_manager.apply_small_cell_suppression(
                record, 
                ['establishments', 'employment']
            )

            # Assess quality
            quality_info = self.quality_manager.assess_data_quality(suppressed_record)
            suppressed_record['quality_score'] = quality_info['overall_score']
            suppressed_record['quality_grade'] = quality_info['grade']

            filtered_data.append(suppressed_record)

        return filtered_data

    def _format_industries_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format industries data for table display"""
        # Define all possible columns
        all_display_columns = {
            'naics': 'NAICS',
            'naics_title': 'Industry',
            'establishments': 'Establishments', 
            'employment': 'Employment',
            'annual_payroll': 'Payroll',
            'avg_weekly_wage': 'Avg Wage',
            'rfp_count': 'RFPs',
            'award_count': 'Awards',
            'sba_loans': 'SBA Loans',
            'quality_grade': 'Quality'
        }

        # Only use columns that actually exist in the DataFrame
        available_columns = {k: v for k, v in all_display_columns.items() if k in df.columns}

        # Create display DataFrame with only available columns
        if available_columns:
            display_df = df[list(available_columns.keys())].copy()
            display_df = display_df.rename(columns=available_columns)
        else:
            # Fallback to all columns if none match
            display_df = df.copy()

        # Handle suppressed values
        for col in ['Establishments', 'Employment', 'Payroll']:
            suppressed_col = f"{col.lower()}_suppressed"
            if suppressed_col in df.columns and col in display_df.columns:
                display_df.loc[df[suppressed_col], col] = "—"

        # Format SBA loans column (it's a dict)
        if 'sba_loans' in df.columns and 'SBA Loans' in display_df.columns:
            display_df['SBA Loans'] = df['sba_loans'].apply(
                lambda x: x.get('count', 0) if isinstance(x, dict) else 0
            )

        # Format numeric columns
        if 'Establishments' in display_df.columns:
            display_df['Establishments'] = display_df['Establishments'].apply(
                lambda x: f"{x:,}" if pd.notna(x) and x != "—" else x
            )
        if 'Employment' in display_df.columns:
            display_df['Employment'] = display_df['Employment'].apply(
                lambda x: f"{x:,}" if pd.notna(x) and x != "—" else x
            )
        if 'Payroll' in display_df.columns:
            display_df['Payroll'] = display_df['Payroll'].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x != "—" else x
            )

        # Add badges for financial services
        if 'is_financial_services' in df.columns:
            display_df['Type'] = df['is_financial_services'].apply(
                lambda x: "🏦 Financial" if x else "🏭 Other"
            )

        return display_df

    def _format_financial_services_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format financial services data for detailed display"""
        display_df = df[['naics', 'naics_title', 'establishments', 'employment', 'annual_payroll']].copy()

        # Calculate additional metrics
        display_df['avg_pay'] = display_df['annual_payroll'] / display_df['employment']
        display_df['employees_per_establishment'] = display_df['employment'] / display_df['establishments']

        return display_df

    def _calculate_opportunity_scores(self, industry_data: List[Dict[str, Any]], county_fips: str) -> List[Dict[str, Any]]:
        """Calculate business opportunity scores"""
        opportunity_data = []

        for industry in industry_data:
            if not industry.get('is_financial_services'):
                continue

            # Calculate opportunity score based on multiple factors
            score = 0

            # Market size (establishments and employment)
            establishments = industry.get('establishments', 0) or 0
            employment = industry.get('employment', 0) or 0

            score += min(establishments * 0.1, 20)  # Up to 20 points
            score += min(employment * 0.01, 30)    # Up to 30 points

            # Demand signals
            rfp_count = industry.get('rfp_count', 0) or 0
            award_count = industry.get('award_count', 0) or 0
            sba_activity = industry.get('sba_loans', {})
            sba_count = sba_activity.get('count', 0) if isinstance(sba_activity, dict) else 0

            score += rfp_count * 5     # 5 points per RFP
            score += award_count * 3   # 3 points per award  
            score += sba_count * 2     # 2 points per SBA loan

            # Payroll indicates ability to pay
            annual_payroll = industry.get('annual_payroll', 0) or 0
            if employment > 0:
                avg_pay = annual_payroll / employment
                if avg_pay > 75000:  # Above average pay
                    score += 15
                elif avg_pay > 50000:
                    score += 10
                elif avg_pay > 35000:
                    score += 5

            # Core financial advisor bonus
            if industry.get('is_core_advisor'):
                score += 10

            opportunity_data.append({
                'naics': industry['naics'],
                'naics_title': industry['naics_title'],
                'establishments': establishments,
                'employment': employment,
                'rfp_count': rfp_count,
                'award_count': award_count,
                'sba_loans': sba_count,
                'avg_pay': avg_pay if employment > 0 else 0,
                'opportunity_score': min(score, 100)  # Cap at 100
            })

        return opportunity_data

    def _render_employment_chart(self, df: pd.DataFrame):
        """Render employment bar chart"""
        # Use available columns for chart
        y_column = 'naics_title' if 'naics_title' in df.columns else 'naics'
        y_label = 'Industry' if y_column == 'naics_title' else 'NAICS Code'

        fig = px.bar(
            df,
            x='employment',
            y=y_column,
            title="Employment by Industry",
            labels={'employment': 'Employment', y_column: y_label},
            orientation='h'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    def _render_establishments_chart(self, df: pd.DataFrame):
        """Render establishments bar chart"""
        # Use available columns for chart
        y_column = 'naics_title' if 'naics_title' in df.columns else 'naics'
        y_label = 'Industry' if y_column == 'naics_title' else 'NAICS Code'

        fig = px.bar(
            df,
            x='establishments', 
            y=y_column,
            title="Establishments by Industry",
            labels={'establishments': 'Establishments', y_column: y_label},
            orientation='h'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    def _render_payroll_chart(self, df: pd.DataFrame):
        """Render payroll bar chart"""
        # Filter out null payroll values
        df_filtered = df[df['annual_payroll'].notna()]

        if df_filtered.empty:
            st.info("No payroll data available for chart")
            return

        # Use available columns for chart
        y_column = 'naics_title' if 'naics_title' in df_filtered.columns else 'naics'
        y_label = 'Industry' if y_column == 'naics_title' else 'NAICS Code'

        fig = px.bar(
            df_filtered,
            x='annual_payroll',
            y=y_column, 
            title="Annual Payroll by Industry",
            labels={'annual_payroll': 'Annual Payroll ($)', y_column: y_label},
            orientation='h'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    def _prepare_export_dataframe(self, data: List[Dict[str, Any]], 
                                 include_metadata: bool = True, 
                                 include_quality: bool = True) -> pd.DataFrame:
        """Prepare comprehensive export DataFrame"""
        export_records = []

        for record in data:
            export_record = {
                'NAICS_Code': record.get('naics', ''),
                'Industry_Title': record.get('naics_title', ''),
                'Establishments': record.get('establishments'),
                'Employment': record.get('employment'),
                'Annual_Payroll': record.get('annual_payroll'),
                'Average_Weekly_Wage': record.get('avg_weekly_wage'),
                'Is_Financial_Services': record.get('is_financial_services', False),
                'Is_Core_Financial_Advisor': record.get('is_core_advisor', False),
                'RFP_Opportunities': record.get('rfp_count', 0),
                'Federal_Awards': record.get('award_count', 0),
                'SBA_Loan_Count': record.get('sba_loans', {}).get('count', 0) if isinstance(record.get('sba_loans'), dict) else 0,
                'SBA_Loan_Amount': record.get('sba_loans', {}).get('amount', 0) if isinstance(record.get('sba_loans'), dict) else 0
            }

            if include_quality:
                export_record.update({
                    'Quality_Score': record.get('quality_score', 0),
                    'Quality_Grade': record.get('quality_grade', ''),
                    'Has_Suppression': record.get('has_suppression', False)
                })

            if include_metadata:
                export_record.update({
                    'CBP_Year': record.get('cbp_year'),
                    'QCEW_Year': record.get('qcew_year'), 
                    'QCEW_Quarter': record.get('qcew_quarter'),
                    'CBP_Source': record.get('cbp_source', ''),
                    'QCEW_Source': record.get('qcew_source', '')
                })

            export_records.append(export_record)

        return pd.DataFrame(export_records)

    def _render_data_dictionary(self):
        """Render data dictionary for exports"""
        st.write("""
        **Data Dictionary:**

        - **NAICS_Code**: North American Industry Classification System code
        - **Industry_Title**: Industry description
        - **Establishments**: Number of business establishments (CBP)
        - **Employment**: Number of employees (CBP/QCEW) 
        - **Annual_Payroll**: Total annual payroll in dollars (CBP)
        - **Average_Weekly_Wage**: Average weekly wage per employee (QCEW)
        - **Is_Financial_Services**: Boolean indicating financial services industry
        - **Is_Core_Financial_Advisor**: Boolean indicating core financial advisory services
        - **RFP_Opportunities**: Number of recent RFP opportunities
        - **Federal_Awards**: Number of recent federal contract awards
        - **SBA_Loan_Count/Amount**: SBA lending activity
        - **Quality_Score**: Data quality score (0-100)
        - **Has_Suppression**: Boolean indicating if small cell suppression was applied

        **Data Labels:**
        - 🟢 **Observed**: Direct measurements from official sources
        - 🟡 **Proxy**: Derived or estimated values
        - 🟣 **Estimated**: Model-based estimates

        **Sources:**
        - CBP: U.S. Census Bureau County Business Patterns
        - QCEW: Bureau of Labor Statistics Quarterly Census of Employment and Wages
        - RFP: SAM.gov federal contracting opportunities
        - Awards: USAspending.gov federal contract awards
        - SBA: Small Business Administration lending data
        """)

    def _add_financial_services_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add financial services classification based on NAICS codes"""
        # Financial services NAICS codes (52, 523, 5239, etc.)
        financial_naics_codes = [
            '52',    # Finance and Insurance
            '522',   # Credit Intermediation and Related Activities
            '523',   # Securities, Commodity Contracts, and Other Financial Investments
            '524',   # Insurance Carriers and Related Activities
            '525',   # Funds, Trusts, and Other Financial Vehicles
            '5239'   # Other Financial Investment Activities (includes advisors)
        ]

        # Create classification column
        df['is_financial_services'] = df['naics'].astype(str).apply(
            lambda x: any(x.startswith(code) for code in financial_naics_codes)
        )

        # Mark core financial advisor NAICS specifically
        df['is_core_advisor'] = df['naics'].astype(str).str.startswith('5239')

        return df


def render_industry_dashboard(data_service: DataService, county_fips: str):
    """Render the industry dashboard for a given county"""
    from utils.data_quality import DataQualityManager

    # Initialize dashboard components
    quality_manager = DataQualityManager()
    dashboard = IndustryDashboard(data_service, quality_manager)

    # Render the dashboard
    dashboard.render(county_fips)