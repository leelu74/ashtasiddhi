#!/usr/bin/env python3
"""
Laghima.py - Paper Search Agent
Searches for exoplanet papers based on keywords using arXiv and other sources
Enhanced with detailed inspection for 9 nearest star systems
"""

import re
import time
import logging
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

try:
    import arxiv
except ImportError:
    arxiv = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


class NASAExoplanetArchive:
    """Client for NASA Exoplanet Archive TAP service"""

    BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

    # 18 Target exoplanets for V2.0
    TARGET_18 = [
        "Proxima Cen b",
        "Ross 128 b",
        "GJ 1061 d",
        "GJ 1061 c",
        "GJ 273 b",
        "Teegarden's Star b",
        "Teegarden's Star c",
        "GJ 1002 b",
        "GJ 1002 c",
        "GJ 667 C f",
        "GJ 667 C e",
        "Wolf 1069 b",
        "TRAPPIST-1 d",
        "TRAPPIST-1 e",
        "TRAPPIST-1 f",
        "TRAPPIST-1 g",
        "TOI-700 d",
        "TOI-700 e"
    ]

    def __init__(self):
        self.logger = logging.getLogger("NASA-Archive")

    def query_planetary_systems(self, where_clause: str = "") -> List[Dict]:
        """
        Query the Planetary Systems (PS) table via TAP

        Args:
            where_clause: SQL WHERE clause (e.g., "pl_name='Proxima Cen b'")

        Returns:
            List of planet data dictionaries
        """
        try:
            # Construct ADQL query
            query = f"""
            SELECT
                pl_name, hostname, discoverymethod, disc_year,
                pl_orbper, pl_orbsmax, pl_rade, pl_bmasse, pl_eqt,
                st_teff, st_rad, st_mass, sy_dist,
                pl_ratdor, pl_ratror
            FROM ps
            """

            if where_clause:
                query += f" WHERE {where_clause}"

            # Make TAP request
            params = {
                'query': query,
                'format': 'json'
            }

            self.logger.info(f"Querying NASA Archive...")
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Parse results
            planets = []
            for row in data:
                planet = {
                    'planet_name': row.get('pl_name'),
                    'hostname': row.get('hostname'),
                    'discovery_method': row.get('discoverymethod'),
                    'discovery_year': row.get('disc_year'),
                    'pl_orbper': row.get('pl_orbper'),
                    'pl_orbsmax': row.get('pl_orbsmax'),
                    'pl_rade': row.get('pl_rade'),
                    'pl_bmasse': row.get('pl_bmasse'),
                    'pl_eqt': row.get('pl_eqt'),
                    'st_teff': row.get('st_teff'),
                    'st_rad': row.get('st_rad'),
                    'st_mass': row.get('st_mass'),
                    'st_dist': row.get('sy_dist'),
                    'archive_url': f"https://exoplanetarchive.ipac.caltech.edu/overview/{row.get('hostname', '')}"
                }

                # Calculate HZ status
                planet['hz_status'] = self._calculate_hz_status(planet)

                planets.append(planet)

            self.logger.info(f"Retrieved {len(planets)} planets from NASA Archive")
            return planets

        except Exception as e:
            self.logger.error(f"NASA Archive query failed: {e}")
            return []

    def fetch_exoplanet_by_name(self, name: str) -> Optional[Dict]:
        """Fetch single exoplanet by name"""
        where_clause = f"pl_name='{name}'"
        results = self.query_planetary_systems(where_clause)
        return results[0] if results else None

    def fetch_target_18(self) -> List[Dict]:
        """Fetch all 18 target exoplanets"""
        self.logger.info("Fetching 18 target exoplanets...")
        planets = []

        for planet_name in self.TARGET_18:
            self.logger.info(f"Fetching {planet_name}...")
            planet = self.fetch_exoplanet_by_name(planet_name)
            if planet:
                planets.append(planet)
            else:
                self.logger.warning(f"Could not find {planet_name} in NASA Archive")

            time.sleep(0.5)  # Rate limiting

        self.logger.info(f"Successfully fetched {len(planets)}/18 target planets")
        return planets

    def _calculate_hz_status(self, planet: Dict) -> str:
        """
        Calculate habitable zone status

        Args:
            planet: Planet data dictionary

        Returns:
            HZ status: 'inner_hz', 'hz', 'outer_hz', 'non_hz'
        """
        try:
            # Need stellar luminosity and semi-major axis
            st_teff = planet.get('st_teff')
            st_rad = planet.get('st_rad')
            pl_orbsmax = planet.get('pl_orbsmax')

            if not all([st_teff, st_rad, pl_orbsmax]):
                return 'unknown'

            # Calculate stellar luminosity (Stefan-Boltzmann)
            # L = 4πR²σT⁴
            # In solar units: L/L_sun = (R/R_sun)² * (T/T_sun)⁴
            T_sun = 5778  # K
            L_star = (st_rad ** 2) * ((st_teff / T_sun) ** 4)

            # Calculate HZ boundaries (Kopparapu et al.)
            # Conservative HZ: 0.95 - 1.37 AU for Sun
            hz_inner = 0.95 * (L_star ** 0.5)
            hz_outer = 1.37 * (L_star ** 0.5)

            # Optimistic HZ
            hz_inner_opt = 0.75 * (L_star ** 0.5)
            hz_outer_opt = 1.77 * (L_star ** 0.5)

            if hz_inner <= pl_orbsmax <= hz_outer:
                return 'hz'
            elif hz_inner_opt <= pl_orbsmax < hz_inner:
                return 'inner_hz'
            elif hz_outer < pl_orbsmax <= hz_outer_opt:
                return 'outer_hz'
            else:
                return 'non_hz'

        except Exception as e:
            self.logger.warning(f"HZ calculation failed: {e}")
            return 'unknown'


class LaghimaAgent:
    """Agent for searching and downloading exoplanet research papers"""
    
    def __init__(self, download_dir: str = "./data/papers"):
        self.logger = logging.getLogger("Laghima")
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # 9 Nearest Star Systems (exact distances in light-years)
        self.NEAREST_SYSTEMS = {
            "Proxima Centauri": 4.24,
            "Alpha Centauri": 4.37, 
            "Barnards Star": 5.96,
            "Wolf 359": 7.86,
            "Lalande 21185": 8.31,
            "Sirius": 8.60,
            "Luyten 726-8": 8.73,
            "Ross 154": 9.69,
            "Ross 248": 10.30
        }
        
        # Chemical patterns for detection
        self.CHEMICAL_PATTERNS = re.compile(
            r'\b(H2O|H2|He|S|SO2|H2S|CH4|CO2|CO|sulfur|water|hydrogen|helium|carbon|methane)\b',
            re.IGNORECASE
        )
        
        # Methods patterns
        self.METHODS_PATTERNS = re.compile(
            r'\b(radial velocity|RV|transit|photometry|HZ|habitable|astrometry|direct imaging)\b',
            re.IGNORECASE
        )
        
        # arXiv categories related to exoplanets
        self.arxiv_categories = [
            'astro-ph.EP',  # Earth and Planetary Astrophysics
            'astro-ph.SR',  # Solar and Stellar Astrophysics
            'astro-ph.IM',  # Instrumentation and Methods for Astrophysics
        ]

        # NASA Exoplanet Archive client
        self.nasa_archive = NASAExoplanetArchive()
        
    def search_papers(self, keywords: List[str], max_papers: int = 10) -> List[Dict]:
        """
        Search for papers using multiple sources
        
        Args:
            keywords: List of search keywords
            max_papers: Maximum number of papers to return
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching papers with keywords: {keywords}")
        
        all_papers = []
        
        # Search arXiv
        arxiv_papers = self._search_arxiv(keywords, max_papers // 2)
        all_papers.extend(arxiv_papers)
        
        # Search CatalyzeX (if available)
        catalyzex_papers = self._search_catalyzex(keywords, max_papers // 2)
        all_papers.extend(catalyzex_papers)
        
        # Remove duplicates based on title similarity
        unique_papers = self._remove_duplicates(all_papers)
        
        # Sort by relevance score
        unique_papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return unique_papers[:max_papers]
    
    def _search_arxiv(self, keywords: List[str], max_papers: int) -> List[Dict]:
        """Search arXiv for papers"""
        papers = []
        
        if not arxiv:
            self.logger.warning("arxiv package not available, using manual search")
            return self._search_arxiv_manual(keywords, max_papers)
        
        try:
            # Construct search query
            query_terms = []
            for keyword in keywords:
                if keyword.lower() in ['exoplanet', 'planet', 'transit', 'atmospheric']:
                    query_terms.append(f'ti:"{keyword}" OR abs:"{keyword}"')
                else:
                    query_terms.append(f'abs:"{keyword}"')
            
            query = " AND ".join(query_terms)
            
            # Search with category filter
            category_filter = " OR ".join([f"cat:{cat}" for cat in self.arxiv_categories])
            full_query = f"({query}) AND ({category_filter})"
            
            self.logger.info(f"arXiv query: {full_query}")
            
            search = arxiv.Search(
                query=full_query,
                max_results=max_papers,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for result in search.results():
                paper = {
                    'title': result.title,
                    'authors': [str(author) for author in result.authors],
                    'abstract': result.summary,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'published': result.published.isoformat() if result.published else None,
                    'categories': result.categories,
                    'source': 'arXiv',
                    'relevance_score': self._calculate_relevance(result.summary, keywords)
                }
                papers.append(paper)
                
        except Exception as e:
            self.logger.error(f"arXiv search failed: {e}")
            
        return papers
    
    def _search_arxiv_manual(self, keywords: List[str], max_papers: int) -> List[Dict]:
        """Manual arXiv search using HTTP API"""
        papers = []
        
        try:
            # Construct query
            search_terms = " AND ".join([f'all:"{keyword}"' for keyword in keywords])
            url = f"http://export.arxiv.org/api/query"
            params = {
                'search_query': search_terms,
                'start': 0,
                'max_results': max_papers,
                'sortBy': 'relevance'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                summary = entry.find('atom:summary', ns)
                published = entry.find('atom:published', ns)
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', ns):
                    name = author.find('atom:name', ns)
                    if name is not None:
                        authors.append(name.text)
                
                # Extract links
                pdf_url = None
                entry_url = None
                for link in entry.findall('atom:link', ns):
                    if link.get('type') == 'application/pdf':
                        pdf_url = link.get('href')
                    elif link.get('rel') == 'alternate':
                        entry_url = link.get('href')
                
                paper = {
                    'title': title.text.strip() if title is not None else "Unknown Title",
                    'authors': authors,
                    'abstract': summary.text.strip() if summary is not None else "",
                    'url': entry_url,
                    'pdf_url': pdf_url,
                    'published': published.text if published is not None else None,
                    'source': 'arXiv',
                    'relevance_score': self._calculate_relevance(
                        summary.text if summary is not None else "", 
                        keywords
                    )
                }
                papers.append(paper)
                
        except Exception as e:
            self.logger.error(f"Manual arXiv search failed: {e}")
            
        return papers
    
    def _search_catalyzex(self, keywords: List[str], max_papers: int) -> List[Dict]:
        """Search CatalyzeX for papers (if API available)"""
        papers = []
        
        try:
            # Note: CatalyzeX doesn't have a public API
            # This is a placeholder for potential integration
            self.logger.info("CatalyzeX search not implemented (no public API)")
            
        except Exception as e:
            self.logger.error(f"CatalyzeX search failed: {e}")
            
        return papers
    
    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Exoplanet-specific keyword weights
        high_priority = ['exoplanet', 'transit', 'radial velocity', 'atmosphere', 'habitable']
        medium_priority = ['planet', 'stellar', 'orbital', 'detection']
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            
            if keyword_lower in high_priority:
                score += count * 3
            elif keyword_lower in medium_priority:
                score += count * 2
            else:
                score += count * 1
        
        # Normalize by text length
        return min(score / len(text.split()) * 100, 1.0)
    
    def _remove_duplicates(self, papers: List[Dict]) -> List[Dict]:
        """Remove duplicate papers based on title similarity"""
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            title_normalized = re.sub(r'[^\w\s]', '', paper['title'].lower())
            title_words = set(title_normalized.split())
            
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                
                # Check for significant overlap (>70% of words)
                if len(title_words.intersection(seen_words)) / max(len(title_words), 1) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_papers.append(paper)
                seen_titles.add(title_normalized)
        
        return unique_papers
    
    def download_paper(self, paper_url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a paper PDF
        
        Args:
            paper_url: URL to the paper PDF
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            if not filename:
                # Extract filename from URL
                filename = paper_url.split('/')[-1]
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
            
            file_path = self.download_dir / filename
            
            # Skip if already downloaded
            if file_path.exists():
                self.logger.info(f"File already exists: {file_path}")
                return str(file_path)
            
            self.logger.info(f"Downloading {paper_url}")
            
            response = requests.get(paper_url, timeout=60)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Download failed for {paper_url}: {e}")
            return None
    
    def download_papers_batch(self, papers: List[Dict], max_downloads: int = 5) -> List[str]:
        """Download multiple papers with rate limiting"""
        downloaded_files = []
        
        for i, paper in enumerate(papers[:max_downloads]):
            if 'pdf_url' in paper and paper['pdf_url']:
                # Create safe filename
                safe_title = re.sub(r'[^\w\s-]', '', paper['title'][:50])
                safe_title = re.sub(r'\s+', '_', safe_title)
                filename = f"{safe_title}.pdf"
                
                file_path = self.download_paper(paper['pdf_url'], filename)
                if file_path:
                    downloaded_files.append(file_path)
                
                # Rate limiting
                if i < len(papers) - 1:
                    time.sleep(2)
        
        return downloaded_files
    
    def search_by_author(self, author_name: str, max_papers: int = 10) -> List[Dict]:
        """Search papers by author name"""
        if not arxiv:
            self.logger.warning("arxiv package not available")
            return []
        
        try:
            search = arxiv.Search(
                query=f"au:{author_name}",
                max_results=max_papers,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            papers = []
            for result in search.results():
                paper = {
                    'title': result.title,
                    'authors': [str(author) for author in result.authors],
                    'abstract': result.summary,
                    'url': result.entry_id,
                    'pdf_url': result.pdf_url,
                    'published': result.published.isoformat() if result.published else None,
                    'categories': result.categories,
                    'source': 'arXiv'
                }
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            self.logger.error(f"Author search failed: {e}")
            return []

    def search_system_papers(self, system: str, max_papers: int = 5) -> List[str]:
        """
        Download MAX 5 papers per system to /data/papers/[system]/
        
        Args:
            system: Star system name (e.g., "Proxima Centauri")
            max_papers: Maximum papers to download (default 5)
            
        Returns:
            List of downloaded PDF paths
        """
        self.logger.info(f"Searching papers for {system}")
        
        # Create system directory
        system_clean = system.replace(" ", "_").replace("'", "")
        system_dir = self.download_dir / system_clean
        system_dir.mkdir(exist_ok=True)
        
        # Handle system aliases
        search_queries = self._get_system_aliases(system)
        
        downloaded_pdfs = []
        papers_found = 0
        
        for query in search_queries:
            if papers_found >= max_papers:
                break
                
            try:
                # Search arXiv for this system
                papers = self._search_arxiv_system(query, max_papers - papers_found)
                
                for paper in papers:
                    if papers_found >= max_papers:
                        break
                        
                    if 'pdf_url' in paper and paper['pdf_url']:
                        # Extract arXiv ID for filename
                        arxiv_id = self._extract_arxiv_id(paper['pdf_url'])
                        if arxiv_id:
                            filename = f"{arxiv_id}.pdf"
                            file_path = system_dir / filename
                            
                            # Download if not exists
                            if not file_path.exists():
                                downloaded_path = self._download_pdf(paper['pdf_url'], str(file_path))
                                if downloaded_path:
                                    downloaded_pdfs.append(downloaded_path)
                                    papers_found += 1
                                    
                                    # Rate limiting
                                    time.sleep(1)
                            else:
                                downloaded_pdfs.append(str(file_path))
                                papers_found += 1
                                
            except Exception as e:
                self.logger.error(f"Error searching {query}: {e}")
                continue
        
        self.logger.info(f"Downloaded {len(downloaded_pdfs)}/{max_papers} papers for {system}")
        return downloaded_pdfs

    def inspect_downloaded_papers(self, system: str) -> dict:
        """
        DETAILED ANALYSIS of downloaded papers - CRISP OUTPUT
        
        Args:
            system: Star system name
            
        Returns:
            Detailed inspection results dictionary
        """
        system_clean = system.replace(" ", "_").replace("'", "")
        system_dir = self.download_dir / system_clean
        
        if not system_dir.exists():
            return {
                "system": system,
                "total_papers": 0,
                "papers": [],
                "summary": "No papers found for this system"
            }
        
        # Find all PDF files
        pdf_files = list(system_dir.glob("*.pdf"))
        papers_analysis = []
        
        h2o_count = 0
        hz_count = 0
        rv_count = 0
        
        for pdf_file in pdf_files:
            try:
                analysis = self._analyze_single_pdf(pdf_file)
                papers_analysis.append(analysis)
                
                # Count key features
                chemicals = analysis.get('chemicals', [])
                if any('H2O' in chem.upper() or 'WATER' in chem.upper() for chem in chemicals):
                    h2o_count += 1
                
                methods = analysis.get('methods', [])
                if any('HZ' in method.upper() or 'HABITABLE' in method.upper() for method in methods):
                    hz_count += 1
                    
                if any('RV' in method.upper() or 'RADIAL' in method.upper() for method in methods):
                    rv_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error analyzing {pdf_file}: {e}")
                continue
        
        # Generate summary
        total_papers = len(papers_analysis)
        summary_parts = []
        
        if h2o_count > 0:
            summary_parts.append(f"{h2o_count}/{total_papers} mention H2O")
        if hz_count > 0:
            summary_parts.append(f"{hz_count} confirm HZ candidate")
        if rv_count > 0:
            summary_parts.append(f"{rv_count} have RV data")
            
        summary = ", ".join(summary_parts) if summary_parts else "No key features detected"
        
        return {
            "system": system,
            "total_papers": total_papers,
            "papers": papers_analysis,
            "summary": summary
        }

    def _get_system_aliases(self, system: str) -> List[str]:
        """Get search query variations for a star system"""
        aliases = [system]
        
        # Add common aliases
        if system == "Barnards Star":
            aliases.extend(["Barnard's Star", "Barnard's b", "Barnard Star"])
        elif system == "Proxima Centauri":
            aliases.extend(["Proxima b", "Proxima Cen", "Alpha Centauri C"])
        elif system == "Alpha Centauri":
            aliases.extend(["Alpha Cen", "Rigil Kent", "Toliman"])
        elif system == "Wolf 359":
            aliases.extend(["CN Leonis", "Wolf 359"])
        elif system == "Sirius":
            aliases.extend(["Alpha Canis Majoris", "Sirius A", "Sirius B"])
            
        return aliases

    def _search_arxiv_system(self, system_name: str, max_papers: int) -> List[Dict]:
        """Search arXiv specifically for a star system"""
        papers = []
        
        try:
            if arxiv:
                # Use arxiv package
                query = f'abs:"{system_name}" OR ti:"{system_name}"'
                search = arxiv.Search(
                    query=query,
                    max_results=max_papers,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                for result in search.results():
                    paper = {
                        'title': result.title,
                        'authors': [str(author) for author in result.authors],
                        'abstract': result.summary,
                        'url': result.entry_id,
                        'pdf_url': result.pdf_url,
                        'published': result.published.isoformat() if result.published else None,
                        'source': 'arXiv'
                    }
                    papers.append(paper)
            else:
                # Manual arXiv search
                papers = self._manual_arxiv_search(system_name, max_papers)
                
        except Exception as e:
            self.logger.error(f"arXiv search failed for {system_name}: {e}")
            
        return papers

    def _manual_arxiv_search(self, system_name: str, max_papers: int) -> List[Dict]:
        """Manual arXiv search for system"""
        papers = []
        
        try:
            url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:"{system_name}"',
                'start': 0,
                'max_results': max_papers,
                'sortBy': 'relevance'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                summary_elem = entry.find('atom:summary', ns)
                
                # Extract PDF URL
                pdf_url = None
                for link in entry.findall('atom:link', ns):
                    if link.get('type') == 'application/pdf':
                        pdf_url = link.get('href')
                        break
                
                if title_elem is not None and pdf_url:
                    paper = {
                        'title': title_elem.text.strip(),
                        'abstract': summary_elem.text.strip() if summary_elem is not None else "",
                        'pdf_url': pdf_url,
                        'source': 'arXiv'
                    }
                    papers.append(paper)
                    
        except Exception as e:
            self.logger.error(f"Manual search failed for {system_name}: {e}")
            
        return papers

    def _extract_arxiv_id(self, url: str) -> Optional[str]:
        """Extract arXiv ID from URL"""
        # Pattern: https://arxiv.org/pdf/2410.12345v1.pdf
        match = re.search(r'(\d{4}\.\d{4,5})', url)
        return match.group(1) if match else None

    def _download_pdf(self, url: str, file_path: str) -> Optional[str]:
        """Download PDF to specific path"""
        try:
            self.logger.info(f"Downloading {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            return file_path
            
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None

    def _analyze_single_pdf(self, pdf_path: Path) -> dict:
        """Analyze single PDF for chemicals, methods, and metrics"""
        analysis = {
            "filename": pdf_path.name,
            "pages": 0,
            "chemicals": [],
            "methods": [],
            "metrics": {},
            "priority": "LOW",
            "score": 0.0
        }
        
        try:
            # Get file size
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            
            if PyPDF2:
                # Extract text using PyPDF2
                text = self._extract_pdf_text(pdf_path)
                analysis["pages"] = text.count('\n\n') // 10  # Rough page estimate
            else:
                # Fallback without text extraction
                analysis["pages"] = int(file_size_mb * 5)  # Rough estimate
                text = ""
            
            if text:
                # Find chemicals
                chemicals = self.CHEMICAL_PATTERNS.findall(text)
                analysis["chemicals"] = list(set(chemicals))
                
                # Find methods
                methods = self.METHODS_PATTERNS.findall(text)
                analysis["methods"] = list(set(methods))
                
                # Extract specific metrics
                analysis["metrics"] = self._extract_metrics(text)
                
                # Calculate priority and score
                analysis["priority"], analysis["score"] = self._calculate_priority(analysis)
            
        except Exception as e:
            self.logger.error(f"PDF analysis failed for {pdf_path}: {e}")
            
        return analysis

    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyPDF2"""
        text = ""
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(min(len(pdf_reader.pages), 10)):  # First 10 pages
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            self.logger.error(f"Text extraction failed for {pdf_path}: {e}")
            
        return text

    def _extract_metrics(self, text: str) -> dict:
        """Extract specific astrophysical metrics from text"""
        metrics = {}
        
        try:
            # Radial velocity values
            rv_match = re.search(r'(?:RV|K)\s*[=:]\s*([\d.]+)\s*m/?s', text, re.IGNORECASE)
            if rv_match:
                metrics["RV_K"] = f"{rv_match.group(1)} m/s"
            
            # Planet radius
            rp_match = re.search(r'R_?p?\s*[=:]\s*([\d.]+)\s*R_?[eE⊕]', text, re.IGNORECASE)
            if rp_match:
                metrics["Rp"] = f"{rp_match.group(1)} Re"
                
            # Habitable zone
            hz_match = re.search(r'\b(habitable zone|HZ)\b', text, re.IGNORECASE)
            if hz_match:
                metrics["HZ"] = True
                
            # Period
            period_match = re.search(r'P\s*[=:]\s*([\d.]+)\s*(?:days?|d)', text, re.IGNORECASE)
            if period_match:
                metrics["Period"] = f"{period_match.group(1)} days"
                
        except Exception as e:
            self.logger.error(f"Metrics extraction failed: {e}")
            
        return metrics

    def _calculate_priority(self, analysis: dict) -> tuple:
        """Calculate priority (HIGH/MED/LOW) and score (0.0-1.0)"""
        score = 0.0
        
        # Chemical detection
        chemicals = [c.upper() for c in analysis.get('chemicals', [])]
        if any(c in ['H2O', 'WATER'] for c in chemicals):
            score += 0.3
        if any(c in ['S', 'SO2', 'H2S', 'SULFUR'] for c in chemicals):
            score += 0.2
            
        # Method detection
        methods = [m.upper() for m in analysis.get('methods', [])]
        if any(m in ['RV', 'RADIAL'] for m in methods):
            score += 0.2
        if any(m in ['TRANSIT'] for m in methods):
            score += 0.2
        if any(m in ['HZ', 'HABITABLE'] for m in methods):
            score += 0.3
            
        # Metrics bonus
        if analysis.get('metrics'):
            score += len(analysis['metrics']) * 0.1
            
        # Determine priority
        if score >= 0.7:
            priority = "HIGH"
        elif score >= 0.3:
            priority = "MEDIUM"
        else:
            priority = "LOW"
            
        return priority, min(score, 1.0)

    # ==================== NASA EXOPLANET ARCHIVE METHODS ====================

    def fetch_nasa_data(self, planet_names: List[str]) -> List[Dict]:
        """
        Fetch data from NASA Exoplanet Archive for multiple planets

        Args:
            planet_names: List of planet names

        Returns:
            List of planet data dictionaries
        """
        planets = []
        for name in planet_names:
            planet = self.nasa_archive.fetch_exoplanet_by_name(name)
            if planet:
                planets.append(planet)
            time.sleep(0.5)  # Rate limiting

        return planets

    def sync_nasa_archive(self) -> List[Dict]:
        """
        Sync all 18 target exoplanets from NASA Archive

        Returns:
            List of planet data
        """
        self.logger.info("Syncing NASA Exoplanet Archive - 18 target planets")
        return self.nasa_archive.fetch_target_18()

    def fetch_proxima_cen_b(self) -> Optional[Dict]:
        """Fetch Proxima Centauri b data from NASA Archive"""
        return self.nasa_archive.fetch_exoplanet_by_name("Proxima Cen b")

def main():
    """Test the Laghima agent"""
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python Laghima.py <keywords>...")
        sys.exit(1)
    
    keywords = sys.argv[1:]
    agent = LaghimaAgent()
    
    papers = agent.search_papers(keywords, max_papers=5)
    
    print(f"Found {len(papers)} papers:")
    print(json.dumps(papers, indent=2, default=str))
    
    # Optionally download papers
    if papers and input("Download papers? (y/n): ").lower() == 'y':
        downloaded = agent.download_papers_batch(papers, max_downloads=3)
        print(f"Downloaded {len(downloaded)} papers: {downloaded}")

if __name__ == "__main__":
    main()