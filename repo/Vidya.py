#!/usr/bin/env python3
"""
Vidya.py - FITS File Processing Agent
Vidya = Knowledge/Wisdom in Sanskrit
Handles astronomical FITS files, spectroscopic data, and header metadata extraction
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import numpy as np

# FITS handling
try:
    from astropy.io import fits
    from astropy.table import Table
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False
    logging.warning("astropy not available - FITS processing will be limited")

# Spectroscopy tools
try:
    from specutils import Spectrum1D
    from specutils.manipulation import extract_region
    from specutils.analysis import line_flux, equivalent_width
    import astropy.units as u
    SPECUTILS_AVAILABLE = True
except ImportError:
    SPECUTILS_AVAILABLE = False
    logging.warning("specutils not available - advanced spectral analysis disabled")


class VidyaAgent:
    """Agent for FITS file processing and spectroscopic analysis"""

    def __init__(self, data_dir: str = "./data"):
        self.logger = logging.getLogger("Vidya")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not ASTROPY_AVAILABLE:
            self.logger.error("astropy is required for FITS processing. Install with: pip install astropy>=5.3.0")

        self.logger.info("Vidya agent initialized")

    def read_fits(self, fits_path: str) -> Optional[Dict[str, Any]]:
        """
        Read FITS file and extract basic information

        Args:
            fits_path: Path to FITS file

        Returns:
            Dictionary containing FITS data structure
        """
        if not ASTROPY_AVAILABLE:
            self.logger.error("astropy not available")
            return None

        try:
            fits_path = Path(fits_path)
            if not fits_path.exists():
                self.logger.error(f"FITS file not found: {fits_path}")
                return None

            with fits.open(fits_path) as hdul:
                result = {
                    'file_path': str(fits_path),
                    'num_extensions': len(hdul),
                    'extensions': []
                }

                for i, hdu in enumerate(hdul):
                    ext_info = {
                        'index': i,
                        'name': hdu.name,
                        'type': type(hdu).__name__,
                        'header_cards': len(hdu.header),
                        'has_data': hdu.data is not None
                    }

                    if hdu.data is not None:
                        ext_info['data_shape'] = hdu.data.shape
                        ext_info['data_dtype'] = str(hdu.data.dtype)

                    result['extensions'].append(ext_info)

                self.logger.info(f"Read FITS file with {len(hdul)} extensions")
                return result

        except Exception as e:
            self.logger.error(f"Failed to read FITS file: {e}")
            return None

    def extract_metadata(self, fits_path: str, extension: int = 0) -> Optional[Dict[str, Any]]:
        """
        Extract header metadata from FITS file

        Args:
            fits_path: Path to FITS file
            extension: FITS extension number (default: 0 for primary)

        Returns:
            Dictionary of header metadata
        """
        if not ASTROPY_AVAILABLE:
            return None

        try:
            with fits.open(fits_path) as hdul:
                header = hdul[extension].header

                metadata = {}
                for key in header.keys():
                    try:
                        value = header[key]
                        # Convert to serializable types
                        if isinstance(value, (int, float, str, bool)):
                            metadata[key] = value
                        else:
                            metadata[key] = str(value)
                    except Exception:
                        continue

                # Extract common astronomical metadata
                result = {
                    'raw_header': metadata,
                    'telescope': metadata.get('TELESCOP', metadata.get('TELESCOPE', 'Unknown')),
                    'instrument': metadata.get('INSTRUME', metadata.get('INSTRUMENT', 'Unknown')),
                    'obs_date': metadata.get('DATE-OBS', metadata.get('DATE', 'Unknown')),
                    'exposure_time': metadata.get('EXPTIME', metadata.get('EXPOSURE', None)),
                    'object_name': metadata.get('OBJECT', metadata.get('TARGNAME', 'Unknown')),
                    'ra': metadata.get('RA_TARG', metadata.get('RA', None)),
                    'dec': metadata.get('DEC_TARG', metadata.get('DEC', None))
                }

                self.logger.info(f"Extracted metadata from {fits_path}")
                return result

        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return None

    def extract_spectrum(self, fits_path: str, extension: int = 1) -> Optional[Dict[str, Any]]:
        """
        Extract spectroscopic data from FITS file

        Args:
            fits_path: Path to FITS file
            extension: Extension containing spectrum (default: 1)

        Returns:
            Dictionary with wavelength and flux arrays
        """
        if not ASTROPY_AVAILABLE:
            return None

        try:
            with fits.open(fits_path) as hdul:
                if extension >= len(hdul):
                    self.logger.error(f"Extension {extension} does not exist")
                    return None

                hdu = hdul[extension]

                # Try to extract spectrum from different formats
                spectrum_data = {}

                # Case 1: Binary table with WAVELENGTH and FLUX columns
                if isinstance(hdu.data, np.ndarray) and hdu.data.dtype.names:
                    # Look for wavelength column
                    wave_col = None
                    for col in ['WAVELENGTH', 'WAVE', 'LAMBDA', 'WAVELENGTH_AIR']:
                        if col in hdu.data.dtype.names:
                            wave_col = col
                            break

                    # Look for flux column
                    flux_col = None
                    for col in ['FLUX', 'FLAMBDA', 'INTENSITY', 'COUNTS']:
                        if col in hdu.data.dtype.names:
                            flux_col = col
                            break

                    if wave_col and flux_col:
                        spectrum_data['wavelength'] = hdu.data[wave_col].tolist()
                        spectrum_data['flux'] = hdu.data[flux_col].tolist()

                        # Look for error column
                        for col in ['ERROR', 'ERR', 'SIGMA', 'UNCERTAINTY']:
                            if col in hdu.data.dtype.names:
                                spectrum_data['error'] = hdu.data[col].tolist()
                                break

                # Case 2: Image data (wavelength from CRVAL1/CDELT1)
                elif isinstance(hdu.data, np.ndarray) and hdu.data.ndim == 1:
                    header = hdu.header
                    n_pixels = len(hdu.data)

                    # Build wavelength array from WCS
                    if 'CRVAL1' in header and 'CDELT1' in header:
                        crval = header['CRVAL1']
                        cdelt = header['CDELT1']
                        crpix = header.get('CRPIX1', 1)

                        wavelength = crval + cdelt * (np.arange(n_pixels) + 1 - crpix)
                        spectrum_data['wavelength'] = wavelength.tolist()
                        spectrum_data['flux'] = hdu.data.tolist()

                if spectrum_data:
                    # Calculate spectral range
                    spectrum_data['wavelength_min'] = min(spectrum_data['wavelength'])
                    spectrum_data['wavelength_max'] = max(spectrum_data['wavelength'])
                    spectrum_data['n_pixels'] = len(spectrum_data['wavelength'])

                    # Calculate continuum level (median of flux)
                    spectrum_data['continuum_level'] = float(np.median(spectrum_data['flux']))

                    # Calculate SNR if error available
                    if 'error' in spectrum_data:
                        flux_arr = np.array(spectrum_data['flux'])
                        error_arr = np.array(spectrum_data['error'])
                        snr = np.median(flux_arr / error_arr)
                        spectrum_data['snr'] = float(snr)

                    self.logger.info(f"Extracted spectrum with {spectrum_data['n_pixels']} pixels")
                    return spectrum_data
                else:
                    self.logger.warning("Could not extract spectrum from FITS file")
                    return None

        except Exception as e:
            self.logger.error(f"Failed to extract spectrum: {e}")
            return None

    def analyze_jwst_nirspec(self, fits_path: str) -> Optional[Dict[str, Any]]:
        """
        Specialized analysis for JWST NIRSpec data

        Args:
            fits_path: Path to JWST NIRSpec FITS file

        Returns:
            Analysis results
        """
        try:
            # Extract metadata
            metadata = self.extract_metadata(fits_path)
            if not metadata or metadata['instrument'] != 'NIRSpec':
                self.logger.warning("File does not appear to be NIRSpec data")

            # Extract spectrum
            spectrum = self.extract_spectrum(fits_path)

            result = {
                'file_path': str(fits_path),
                'instrument': 'JWST/NIRSpec',
                'metadata': metadata,
                'spectrum': spectrum
            }

            if spectrum:
                # Detect common spectral features
                features = self._detect_spectral_features(
                    np.array(spectrum['wavelength']),
                    np.array(spectrum['flux'])
                )
                result['detected_features'] = features

            self.logger.info("Completed JWST NIRSpec analysis")
            return result

        except Exception as e:
            self.logger.error(f"JWST NIRSpec analysis failed: {e}")
            return None

    def _detect_spectral_features(self, wavelength: np.ndarray, flux: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect spectral lines and features

        Args:
            wavelength: Wavelength array (microns)
            flux: Flux array

        Returns:
            List of detected features
        """
        features = []

        # Common molecular absorption features in exoplanet atmospheres (in microns)
        known_features = {
            'H2O': [(1.15, 1.15), (1.4, 1.4), (1.8, 1.9), (2.5, 3.0), (5.0, 8.0)],
            'CO2': [(2.7, 2.8), (4.2, 4.4), (15.0, 16.0)],
            'CH4': [(2.2, 2.5), (3.3, 3.4), (7.5, 8.0)],
            'CO': [(2.3, 2.4), (4.6, 4.8)],
            'NH3': [(1.5, 1.6), (2.0, 2.2), (10.0, 11.0)],
            'H2S': [(2.6, 2.7), (3.8, 4.0)],
            'SO2': [(4.0, 4.2), (7.3, 7.6)]
        }

        # Calculate continuum
        continuum = np.median(flux)

        for species, wavelength_ranges in known_features.items():
            for wave_min, wave_max in wavelength_ranges:
                # Check if this range is in our spectrum
                mask = (wavelength >= wave_min) & (wavelength <= wave_max)
                if np.sum(mask) > 5:  # Need at least 5 points
                    region_flux = flux[mask]
                    region_wave = wavelength[mask]

                    # Check for absorption (flux below continuum)
                    mean_flux = np.mean(region_flux)
                    if mean_flux < continuum * 0.95:  # 5% absorption threshold
                        depth = (continuum - mean_flux) / continuum
                        features.append({
                            'species': species,
                            'wavelength_range': [wave_min, wave_max],
                            'center_wavelength': float(np.mean(region_wave)),
                            'depth': float(depth),
                            'significance': float(depth / np.std(flux) * np.sqrt(len(region_flux)))
                        })

        self.logger.info(f"Detected {len(features)} spectral features")
        return features

    def detect_spectral_lines(self, fits_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Detect emission and absorption lines in spectrum

        Args:
            fits_path: Path to FITS file

        Returns:
            List of detected lines
        """
        spectrum_data = self.extract_spectrum(fits_path)
        if not spectrum_data:
            return None

        wavelength = np.array(spectrum_data['wavelength'])
        flux = np.array(spectrum_data['flux'])

        return self._detect_spectral_features(wavelength, flux)

    def get_fits_summary(self, fits_path: str) -> str:
        """
        Get human-readable summary of FITS file

        Args:
            fits_path: Path to FITS file

        Returns:
            Summary string
        """
        fits_info = self.read_fits(fits_path)
        if not fits_info:
            return "Failed to read FITS file"

        metadata = self.extract_metadata(fits_path)
        spectrum = self.extract_spectrum(fits_path)

        summary = f"""
FITS File Summary: {fits_info['file_path']}
{'=' * 60}

Extensions: {fits_info['num_extensions']}
"""

        if metadata:
            summary += f"""
Observation Metadata:
  Telescope: {metadata['telescope']}
  Instrument: {metadata['instrument']}
  Target: {metadata['object_name']}
  Date: {metadata['obs_date']}
  Exposure Time: {metadata['exposure_time']} s
"""

        if spectrum:
            summary += f"""
Spectrum Information:
  Wavelength Range: {spectrum['wavelength_min']:.3f} - {spectrum['wavelength_max']:.3f} µm
  Number of Pixels: {spectrum['n_pixels']}
  Continuum Level: {spectrum['continuum_level']:.2e}
  SNR: {spectrum.get('snr', 'N/A')}
"""

        return summary


def main():
    """Test the Vidya agent"""
    import sys

    agent = VidyaAgent()

    if len(sys.argv) > 1:
        fits_file = sys.argv[1]

        print(f"Analyzing FITS file: {fits_file}")
        print()

        # Get summary
        summary = agent.get_fits_summary(fits_file)
        print(summary)

        # Detect spectral lines
        lines = agent.detect_spectral_lines(fits_file)
        if lines:
            print("\nDetected Spectral Features:")
            print("-" * 60)
            for line in lines:
                print(f"  {line['species']}: {line['center_wavelength']:.3f} µm "
                      f"(depth: {line['depth']*100:.2f}%, sig: {line['significance']:.1f}σ)")

    else:
        print("Usage: python Vidya.py <fits_file>")
        print("\nExample: python Vidya.py data/lhs1140b_nirspec.fits")


if __name__ == "__main__":
    main()
