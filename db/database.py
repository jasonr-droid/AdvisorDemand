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
        
        # Check each data source
        sources = [
            ('CBP', 'industry_cbp'),
            ('QCEW', 'industry_qcew'),
            ('SBA', 'sba_loans'),
            ('RFPs', 'rfp_opps'),
            ('Awards', 'awards'),
            ('Licenses', 'business_licenses'),
            ('Firms', 'firms'),
            ('BFS', 'bfs_county')
        ]
        
        for source_name, table_name in sources:
            if table_name in ['rfp_opps']:
                query = f"SELECT COUNT(*) as count FROM {table_name} WHERE place_county_fips = ?"
            elif table_name in ['awards']:
                query = f"SELECT COUNT(*) as count FROM {table_name} WHERE recipient_county_fips = ?"
            else:
                query = f"SELECT COUNT(*) as count FROM {table_name} WHERE county_fips = ?"
            
            try:
                result = self.execute_query(query, (county_fips,))
                coverage[source_name] = result['count'].iloc[0] > 0
            except Exception:
                coverage[source_name] = False
        
        return coverage
