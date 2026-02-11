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

        # Run migrations if needed
        self._run_migrations()
        
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

            # Analysis rules table for customizable patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    display_name TEXT,
                    patterns TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    UNIQUE(category, name)
                )
            """)

            conn.commit()
            conn.close()

            # Initialize default rules if not present
            self._initialize_default_rules()

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

    # ==================== NASA EXOPLANET ARCHIVE DATA ====================

    def store_nasa_exoplanet(self, nasa_data: Dict[str, Any]) -> int:
        """
        Store NASA Exoplanet Archive data

        Args:
            nasa_data: NASA Archive planet data

        Returns:
            Database ID of stored planet
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO nasa_exoplanets (
                    planet_name, hostname, discovery_method, discovery_year,
                    pl_orbper, pl_orbsmax, pl_rade, pl_bmasse, pl_eqt,
                    st_teff, st_rad, st_mass, st_dist,
                    has_atmosphere, atmosphere_composition, water_percent, mineral_composition,
                    hz_status, hz_confidence,
                    data_source, last_updated, archive_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                nasa_data.get('planet_name'),
                nasa_data.get('hostname'),
                nasa_data.get('discovery_method'),
                nasa_data.get('discovery_year'),
                nasa_data.get('pl_orbper'),
                nasa_data.get('pl_orbsmax'),
                nasa_data.get('pl_rade'),
                nasa_data.get('pl_bmasse'),
                nasa_data.get('pl_eqt'),
                nasa_data.get('st_teff'),
                nasa_data.get('st_rad'),
                nasa_data.get('st_mass'),
                nasa_data.get('st_dist'),
                nasa_data.get('has_atmosphere', False),
                json.dumps(nasa_data.get('atmosphere_composition', [])),
                nasa_data.get('water_percent'),
                json.dumps(nasa_data.get('mineral_composition', {})),
                nasa_data.get('hz_status'),
                nasa_data.get('hz_confidence'),
                nasa_data.get('data_source', 'NASA Exoplanet Archive'),
                datetime.now().isoformat(),
                nasa_data.get('archive_url')
            ))

            planet_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"Stored NASA planet: {nasa_data.get('planet_name', 'Unknown')}")
            return planet_id

        except Exception as e:
            self.logger.error(f"Failed to store NASA planet: {e}")
            raise

    def get_nasa_exoplanet(self, planet_name: str) -> Optional[Dict[str, Any]]:
        """Get NASA Archive planet by name"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT * FROM nasa_exoplanets
                WHERE planet_name = ?
            """, conn, params=[planet_name])
            conn.close()

            if len(df) > 0:
                return df.iloc[0].to_dict()
            return None

        except Exception as e:
            self.logger.error(f"Failed to get NASA planet: {e}")
            return None

    def sync_nasa_batch(self, exoplanets_list: List[Dict[str, Any]]) -> int:
        """Sync batch of NASA Archive planets"""
        count = 0
        for planet_data in exoplanets_list:
            try:
                self.store_nasa_exoplanet(planet_data)
                count += 1
            except Exception as e:
                self.logger.error(f"Failed to sync {planet_data.get('planet_name')}: {e}")
                continue

        self.logger.info(f"Synced {count}/{len(exoplanets_list)} NASA planets")
        return count

    def get_all_nasa_exoplanets(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all NASA Archive planets with optional filters"""
        try:
            conn = sqlite3.connect(self.db_path)

            where_clauses = []
            params = []

            if filters:
                if filters.get('hz_only'):
                    where_clauses.append("hz_status IN ('inner_hz', 'hz', 'outer_hz')")

                if filters.get('has_atmosphere'):
                    where_clauses.append("has_atmosphere = ?")
                    params.append(True)

                if filters.get('min_radius'):
                    where_clauses.append("pl_rade >= ?")
                    params.append(filters['min_radius'])

                if filters.get('max_radius'):
                    where_clauses.append("pl_rade <= ?")
                    params.append(filters['max_radius'])

            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            query = f"""
                SELECT * FROM nasa_exoplanets
                {where_sql}
                ORDER BY planet_name
            """

            results = pd.read_sql_query(query, conn, params=params if params else None)
            conn.close()

            return results.to_dict('records')

        except Exception as e:
            self.logger.error(f"Failed to get NASA planets: {e}")
            return []

    # ==================== FITS OBSERVATIONS ====================

    def store_fits_observation(self, fits_data: Dict[str, Any]) -> int:
        """Store FITS observation data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO fits_observations (
                    exoplanet_id, fits_file_path, telescope, instrument, obs_date, exposure_time,
                    wavelength_min, wavelength_max, spectral_resolution,
                    detected_lines, continuum_level, snr, header_metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fits_data.get('exoplanet_id'),
                fits_data.get('fits_file_path'),
                fits_data.get('telescope'),
                fits_data.get('instrument'),
                fits_data.get('obs_date'),
                fits_data.get('exposure_time'),
                fits_data.get('wavelength_min'),
                fits_data.get('wavelength_max'),
                fits_data.get('spectral_resolution'),
                json.dumps(fits_data.get('detected_lines', [])),
                fits_data.get('continuum_level'),
                fits_data.get('snr'),
                json.dumps(fits_data.get('header_metadata', {}))
            ))

            obs_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"Stored FITS observation ID {obs_id}")
            return obs_id

        except Exception as e:
            self.logger.error(f"Failed to store FITS observation: {e}")
            raise

    # ==================== SIMULATIONS ====================

    def store_simulation(self, sim_data: Dict[str, Any]) -> int:
        """Store simulation results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert numpy types to Python native types for JSON serialization
            def convert_numpy(obj):
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return obj

            cursor.execute("""
                INSERT INTO simulations (
                    exoplanet_id, simulation_type, input_params, results,
                    chi_squared, snr, depth_accuracy, created_at, galsim_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sim_data.get('exoplanet_id'),
                sim_data.get('simulation_type'),
                json.dumps(sim_data.get('input_params', {}), default=convert_numpy),
                json.dumps(sim_data.get('results', {}), default=convert_numpy),
                float(sim_data.get('chi_squared')) if sim_data.get('chi_squared') is not None else None,
                float(sim_data.get('snr')) if sim_data.get('snr') is not None else None,
                float(sim_data.get('depth_accuracy')) if sim_data.get('depth_accuracy') is not None else None,
                datetime.now().isoformat(),
                sim_data.get('galsim_version')
            ))

            sim_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"Stored simulation ID {sim_id}")
            return sim_id

        except Exception as e:
            self.logger.error(f"Failed to store simulation: {e}")
            raise

    # ==================== ML PREDICTIONS ====================

    def store_ml_prediction(self, pred_data: Dict[str, Any]) -> int:
        """Store ML model prediction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ml_predictions (
                    exoplanet_id, model_version, planet_type, planet_type_confidence, habitability_score,
                    predicted_mass, predicted_radius, predicted_temperature,
                    inference_time, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred_data.get('exoplanet_id'),
                pred_data.get('model_version'),
                pred_data.get('planet_type'),
                pred_data.get('planet_type_confidence'),
                pred_data.get('habitability_score'),
                pred_data.get('predicted_mass'),
                pred_data.get('predicted_radius'),
                pred_data.get('predicted_temperature'),
                pred_data.get('inference_time'),
                datetime.now().isoformat()
            ))

            pred_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"Stored ML prediction ID {pred_id}")
            return pred_id

        except Exception as e:
            self.logger.error(f"Failed to store ML prediction: {e}")
            raise

    # ==================== RULES MANAGEMENT ====================

    def _initialize_default_rules(self):
        """Initialize default analysis rules if not present"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if rules already exist
            cursor.execute("SELECT COUNT(*) FROM analysis_rules")
            count = cursor.fetchone()[0]

            if count == 0:
                self.logger.info("Initializing default analysis rules...")
                timestamp = datetime.now().isoformat()

                # Default chemical species patterns
                chemical_rules = [
                    ('chemical_species', 'h2o', 'Water (H2O)', r'\bh2o\b|\bwater\b|h₂o', 'Detects water/H2O mentions', 1),
                    ('chemical_species', 'h2s', 'Hydrogen Sulfide (H2S)', r'\bh2s\b|hydrogen\s+sulfide|h₂s', 'Detects H2S mentions', 2),
                    ('chemical_species', 'so2', 'Sulfur Dioxide (SO2)', r'\bso2\b|sulfur\s+dioxide|so₂', 'Detects SO2 mentions', 3),
                    ('chemical_species', 'h2', 'Hydrogen (H2)', r'\bh2\b(?!\w)|\bhydrogen\b(?!\s+sulfide)|h₂(?!\w)', 'Detects molecular hydrogen', 4),
                    ('chemical_species', 'he', 'Helium (He)', r'\bhe\b(?!\w)|\bhelium\b|⁴he', 'Detects helium mentions', 5),
                    ('chemical_species', 'ch4', 'Methane (CH4)', r'\bch4\b|\bmethane\b|ch₄', 'Detects methane mentions', 6),
                    ('chemical_species', 'co2', 'Carbon Dioxide (CO2)', r'\bco2\b|carbon\s+dioxide|co₂', 'Detects CO2 mentions', 7),
                    ('chemical_species', 'co', 'Carbon Monoxide (CO)', r'\bco\b(?!\w)|carbon\s+monoxide', 'Detects CO mentions', 8),
                    ('chemical_species', 'nh3', 'Ammonia (NH3)', r'\bnh3\b|\bammonia\b|nh₃', 'Detects ammonia mentions', 9),
                    ('chemical_species', 'n2', 'Nitrogen (N2)', r'\bn2\b(?!\w)|\bnitrogen\b|n₂', 'Detects nitrogen mentions', 10),
                    ('chemical_species', 'sulfur', 'Sulfur (S)', r'\bsulfur\b|\bs\b(?=\s+species)|\bsulphur\b', 'Detects sulfur mentions', 11),
                ]

                # Detection method patterns
                detection_rules = [
                    ('detection_methods', 'transit', 'Transit Method', r'\btransit\b|transit\s+photometry|transit\s+detection', 'Detects transit method mentions', 1),
                    ('detection_methods', 'radial_velocity', 'Radial Velocity', r'radial\s+velocity|\brv\b|doppler\s+shift', 'Detects RV method mentions', 2),
                    ('detection_methods', 'direct_imaging', 'Direct Imaging', r'direct\s+imaging|coronagraph', 'Detects direct imaging mentions', 3),
                    ('detection_methods', 'astrometry', 'Astrometry', r'\bastrometry\b|astrometric', 'Detects astrometry method', 4),
                    ('detection_methods', 'gravitational_lensing', 'Gravitational Lensing', r'gravitational\s+lensing|microlensing', 'Detects lensing method', 5),
                ]

                # Habitable zone patterns
                hz_rules = [
                    ('habitable_zone', 'hz_keywords', 'Habitable Zone Keywords', r'habitable\s+zone|goldilocks\s+zone|\bhz\b|potentially\s+habitable', 'Detects HZ keywords', 1),
                    ('habitable_zone', 'insolation', 'Insolation Pattern', r'insolation\s*=?\s*(\d+\.?\d*)\s*(s_earth|earth)', 'Extracts insolation values', 2),
                    ('habitable_zone', 'stellar_flux', 'Stellar Flux', r'stellar\s+flux\s*=?\s*(\d+\.?\d*)', 'Extracts stellar flux', 3),
                ]

                # Radial velocity extraction patterns
                rv_rules = [
                    ('rv_patterns', 'k_velocity', 'K Velocity', r'k\s*=?\s*(\d+\.?\d*)\s*(m/s|ms⁻¹|m\s*s⁻¹)', 'Extracts K velocity', 1),
                    ('rv_patterns', 'rv_amplitude', 'RV Amplitude', r'radial\s+velocity\s+amplitude\s*=?\s*(\d+\.?\d*)\s*(m/s)', 'Extracts RV amplitude', 2),
                    ('rv_patterns', 'period', 'Orbital Period', r'period\s*=?\s*(\d+\.?\d*)\s*(days?|d\b)', 'Extracts orbital period', 3),
                    ('rv_patterns', 'eccentricity', 'Eccentricity', r'eccentricity\s*=?\s*(\d+\.?\d*)', 'Extracts eccentricity', 4),
                ]

                # Transit patterns
                transit_rules = [
                    ('transit_patterns', 'depth', 'Transit Depth', r'transit\s+depth\s*=?\s*(\d+\.?\d*(?:[eE][+-]?\d+)?)\s*(%|ppm|mmag)', 'Extracts transit depth', 1),
                    ('transit_patterns', 'radius_ratio', 'Radius Ratio', r'r[_p]?/r[_\*]?\s*=?\s*(\d+\.?\d*)', 'Extracts Rp/Rs ratio', 2),
                    ('transit_patterns', 'planet_radius', 'Planet Radius', r'planet\s+radius\s*=?\s*(\d+\.?\d*)\s*(r_earth|earth\s+radii|r_⊕)', 'Extracts planet radius', 3),
                ]

                # Planetary properties patterns
                planetary_rules = [
                    ('planetary_properties', 'mass', 'Planet Mass', r'mass\s*=?\s*(\d+\.?\d*)\s*(m_earth|earth\s+masses|m_⊕)', 'Extracts planet mass', 1),
                    ('planetary_properties', 'radius', 'Planet Radius', r'radius\s*=?\s*(\d+\.?\d*)\s*(r_earth|earth\s+radii|r_⊕)', 'Extracts planet radius', 2),
                    ('planetary_properties', 'temperature', 'Temperature', r'temperature\s*=?\s*(\d+\.?\d*)\s*k', 'Extracts temperature', 3),
                    ('planetary_properties', 'density', 'Density', r'density\s*=?\s*(\d+\.?\d*)\s*(g/cm|kg/m)', 'Extracts density', 4),
                ]

                # Unique materials patterns
                unique_rules = [
                    ('unique_materials', 'tio2', 'Titanium Oxide', r'\btio2\b|titanium\s+oxide', 'Detects TiO2', 1),
                    ('unique_materials', 'vo', 'Vanadium Oxide', r'\bvo\b|vanadium\s+oxide', 'Detects VO', 2),
                    ('unique_materials', 'na', 'Sodium', r'\bna\b|sodium', 'Detects sodium', 3),
                    ('unique_materials', 'k', 'Potassium', r'\bk\b|potassium', 'Detects potassium', 4),
                    ('unique_materials', 'fe', 'Iron', r'\bfe\b|iron', 'Detects iron', 5),
                    ('unique_materials', 'clouds', 'Clouds/Hazes', r'clouds?|hazes?|aerosols?', 'Detects cloud mentions', 6),
                ]

                all_rules = chemical_rules + detection_rules + hz_rules + rv_rules + transit_rules + planetary_rules + unique_rules

                for category, name, display_name, patterns, description, priority in all_rules:
                    cursor.execute("""
                        INSERT INTO analysis_rules (category, name, display_name, patterns, description, is_active, priority, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (category, name, display_name, patterns, description, True, priority, timestamp))

                conn.commit()
                self.logger.info(f"Initialized {len(all_rules)} default rules")

            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to initialize default rules: {e}")

    # ==================== DATABASE VERSION & MIGRATIONS ====================

    def get_database_version(self) -> str:
        """Get current database schema version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if version table exists
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='schema_version'
            """)

            if cursor.fetchone() is None:
                conn.close()
                return "1.0"  # Default version before migrations

            cursor.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()

            return result[0] if result else "1.0"

        except Exception as e:
            self.logger.error(f"Failed to get database version: {e}")
            return "1.0"

    def _set_database_version(self, version: str):
        """Set database schema version"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create version table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                INSERT INTO schema_version (version, applied_at)
                VALUES (?, ?)
            """, (version, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            self.logger.info(f"Database version set to {version}")

        except Exception as e:
            self.logger.error(f"Failed to set database version: {e}")
            raise

    def _run_migrations(self):
        """Run pending database migrations"""
        current_version = self.get_database_version()

        self.logger.info(f"Current database version: {current_version}")

        # Run migrations in sequence
        if current_version == "1.0":
            self.logger.info("Running migration to v2.0...")
            self._migration_v2_0()
            current_version = "2.0"  # Update after migration

        if current_version == "2.0":
            self.logger.info("Running migration to v2.1...")
            self._migration_v2_1()

    def _migration_v2_0(self):
        """
        Migration to version 2.0
        Adds:
        - nasa_exoplanets table
        - fits_observations table
        - simulations table
        - ml_predictions table
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            self.logger.info("Creating NASA exoplanets table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nasa_exoplanets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    planet_name TEXT UNIQUE NOT NULL,
                    hostname TEXT,
                    discovery_method TEXT,
                    discovery_year INTEGER,

                    -- NASA Archive specific fields
                    pl_orbper REAL,
                    pl_orbsmax REAL,
                    pl_rade REAL,
                    pl_bmasse REAL,
                    pl_eqt REAL,

                    -- Stellar parameters
                    st_teff REAL,
                    st_rad REAL,
                    st_mass REAL,
                    st_dist REAL,

                    -- Atmospheric data
                    has_atmosphere BOOLEAN DEFAULT FALSE,
                    atmosphere_composition TEXT,
                    water_percent REAL,
                    mineral_composition TEXT,

                    -- Habitability
                    hz_status TEXT,
                    hz_confidence REAL,

                    -- Metadata
                    data_source TEXT DEFAULT 'NASA Exoplanet Archive',
                    last_updated TEXT,
                    archive_url TEXT
                )
            """)

            self.logger.info("Creating FITS observations table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fits_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exoplanet_id INTEGER,
                    fits_file_path TEXT NOT NULL,

                    -- Observation metadata
                    telescope TEXT,
                    instrument TEXT,
                    obs_date TEXT,
                    exposure_time REAL,

                    -- Spectroscopic data
                    wavelength_min REAL,
                    wavelength_max REAL,
                    spectral_resolution REAL,

                    -- Extracted features
                    detected_lines TEXT,
                    continuum_level REAL,
                    snr REAL,

                    -- FITS header JSON
                    header_metadata TEXT,

                    FOREIGN KEY (exoplanet_id) REFERENCES exoplanets (id)
                )
            """)

            self.logger.info("Creating simulations table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exoplanet_id INTEGER,
                    simulation_type TEXT,

                    -- Input parameters (JSON)
                    input_params TEXT,

                    -- Results (JSON)
                    results TEXT,

                    -- Validation metrics
                    chi_squared REAL,
                    snr REAL,
                    depth_accuracy REAL,

                    -- Metadata
                    created_at TEXT,
                    galsim_version TEXT,

                    FOREIGN KEY (exoplanet_id) REFERENCES exoplanets (id)
                )
            """)

            self.logger.info("Creating ML predictions table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ml_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exoplanet_id INTEGER,
                    model_version TEXT,

                    -- Predictions
                    planet_type TEXT,
                    planet_type_confidence REAL,
                    habitability_score REAL,

                    -- Extracted parameters
                    predicted_mass REAL,
                    predicted_radius REAL,
                    predicted_temperature REAL,

                    -- Model metadata
                    inference_time REAL,
                    created_at TEXT,

                    FOREIGN KEY (exoplanet_id) REFERENCES exoplanets (id)
                )
            """)

            # Create indexes for better query performance
            self.logger.info("Creating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nasa_planet_name ON nasa_exoplanets (planet_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_nasa_hz_status ON nasa_exoplanets (hz_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fits_exoplanet_id ON fits_observations (exoplanet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_simulations_exoplanet_id ON simulations (exoplanet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ml_predictions_exoplanet_id ON ml_predictions (exoplanet_id)")

            conn.commit()
            conn.close()

            # Set version to 2.0
            self._set_database_version("2.0")

            self.logger.info("✓ Migration to v2.0 completed successfully")

        except Exception as e:
            self.logger.error(f"Migration to v2.0 failed: {e}")
            raise

    def _migration_v2_1(self):
        """
        Migration to version 2.1
        Adds:
        - model_registry table (track ML models)
        - training_runs table (experiment tracking)
        - is_synthetic flag to fits_observations
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            self.logger.info("Creating model_registry table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT UNIQUE NOT NULL,
                    version TEXT NOT NULL,
                    model_file_path TEXT,
                    architecture TEXT,

                    -- Performance metrics
                    test_precision REAL,
                    test_recall REAL,
                    test_f1 REAL,

                    -- Training metadata
                    trained_on TEXT,
                    training_samples INTEGER,
                    validation_samples INTEGER,

                    -- Status
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TEXT,

                    UNIQUE(model_name, version)
                )
            """)

            self.logger.info("Creating training_runs table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    run_name TEXT,

                    -- Configuration
                    config TEXT,

                    -- Training progress
                    status TEXT,
                    current_epoch INTEGER,
                    total_epochs INTEGER,

                    -- Metrics
                    best_val_loss REAL,
                    final_metrics TEXT,

                    -- Timestamps
                    started_at TEXT,
                    completed_at TEXT
                )
            """)

            self.logger.info("Adding is_synthetic column to fits_observations...")
            # Check if column exists first
            cursor.execute("PRAGMA table_info(fits_observations)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'is_synthetic' not in columns:
                cursor.execute("""
                    ALTER TABLE fits_observations
                    ADD COLUMN is_synthetic BOOLEAN DEFAULT FALSE
                """)

            # Create indexes for better query performance
            self.logger.info("Creating indexes...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_registry_active ON model_registry (is_active)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_runs_status ON training_runs (status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_fits_synthetic ON fits_observations (is_synthetic)")

            conn.commit()
            conn.close()

            # Set version to 2.1
            self._set_database_version("2.1")

            self.logger.info("✓ Migration to v2.1 completed successfully")

        except Exception as e:
            self.logger.error(f"Migration to v2.1 failed: {e}")
            raise

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Get all analysis rules"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT * FROM analysis_rules
                ORDER BY category, priority
            """, conn)
            conn.close()
            return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Failed to get rules: {e}")
            return []

    def get_rules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get rules by category"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT * FROM analysis_rules
                WHERE category = ? AND is_active = 1
                ORDER BY priority
            """, conn, params=[category])
            conn.close()
            return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Failed to get rules for {category}: {e}")
            return []

    def get_rule_categories(self) -> List[str]:
        """Get list of unique rule categories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM analysis_rules ORDER BY category")
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            return categories
        except Exception as e:
            self.logger.error(f"Failed to get categories: {e}")
            return []

    def add_rule(self, category: str, name: str, patterns: str,
                 display_name: str = None, description: str = None,
                 priority: int = 1) -> int:
        """Add a new analysis rule"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.now().isoformat()
            display_name = display_name or name.replace('_', ' ').title()

            cursor.execute("""
                INSERT INTO analysis_rules (category, name, display_name, patterns, description, is_active, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (category, name, display_name, patterns, description, True, priority, timestamp))

            rule_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"Added rule: {name} in category {category}")
            return rule_id

        except sqlite3.IntegrityError:
            self.logger.error(f"Rule {name} already exists in category {category}")
            return -1
        except Exception as e:
            self.logger.error(f"Failed to add rule: {e}")
            return -1

    def update_rule(self, rule_id: int, patterns: str = None, display_name: str = None,
                    description: str = None, is_active: bool = None, priority: int = None) -> bool:
        """Update an existing rule"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            updates = []
            params = []

            if patterns is not None:
                updates.append("patterns = ?")
                params.append(patterns)
            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)

            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(rule_id)

                cursor.execute(f"""
                    UPDATE analysis_rules
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)

                conn.commit()

            conn.close()
            self.logger.info(f"Updated rule ID {rule_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update rule: {e}")
            return False

    def delete_rule(self, rule_id: int) -> bool:
        """Delete a rule by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM analysis_rules WHERE id = ?", (rule_id,))
            conn.commit()
            conn.close()

            self.logger.info(f"Deleted rule ID {rule_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete rule: {e}")
            return False

    def toggle_rule(self, rule_id: int) -> bool:
        """Toggle rule active status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE analysis_rules
                SET is_active = NOT is_active, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), rule_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.logger.error(f"Failed to toggle rule: {e}")
            return False

    def reset_rules_to_default(self) -> bool:
        """Reset all rules to default values"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM analysis_rules")
            conn.commit()
            conn.close()

            self._initialize_default_rules()
            self.logger.info("Rules reset to default")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset rules: {e}")
            return False

    def get_chemical_patterns(self) -> Dict[str, List[str]]:
        """Get chemical patterns in format for Garima agent"""
        rules = self.get_rules_by_category('chemical_species')
        patterns = {}
        for rule in rules:
            pattern_list = rule['patterns'].split('|')
            patterns[rule['name']] = pattern_list
        return patterns

    def get_detection_patterns(self) -> Dict[str, List[str]]:
        """Get detection method patterns"""
        rules = self.get_rules_by_category('detection_methods')
        patterns = {}
        for rule in rules:
            pattern_list = rule['patterns'].split('|')
            patterns[rule['name']] = pattern_list
        return patterns


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

        elif command == "version":
            version = agent.get_database_version()
            print(f"Database version: {version}")

        elif command == "migrate":
            print("Running database migrations...")
            agent._run_migrations()
            print(f"✓ Migrations complete. Current version: {agent.get_database_version()}")

        else:
            print("Unknown command")

    else:
        print("Usage: python Isitva.py [summary|stats|export|backup|version|migrate]")

if __name__ == "__main__":
    main()