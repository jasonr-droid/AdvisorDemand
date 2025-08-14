import os
import json
import pickle
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

class CacheManager:
    """Manages data caching to avoid repeated API calls during development"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache duration in hours
        self.cache_duration = {
            'cbp_data': 24,      # Census data changes infrequently
            'qcew_data': 24,     # BLS quarterly data
            'sba_data': 48,      # SBA data updates monthly
            'sam_data': 12,      # SAM.gov updates more frequently
            'firm_data': 48,     # Firm demographics change slowly
            'signals_data': 6    # Demand signals more dynamic
        }
    
    def _get_cache_key(self, data_type: str, county_fips: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_parts = [data_type, county_fips]
        
        # Add any additional parameters to the key
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}_{v}")
        
        return "_".join(key_parts)
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get metadata file path for cache key"""
        return self.cache_dir / f"{cache_key}_meta.json"
    
    def is_cache_valid(self, cache_key: str, data_type: str) -> bool:
        """Check if cached data is still valid"""
        meta_path = self._get_metadata_path(cache_key)
        
        if not meta_path.exists():
            return False
        
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata['timestamp'])
            max_age = timedelta(hours=self.cache_duration.get(data_type, 24))
            
            return datetime.now() - cached_time < max_age
        except Exception:
            return False
    
    def get_cached_data(self, data_type: str, county_fips: str, **kwargs) -> Optional[pd.DataFrame]:
        """Retrieve cached data if available and valid"""
        cache_key = self._get_cache_key(data_type, county_fips, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        if not self.is_cache_valid(cache_key, data_type):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            print(f"📋 Using cached {data_type} for {county_fips} ({len(data)} rows)")
            return data
        except Exception as e:
            print(f"Error reading cache: {e}")
            return None
    
    def cache_data(self, data: pd.DataFrame, data_type: str, county_fips: str, **kwargs) -> None:
        """Store data in cache"""
        if data is None or data.empty:
            return
        
        cache_key = self._get_cache_key(data_type, county_fips, **kwargs)
        cache_path = self._get_cache_path(cache_key)
        meta_path = self._get_metadata_path(cache_key)
        
        try:
            # Save data
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'data_type': data_type,
                'county_fips': county_fips,
                'rows': len(data),
                'kwargs': kwargs
            }
            
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 Cached {data_type} for {county_fips} ({len(data)} rows)")
            
        except Exception as e:
            print(f"Error caching data: {e}")
    
    def clear_cache(self, data_type: Optional[str] = None, county_fips: Optional[str] = None) -> None:
        """Clear cache files"""
        pattern = "*"
        
        if data_type and county_fips:
            pattern = f"{data_type}_{county_fips}_*"
        elif data_type:
            pattern = f"{data_type}_*"
        elif county_fips:
            pattern = f"*_{county_fips}_*"
        
        files_removed = 0
        for file_path in self.cache_dir.glob(f"{pattern}.pkl"):
            file_path.unlink()
            files_removed += 1
        
        for file_path in self.cache_dir.glob(f"{pattern}_meta.json"):
            file_path.unlink()
            files_removed += 1
        
        print(f"🗑️  Cleared {files_removed} cache files")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'total_files': len(cache_files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }
    
    def list_cached_data(self) -> List[Dict[str, Any]]:
        """List all cached data with metadata"""
        cached_items = []
        
        for meta_file in self.cache_dir.glob("*_meta.json"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                cached_items.append(metadata)
            except Exception:
                continue
        
        return sorted(cached_items, key=lambda x: x.get('timestamp', ''), reverse=True)