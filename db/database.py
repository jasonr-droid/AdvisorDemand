import sqlite3
import os
from contextlib import contextmanager
from typing import Generator, Dict, Any, List
import pandas as pd
from datetime import datetime

class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_path: str = "financial_advisor_analyzer.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        with self.get_connection() as conn:
            # Read and execute schema
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return DataFrame"""
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
    
    def execute_insert(self, table: str, data: Dict[str, Any]) -> None:
        """Insert data into table"""
        with self.get_connection() as conn:
            columns = list(data.keys())
            placeholders = ', '.join(['?' for _ in columns])
            # Use proper SQL identifier escaping to prevent injection
            escaped_table = table.replace('"', '""')  # Escape any quotes in table name
            query = f'INSERT OR REPLACE INTO "{escaped_table}" ({", ".join(columns)}) VALUES ({placeholders})'
            conn.execute(query, list(data.values()))
            conn.commit()
    
    def execute_bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> None:
        """Bulk insert data into table"""
        if not data:
            return
        
        with self.get_connection() as conn:
            columns = list(data[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            # Use proper SQL identifier escaping to prevent injection
            escaped_table = table.replace('"', '""')  # Escape any quotes in table name
            query = f'INSERT OR REPLACE INTO "{escaped_table}" ({", ".join(columns)}) VALUES ({placeholders})'
            
            values_list = [list(row.values()) for row in data]
            conn.executemany(query, values_list)
            conn.commit()
    
    def update_data_freshness(self, source_name: str, records_count: int = 0):
        """Update data freshness tracking"""
        freshness_data = {
            'source_name': source_name,
            'last_updated': datetime.now().isoformat(),
            'status': 'success',
            'records_count': records_count
        }
        self.execute_insert('data_freshness', freshness_data)
    
    def get_data_freshness(self) -> Dict[str, str]:
        """Get data freshness for all sources"""
        query = "SELECT source_name, last_updated FROM data_freshness"
        df = self.execute_query(query)
        return dict(zip(df['source_name'], df['last_updated']))
    
    def get_coverage_status(self, county_fips: str) -> Dict[str, bool]:
        """Check data coverage for a county"""
        coverage = {}
        
        # Check each data source with predefined table configurations
        # This prevents SQL injection by using hardcoded table names and column mappings
        table_configs = {
            'CBP': {'table': 'industry_cbp', 'fips_column': 'county_fips'},
            'QCEW': {'table': 'industry_qcew', 'fips_column': 'county_fips'},
            'SBA': {'table': 'sba_loans', 'fips_column': 'county_fips'},
            'RFPs': {'table': 'rfp_opps', 'fips_column': 'place_county_fips'},
            'Awards': {'table': 'awards', 'fips_column': 'recipient_county_fips'},
            'Licenses': {'table': 'business_licenses', 'fips_column': 'county_fips'},
            'Firms': {'table': 'firms', 'fips_column': 'county_fips'},
            'BFS': {'table': 'bfs_county', 'fips_column': 'county_fips'}
        }
        
        for source_name, config in table_configs.items():
            # Use parameterized query with hardcoded table and column names
            query = f"SELECT COUNT(*) as count FROM {config['table']} WHERE {config['fips_column']} = ?"
            
            try:
                result = self.execute_query(query, (county_fips,))
                coverage[source_name] = result['count'].iloc[0] > 0
            except Exception:
                coverage[source_name] = False
        
        return coverage
