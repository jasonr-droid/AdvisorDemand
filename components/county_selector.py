import streamlit as st
from lib.fips import FIPSHelper

def render_county_selector():
    """Render county selection component"""
    fips_helper = FIPSHelper()
    
    # Initialize session state for selected county
    if 'selected_county' not in st.session_state:
        st.session_state.selected_county = None
    
    # County selection options
    st.subheader("Select County")
    
    # Option 1: Search by name or FIPS
    search_term = st.text_input(
        "Search by county name or FIPS code",
        placeholder="e.g., San Diego County, CA or 06073",
        help="Enter county name with state or 5-digit FIPS code"
    )
    
    if search_term:
        found_fips = fips_helper.parse_county_search(search_term)
        if found_fips:
            county_info = fips_helper.get_county_info(found_fips)
            if county_info:
                st.success(f"✅ Found: {county_info['name']}, {county_info['state']} ({county_info['fips']})")
                if st.button("Select This County", key="search_select"):
                    st.session_state.selected_county = county_info
                    st.rerun()
        else:
            st.warning("County not found. Try a different search term or select from the list below.")
    
    st.divider()
    
    # Option 2: Select from dropdown
    st.subheader("Or select from major counties:")
    sample_counties = fips_helper.get_sample_counties()
    
    county_options = [""] + [county['display_name'] for county in sample_counties]
    
    selected_display = st.selectbox(
        "Choose a county",
        county_options,
        help="Select from major U.S. counties with available data"
    )
    
    if selected_display:
        # Find the corresponding county info
        for county in sample_counties:
            if county['display_name'] == selected_display:
                if st.session_state.selected_county != county:
                    st.session_state.selected_county = county
                    st.rerun()
                break
    
    # Display current selection
    if st.session_state.selected_county:
        st.divider()
        county = st.session_state.selected_county
        
        st.info(f"**Current Selection:** {county['name']}, {county['state']} (FIPS: {county['fips']})")
        
        if st.button("Clear Selection", key="clear_county"):
            st.session_state.selected_county = None
            st.rerun()
    
    return st.session_state.selected_county
