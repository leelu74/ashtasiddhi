#!/usr/bin/env python3
"""
Prapti.py - Repository Management Agent
Finds and implements code from external repositories like GalSim and GREAT3
"""

import os
import git
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

try:
    import galsim
except ImportError:
    galsim = None

class PraptiAgent:
    """Agent for managing external repositories and simulations"""
    
    def __init__(self, repos_dir: str = "/data/repos"):
        self.logger = logging.getLogger("Prapti")
        self.repos_dir = Path(repos_dir)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        
        # Repository configurations
        self.repositories = {
            'galsim': {
                'url': 'https://github.com/GalSim-developers/GalSim.git',
                'branch': 'releases/2.7',
                'path': self.repos_dir / 'GalSim'
            },
            'great3': {
                'url': 'https://github.com/barnabytprowe/great3-public.git',
                'branch': 'master',
                'path': self.repos_dir / 'great3-public'
            }
        }
        
        # Transit simulation parameters
        self.default_sim_params = {
            'pixel_scale': 0.2,  # arcsec/pixel
            'exposure_time': 30.0,  # seconds
            'gain': 1.0,
            'read_noise': 5.0,
            'sky_level': 1000.0
        }
    
    def setup_repositories(self) -> Dict[str, str]:
        """
        Clone and setup external repositories
        
        Returns:
            Dictionary with setup status for each repository
        """
        self.logger.info("Setting up external repositories...")
        
        results = {}
        
        for repo_name, config in self.repositories.items():
            try:
                repo_path = config['path']
                
                if repo_path.exists():
                    self.logger.info(f"{repo_name} already exists, updating...")
                    repo = git.Repo(repo_path)
                    origin = repo.remotes.origin
                    origin.pull()
                    results[repo_name] = f"Updated at {repo_path}"
                else:
                    self.logger.info(f"Cloning {repo_name}...")
                    git.Repo.clone_from(
                        config['url'], 
                        repo_path,
                        branch=config['branch']
                    )
                    results[repo_name] = f"Cloned to {repo_path}"
                
                # Check if we need to install/build
                if repo_name == 'galsim':
                    self._setup_galsim(repo_path)
                elif repo_name == 'great3':
                    self._setup_great3(repo_path)
                    
            except Exception as e:
                self.logger.error(f"Failed to setup {repo_name}: {e}")
                results[repo_name] = f"Failed: {e}"
        
        return results
    
    def _setup_galsim(self, repo_path: Path):
        """Setup GalSim repository"""
        try:
            # Check if GalSim is already installed
            if galsim is not None:
                self.logger.info("GalSim already installed")
                return
            
            # Try to install via pip first
            try:
                subprocess.run(['pip', 'install', 'galsim'], check=True, capture_output=True)
                self.logger.info("GalSim installed via pip")
                return
            except subprocess.CalledProcessError:
                self.logger.warning("Could not install GalSim via pip")
            
            # Read setup instructions from README
            readme_path = repo_path / "README.md"
            if readme_path.exists():
                with open(readme_path, 'r') as f:
                    readme_content = f.read()
                self.logger.info("Check README.md for manual installation instructions")
                
        except Exception as e:
            self.logger.error(f"GalSim setup failed: {e}")
    
    def _setup_great3(self, repo_path: Path):
        """Setup GREAT3 repository"""
        try:
            # GREAT3 is primarily data/metrics, check for data files
            data_dir = repo_path / "data"
            if data_dir.exists():
                self.logger.info(f"GREAT3 data found at {data_dir}")
            else:
                self.logger.info("GREAT3 repository setup complete")
                
        except Exception as e:
            self.logger.error(f"GREAT3 setup failed: {e}")
    
    def parse_galsim_config(self, config_path: str) -> Dict[str, Any]:
        """
        Parse GalSim YAML configuration file
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Parsed configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Parsed GalSim config from {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to parse config {config_path}: {e}")
            return {}
    
    def run_transit_simulation(self, planet_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run exoplanet transit simulation using GalSim
        
        Args:
            planet_params: Planet parameters (radius_ratio, period, etc.)
            
        Returns:
            Simulation results
        """
        self.logger.info("Running transit simulation...")
        
        if galsim is None:
            return self._run_simple_transit_simulation(planet_params)
        
        try:
            # Extract planet parameters
            radius_ratio = planet_params.get('radius_ratio', 0.1)  # Rp/Rs
            period = planet_params.get('period', 3.0)  # days
            inclination = planet_params.get('inclination', 90.0)  # degrees
            semi_major_axis = planet_params.get('semi_major_axis', 0.03)  # AU
            
            # Simulation parameters
            n_exposures = planet_params.get('n_exposures', 100)
            obs_duration = planet_params.get('obs_duration', 6.0)  # hours
            
            # Create time series
            times = np.linspace(0, obs_duration, n_exposures)  # hours
            
            # Generate transit light curve
            light_curve = self._generate_transit_lightcurve(
                times, radius_ratio, period, inclination, semi_major_axis
            )
            
            # Simulate observations with GalSim
            fluxes = []
            images = []
            
            for i, (time, flux_factor) in enumerate(zip(times, light_curve)):
                # Create star with transit modulation
                star = galsim.Gaussian(flux=1000 * flux_factor, sigma=2.0)
                
                # Add PSF
                psf = galsim.Gaussian(sigma=1.0)
                star_convolved = galsim.Convolve(star, psf)
                
                # Create image
                image = galsim.Image(64, 64, scale=self.default_sim_params['pixel_scale'])
                star_convolved.drawImage(image, add_to_image=False)
                
                # Add noise
                noise = galsim.GaussianNoise(sigma=np.sqrt(self.default_sim_params['read_noise']**2 + 
                                                         self.default_sim_params['sky_level']))
                image.addNoise(noise)
                
                # Measure flux
                measured_flux = np.sum(image.array)
                fluxes.append(measured_flux)
                
                if i < 10:  # Save first 10 images as examples
                    images.append(image.array.tolist())
            
            # Calculate transit depth
            out_of_transit = np.median(fluxes[:20])  # First 20 points
            in_transit = np.min(fluxes)
            transit_depth = (out_of_transit - in_transit) / out_of_transit
            
            results = {
                'times': times.tolist(),
                'fluxes': fluxes,
                'light_curve_model': light_curve.tolist(),
                'transit_depth_measured': transit_depth,
                'transit_depth_expected': radius_ratio**2,
                'planet_params': planet_params,
                'simulation_params': self.default_sim_params,
                'sample_images': images[:5]  # First 5 images
            }
            
            self.logger.info(f"Transit simulation completed. Depth: {transit_depth:.6f}")
            return results
            
        except Exception as e:
            self.logger.error(f"Transit simulation failed: {e}")
            return self._run_simple_transit_simulation(planet_params)
    
    def _generate_transit_lightcurve(self, times: np.ndarray, radius_ratio: float, 
                                   period: float, inclination: float, 
                                   semi_major_axis: float) -> np.ndarray:
        """Generate theoretical transit light curve"""
        # Convert time to phase
        phases = (times / 24.0) % period  # Convert hours to days, then to phase
        
        # Simple transit model (box-shaped for simplicity)
        transit_duration = 0.1  # hours
        transit_phase = transit_duration / 24.0 / period
        
        light_curve = np.ones_like(phases)
        
        # Apply transit
        in_transit = np.abs(phases - period/2) < transit_phase/2
        light_curve[in_transit] = 1 - radius_ratio**2
        
        return light_curve
    
    def _run_simple_transit_simulation(self, planet_params: Dict[str, Any]) -> Dict[str, Any]:
        """Simple transit simulation without GalSim"""
        self.logger.info("Running simple transit simulation (GalSim not available)")
        
        try:
            radius_ratio = planet_params.get('radius_ratio', 0.1)
            period = planet_params.get('period', 3.0)
            n_points = planet_params.get('n_exposures', 100)
            
            # Generate time series
            times = np.linspace(0, 6.0, n_points)  # 6 hours
            
            # Simple box transit
            light_curve = np.ones(n_points)
            transit_start = 2.0  # 2 hours
            transit_duration = 1.0  # 1 hour
            
            in_transit = (times >= transit_start) & (times <= transit_start + transit_duration)
            light_curve[in_transit] = 1 - radius_ratio**2
            
            # Add noise
            noise_level = 0.001
            noisy_curve = light_curve + np.random.normal(0, noise_level, n_points)
            
            return {
                'times': times.tolist(),
                'fluxes': noisy_curve.tolist(),
                'light_curve_model': light_curve.tolist(),
                'transit_depth_measured': radius_ratio**2,
                'transit_depth_expected': radius_ratio**2,
                'planet_params': planet_params,
                'note': 'Simple simulation without GalSim'
            }
            
        except Exception as e:
            self.logger.error(f"Simple simulation failed: {e}")
            return {'error': str(e)}
    
    def validate_with_great3_metrics(self, simulation_results: Dict[str, Any]) -> Dict[str, float]:
        """
        Validate simulation using GREAT3-inspired metrics
        
        Args:
            simulation_results: Results from transit simulation
            
        Returns:
            Validation metrics
        """
        self.logger.info("Validating simulation with GREAT3-inspired metrics")
        
        try:
            times = np.array(simulation_results['times'])
            fluxes = np.array(simulation_results['fluxes'])
            model = np.array(simulation_results['light_curve_model'])
            
            # Calculate metrics
            metrics = {}
            
            # Chi-squared goodness of fit
            residuals = fluxes - np.median(fluxes) * model / np.median(model)
            chi_squared = np.sum(residuals**2)
            metrics['chi_squared'] = chi_squared
            
            # Signal-to-noise ratio
            out_of_transit_std = np.std(fluxes[:20])
            transit_depth = simulation_results.get('transit_depth_measured', 0)
            snr = transit_depth / out_of_transit_std if out_of_transit_std > 0 else 0
            metrics['snr'] = snr
            
            # Photometric precision
            metrics['photometric_precision'] = out_of_transit_std
            
            # Depth accuracy
            expected_depth = simulation_results.get('transit_depth_expected', 0)
            if expected_depth > 0:
                depth_accuracy = 1 - abs(transit_depth - expected_depth) / expected_depth
                metrics['depth_accuracy'] = max(0, depth_accuracy)
            
            self.logger.info(f"Validation metrics: SNR={snr:.1f}, Precision={out_of_transit_std:.6f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {'error': str(e)}
    
    def get_example_configs(self) -> Dict[str, Dict]:
        """Get example configurations for simulations"""
        return {
            'hot_jupiter': {
                'radius_ratio': 0.15,
                'period': 3.5,
                'inclination': 89.0,
                'semi_major_axis': 0.045,
                'n_exposures': 200,
                'obs_duration': 8.0
            },
            'super_earth': {
                'radius_ratio': 0.08,
                'period': 10.0,
                'inclination': 90.0,
                'semi_major_axis': 0.1,
                'n_exposures': 150,
                'obs_duration': 12.0
            },
            'earth_analog': {
                'radius_ratio': 0.05,
                'period': 365.0,
                'inclination': 90.0,
                'semi_major_axis': 1.0,
                'n_exposures': 100,
                'obs_duration': 16.0
            }
        }
    
    def cleanup_repositories(self):
        """Clean up repository directories"""
        try:
            import shutil
            if self.repos_dir.exists():
                shutil.rmtree(self.repos_dir)
                self.logger.info(f"Cleaned up repositories at {self.repos_dir}")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

def main():
    """Test the Prapti agent"""
    import sys
    import json
    
    agent = PraptiAgent()
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        # Setup repositories
        results = agent.setup_repositories()
        print("Repository setup results:")
        print(json.dumps(results, indent=2))
    
    elif len(sys.argv) > 1 and sys.argv[1] == "simulate":
        # Run simulation
        example_configs = agent.get_example_configs()
        planet_params = example_configs['hot_jupiter']
        
        print("Running transit simulation...")
        results = agent.run_transit_simulation(planet_params)
        
        print("Simulation results:")
        print(json.dumps(results, indent=2, default=str))
        
        # Validate
        metrics = agent.validate_with_great3_metrics(results)
        print("Validation metrics:")
        print(json.dumps(metrics, indent=2))
    
    else:
        print("Usage: python Prapti.py [setup|simulate]")

if __name__ == "__main__":
    main()