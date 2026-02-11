#!/usr/bin/env python3
"""
Prakamya.py - Keywords Extraction Agent
Pulls key works and extracts relevant keywords from exoplanet PDFs
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Set
import PyPDF2
import nltk
import spacy
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag

class PrakamyaAgent:
    """Agent for extracting keywords from exoplanet research papers"""
    
    def __init__(self):
        self.logger = logging.getLogger("Prakamya")
        
        # Load spaCy model (download if needed)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found, using basic extraction")
            self.nlp = None
        
        # Exoplanet-specific keyword patterns
        self.exoplanet_keywords = {
            'detection_methods': [
                'transit', 'radial velocity', 'rv', 'direct imaging', 
                'gravitational lensing', 'astrometry', 'timing variations'
            ],
            'atmospheric_compounds': [
                'h2o', 'water', 'h2', 'hydrogen', 'he', 'helium', 
                'sulfur', 'h2s', 'so2', 'ch4', 'methane', 'co2', 'carbon dioxide',
                'co', 'carbon monoxide', 'nh3', 'ammonia', 'n2', 'nitrogen'
            ],
            'planetary_properties': [
                'radius', 'mass', 'density', 'temperature', 'period',
                'semi-major axis', 'eccentricity', 'inclination'
            ],
            'habitable_zone': [
                'habitable zone', 'goldilocks zone', 'hz', 'habitable',
                'insolation', 'stellar flux', 'effective temperature'
            ],
            'stellar_properties': [
                'stellar mass', 'stellar radius', 'luminosity', 'effective temperature',
                'metallicity', 'age', 'spectral type'
            ]
        }
        
        self.stop_words = set(stopwords.words('english'))
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file

        For large files (>25MB), automatically uses chunked processing
        """
        try:
            import os
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

            # Use chunked processing for large files
            if file_size_mb > 25:
                self.logger.info(f"Large PDF detected ({file_size_mb:.1f} MB), using chunked processing")
                return self.extract_text_from_pdf_chunked(pdf_path)

            # Standard processing for smaller files
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                self.logger.info(f"Extracting text from {total_pages} pages")

                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            self.logger.error(f"Error extracting text from {pdf_path}: {e}")
            return ""

    def extract_text_from_pdf_chunked(self, pdf_path: str, chunk_size: int = 10) -> str:
        """
        Extract text from large PDFs in chunks to avoid memory issues

        Args:
            pdf_path: Path to PDF file
            chunk_size: Number of pages to process at once (default: 10)

        Returns:
            Extracted text from entire PDF
        """
        try:
            import os
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            self.logger.info(f"Processing large PDF ({file_size_mb:.1f} MB) in chunks of {chunk_size} pages")

            text_chunks = []

            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                self.logger.info(f"Total pages: {total_pages}")

                # Process pages in chunks
                for start_idx in range(0, total_pages, chunk_size):
                    end_idx = min(start_idx + chunk_size, total_pages)
                    chunk_text = ""

                    self.logger.info(f"Processing pages {start_idx+1} to {end_idx}")

                    for page_idx in range(start_idx, end_idx):
                        try:
                            page = pdf_reader.pages[page_idx]
                            page_text = page.extract_text()
                            if page_text:
                                chunk_text += page_text + "\n"
                        except Exception as e:
                            self.logger.warning(f"Failed to extract page {page_idx+1}: {e}")
                            continue

                    text_chunks.append(chunk_text)

                    # Log progress
                    progress = (end_idx / total_pages) * 100
                    self.logger.info(f"Progress: {progress:.1f}%")

            # Combine all chunks
            full_text = "\n".join(text_chunks)
            self.logger.info(f"Successfully extracted {len(full_text)} characters from {total_pages} pages")

            return full_text

        except Exception as e:
            self.logger.error(f"Error in chunked PDF extraction from {pdf_path}: {e}")
            return ""
    
    def extract_keywords(self, pdf_path: str) -> Dict[str, List[str]]:
        """
        Extract exoplanet-relevant keywords from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary of categorized keywords
        """
        self.logger.info(f"Extracting keywords from {pdf_path}")
        
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {"error": ["Could not extract text from PDF"]}
        
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s\.\-]', ' ', text)
        
        results = {
            'detection_methods': [],
            'atmospheric_compounds': [],
            'planetary_properties': [],
            'habitable_zone': [],
            'stellar_properties': [],
            'chemical_abundances': [],
            'key_phrases': []
        }
        
        # Extract category-specific keywords
        for category, keywords in self.exoplanet_keywords.items():
            found = self._find_keywords_in_text(text, keywords)
            results[category] = list(found)
        
        # Extract chemical abundances with values
        results['chemical_abundances'] = self._extract_chemical_abundances(text)
        
        # Extract key phrases using NER if available
        if self.nlp:
            results['key_phrases'] = self._extract_key_phrases_ner(text)
        else:
            results['key_phrases'] = self._extract_key_phrases_simple(text)
        
        # Filter abstract and introduction for main concepts
        abstract_keywords = self._extract_from_abstract(text)
        if abstract_keywords:
            results['abstract_concepts'] = abstract_keywords
        
        self.logger.info(f"Extracted {sum(len(v) for v in results.values())} keywords")
        return results
    
    def _find_keywords_in_text(self, text: str, keywords: List[str]) -> Set[str]:
        """Find specific keywords in text"""
        found = set()
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text):
                found.add(keyword)
        return found
    
    def _extract_chemical_abundances(self, text: str) -> List[str]:
        """Extract chemical abundances with numerical values"""
        abundances = []
        
        # Patterns for chemical abundances
        patterns = [
            r'(h2o|water)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(h2s|hydrogen\s*sulfide)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(so2|sulfur\s*dioxide)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(ch4|methane)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(co2|carbon\s*dioxide)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(h2|hydrogen)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)',
            r'(he|helium)\s*[:\=\~]?\s*([0-9\.e\-\+]+)\s*(ppm|ppb|%|\%)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                compound = match.group(1)
                value = match.group(2)
                unit = match.group(3)
                abundances.append(f"{compound}: {value} {unit}")
        
        return abundances
    
    def _extract_key_phrases_ner(self, text: str) -> List[str]:
        """Extract key phrases using spaCy NER"""
        phrases = []
        
        # Process text in chunks due to length limits
        max_chunk_size = 1000000  # 1M characters
        for i in range(0, len(text), max_chunk_size):
            chunk = text[i:i + max_chunk_size]
            try:
                doc = self.nlp(chunk)
                
                # Extract named entities
                for ent in doc.ents:
                    if ent.label_ in ['ORG', 'PRODUCT', 'WORK_OF_ART', 'EVENT']:
                        phrases.append(ent.text.strip())
                
                # Extract noun phrases related to exoplanets
                for chunk in doc.noun_chunks:
                    chunk_text = chunk.text.lower()
                    if any(keyword in chunk_text for keyword in 
                          ['planet', 'exoplanet', 'atmosphere', 'transit', 'star']):
                        phrases.append(chunk.text.strip())
                        
            except Exception as e:
                self.logger.warning(f"NER processing failed for chunk: {e}")
                continue
        
        return list(set(phrases))[:50]  # Limit to top 50
    
    def _extract_key_phrases_simple(self, text: str) -> List[str]:
        """Extract key phrases using simple NLP techniques"""
        phrases = []
        sentences = sent_tokenize(text)[:100]  # First 100 sentences
        
        for sentence in sentences:
            tokens = word_tokenize(sentence)
            pos_tags = pos_tag(tokens)
            
            # Extract noun phrases
            noun_phrase = []
            for word, pos in pos_tags:
                if pos.startswith('N') or pos.startswith('J'):  # Nouns and adjectives
                    noun_phrase.append(word)
                else:
                    if len(noun_phrase) >= 2:
                        phrase = ' '.join(noun_phrase)
                        if any(keyword in phrase.lower() for keyword in 
                              ['planet', 'atmosphere', 'transit', 'star', 'orbit']):
                            phrases.append(phrase)
                    noun_phrase = []
        
        return list(set(phrases))[:30]  # Limit to top 30
    
    def _extract_from_abstract(self, text: str) -> List[str]:
        """Extract keywords specifically from abstract section"""
        # Find abstract section
        abstract_pattern = r'abstract[:\s]+(.*?)(?:introduction|keywords|1\.|i\.|background)'
        abstract_match = re.search(abstract_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if not abstract_match:
            return []
        
        abstract_text = abstract_match.group(1)
        
        # Extract important terms from abstract
        tokens = word_tokenize(abstract_text.lower())
        filtered_tokens = [word for word in tokens if word not in self.stop_words 
                          and len(word) > 3 and word.isalpha()]
        
        # Get most common terms
        freq_dist = Counter(filtered_tokens)
        common_terms = [term for term, count in freq_dist.most_common(15)]
        
        return common_terms
    
    def get_relevance_score(self, keywords: Dict[str, List[str]]) -> float:
        """
        Calculate relevance score for exoplanet research
        
        Args:
            keywords: Extracted keywords dictionary
            
        Returns:
            Relevance score (0-1)
        """
        score = 0.0
        
        # Weight different categories
        weights = {
            'detection_methods': 0.25,
            'atmospheric_compounds': 0.3,
            'planetary_properties': 0.2,
            'habitable_zone': 0.15,
            'stellar_properties': 0.1
        }
        
        for category, weight in weights.items():
            if category in keywords:
                count = len(keywords[category])
                # Normalize by expected maximum
                normalized_count = min(count / 10, 1.0)
                score += weight * normalized_count
        
        return min(score, 1.0)

def main():
    """Test the Prakamya agent"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python Prakamya.py <pdf_path>")
        sys.exit(1)
    
    agent = PrakamyaAgent()
    keywords = agent.extract_keywords(sys.argv[1])
    
    import json
    print(json.dumps(keywords, indent=2))

if __name__ == "__main__":
    main()