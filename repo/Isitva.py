#!/usr/bin/env python3
"""
Isitva.py - Data Storage Agent
Sits under one place data - unified SQLite/JSON store for all exoplanet analysis data
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

class IsitvaAgent:
    """Agent for unified data storage and management"""
    
    def __init__(self, data_dir: str = "./data"):
        self.logger = logging.getLogger("Isitva")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Database file
        self.db_path = self.data_dir / "exoplanets.db"
        
        # Initialize database
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Main exoplanets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exoplanets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pdf_path TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    
                    -- Chemical composition
                    h2o_detected BOOLEAN DEFAULT FALSE,
                    h2s_detected BOOLEAN DEFAULT FALSE,
                    so2_detected BOOLEAN DEFAULT FALSE,
                    h2_detected BOOLEAN DEFAULT FALSE,
                    he_detected BOOLEAN DEFAULT FALSE,
                    ch4_detected BOOLEAN DEFAULT FALSE,
                    co2_detected BOOLEAN DEFAULT FALSE,
                    sulfur_detected BOOLEAN DEFAULT FALSE,
                    
                    -- Radial velocity data
                    rv_k_velocity REAL,
                    rv_period REAL,
                    rv_eccentricity REAL,
                    rv_minimum_mass REAL,
                    
                    -- Transit data
                    transit_depth REAL,
                    transit_radius_ratio REAL,
                    transit_period REAL,
                    planet_radius_earth REAL,
                    
                    -- Habitable zone
                    in_habitable_zone BOOLEAN DEFAULT FALSE,
                    insolation REAL,
                    effective_temperature REAL,
                    semi_major_axis REAL,
                    
                    -- Planetary properties
                    planet_mass_earth REAL,
                    planet_density REAL,
                    
                    -- Stellar properties
                    stellar_mass_solar REAL,
                    stellar_radius_solar REAL,
                    stellar_temperature REAL,
                    
                    -- Detection confidence
                    detection_significance REAL,
                    confirmation_status TEXT,
                    detection_methods TEXT,
                    
                    -- Computed metrics
                    atmospheric_detectability REAL,
                    confirmation_score REAL,
                    habitability_index REAL
                )
            """)
            
            # Chemical abundances table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chemical_abundances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exoplanet_id INTEGER,
                    species TEXT NOT NULL,
                    abundance_value REAL,
                    abundance_unit TEXT,
                    FOREIGN KEY (exoplanet_id) REFERENCES exoplanets (id)
                )
            """)
            
            # Papers table for tracking literature
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    url TEXT,
                    pdf_url TEXT,
                    published_date TEXT,
                    source TEXT,
                    keywords TEXT,
                    relevance_score REAL,
                    downloaded_path TEXT,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Analysis sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_name TEXT,
                    timestamp TEXT NOT NULL,
                    papers_analyzed INTEGER DEFAULT 0,
                    exoplanets_found INTEGER DEFAULT 0,
                    session_summary TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            self.logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def store_analysis(self, pdf_path: str, analysis_results: Dict[str, Any]) -> int:
        """
        Store complete analysis results in database
        
        Args:
            pdf_path: Path to analyzed PDF
            analysis_results: Complete analysis results from Garima agent
            
        Returns:
            Database ID of stored record
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract data from analysis results
            composition = analysis_results.get('chemical_composition', {})
            rv_data = analysis_results.get('radial_velocity', {})
            transit_data = analysis_results.get('transit_analysis', {})
            hz_data = analysis_results.get('habitable_zone', {})
            planetary = analysis_results.get('planetary_properties', {})
            stellar = analysis_results.get('stellar_properties', {})
            confidence = analysis_results.get('detection_confidence', {})
            metrics = analysis_results.get('computed_metrics', {})
            
            # Prepare data for insertion
            filename = Path(pdf_path).name
            timestamp = datetime.now().isoformat()
            analysis_json = json.dumps(analysis_results, default=str)
            
            # Chemical species detection flags
            detected_species = composition.get('detected_species', [])
            
            # Insert main record
            cursor.execute("""
                INSERT OR REPLACE INTO exoplanets (
                    pdf_path, filename, timestamp, analysis_json,
                    h2o_detected, h2s_detected, so2_detected, h2_detected, he_detected,
                    ch4_detected, co2_detected, sulfur_detected,
                    rv_k_velocity, rv_period, rv_eccentricity, rv_minimum_mass,
                    transit_depth, transit_radius_ratio, transit_period, planet_radius_earth,
                    in_habitable_zone, insolation, effective_temperature, semi_major_axis,
                    planet_mass_earth, planet_density,
                    stellar_mass_solar, stellar_radius_solar, stellar_temperature,
                    detection_significance, confirmation_status, detection_methods,
                    atmospheric_detectability, confirmation_score, habitability_index
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pdf_path, filename, timestamp, analysis_json,
                'h2o' in detected_species, 'h2s' in detected_species, 'so2' in detected_species,
                'h2' in detected_species, 'he' in detected_species, 'ch4' in detected_species,
                'co2' in detected_species, 'sulfur' in detected_species,
                rv_data.get('k_velocity'), rv_data.get('period'), rv_data.get('eccentricity'),
                rv_data.get('minimum_mass'),
                transit_data.get('depth'), transit_data.get('radius_ratio'),
                transit_data.get('period'), transit_data.get('planet_radius'),
                hz_data.get('in_habitable_zone', False), hz_data.get('insolation'),
                hz_data.get('effective_temperature'), hz_data.get('semi_major_axis'),
                planetary.get('mass_earth'), planetary.get('density'),
                stellar.get('mass_solar'), stellar.get('radius_solar'), stellar.get('temperature'),
                confidence.get('detection_significance'), confidence.get('confirmation_status'),
                json.dumps(confidence.get('methods_used', [])),
                metrics.get('atmospheric_detectability'), metrics.get('confirmation_score'),
                metrics.get('habitability_index')
            ))
            
            exoplanet_id = cursor.lastrowid
            
            # Store chemical abundances
            abundances = composition.get('abundances', {})
            for species, abundance_data in abundances.items():
                cursor.execute("""
                    INSERT INTO chemical_abundances (exoplanet_id, species, abundance_value, abundance_unit)
                    VALUES (?, ?, ?, ?)
                """, (
                    exoplanet_id, species, abundance_data.get('value'), abundance_data.get('unit')
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored analysis for {filename} with ID {exoplanet_id}")
            return exoplanet_id
            
        except Exception as e:
            self.logger.error(f"Failed to store analysis: {e}")
            raise
    
    def store_paper(self, paper_data: Dict[str, Any]) -> int:
        """
        Store paper metadata in database
        
        Args:
            paper_data: Paper metadata from Laghima agent
            
        Returns:
            Database ID of stored paper
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO papers (
                    title, authors, abstract, url, pdf_url, published_date,
                    source, keywords, relevance_score, downloaded_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_data.get('title'),
                json.dumps(paper_data.get('authors', [])),
                paper_data.get('abstract'),
                paper_data.get('url'),
                paper_data.get('pdf_url'),
                paper_data.get('published'),
                paper_data.get('source'),
                json.dumps(paper_data.get('keywords', [])),
                paper_data.get('relevance_score'),
                paper_data.get('downloaded_path')
            ))
            
            paper_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored paper: {paper_data.get('title', 'Unknown')}")
            return paper_id
            
        except Exception as e:
            self.logger.error(f"Failed to store paper: {e}")
            raise
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get comprehensive analysis summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Overall statistics
            total_analyses = pd.read_sql_query("SELECT COUNT(*) as count FROM exoplanets", conn).iloc[0]['count']
            
            # Chemical composition statistics
            composition_stats = pd.read_sql_query("""
                SELECT 
                    SUM(h2o_detected) as h2o_count,
                    SUM(h2s_detected) as h2s_count,
                    SUM(so2_detected) as so2_count,
                    SUM(sulfur_detected) as sulfur_count,
                    SUM(ch4_detected) as ch4_count,
                    SUM(co2_detected) as co2_count
                FROM exoplanets
            """, conn)
            
            # Habitable zone statistics
            hz_stats = pd.read_sql_query("""
                SELECT 
                    SUM(in_habitable_zone) as habitable_count,
                    AVG(insolation) as avg_insolation,
                    AVG(habitability_index) as avg_habitability_index
                FROM exoplanets
            """, conn)
            
            # Detection method statistics
            detection_stats = pd.read_sql_query("""
                SELECT 
                    COUNT(CASE WHEN rv_k_velocity IS NOT NULL THEN 1 END) as rv_detections,
                    COUNT(CASE WHEN transit_depth IS NOT NULL THEN 1 END) as transit_detections,
                    AVG(detection_significance) as avg_significance
                FROM exoplanets
            """, conn)
            
            # Recent analyses
            recent_analyses = pd.read_sql_query("""
                SELECT filename, timestamp, in_habitable_zone, atmospheric_detectability, habitability_index
                FROM exoplanets 
                ORDER BY timestamp DESC 
                LIMIT 10
            """, conn)
            
            conn.close()
            
            summary = {
                'total_analyses': total_analyses,
                'composition_statistics': composition_stats.to_dict('records')[0],
                'habitable_zone_statistics': hz_stats.to_dict('records')[0],
                'detection_statistics': detection_stats.to_dict('records')[0],
                'recent_analyses': recent_analyses.to_dict('records'),
                'generated_at': datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            return {'error': str(e)}
    
    def search_exoplanets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search exoplanets with filters
        
        Args:
            filters: Search criteria
            
        Returns:
            List of matching exoplanet records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            where_clauses = []
            params = []
            
            # Build WHERE clause from filters
            if filters.get('habitable_only'):
                where_clauses.append("in_habitable_zone = ?")
                params.append(True)
            
            if filters.get('has_atmosphere'):
                where_clauses.append("(h2o_detected = 1 OR h2s_detected = 1 OR ch4_detected = 1)")
            
            if filters.get('min_radius'):
                where_clauses.append("planet_radius_earth >= ?")
                params.append(filters['min_radius'])
            
            if filters.get('max_radius'):
                where_clauses.append("planet_radius_earth <= ?")
                params.append(filters['max_radius'])
            
            if filters.get('detection_method'):
                method = filters['detection_method']
                if method == 'transit':
                    where_clauses.append("transit_depth IS NOT NULL")
                elif method == 'radial_velocity':
                    where_clauses.append("rv_k_velocity IS NOT NULL")
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT * FROM exoplanets
                {where_sql}
                ORDER BY timestamp DESC
            """
            
            results = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            return results.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def export_data(self, format_type: str = 'json', output_path: Optional[str] = None) -> str:
        """
        Export analysis data in various formats
        
        Args:
            format_type: 'json', 'csv', or 'excel'
            output_path: Optional output file path
            
        Returns:
            Path to exported file
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Export main exoplanets data
            df_exoplanets = pd.read_sql_query("SELECT * FROM exoplanets", conn)
            df_abundances = pd.read_sql_query("SELECT * FROM chemical_abundances", conn)
            df_papers = pd.read_sql_query("SELECT * FROM papers", conn)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == 'json':
                if not output_path:
                    output_path = self.data_dir / f"exoplanet_data_{timestamp}.json"
                
                export_data = {
                    'exoplanets': df_exoplanets.to_dict('records'),
                    'chemical_abundances': df_abundances.to_dict('records'),
                    'papers': df_papers.to_dict('records'),
                    'export_timestamp': datetime.now().isoformat()
                }
                
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif format_type == 'csv':
                if not output_path:
                    output_path = self.data_dir / f"exoplanet_data_{timestamp}.csv"
                df_exoplanets.to_csv(output_path, index=False)
            
            elif format_type == 'excel':
                if not output_path:
                    output_path = self.data_dir / f"exoplanet_data_{timestamp}.xlsx"
                
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    df_exoplanets.to_excel(writer, sheet_name='Exoplanets', index=False)
                    df_abundances.to_excel(writer, sheet_name='Chemical_Abundances', index=False)
                    df_papers.to_excel(writer, sheet_name='Papers', index=False)
            
            conn.close()
            self.logger.info(f"Data exported to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics for dashboard"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            stats = {}
            
            # Planet type distribution
            planet_types = pd.read_sql_query("""
                SELECT 
                    CASE 
                        WHEN planet_radius_earth < 1.25 THEN 'Earth-like'
                        WHEN planet_radius_earth < 2.0 THEN 'Super-Earth'
                        WHEN planet_radius_earth < 4.0 THEN 'Mini-Neptune'
                        WHEN planet_radius_earth < 11.0 THEN 'Neptune-like'
                        ELSE 'Jupiter-like'
                    END as planet_type,
                    COUNT(*) as count
                FROM exoplanets 
                WHERE planet_radius_earth IS NOT NULL
                GROUP BY planet_type
            """, conn)
            
            stats['planet_type_distribution'] = planet_types.to_dict('records')
            
            # Atmospheric composition trends
            atm_composition = pd.read_sql_query("""
                SELECT 
                    'H2O' as species, SUM(h2o_detected) as count
                FROM exoplanets
                UNION ALL
                SELECT 'H2S', SUM(h2s_detected) FROM exoplanets
                UNION ALL
                SELECT 'SO2', SUM(so2_detected) FROM exoplanets
                UNION ALL
                SELECT 'CH4', SUM(ch4_detected) FROM exoplanets
                UNION ALL
                SELECT 'CO2', SUM(co2_detected) FROM exoplanets
                ORDER BY count DESC
            """, conn)
            
            stats['atmospheric_composition'] = atm_composition.to_dict('records')
            
            # Habitability metrics
            habitability = pd.read_sql_query("""
                SELECT 
                    AVG(habitability_index) as avg_habitability,
                    COUNT(CASE WHEN in_habitable_zone = 1 THEN 1 END) as habitable_count,
                    COUNT(*) as total_count,
                    AVG(insolation) as avg_insolation
                FROM exoplanets
            """, conn)
            
            stats['habitability_metrics'] = habitability.to_dict('records')[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            self.logger.error(f"Statistics calculation failed: {e}")
            return {}
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """Create database backup"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.data_dir / f"exoplanets_backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"Database backed up to {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise
    
    def clear_all_data(self):
        """Clear all data from database (use with caution!)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM chemical_abundances")
            cursor.execute("DELETE FROM exoplanets")
            cursor.execute("DELETE FROM papers")
            cursor.execute("DELETE FROM analysis_sessions")
            
            conn.commit()
            conn.close()
            
            self.logger.warning("All data cleared from database")
            
        except Exception as e:
            self.logger.error(f"Data clearing failed: {e}")
            raise

def main():
    """Test the Isitva agent"""
    import sys
    
    agent = IsitvaAgent()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            summary = agent.get_analysis_summary()
            print(json.dumps(summary, indent=2, default=str))
        
        elif command == "stats":
            stats = agent.get_statistics()
            print(json.dumps(stats, indent=2, default=str))
        
        elif command == "export":
            format_type = sys.argv[2] if len(sys.argv) > 2 else 'json'
            path = agent.export_data(format_type)
            print(f"Data exported to: {path}")
        
        elif command == "backup":
            path = agent.backup_database()
            print(f"Database backed up to: {path}")
        
        else:
            print("Unknown command")
    
    else:
        print("Usage: python Isitva.py [summary|stats|export|backup]")

if __name__ == "__main__":
    main()