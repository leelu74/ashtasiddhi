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
from Vasitva import VasitvaAgent
from Mahima import MahimaAgent

class AnimaAgent:
    """Master Agent - Conquers and orchestrates exoplanet analysis"""
    
    def __init__(self, data_dir: str = "/data"):
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
            self.garima = GarimaAgent()      # Analysis & metrics
            self.isitva = IsitvaAgent()      # Data storage
            self.vasitva = VasitvaAgent()    # UI handling
            self.mahima = MahimaAgent()      # Backend ops
            self.logger.info("All agents initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
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
    parser.add_argument("--setup-repos", action="store_true", help="Setup GalSim/GREAT3 repositories")
    parser.add_argument("--ui", action="store_true", help="Start Streamlit UI")
    parser.add_argument("--api", action="store_true", help="Start FastAPI backend")
    parser.add_argument("--summary", action="store_true", help="Get analysis summary")
    parser.add_argument("--data-dir", type=str, default="/data", help="Data directory path")
    
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