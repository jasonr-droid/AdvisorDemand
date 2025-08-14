import streamlit as st
from services.cache_manager import CacheManager

def render_cache_manager():
    """Render cache management interface for troubleshooting"""
    cache_manager = CacheManager()
    
    with st.expander("🗄️ Data Cache Management", expanded=False):
        st.write("**Cache Status for Development & Troubleshooting**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Cache info
            cache_info = cache_manager.get_cache_info()
            st.metric("Cached Files", cache_info['total_files'])
            st.metric("Cache Size (MB)", cache_info['total_size_mb'])
        
        with col2:
            # List cached data
            if st.button("📋 List Cached Data"):
                cached_items = cache_manager.list_cached_data()
                if cached_items:
                    for item in cached_items[:5]:  # Show latest 5
                        st.write(f"• {item['data_type']} - {item['county_fips']} ({item['rows']} rows)")
                else:
                    st.write("No cached data found")
        
        with col3:
            # Cache controls
            if st.button("🗑️ Clear All Cache"):
                cache_manager.clear_cache()
                st.success("Cache cleared!")
                st.rerun()
        
        # Cache retention notice
        st.info("💡 **Cache Retention**: Data is cached for 24-48 hours to avoid repeated API calls during troubleshooting. This prevents hitting API rate limits while we fix display issues.")