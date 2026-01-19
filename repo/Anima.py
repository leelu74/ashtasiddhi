#!/usr/bin/env python3
"""
Anima.py - Master Agent for Exoplanet Analysis System
Orchestrates all sub-agents and manages the complete analysis workflow
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

from Prakamya import PrakamyaAgent
from Laghima import LaghimaAgent  
from Prapti import PraptiAgent
from Garima import GarimaAgent
from Isitva import IsitvaAgent
from Mahima import MahimaAgent

class AnimaAgent:
    """Master Agent - Conquers and orchestrates exoplanet analysis"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.unified_data_path = self.data_dir / "unified_data.json"
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("Anima")
        
        # Initialize sub-agents
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize all sub-agents"""
        try:
            self.prakamya = PrakamyaAgent()  # Keywords extraction
            self.laghima = LaghimaAgent()    # Paper search
            self.prapti = PraptiAgent()      # Repo management
            self.garima = GarimaAgent(str(self.data_dir))  # Analysis & metrics (with DB rules)
            self.isitva = IsitvaAgent(str(self.data_dir))  # Data storage
            self.mahima = MahimaAgent()      # Backend ops
            
            # Initialize vasitva lazily to avoid circular import
            self._vasitva = None
            
            self.logger.info("All agents initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    @property
    def vasitva(self):
        """Lazy loading of Vasitva agent to avoid circular import"""
        if self._vasitva is None:
            from Vasitva import VasitvaAgent
            self._vasitva = VasitvaAgent(str(self.data_dir))
        return self._vasitva
    
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Complete PDF analysis workflow
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Analysis results dictionary
        """
        self.logger.info(f"Starting analysis of {pdf_path}")
        
        try:
            # Step 1: Extract keywords from PDF
            self.logger.info("Extracting keywords...")
            keywords = self.prakamya.extract_keywords(pdf_path)
            
            # Step 2: Analyze PDF content for exoplanet data
            self.logger.info("Analyzing exoplanet characteristics...")
            analysis_results = self.garima.analyze_pdf(pdf_path)
            
            # Step 3: Store results
            self.logger.info("Storing analysis results...")
            stored_id = self.isitva.store_analysis(pdf_path, analysis_results)
            
            # Step 4: Update unified data
            unified_data = {
                "pdf_path": pdf_path,
                "keywords": keywords,
                "analysis": analysis_results,
                "storage_id": stored_id,
                "timestamp": self.isitva.get_timestamp()
            }
            
            self._update_unified_data(unified_data)
            
            self.logger.info("Analysis completed successfully")
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            raise
    
    def search_papers(self, query_terms: List[str], max_papers: int = 10) -> List[Dict]:
        """Search for papers using Laghima agent"""
        self.logger.info(f"Searching papers with terms: {query_terms}")
        return self.laghima.search_papers(query_terms, max_papers)
    
    def setup_repositories(self) -> Dict[str, str]:
        """Setup GalSim and GREAT3 repositories"""
        self.logger.info("Setting up external repositories...")
        return self.prapti.setup_repositories()
    
    def run_simulation(self, planet_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run transit simulation using GalSim"""
        self.logger.info("Running transit simulation...")
        return self.prapti.run_transit_simulation(planet_params)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all analyses"""
        return self.isitva.get_analysis_summary()
    
    def search_all_nearest_papers(self):
        """CLI: python Anima.py --search-all"""
        self.logger.info("Starting paper search for all 9 nearest star systems")
        
        # Get systems from Laghima agent
        systems = self.laghima.NEAREST_SYSTEMS
        
        total_downloaded = 0
        
        for system in systems.keys():
            try:
                self.logger.info(f"Searching papers for {system}...")
                papers = self.laghima.search_system_papers(system, 5)
                print(f"✅ {system}: {len(papers)}/5 papers")
                total_downloaded += len(papers)
                
                # Brief pause between systems
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Failed to search papers for {system}: {e}")
                print(f"❌ {system}: Error occurred")
        
        print(f"\n🎉 TOTAL: {total_downloaded} papers downloaded across 9 systems")
        return total_downloaded
    
    def inspect_all_systems(self):
        """CLI: python Anima.py --inspect-all"""
        self.logger.info("Inspecting all downloaded papers")
        
        systems = self.laghima.NEAREST_SYSTEMS
        
        for system, distance in systems.items():
            try:
                inspection = self.laghima.inspect_downloaded_papers(system)
                self.print_crisp_table(system, distance, inspection)
                
            except Exception as e:
                self.logger.error(f"Failed to inspect {system}: {e}")
                print(f"❌ {system}: Inspection failed")
        
        return True
    
    def inspect_single_system(self, system: str):
        """CLI: python Anima.py --inspect [system]"""
        systems = self.laghima.NEAREST_SYSTEMS
        
        if system not in systems:
            print(f"❌ System '{system}' not found. Available systems:")
            for sys_name in systems.keys():
                print(f"   - {sys_name}")
            return False
        
        try:
            inspection = self.laghima.inspect_downloaded_papers(system)
            distance = systems[system]
            self.print_crisp_table(system, distance, inspection)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to inspect {system}: {e}")
            print(f"❌ {system}: Inspection failed")
            return False
    
    def print_crisp_table(self, system: str, distance: float, inspection: dict):
        """Clean table output for CLI/UI"""
        print(f"\n🪐 {system.upper()} ({distance} ly) - {inspection['total_papers']} PAPERS")
        
        if inspection['total_papers'] == 0:
            print("   No papers found for this system")
            return
        
        # Print table header
        print("┌──────────────────┬────────┬──────────────┬──────────┐")
        print("│ File             │ Pages  │ Chemicals    │ Priority │")
        print("├──────────────────┼────────┼──────────────┼──────────┤")
        
        # Print each paper
        for paper in inspection['papers']:
            filename = paper['filename'][:15] + "..." if len(paper['filename']) > 18 else paper['filename']
            pages = str(paper.get('pages', 'N/A'))
            
            # Format chemicals
            chemicals = paper.get('chemicals', [])
            chem_str = ','.join(chemicals[:3])  # First 3 chemicals
            if len(chemicals) > 3:
                chem_str += "..."
            if len(chem_str) > 12:
                chem_str = chem_str[:12] + "..."
                
            priority = paper.get('priority', 'LOW')
            
            print(f"│ {filename:<16} │ {pages:<6} │ {chem_str:<12} │ {priority:<8} │")
        
        print("└──────────────────┴────────┴──────────────┴──────────┘")
        print(f"SUMMARY: {inspection['summary']}")
        
        # Show metrics if available
        high_priority = [p for p in inspection['papers'] if p.get('priority') == 'HIGH']
        if high_priority:
            print(f"🔥 HIGH PRIORITY: {len(high_priority)} papers with key features")
    
    def _update_unified_data(self, new_data: Dict[str, Any]):
        """Update the unified data file"""
        unified_data = []
        
        # Load existing data if file exists
        if self.unified_data_path.exists():
            try:
                with open(self.unified_data_path, 'r') as f:
                    unified_data = json.load(f)
            except json.JSONDecodeError:
                self.logger.warning("Corrupted unified data file, starting fresh")
                unified_data = []
        
        # Append new data
        unified_data.append(new_data)
        
        # Save back to file
        with open(self.unified_data_path, 'w') as f:
            json.dump(unified_data, f, indent=2, default=str)
    
    def start_ui(self, host: str = "0.0.0.0", port: int = 8501):
        """Start the Streamlit UI"""
        self.logger.info(f"Starting UI on {host}:{port}")
        self.vasitva.start_ui(host, port)
    
    def start_api(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI backend"""
        self.logger.info(f"Starting API on {host}:{port}")
        self.mahima.start_api(host, port)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Anima - Exoplanet Analysis Master Agent")
    parser.add_argument("--pdf", type=str, help="Path to PDF file for analysis")
    parser.add_argument("--search", nargs="+", help="Search terms for paper search")
    parser.add_argument("--search-all", action="store_true", help="Search papers for all 9 nearest systems")
    parser.add_argument("--inspect-all", action="store_true", help="Inspect all downloaded papers")
    parser.add_argument("--inspect", type=str, help="Inspect specific system (e.g., 'Proxima Centauri')")
    parser.add_argument("--setup-repos", action="store_true", help="Setup GalSim/GREAT3 repositories")
    parser.add_argument("--ui", action="store_true", help="Start Streamlit UI")
    parser.add_argument("--api", action="store_true", help="Start FastAPI backend")
    parser.add_argument("--summary", action="store_true", help="Get analysis summary")
    parser.add_argument("--data-dir", type=str, default="./data", help="Data directory path")
    
    args = parser.parse_args()
    
    # Initialize Anima
    anima = AnimaAgent(args.data_dir)
    
    try:
        if args.pdf:
            # Analyze PDF
            result = anima.analyze_pdf(args.pdf)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.search:
            # Search papers
            papers = anima.search_papers(args.search)
            print(json.dumps(papers, indent=2, default=str))
            
        elif args.search_all:
            # Search all nearest systems
            anima.search_all_nearest_papers()
            
        elif args.inspect_all:
            # Inspect all systems
            anima.inspect_all_systems()
            
        elif args.inspect:
            # Inspect specific system
            anima.inspect_single_system(args.inspect)
            
        elif args.setup_repos:
            # Setup repositories
            repos = anima.setup_repositories()
            print(json.dumps(repos, indent=2))
            
        elif args.summary:
            # Get summary
            summary = anima.get_analysis_summary()
            print(json.dumps(summary, indent=2, default=str))
            
        elif args.ui:
            # Start UI
            anima.start_ui()
            
        elif args.api:
            # Start API
            anima.start_api()
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()