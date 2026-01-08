#!/usr/bin/env python3
"""
Garima.py - Analysis Agent
Gives required output/operations for exoplanet analysis including RV, transit, and HZ calculations
"""

import re
import math
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import PyPDF2

class GarimaAgent:
    """Agent for exoplanet analysis and metric computation"""
    
    def __init__(self):
        self.logger = logging.getLogger("Garima")
        
        # Physical constants
        self.G = 6.67430e-11  # m^3 kg^-1 s^-2
        self.M_sun = 1.989e30  # kg
        self.R_sun = 6.96e8   # m
        self.AU = 1.496e11    # m
        self.L_sun = 3.828e26 # W
        self.S_earth = 1361   # W/m^2 (Solar constant at Earth)
        
        # Chemical species patterns for NER
        self.chemical_patterns = {
            'h2o': [r'\bh2o\b', r'\bwater\b', r'h₂o'],
            'h2s': [r'\bh2s\b', r'hydrogen\s+sulfide', r'h₂s'],
            'so2': [r'\bso2\b', r'sulfur\s+dioxide', r'so₂'],
            'h2': [r'\bh2\b(?!\w)', r'\bhydrogen\b(?!\s+sulfide)', r'h₂(?!\w)'],
            'he': [r'\bhe\b(?!\w)', r'\bhelium\b', r'⁴he'],
            'ch4': [r'\bch4\b', r'\bmethane\b', r'ch₄'],
            'co2': [r'\bco2\b', r'carbon\s+dioxide', r'co₂'],
            'co': [r'\bco\b(?!\w)', r'carbon\s+monoxide'],
            'nh3': [r'\bnh3\b', r'\bammonia\b', r'nh₃'],
            'n2': [r'\bn2\b(?!\w)', r'\bnitrogen\b', r'n₂'],
            'sulfur': [r'\bsulfur\b', r'\bs\b(?=\s+species)', r'\bsulphur\b']
        }
        
        # Radial velocity extraction patterns
        self.rv_patterns = {
            'k_velocity': [
                r'k\s*=?\s*([0-9\.]+)\s*(m/s|ms⁻¹|m\s*s⁻¹)',
                r'radial\s+velocity\s+amplitude\s*=?\s*([0-9\.]+)\s*(m/s|ms⁻¹)',
                r'rv\s+amplitude\s*=?\s*([0-9\.]+)\s*(m/s|ms⁻¹)'
            ],
            'period': [
                r'period\s*=?\s*([0-9\.]+)\s*(days?|d\b)',
                r'orbital\s+period\s*=?\s*([0-9\.]+)\s*(days?|d\b)',
                r'p\s*=?\s*([0-9\.]+)\s*(days?|d\b)'
            ],
            'eccentricity': [
                r'eccentricity\s*=?\s*([0-9\.]+)',
                r'e\s*=?\s*([0-9\.]+)'
            ]
        }
        
        # Transit patterns
        self.transit_patterns = {
            'depth': [
                r'transit\s+depth\s*=?\s*([0-9\.e\-\+]+)\s*(%|ppm|mmag)',
                r'depth\s*=?\s*([0-9\.e\-\+]+)\s*(%|ppm|mmag)',
                r'δ\s*=?\s*([0-9\.e\-\+]+)\s*(%|ppm|mmag)'
            ],
            'radius_ratio': [
                r'r[_p]?/r[_\*]?\s*=?\s*([0-9\.]+)',
                r'planet\s+radius\s+ratio\s*=?\s*([0-9\.]+)',
                r'rp/rs?\s*=?\s*([0-9\.]+)'
            ],
            'planet_radius': [
                r'planet\s+radius\s*=?\s*([0-9\.]+)\s*(r_earth|earth\s+radii|r_⊕)',
                r'r[_p]?\s*=?\s*([0-9\.]+)\s*(r_earth|earth\s+radii|r_⊕)'
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.lower()  # Convert to lowercase for pattern matching
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Complete exoplanet analysis of PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Comprehensive analysis results
        """
        self.logger.info(f"Analyzing exoplanet characteristics in {pdf_path}")
        
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {"error": "Could not extract text from PDF"}
        
        results = {
            'pdf_path': pdf_path,
            'chemical_composition': self._analyze_chemical_composition(text),
            'radial_velocity': self._analyze_radial_velocity(text),
            'transit_analysis': self._analyze_transit_method(text),
            'habitable_zone': self._analyze_habitable_zone(text),
            'planetary_properties': self._extract_planetary_properties(text),
            'stellar_properties': self._extract_stellar_properties(text),
            'detection_confidence': self._assess_detection_confidence(text)
        }
        
        # Add computed metrics
        results['computed_metrics'] = self._compute_derived_metrics(results)
        
        self.logger.info("Analysis completed")
        return results
    
    def _analyze_chemical_composition(self, text: str) -> Dict[str, Any]:
        """Analyze atmospheric chemical composition"""
        composition = {
            'detected_species': [],
            'abundances': {},
            'unique_materials': []
        }
        
        # Detect chemical species
        for species, patterns in self.chemical_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    composition['detected_species'].append(species)
                    break
        
        # Extract abundances with values
        abundance_patterns = [
            r'(h2o|water)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(h2s|hydrogen\s+sulfide)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(so2|sulfur\s+dioxide)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(ch4|methane)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(co2|carbon\s+dioxide)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(h2|hydrogen)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(he|helium)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)'
        ]
        
        for pattern in abundance_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                species = match.group(1).lower()
                value = float(match.group(2))
                unit = match.group(3)
                composition['abundances'][species] = {'value': value, 'unit': unit}
        
        # Look for unique/unusual materials
        unique_patterns = [
            r'(tio2|titanium\s+oxide)',
            r'(vo|vanadium\s+oxide)',
            r'(na|sodium)',
            r'(k|potassium)',
            r'(mg|magnesium)',
            r'(fe|iron)',
            r'(al|aluminum|aluminium)',
            r'(si|silicon)',
            r'(clouds?|hazes?)',
            r'(aerosols?)'
        ]
        
        for pattern in unique_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                composition['unique_materials'].append(match.group(1))
        
        return composition
    
    def _analyze_radial_velocity(self, text: str) -> Dict[str, Any]:
        """Analyze radial velocity data and compute masses"""
        rv_data = {
            'k_velocity': None,
            'period': None,
            'eccentricity': 0.0,
            'mass_function': None,
            'minimum_mass': None,
            'detection_method': 'radial_velocity' if 'radial velocity' in text else None
        }
        
        # Extract K velocity
        for pattern in self.rv_patterns['k_velocity']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rv_data['k_velocity'] = float(match.group(1))
                break
        
        # Extract period
        for pattern in self.rv_patterns['period']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rv_data['period'] = float(match.group(1))
                break
        
        # Extract eccentricity
        for pattern in self.rv_patterns['eccentricity']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rv_data['eccentricity'] = float(match.group(1))
                break
        
        # Compute mass function if we have K and P
        if rv_data['k_velocity'] and rv_data['period']:
            rv_data['mass_function'] = self._compute_mass_function(
                rv_data['k_velocity'], rv_data['period'], rv_data['eccentricity']
            )
            
            # Estimate minimum mass (assuming M_star = 1 M_sun, sin(i) = 1)
            stellar_mass = 1.0  # Solar masses
            rv_data['minimum_mass'] = self._compute_minimum_mass(
                rv_data['mass_function'], stellar_mass
            )
        
        return rv_data
    
    def _analyze_transit_method(self, text: str) -> Dict[str, Any]:
        """Analyze transit photometry data"""
        transit_data = {
            'depth': None,
            'radius_ratio': None,
            'planet_radius': None,
            'period': None,
            'duration': None,
            'detection_method': 'transit' if 'transit' in text else None
        }
        
        # Extract transit depth
        for pattern in self.transit_patterns['depth']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                depth_value = float(match.group(1))
                unit = match.group(2)
                
                # Convert to fraction
                if unit == '%':
                    transit_data['depth'] = depth_value / 100.0
                elif unit == 'ppm':
                    transit_data['depth'] = depth_value / 1e6
                elif unit == 'mmag':
                    # Convert magnitude to flux ratio
                    transit_data['depth'] = 1 - 10**(-depth_value/2500.0)
                break
        
        # Extract radius ratio
        for pattern in self.transit_patterns['radius_ratio']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                transit_data['radius_ratio'] = float(match.group(1))
                # Compute depth from radius ratio
                if not transit_data['depth']:
                    transit_data['depth'] = transit_data['radius_ratio']**2
                break
        
        # Extract planet radius
        for pattern in self.transit_patterns['planet_radius']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                transit_data['planet_radius'] = float(match.group(1))
                break
        
        # If we have depth but not radius ratio, compute it
        if transit_data['depth'] and not transit_data['radius_ratio']:
            transit_data['radius_ratio'] = math.sqrt(transit_data['depth'])
        
        return transit_data
    
    def _analyze_habitable_zone(self, text: str) -> Dict[str, Any]:
        """Analyze habitable zone characteristics"""
        hz_data = {
            'in_habitable_zone': False,
            'insolation': None,
            'effective_temperature': None,
            'semi_major_axis': None,
            'stellar_luminosity': None,
            'hz_inner_edge': None,
            'hz_outer_edge': None
        }
        
        # Look for explicit HZ mentions
        hz_keywords = [
            r'habitable\s+zone', r'goldilocks\s+zone', r'\bhz\b',
            r'potentially\s+habitable', r'in\s+the\s+hz'
        ]
        
        for keyword in hz_keywords:
            if re.search(keyword, text, re.IGNORECASE):
                hz_data['in_habitable_zone'] = True
                break
        
        # Extract insolation/stellar flux
        flux_patterns = [
            r'insolation\s*=?\s*([0-9\.]+)\s*(s_earth|earth)',
            r'stellar\s+flux\s*=?\s*([0-9\.]+)\s*(s_earth|earth)',
            r'incident\s+flux\s*=?\s*([0-9\.]+)\s*(s_earth|earth)'
        ]
        
        for pattern in flux_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hz_data['insolation'] = float(match.group(1))
                break
        
        # Extract effective temperature
        temp_patterns = [
            r'effective\s+temperature\s*=?\s*([0-9\.]+)\s*k',
            r't_eff\s*=?\s*([0-9\.]+)\s*k',
            r'equilibrium\s+temperature\s*=?\s*([0-9\.]+)\s*k'
        ]
        
        for pattern in temp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hz_data['effective_temperature'] = float(match.group(1))
                break
        
        # Extract semi-major axis
        axis_patterns = [
            r'semi[- ]?major\s+axis\s*=?\s*([0-9\.]+)\s*(au|a\.u\.)',
            r'orbital\s+distance\s*=?\s*([0-9\.]+)\s*(au|a\.u\.)',
            r'a\s*=?\s*([0-9\.]+)\s*(au|a\.u\.)'
        ]
        
        for pattern in axis_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                hz_data['semi_major_axis'] = float(match.group(1))
                break
        
        # Compute HZ status if we have the data
        if hz_data['semi_major_axis'] and hz_data['stellar_luminosity']:
            hz_data = self._compute_habitable_zone_status(hz_data)
        elif hz_data['insolation']:
            # Direct insolation measurement
            if 0.2 <= hz_data['insolation'] <= 1.1:
                hz_data['in_habitable_zone'] = True
        
        return hz_data
    
    def _extract_planetary_properties(self, text: str) -> Dict[str, Any]:
        """Extract general planetary properties"""
        properties = {}
        
        # Mass patterns
        mass_patterns = [
            r'mass\s*=?\s*([0-9\.]+)\s*(m_earth|earth\s+masses|m_⊕)',
            r'm[_p]?\s*=?\s*([0-9\.]+)\s*(m_earth|earth\s+masses|m_⊕)',
            r'planet\s+mass\s*=?\s*([0-9\.]+)\s*(m_earth|earth\s+masses|m_⊕)'
        ]
        
        for pattern in mass_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                properties['mass_earth'] = float(match.group(1))
                break
        
        # Radius patterns (already partially handled in transit analysis)
        radius_patterns = [
            r'radius\s*=?\s*([0-9\.]+)\s*(r_earth|earth\s+radii|r_⊕)',
            r'r[_p]?\s*=?\s*([0-9\.]+)\s*(r_earth|earth\s+radii|r_⊕)'
        ]
        
        for pattern in radius_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                properties['radius_earth'] = float(match.group(1))
                break
        
        # Density (if mass and radius available)
        if 'mass_earth' in properties and 'radius_earth' in properties:
            properties['density'] = self._compute_planet_density(
                properties['mass_earth'], properties['radius_earth']
            )
        
        return properties
    
    def _extract_stellar_properties(self, text: str) -> Dict[str, Any]:
        """Extract stellar host properties"""
        stellar = {}
        
        # Stellar mass
        stellar_mass_patterns = [
            r'stellar\s+mass\s*=?\s*([0-9\.]+)\s*(m_sun|solar\s+masses|m_☉)',
            r'm[_\*]?\s*=?\s*([0-9\.]+)\s*(m_sun|solar\s+masses|m_☉)'
        ]
        
        for pattern in stellar_mass_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                stellar['mass_solar'] = float(match.group(1))
                break
        
        # Stellar radius
        stellar_radius_patterns = [
            r'stellar\s+radius\s*=?\s*([0-9\.]+)\s*(r_sun|solar\s+radii|r_☉)',
            r'r[_\*]?\s*=?\s*([0-9\.]+)\s*(r_sun|solar\s+radii|r_☉)'
        ]
        
        for pattern in stellar_radius_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                stellar['radius_solar'] = float(match.group(1))
                break
        
        # Stellar temperature
        temp_patterns = [
            r'stellar\s+temperature\s*=?\s*([0-9\.]+)\s*k',
            r't[_\*]?\s*=?\s*([0-9\.]+)\s*k'
        ]
        
        for pattern in temp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                stellar['temperature'] = float(match.group(1))
                break
        
        return stellar
    
    def _assess_detection_confidence(self, text: str) -> Dict[str, Any]:
        """Assess confidence in exoplanet detection"""
        confidence = {
            'detection_significance': None,
            'false_alarm_probability': None,
            'confirmation_status': None,
            'methods_used': []
        }
        
        # Look for significance measures
        significance_patterns = [
            r'([0-9\.]+)\s*σ\s+detection',
            r'significance\s*=?\s*([0-9\.]+)\s*σ',
            r'([0-9\.]+)\s*sigma'
        ]
        
        for pattern in significance_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                confidence['detection_significance'] = float(match.group(1))
                break
        
        # Look for confirmation status
        if re.search(r'confirmed\s+planet', text, re.IGNORECASE):
            confidence['confirmation_status'] = 'confirmed'
        elif re.search(r'planet\s+candidate', text, re.IGNORECASE):
            confidence['confirmation_status'] = 'candidate'
        
        # Identify detection methods
        methods = []
        if 'transit' in text:
            methods.append('transit')
        if 'radial velocity' in text or 'rv' in text:
            methods.append('radial_velocity')
        if 'direct imaging' in text:
            methods.append('direct_imaging')
        
        confidence['methods_used'] = methods
        
        return confidence
    
    def _compute_mass_function(self, k_velocity: float, period: float, 
                             eccentricity: float = 0.0) -> float:
        """
        Compute mass function from radial velocity parameters
        M sin i = (P/2πG)^(1/3) * K * (1-e^2)^(1/2)
        """
        try:
            P_seconds = period * 24 * 3600  # Convert days to seconds
            K_ms = k_velocity  # m/s
            
            # Mass function formula
            mass_function = (P_seconds / (2 * math.pi * self.G))**(1/3) * K_ms * (1 - eccentricity**2)**0.5
            
            return mass_function / self.M_sun  # Return in solar masses
        except:
            return None
    
    def _compute_minimum_mass(self, mass_function: float, stellar_mass: float) -> float:
        """Compute minimum planet mass assuming sin(i) = 1"""
        try:
            # Simplified: M_p sin(i) ≈ mass_function for M_star >> M_planet
            return mass_function * (self.M_sun / 5.972e24)  # Convert to Earth masses
        except:
            return None
    
    def _compute_planet_density(self, mass_earth: float, radius_earth: float) -> float:
        """Compute planet bulk density"""
        try:
            # Earth values
            M_earth = 5.972e24  # kg
            R_earth = 6.371e6   # m
            
            planet_mass = mass_earth * M_earth
            planet_radius = radius_earth * R_earth
            
            volume = (4/3) * math.pi * planet_radius**3
            density = planet_mass / volume  # kg/m^3
            
            return density / 1000  # Convert to g/cm^3
        except:
            return None
    
    def _compute_habitable_zone_status(self, hz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute habitable zone status from orbital parameters"""
        try:
            a = hz_data['semi_major_axis']  # AU
            L_star = hz_data.get('stellar_luminosity', 1.0)  # Solar luminosities
            
            # Insolation = L_star / (4π a^2) in units of Earth's insolation
            insolation = L_star / a**2
            hz_data['insolation'] = insolation
            
            # Habitable zone boundaries (conservative)
            hz_inner = 0.95 * math.sqrt(L_star)  # AU
            hz_outer = 1.37 * math.sqrt(L_star)  # AU
            
            hz_data['hz_inner_edge'] = hz_inner
            hz_data['hz_outer_edge'] = hz_outer
            
            # Check if planet is in HZ
            if hz_inner <= a <= hz_outer:
                hz_data['in_habitable_zone'] = True
            
            return hz_data
        except:
            return hz_data
    
    def _compute_derived_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compute additional derived metrics from analysis"""
        metrics = {}
        
        # Atmospheric detectability score
        composition = analysis_results.get('chemical_composition', {})
        detected_species = composition.get('detected_species', [])
        metrics['atmospheric_detectability'] = len(detected_species) / 10.0  # Normalized
        
        # Multi-method confirmation score
        confidence = analysis_results.get('detection_confidence', {})
        methods = confidence.get('methods_used', [])
        metrics['confirmation_score'] = len(methods) / 3.0  # Normalized
        
        # Habitability index
        hz_data = analysis_results.get('habitable_zone', {})
        habitability_factors = []
        
        if hz_data.get('in_habitable_zone', False):
            habitability_factors.append(1.0)
        
        if 'h2o' in detected_species:
            habitability_factors.append(0.8)
        
        planetary = analysis_results.get('planetary_properties', {})
        if 'radius_earth' in planetary:
            radius = planetary['radius_earth']
            if 0.5 <= radius <= 2.0:  # Earth-like size
                habitability_factors.append(0.6)
        
        metrics['habitability_index'] = sum(habitability_factors) / 3.0 if habitability_factors else 0.0
        
        return metrics
    
    def generate_summary_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable summary report"""
        report_lines = []
        
        report_lines.append("=== EXOPLANET ANALYSIS REPORT ===")
        report_lines.append(f"PDF: {analysis_results.get('pdf_path', 'Unknown')}")
        report_lines.append("")
        
        # Chemical composition
        composition = analysis_results.get('chemical_composition', {})
        if composition.get('detected_species'):
            report_lines.append("ATMOSPHERIC COMPOSITION:")
            for species in composition['detected_species']:
                abundance = composition.get('abundances', {}).get(species, {})
                if abundance:
                    report_lines.append(f"  - {species.upper()}: {abundance['value']} {abundance['unit']}")
                else:
                    report_lines.append(f"  - {species.upper()}: detected")
        
        # Radial velocity results
        rv_data = analysis_results.get('radial_velocity', {})
        if rv_data.get('k_velocity'):
            report_lines.append("")
            report_lines.append("RADIAL VELOCITY ANALYSIS:")
            report_lines.append(f"  - K velocity: {rv_data['k_velocity']:.2f} m/s")
            if rv_data.get('minimum_mass'):
                report_lines.append(f"  - Minimum mass: {rv_data['minimum_mass']:.2f} Earth masses")
        
        # Transit analysis
        transit = analysis_results.get('transit_analysis', {})
        if transit.get('depth'):
            report_lines.append("")
            report_lines.append("TRANSIT ANALYSIS:")
            report_lines.append(f"  - Transit depth: {transit['depth']:.6f}")
            if transit.get('radius_ratio'):
                report_lines.append(f"  - Radius ratio (Rp/Rs): {transit['radius_ratio']:.3f}")
        
        # Habitable zone
        hz_data = analysis_results.get('habitable_zone', {})
        report_lines.append("")
        report_lines.append("HABITABILITY ASSESSMENT:")
        report_lines.append(f"  - In habitable zone: {hz_data.get('in_habitable_zone', False)}")
        if hz_data.get('insolation'):
            report_lines.append(f"  - Insolation: {hz_data['insolation']:.2f} S_Earth")
        
        # Summary metrics
        metrics = analysis_results.get('computed_metrics', {})
        if metrics:
            report_lines.append("")
            report_lines.append("SUMMARY METRICS:")
            for key, value in metrics.items():
                report_lines.append(f"  - {key.replace('_', ' ').title()}: {value:.2f}")
        
        return "\n".join(report_lines)

def main():
    """Test the Garima agent"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python Garima.py <pdf_path>")
        sys.exit(1)
    
    agent = GarimaAgent()
    results = agent.analyze_pdf(sys.argv[1])
    
    print(json.dumps(results, indent=2, default=str))
    
    print("\n" + "="*50)
    print(agent.generate_summary_report(results))

if __name__ == "__main__":
    main()