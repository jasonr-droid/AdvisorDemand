import sqlite3
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the Financial Advisor Demand Analyzer"""
    
    def __init__(self, db_path: str = "financial_advisor_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        try:
            # Read and execute schema
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript(schema_sql)
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []
    
    def execute_insert(self, query: str, params: tuple = ()) -> bool:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            with self.get_connection() as conn:
                conn.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error executing insert: {e}")
            return False
    
    def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> bool:
        """Bulk insert data into table"""
        if not data:
            return True
            
        try:
            df = pd.DataFrame(data)
            with self.get_connection() as conn:
                df.to_sql(table, conn, if_exists='append', index=False)
                return True
        except Exception as e:
            logger.error(f"Error bulk inserting into {table}: {e}")
            return False
    
    def get_industry_data(self, county_fips: str, naics_level: int = 2) -> List[Dict[str, Any]]:
        """Get industry data for county with specified NAICS level"""
        naics_filter = ""
        if naics_level == 2:
            naics_filter = "AND LENGTH(c.naics) = 2"
        elif naics_level == 4:
            naics_filter = "AND LENGTH(c.naics) = 4"
        elif naics_level == 6:
            naics_filter = "AND LENGTH(c.naics) = 6"
        
        query = f"""
        SELECT 
            c.naics,
            n.title as naics_title,
            c.establishments,
            c.employment,
            c.annual_payroll,
            c.year as cbp_year,
            q.employment as qcew_employment,
            q.avg_weekly_wage,
            q.year as qcew_year,
            q.quarter as qcew_quarter,
            c.source_url as cbp_source,
            q.source_url as qcew_source
        FROM industry_cbp c
        LEFT JOIN industry_qcew q ON c.county_fips = q.county_fips AND c.naics = q.naics
        LEFT JOIN naics_codes n ON c.naics = n.naics
        WHERE c.county_fips = ? {naics_filter}
        ORDER BY c.establishments DESC, c.naics
        """
        
        return self.execute_query(query, (county_fips,))
    
    def get_sba_data(self, county_fips: str) -> List[Dict[str, Any]]:
        """Get SBA lending data for county"""
        query = """
        SELECT 
            program,
            COUNT(*) as loan_count,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount,
            MAX(approval_date) as latest_date,
            source_url
        FROM sba_loans
        WHERE county_fips = ?
        GROUP BY program
        ORDER BY total_amount DESC
        """
        
        return self.execute_query(query, (county_fips,))
    
    def get_rfp_data(self, county_fips: str) -> List[Dict[str, Any]]:
        """Get RFP opportunities for county"""
        query = """
        SELECT 
            notice_id,
            title,
            naics,
            posted_date,
            close_date,
            agency,
            url,
            source_url
        FROM rfp_opps
        WHERE place_county_fips = ?
        ORDER BY posted_date DESC
        LIMIT 100
        """
        
        return self.execute_query(query, (county_fips,))
    
    def get_awards_data(self, county_fips: str) -> List[Dict[str, Any]]:
        """Get federal awards for county"""
        query = """
        SELECT 
            award_id,
            naics,
            amount,
            action_date,
            agency,
            recipient_name,
            award_type,
            url,
            source_url
        FROM awards
        WHERE recipient_county_fips = ?
        ORDER BY action_date DESC, amount DESC
        LIMIT 100
        """
        
        return self.execute_query(query, (county_fips,))
    
    def get_licenses_data(self, county_fips: str) -> List[Dict[str, Any]]:
        """Get business licenses for county"""
        query = """
        SELECT 
            jurisdiction,
            business_name,
            naics,
            license_type,
            issued_date,
            status,
            source_url
        FROM business_licenses
        WHERE county_fips = ?
        ORDER BY issued_date DESC
        LIMIT 100
        """
        
        return self.execute_query(query, (county_fips,))
    
    def get_firm_age_data(self, county_fips: str) -> Dict[str, Any]:
        """Get firm age distribution for county"""
        query = """
        SELECT 
            incorporation_date,
            status,
            company_type
        FROM firms
        WHERE county_fips = ? AND incorporation_date IS NOT NULL
        """
        
        firms = self.execute_query(query, (county_fips,))
        
        # Calculate age buckets
        current_year = datetime.now().year
        age_buckets = {"0-1": 0, "1-3": 0, "3-5": 0, "5+": 0}
        
        for firm in firms:
            try:
                inc_year = int(firm['incorporation_date'][:4])
                age = current_year - inc_year
                
                if age <= 1:
                    age_buckets["0-1"] += 1
                elif age <= 3:
                    age_buckets["1-3"] += 1
                elif age <= 5:
                    age_buckets["3-5"] += 1
                else:
                    age_buckets["5+"] += 1
            except (ValueError, TypeError):
                continue
        
        total_firms = sum(age_buckets.values())
        match_rate = (total_firms / len(firms)) * 100 if firms else 0
        
        return {
            "age_buckets": age_buckets,
            "total_firms": total_firms,
            "match_rate": match_rate
        }
    
    def get_formations_data(self, county_fips: str) -> List[Dict[str, Any]]:
        """Get business formation statistics for county"""
        query = """
        SELECT 
            year,
            applications_total,
            high_propensity_apps,
            applications_with_planned_wages,
            source_url
        FROM bfs_county
        WHERE county_fips = ?
        ORDER BY year DESC
        """
        
        return self.execute_query(query, (county_fips,))
    
    def get_coverage_status(self, county_fips: str) -> Dict[str, Any]:
        """Get data coverage information for county"""
        coverage = {}
        
        # Check CBP data
        cbp_data = self.execute_query(
            "SELECT MAX(year) as latest_year FROM industry_cbp WHERE county_fips = ?",
            (county_fips,)
        )
        if cbp_data and cbp_data[0]['latest_year']:
            coverage['cbp'] = True
            coverage['cbp_date'] = str(cbp_data[0]['latest_year'])
        
        # Check QCEW data
        qcew_data = self.execute_query(
            "SELECT MAX(year || '-' || quarter) as latest_period FROM industry_qcew WHERE county_fips = ?",
            (county_fips,)
        )
        if qcew_data and qcew_data[0]['latest_period']:
            coverage['qcew'] = True
            coverage['qcew_date'] = qcew_data[0]['latest_period']
        
        # Check SBA data
        sba_data = self.execute_query(
            "SELECT COUNT(*) as count FROM sba_loans WHERE county_fips = ?",
            (county_fips,)
        )
        if sba_data and sba_data[0]['count'] > 0:
            coverage['sba'] = True
            latest_sba = self.execute_query(
                "SELECT MAX(approval_date) as latest FROM sba_loans WHERE county_fips = ?",
                (county_fips,)
            )
            if latest_sba and latest_sba[0]['latest']:
                coverage['sba_date'] = latest_sba[0]['latest']
        
        # Check contracts data
        contracts_data = self.execute_query(
            "SELECT COUNT(*) as rfp_count, (SELECT COUNT(*) FROM awards WHERE recipient_county_fips = ?) as award_count FROM rfp_opps WHERE place_county_fips = ?",
            (county_fips, county_fips)
        )
        if contracts_data and (contracts_data[0]['rfp_count'] > 0 or contracts_data[0]['award_count'] > 0):
            coverage['contracts'] = True
            coverage['contracts_date'] = "2024"  # Default current year
        
        return coverage
    
    def log_data_refresh(self, source: str, county_fips: str, status: str, records_updated: int = 0, error_message: str = None):
        """Log data refresh attempt"""
        query = """
        INSERT OR REPLACE INTO data_refresh_log 
        (source, county_fips, last_refresh, status, records_updated, error_message)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        current_time = datetime.now().isoformat()
        self.execute_insert(query, (source, county_fips, current_time, status, records_updated, error_message))
    
    def get_data_freshness(self) -> Dict[str, str]:
        """Get data freshness information for all sources"""
        freshness = {}
        
        # CBP data freshness
        cbp_query = """
        SELECT MAX(retrieved_at) as latest_retrieval 
        FROM industry_cbp 
        WHERE retrieved_at IS NOT NULL
        """
        cbp_result = self.execute_query(cbp_query)
        if cbp_result and cbp_result[0]['latest_retrieval']:
            freshness['CBP'] = cbp_result[0]['latest_retrieval']
        
        # QCEW data freshness
        qcew_query = """
        SELECT MAX(retrieved_at) as latest_retrieval 
        FROM industry_qcew 
        WHERE retrieved_at IS NOT NULL
        """
        qcew_result = self.execute_query(qcew_query)
        if qcew_result and qcew_result[0]['latest_retrieval']:
            freshness['QCEW'] = qcew_result[0]['latest_retrieval']
        
        # SBA data freshness
        sba_query = """
        SELECT MAX(retrieved_at) as latest_retrieval 
        FROM sba_loans 
        WHERE retrieved_at IS NOT NULL
        """
        sba_result = self.execute_query(sba_query)
        if sba_result and sba_result[0]['latest_retrieval']:
            freshness['SBA'] = sba_result[0]['latest_retrieval']
        
        # RFP data freshness
        rfp_query = """
        SELECT MAX(retrieved_at) as latest_retrieval 
        FROM rfp_opps 
        WHERE retrieved_at IS NOT NULL
        """
        rfp_result = self.execute_query(rfp_query)
        if rfp_result and rfp_result[0]['latest_retrieval']:
            freshness['RFPs'] = rfp_result[0]['latest_retrieval']
        
        # Awards data freshness
        awards_query = """
        SELECT MAX(retrieved_at) as latest_retrieval 
        FROM awards 
        WHERE retrieved_at IS NOT NULL
        """
        awards_result = self.execute_query(awards_query)
        if awards_result and awards_result[0]['latest_retrieval']:
            freshness['Awards'] = awards_result[0]['latest_retrieval']
        
        return freshness
