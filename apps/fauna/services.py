"""
Smart Species Matching Service

This service provides intelligent species name matching with:
- Fuzzy matching for typos and variations
- Synonym recognition
- Scientific name parsing
- Scoring system for relevance ranking
- Common name extraction and normalization
"""

import re
from typing import List, Dict, Tuple, Optional
from django.db.models import Q
from .models import Species


class SpeciesMatcher:
    """
    Intelligent species matching service
    """
    
    # Synonym database for common species variations
    SYNONYMS = {
        'chinese egret': ['swinhoe egret', 'swinhoes egret', 'swinhoe\'s egret'],
        'little egret': ['small egret', 'lesser egret'],
        'great egret': ['large egret', 'white egret', 'common egret'],
        'cattle egret': ['bubulcus egret'],
        'pacific reef heron': ['eastern reef egret', 'reef heron'],
        'intermediate egret': ['median egret', 'yellow-billed egret'],
        'black-crowned night heron': ['black crowned night heron', 'night heron'],
        'grey heron': ['gray heron', 'common heron'],
        'purple heron': ['purpurea heron'],
        'yellow bittern': ['small bittern'],
        'cinnamon bittern': ['chestnut bittern'],
        'black bittern': ['dark bittern'],
        'bar-tailed godwit': ['bartailed godwit', 'bar tailed godwit'],
        'black-tailed godwit': ['blacktailed godwit', 'black tailed godwit'],
        'asiatic dowitcher': ['asian dowitcher', 'dowitcher'],
        'barnes swallow': ['barn swallow', 'barn\'s swallow'],
    }
    
    # Common words to ignore in matching
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'common', 'typical', 'standard', 'regular', 'normal'
    }
    
    def __init__(self):
        self.species_cache = {}
        self._build_species_cache()
    
    def _build_species_cache(self):
        """Build cache of all species for faster matching"""
        species_list = Species.objects.filter(is_archived=False)
        for species in species_list:
            key = f"{species.name}|{species.scientific_name}"
            self.species_cache[key] = species
    
    def find_species(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find species using intelligent matching
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with species info and match scores
        """
        if not query or not query.strip():
            return []
        
        normalized_query = self._normalize_text(query)
        matches = []
        
        # Get all species for analysis
        all_species = Species.objects.filter(is_archived=False)
        
        for species in all_species:
            score, reasons = self._calculate_match_score(species, normalized_query)
            
            if score > 0:
                matches.append({
                    'species': species,
                    'score': score,
                    'reasons': reasons,
                    'match_type': self._get_match_type(reasons)
                })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:limit]
    
    def _calculate_match_score(self, species: Species, query: str) -> Tuple[int, List[str]]:
        """
        Calculate match score for a species against a query
        
        Returns:
            Tuple of (score, reasons)
        """
        score = 0
        reasons = []
        
        # Normalize species names
        species_name = self._normalize_text(species.name)
        scientific_name = self._normalize_text(species.scientific_name)
        
        # 1. Exact name match (highest score)
        if species_name == query:
            score += 100
            reasons.append("Exact name match")
        
        # 2. Exact scientific name match
        if scientific_name == query:
            score += 90
            reasons.append("Exact scientific name match")
        
        # 3. Scientific name parsing match
        if self._match_scientific_name(scientific_name, query):
            score += 85
            reasons.append("Scientific name parsing match")
        
        # 4. Synonym detection
        if self._is_synonym(species_name, query):
            score += 80
            reasons.append("Synonym detected")
        
        # 5. Common name extraction match
        if self._extract_common_name(species_name) == self._extract_common_name(query):
            score += 70
            reasons.append("Common name match")
        
        # 6. Fuzzy name matching
        if self._fuzzy_match(species_name, query):
            score += 60
            reasons.append("Fuzzy name match")
        
        # 7. Partial word matching
        if self._partial_word_match(species_name, query):
            score += 50
            reasons.append("Partial word match")
        
        # 8. Contains match
        if query in species_name or species_name in query:
            score += 30
            reasons.append("Contains match")
        
        # 9. Scientific name contains match
        if query in scientific_name:
            score += 40
            reasons.append("Scientific name contains match")
        
        # 10. Handle parenthetical information
        if self._match_with_parentheses(species_name, query):
            score += 45
            reasons.append("Parenthetical match")
        
        return score, reasons
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s\-\(\)]', '', text)
        
        return text
    
    def _extract_common_name(self, name: str) -> str:
        """Extract the main common name (remove parenthetical info)"""
        # Remove parenthetical information
        clean_name = re.sub(r'\([^)]*\)', '', name).strip()
        
        # Get the first two significant words
        words = []
        for word in clean_name.split():
            if word.lower() not in self.STOP_WORDS:
                words.append(word.lower())
                if len(words) >= 2:
                    break
        
        return ' '.join(words)
    
    def _match_scientific_name(self, scientific_name: str, query: str) -> bool:
        """Check if query matches scientific name format"""
        # Extract genus and species from scientific name
        scientific_parts = scientific_name.split()
        if len(scientific_parts) >= 2:
            genus_species = ' '.join(scientific_parts[:2])
            if genus_species == query:
                return True
            
            # Check if query contains genus or species
            genus = scientific_parts[0]
            species = scientific_parts[1]
            
            if genus == query or species == query:
                return True
        
        return False
    
    def _is_synonym(self, name1: str, name2: str) -> bool:
        """Check if two names are synonyms"""
        # Direct synonym lookup
        for main_name, synonyms in self.SYNONYMS.items():
            if (name1 == main_name and name2 in synonyms) or (name2 == main_name and name1 in synonyms):
                return True
        
        # Check if either name is a synonym of the other
        for main_name, synonyms in self.SYNONYMS.items():
            if name1 in synonyms and name2 == main_name:
                return True
            if name2 in synonyms and name1 == main_name:
                return True
        
        return False
    
    def _fuzzy_match(self, text1: str, text2: str) -> bool:
        """Simple fuzzy matching based on word overlap - more strict to avoid false positives"""
        # Remove common words and normalize
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))
        
        # Remove stop words
        words1 = {w for w in words1 if w not in self.STOP_WORDS}
        words2 = {w for w in words2 if w not in self.STOP_WORDS}
        
        # Check if significant words overlap
        overlap = words1.intersection(words2)
        
        # Require at least 2 overlapping words AND 60% overlap for fuzzy matching
        # This prevents false positives like "Chinese Egret" matching "Great Egret"
        if len(overlap) < 2:
            return False
        
        overlap_ratio = len(overlap) / max(len(words1), len(words2))
        return overlap_ratio >= 0.6
    
    def _partial_word_match(self, text1: str, text2: str) -> bool:
        """Check for partial word matches - more strict to avoid false positives"""
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))
        
        # Remove stop words
        words1 = {w for w in words1 if w not in self.STOP_WORDS}
        words2 = {w for w in words2 if w not in self.STOP_WORDS}
        
        # Only match if there's significant word overlap (at least 50%)
        overlap = words1.intersection(words2)
        if len(overlap) == 0:
            return False
        
        overlap_ratio = len(overlap) / max(len(words1), len(words2))
        return overlap_ratio >= 0.5
    
    def _match_with_parentheses(self, species_name: str, query: str) -> bool:
        """Check if query matches species name with parenthetical info"""
        # Extract content within parentheses
        parentheses_match = re.search(r'\(([^)]+)\)', species_name)
        if parentheses_match:
            parentheses_content = parentheses_match.group(1).lower()
            if query in parentheses_content:
                return True
        
        # Check if query matches the main name when parenthetical info is removed
        main_name = re.sub(r'\([^)]*\)', '', species_name).strip()
        if main_name == query:
            return True
        
        return False
    
    def _get_match_type(self, reasons: List[str]) -> str:
        """Determine the type of match based on reasons"""
        if "Exact name match" in reasons:
            return "exact"
        elif "Exact scientific name match" in reasons:
            return "scientific_exact"
        elif "Synonym detected" in reasons:
            return "synonym"
        elif "Fuzzy name match" in reasons:
            return "fuzzy"
        elif "Scientific name parsing match" in reasons:
            return "scientific_parsed"
        else:
            return "partial"
    
    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get species name suggestions based on partial input
        
        Args:
            query: Partial query string
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested species names
        """
        matches = self.find_species(query, limit)
        suggestions = []
        
        for match in matches:
            species = match['species']
            suggestions.append({
                'name': species.name,
                'scientific_name': species.scientific_name,
                'score': match['score'],
                'match_type': match['match_type']
            })
        
        return suggestions
    
    def is_likely_same_species(self, name1: str, name2: str) -> bool:
        """
        Determine if two species names likely refer to the same species
        - Made more strict to avoid false positives
        
        Args:
            name1: First species name
            name2: Second species name
            
        Returns:
            True if likely the same species
        """
        norm1 = self._normalize_text(name1)
        norm2 = self._normalize_text(name2)
        
        # Check various matching criteria - more strict
        if norm1 == norm2:
            return True
        
        if self._is_synonym(norm1, norm2):
            return True
        
        # Only consider common name match if names are very similar
        common1 = self._extract_common_name(norm1)
        common2 = self._extract_common_name(norm2)
        if common1 == common2 and len(common1) > 10:  # Only for longer names
            return True
        
        # More strict fuzzy matching
        if self._fuzzy_match(norm1, norm2):
            return True
        
        return False
