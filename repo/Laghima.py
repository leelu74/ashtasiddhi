#!/usr/bin/env python3
"""
Laghima.py - Paper Search Agent
Searches for exoplanet papers based on keywords using arXiv and other sources
"""

import re
import time
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote
import xml.etree.ElementTree as ET

try:
    import arxiv
except ImportError:
    arxiv = None

class LaghimaAgent:
    """Agent for searching and downloading exoplanet research papers"""
    
    def __init__(self, download_dir: str = "/data/papers"):
        self.logger = logging.getLogger("Laghima")
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # arXiv categories related to exoplanets
        self.arxiv_categories = [
            'astro-ph.EP',  # Earth and Planetary Astrophysics
            'astro-ph.SR',  # Solar and Stellar Astrophysics
            'astro-ph.IM',  # Instrumentation and Methods for Astrophysics
        ]
        
        # CatalyzeX API endpoint (if available)
        self.catalyzex_base_url = "https://www.catalyzex.com/api/papers"
        
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