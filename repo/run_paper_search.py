#!/usr/bin/env python3
"""
run_paper_search.py - Standalone Paper Search Script
Quick start script for downloading and analyzing papers from 9 nearest star systems
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Anima import AnimaAgent

def main():
    """Quick start paper search and inspection"""
    print("🪐 EXOPLANET PAPER SEARCH - 9 Nearest Star Systems")
    print("=" * 60)
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize Anima agent
        print("🚀 Initializing Exoplanet Analysis System...")
        anima = AnimaAgent("./data")
        
        print("\n📊 Available Star Systems:")
        systems = anima.laghima.NEAREST_SYSTEMS
        for i, (system, distance) in enumerate(systems.items(), 1):
            print(f"  {i:2d}. {system:<18} ({distance:5.2f} ly)")
        
        print(f"\n🔍 Will search for MAX 5 papers per system (45 total)")
        
        # Ask user what to do
        while True:
            print("\n" + "="*60)
            print("OPTIONS:")
            print("  1. Download papers for all 9 systems")
            print("  2. Inspect already downloaded papers")
            print("  3. Download + Inspect specific system")
            print("  4. Exit")
            
            try:
                choice = input("\nEnter choice (1-4): ").strip()
                
                if choice == "1":
                    print("\n🔍 DOWNLOADING PAPERS FOR ALL SYSTEMS...")
                    print("-" * 50)
                    total = anima.search_all_nearest_papers()
                    print(f"\n✅ DOWNLOAD COMPLETE: {total} papers downloaded")
                    
                elif choice == "2":
                    print("\n📊 INSPECTING ALL DOWNLOADED PAPERS...")
                    print("-" * 50)
                    anima.inspect_all_systems()
                    print(f"\n✅ INSPECTION COMPLETE")
                    
                elif choice == "3":
                    print("\n📋 Available systems:")
                    for i, system in enumerate(systems.keys(), 1):
                        print(f"  {i}. {system}")
                    
                    try:
                        sys_choice = int(input(f"\nSelect system (1-{len(systems)}): ")) - 1
                        system_list = list(systems.keys())
                        
                        if 0 <= sys_choice < len(system_list):
                            selected_system = system_list[sys_choice]
                            
                            print(f"\n🔍 Downloading papers for {selected_system}...")
                            papers = anima.laghima.search_system_papers(selected_system, 5)
                            print(f"✅ Downloaded {len(papers)} papers")
                            
                            print(f"\n📊 Inspecting {selected_system}...")
                            anima.inspect_single_system(selected_system)
                            
                        else:
                            print("❌ Invalid selection")
                            
                    except ValueError:
                        print("❌ Please enter a valid number")
                    
                elif choice == "4":
                    print("👋 Exiting...")
                    break
                    
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Exiting...")
                break
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())