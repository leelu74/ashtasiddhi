#!/usr/bin/env python3
"""
test_paper_system.py - Test the paper search and inspection system
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Laghima import LaghimaAgent

def test_paper_search():
    """Test paper search functionality for one system"""
    print("🧪 TESTING PAPER SEARCH SYSTEM")
    print("=" * 50)
    
    # Configure minimal logging
    logging.basicConfig(level=logging.WARNING)
    
    try:
        # Initialize agent
        print("1️⃣  Initializing Laghima agent...")
        laghima = LaghimaAgent("./data/papers")
        
        # Show available systems
        print("2️⃣  Available nearest star systems:")
        for i, (system, distance) in enumerate(laghima.NEAREST_SYSTEMS.items(), 1):
            print(f"    {i:2d}. {system:<18} ({distance:5.2f} ly)")
        
        # Test search for one system (Proxima Centauri)
        print("\n3️⃣  Testing search for Proxima Centauri...")
        test_system = "Proxima Centauri"
        
        # Search and download papers (limit to 2 for testing)
        papers = laghima.search_system_papers(test_system, max_papers=2)
        print(f"    ✅ Found {len(papers)} papers for {test_system}")
        
        # Inspect downloaded papers
        print("\n4️⃣  Testing paper inspection...")
        inspection = laghima.inspect_downloaded_papers(test_system)
        print(f"    📊 Inspection results:")
        print(f"       System: {inspection['system']}")
        print(f"       Total papers: {inspection['total_papers']}")
        print(f"       Summary: {inspection['summary']}")
        
        if inspection['papers']:
            print("       Papers found:")
            for paper in inspection['papers']:
                print(f"         - {paper['filename']} ({paper.get('priority', 'UNKNOWN')})")
        
        # Test system aliases
        print("\n5️⃣  Testing system aliases...")
        aliases = laghima._get_system_aliases("Barnards Star")
        print(f"    Barnards Star aliases: {aliases}")
        
        print("\n✅ ALL TESTS PASSED!")
        print(f"📂 Papers stored in: {laghima.download_dir}")
        print("🎉 Paper search and inspection system is working!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_paper_search()
    sys.exit(0 if success else 1)