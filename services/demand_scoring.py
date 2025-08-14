# services/demand_scoring.py
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@dataclass
class DemandWeights:
    bfs_apps_yoy: float = 0.30
    licenses_per_1k: float = 0.25
    rfps_per_1k: float = 0.25
    qcew_emp_yoy: float = 0.20  # optional if available

class DemandScoringService:
    """Compute demand by industry, company targets, size buckets, and spend bands."""
    def __init__(self, data_service, weights: DemandWeights = DemandWeights()):
        self.ds = data_service
        self.w = weights

    @staticmethod
    def _z(series: pd.Series) -> pd.Series:
        if series.std(ddof=0) == 0 or series.count() < 2:
            return pd.Series(np.zeros(len(series)), index=series.index)
        return (series - series.mean()) / series.std(ddof=0)

    def industry_scores(self, county_fips: str) -> pd.DataFrame:
        cbp = self.ds.get_industry_data(county_fips, refresh=False)  # latest CBP frame
        bfs = self.ds.get_business_formation_data(county_fips, refresh=False)  # year, naics, applications, formations
        rfps = self.ds.get_rfp_data(county_fips, refresh=False)  # posted_date, naics
        qcew = None  # optional: pull from your existing qcew table if needed

        if cbp is None or cbp.empty:
            return pd.DataFrame(columns=["naics","naics_title","establishments","demand_score","spend_low","spend_high"])

        # Latest year establishments by NAICS (2-digit rollup suggested)
        cbp["naics2"] = cbp["naics"].astype(str).str[:2]
        latest_year = cbp["year"].max()
        estabs = (cbp[cbp["year"]==latest_year]
                  .groupby("naics2", as_index=False)["establishments"].sum())

        # BFS YoY applications by NAICS (if available)
        bfs = bfs.copy() if bfs is not None and not bfs.empty else pd.DataFrame(columns=["year","naics","applications"])
        if not bfs.empty:
            bfs["naics2"] = bfs["naics"].astype(str).str[:2]
            bfs_apps = bfs.groupby(["naics2","year"], as_index=False)["applications"].sum()
            bfs_apps["apps_yoy"] = bfs_apps.sort_values("year").groupby("naics2")["applications"].pct_change()
            bfs_apps_yoy = bfs_apps[bfs_apps["year"]==bfs_apps["year"].max()][["naics2","apps_yoy"]]
        else:
            bfs_apps_yoy = pd.DataFrame(columns=["naics2","apps_yoy"])

        # Licenses per 1k establishments (last 180 days)
        licenses = self.ds.get_license_data(county_fips, refresh=False)
        
        # Convert to DataFrame if it's a list
        if isinstance(licenses, list):
            licenses = pd.DataFrame(licenses) if licenses else pd.DataFrame()
        
        if licenses is not None and not licenses.empty:
            licenses["issued_date"] = pd.to_datetime(licenses["issued_date"], errors="coerce")
            cutoff = datetime.now() - timedelta(days=180)
            recent_lic = licenses[licenses["issued_date"] >= cutoff].copy()
            
            # Handle missing naics column
            if "naics" not in recent_lic.columns:
                recent_lic["naics"] = "00"  # Default NAICS if missing
                
            recent_lic["naics2"] = recent_lic["naics"].astype(str).str[:2]
            
            # Handle license_id column
            id_column = "license_id" if "license_id" in recent_lic.columns else recent_lic.columns[0]
            lic_counts = recent_lic.groupby("naics2", as_index=False)[id_column].count().rename(columns={id_column:"license_cnt"})
        else:
            lic_counts = pd.DataFrame(columns=["naics2","license_cnt"])

        # RFPs per 1k establishments (last 365 days)
        if rfps is not None and len(rfps) > 0:
            rfp_df = pd.DataFrame(rfps) if not isinstance(rfps, pd.DataFrame) else rfps.copy()
            rfp_df["posted_date"] = pd.to_datetime(rfp_df["posted_date"], errors="coerce")
            cutoff = datetime.now() - timedelta(days=365)
            rfp_df = rfp_df[rfp_df["posted_date"] >= cutoff]
            rfp_df["naics2"] = rfp_df["naics"].astype(str).str[:2]
            rfp_counts = rfp_df.groupby("naics2", as_index=False)["notice_id"].count().rename(columns={"notice_id":"rfp_cnt"})
        else:
            rfp_counts = pd.DataFrame(columns=["naics2","rfp_cnt"])

        # Join signals
        df = estabs.merge(bfs_apps_yoy, on="naics2", how="left") \
                   .merge(lic_counts, on="naics2", how="left") \
                   .merge(rfp_counts, on="naics2", how="left")
        df[["apps_yoy","license_cnt","rfp_cnt"]] = df[["apps_yoy","license_cnt","rfp_cnt"]].fillna(0.0)

        # Per-1k normalization where appropriate
        df["licenses_per_1k"] = np.where(df["establishments"]>0, 1000*df["license_cnt"]/df["establishments"], 0.0)
        df["rfps_per_1k"]     = np.where(df["establishments"]>0, 1000*df["rfp_cnt"]/df["establishments"], 0.0)

        # Z-score & weighted sum
        df["z_apps_yoy"]     = self._z(df["apps_yoy"])
        df["z_licenses_1k"]  = self._z(df["licenses_per_1k"])
        df["z_rfps_1k"]      = self._z(df["rfps_per_1k"])
        # Optional QCEW YoY employment growth could be added here as z_qcew_yoy

        df["demand_score"] = (
            self.w.bfs_apps_yoy * df["z_apps_yoy"] +
            self.w.licenses_per_1k * df["z_licenses_1k"] +
            self.w.rfps_per_1k * df["z_rfps_1k"]
        )

        # Spend bands by size proxy (employees per establishment ≈ avg firm size)
        # If you have CBP employment by naics2, compute avg_firm_size. Fallback to a simple mapping by establishments.
        df["spend_low"]  = np.where(df["establishments"]<200, 200, np.where(df["establishments"]<1000, 500, 1500))
        df["spend_high"] = np.where(df["establishments"]<200, 600, np.where(df["establishments"]<1000, 1500, 2500))

        df.rename(columns={"naics2":"naics"}, inplace=True)
        return df[["naics","establishments","demand_score","spend_low","spend_high"]].sort_values("demand_score", ascending=False)

    def top_companies(self, county_fips: str, limit:int=50) -> pd.DataFrame:
        """Heuristic: new/changed firms & recent licenses ≈ near-term bookkeeping demand."""
        firms = self.ds.get_firm_age_data(county_fips, refresh=False)  # your method returns dict; use firm table directly if available
        lic = self.ds.get_license_data(county_fips, refresh=False)
        
        # Convert to DataFrame if it's a list
        if isinstance(lic, list):
            lic = pd.DataFrame(lic) if lic else pd.DataFrame()
        
        if lic is None or lic.empty:
            return pd.DataFrame(columns=["company_name","naics","issued_date","signal"])
            
        lic["signal"] = "New/renewed license"
        
        # Handle missing columns gracefully
        available_cols = ["company_name", "naics", "issued_date", "signal", "jurisdiction", "status"]
        cols = [c for c in available_cols if c in lic.columns]
        
        # Ensure we have at least basic columns
        if "issued_date" not in lic.columns and "date" in lic.columns:
            lic["issued_date"] = lic["date"]
            cols.append("issued_date")
        
        # Sort and return top companies
        if "issued_date" in lic.columns:
            lic["issued_date"] = pd.to_datetime(lic["issued_date"], errors="coerce")
            return lic.sort_values("issued_date", ascending=False)[cols].head(limit)
        else:
            return lic[cols].head(limit)

    def size_breakdown(self, county_fips: str) -> pd.DataFrame:
        base = self.ds.get_firm_demographics(county_fips, refresh=False)
        return base  # already returns avg size and category in your current service

    def spend_estimates(self, county_fips: str) -> pd.DataFrame:
        ind = self.industry_scores(county_fips)
        return ind[["naics","spend_low","spend_high"]]