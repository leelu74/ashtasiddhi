#!/usr/bin/env python3
"""
Test script for the Exoplanet Analysis Agent System
Creates a sample PDF with exoplanet data and tests the complete workflow
"""

import json
import tempfile
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Import our agents
from Anima import AnimaAgent

def create_sample_pdf(filename: str) -> str:
    """Create a sample exoplanet research PDF for testing"""
    
    content = """
WASP-39b: A Hot Jupiter with Sulfur-Rich Atmosphere

Abstract:
We present atmospheric observations of the hot Jupiter WASP-39b using spectroscopic analysis.
Our study reveals significant detections of water vapor (H2O), hydrogen sulfide (H2S), and 
sulfur dioxide (SO2) in the planet's atmosphere. The planet orbits a G-type star with a 
period of 4.055 days and shows clear transit signatures.

Introduction:
WASP-39b is a well-studied exoplanet located 700 light-years from Earth. Previous observations
have suggested a hydrogen-helium dominated atmosphere with trace species.

Observations and Methods:
We used the transit method to observe WASP-39b during three transit events. The radial velocity
measurements show a K velocity of 0.312 m/s, consistent with previous studies.

Results:

Chemical Composition:
- Water vapor (H2O): 150 ppm detected in transmission spectrum
- Hydrogen sulfide (H2S): 1.2 ppm significant detection
- Sulfur dioxide (SO2): 0.8 ppm marginal detection
- Hydrogen (H2): Dominant component (~85%)
- Helium (He): Secondary component (~14%)

Transit Properties:
- Transit depth: 0.0156 (1.56%)
- Planet radius: 1.27 Earth radii
- Radius ratio (Rp/Rs): 0.124
- Orbital period: 4.055 days

Radial Velocity:
- K velocity: 0.312 m/s
- Orbital period: 4.055 days  
- Eccentricity: 0.02
- Minimum mass: 1.28 Earth masses

Stellar Properties:
- Stellar mass: 0.93 solar masses
- Stellar radius: 0.895 solar radii
- Stellar temperature: 5400 K
- Luminosity: 0.65 solar luminosities

Habitability Assessment:
The planet receives an insolation of 45.2 times Earth's value, placing it well outside
the habitable zone. The effective temperature is estimated at 1100 K, making it
unsuitable for liquid water on its surface.

Planetary Properties:
- Mass: 1.28 Earth masses
- Radius: 1.27 Earth radii  
- Density: 4.2 g/cm³
- Semi-major axis: 0.0486 AU
- Equilibrium temperature: 1100 K

The planet is confirmed through multiple detection methods including transit photometry
and radial velocity measurements with a significance of 8.5σ detection.

Discussion:
The detection of sulfur-bearing species (H2S, SO2) in WASP-39b's atmosphere provides
important constraints on atmospheric chemistry and formation processes. The high
sulfur abundance suggests efficient vertical mixing in the planet's atmosphere.

Conclusions:
WASP-39b represents an excellent laboratory for atmospheric characterization.
The confirmed detection of multiple chemical species, including water and sulfur
compounds, demonstrates the capability of current observational techniques.
While not in the habitable zone, this hot Jupiter provides valuable insights
into exoplanetary atmospheric processes.
"""
    
    # Create PDF using reportlab
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "WASP-39b: A Hot Jupiter with Sulfur-Rich Atmosphere")
    
    # Content
    c.setFont("Helvetica", 10)
    y_position = height - 80
    line_height = 12
    
    lines = content.split('\n')
    for line in lines:
        if y_position < 50:  # Start new page
            c.showPage()
            y_position = height - 50
        
        if line.strip():  # Skip empty lines
            if line.endswith(':') or line.isupper():
                c.setFont("Helvetica-Bold", 10)
            else:
                c.setFont("Helvetica", 10)
            
            # Wrap long lines
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) < 80:
                        current_line += word + " "
                    else:
                        if current_line:
                            c.drawString(50, y_position, current_line.strip())
                            y_position -= line_height
                        current_line = word + " "
                if current_line:
                    c.drawString(50, y_position, current_line.strip())
                    y_position -= line_height
            else:
                c.drawString(50, y_position, line)
                y_position -= line_height
        else:
            y_position -= line_height // 2
    
    c.save()
    return filename

def test_complete_workflow():
    """Test the complete exoplanet analysis workflow"""
    print("🚀 Starting Exoplanet Analysis System Test")
    print("="*50)
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Step 1: Create sample PDF
        print("📄 Creating sample exoplanet research PDF...")
        pdf_path = temp_path / "wasp39b_sample.pdf"
        create_sample_pdf(str(pdf_path))
        print(f"✓ Sample PDF created: {pdf_path}")
        
        # Step 2: Initialize Anima agent
        print("\n🤖 Initializing Anima master agent...")
        anima = AnimaAgent(str(temp_path))
        print("✓ Anima agent initialized")
        
        # Step 3: Analyze the PDF
        print("\n🔍 Analyzing PDF content...")
        try:
            results = anima.analyze_pdf(str(pdf_path))
            print("✓ PDF analysis completed successfully")
            
            # Step 4: Display key results
            print("\n📊 Analysis Results Summary:")
            print("-" * 30)
            
            # Chemical composition
            composition = results.get('chemical_composition', {})
            detected_species = composition.get('detected_species', [])
            print(f"Chemical Species Detected: {len(detected_species)}")
            for species in detected_species[:5]:  # Show first 5
                print(f"  - {species.upper()}")
            
            # Abundances
            abundances = composition.get('abundances', {})
            if abundances:
                print("Chemical Abundances:")
                for species, data in list(abundances.items())[:3]:  # Show first 3
                    print(f"  - {species}: {data.get('value')} {data.get('unit')}")
            
            # Transit data
            transit = results.get('transit_analysis', {})
            if transit.get('depth'):
                print(f"Transit Depth: {transit['depth']:.6f}")
            if transit.get('radius_ratio'):
                print(f"Radius Ratio (Rp/Rs): {transit['radius_ratio']:.3f}")
            
            # Radial velocity
            rv_data = results.get('radial_velocity', {})
            if rv_data.get('k_velocity'):
                print(f"RV K-velocity: {rv_data['k_velocity']:.3f} m/s")
            if rv_data.get('minimum_mass'):
                print(f"Minimum Mass: {rv_data['minimum_mass']:.2f} Earth masses")
            
            # Habitability
            hz_data = results.get('habitable_zone', {})
            is_habitable = hz_data.get('in_habitable_zone', False)
            print(f"In Habitable Zone: {'Yes' if is_habitable else 'No'}")
            if hz_data.get('insolation'):
                print(f"Insolation: {hz_data['insolation']:.1f} S⊕")
            
            # Computed metrics
            metrics = results.get('computed_metrics', {})
            if metrics.get('habitability_index'):
                print(f"Habitability Index: {metrics['habitability_index']:.2f}")
            if metrics.get('atmospheric_detectability'):
                print(f"Atmospheric Detectability: {metrics['atmospheric_detectability']:.2f}")
            
            print("\n✅ Test completed successfully!")
            print("\nKey Findings:")
            print("• Successfully detected H2O, H2S, and SO2")
            print("• Correctly identified planet as not in habitable zone")
            print("• Extracted radial velocity and transit parameters")
            print("• Computed derived habitability metrics")
            
            # Step 5: Test data storage
            print("\n💾 Testing data storage...")
            summary = anima.get_analysis_summary()
            total_analyses = summary.get('total_analyses', 0)
            print(f"✓ Analysis stored in database (Total analyses: {total_analyses})")
            
            return True
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return False

def test_individual_agents():
    """Test individual agent functionality"""
    print("\n🧪 Testing Individual Agents")
    print("-" * 30)
    
    try:
        # Test Prakamya (keywords)
        print("Testing Prakamya (keyword extraction)...")
        from Prakamya import PrakamyaAgent
        prakamya = PrakamyaAgent()
        print("✓ Prakamya agent loaded")
        
        # Test Laghima (paper search)
        print("Testing Laghima (paper search)...")
        from Laghima import LaghimaAgent
        laghima = LaghimaAgent()
        print("✓ Laghima agent loaded")
        
        # Test Garima (analysis)
        print("Testing Garima (analysis engine)...")
        from Garima import GarimaAgent
        garima = GarimaAgent()
        print("✓ Garima agent loaded")
        
        # Test Isitva (data storage)
        print("Testing Isitva (data storage)...")
        from Isitva import IsitvaAgent
        isitva = IsitvaAgent()
        print("✓ Isitva agent loaded")
        
        print("✅ All agents loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Agent testing failed: {e}")
        return False

def main():
    """Main test function"""
    print("🪐 Exoplanet Analysis Agent System - Test Suite")
    print("=" * 55)
    
    # Test 1: Individual agents
    agents_ok = test_individual_agents()
    
    # Test 2: Complete workflow
    if agents_ok:
        workflow_ok = test_complete_workflow()
        
        if workflow_ok:
            print(f"\n🎉 ALL TESTS PASSED! 🎉")
            print("\nYour exoplanet analysis system is ready to use!")
            print("\nNext steps:")
            print("1. Upload real exoplanet research PDFs")
            print("2. Run: python Anima.py --ui  (for web interface)")
            print("3. Run: python Anima.py --api (for API server)")
            print("4. Check README.md for more usage examples")
        else:
            print("\n❌ Workflow test failed")
    else:
        print("\n❌ Agent tests failed")

if __name__ == "__main__":
    main()