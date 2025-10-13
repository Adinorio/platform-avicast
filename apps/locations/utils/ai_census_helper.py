"""
AI-Assisted Census Data Management using Local LLM (Ollama)
AGENTS.md: Local-first deployment, no external API calls

Requires Ollama installed locally: https://ollama.com
Recommended models: llama3.2, mistral, or phi3
"""

import json
import requests
from typing import Dict, List, Optional, Tuple


class OllamaHelper:
    """Helper class for local LLM interactions via Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Initialize Ollama helper
        
        Args:
            base_url: Ollama API endpoint (default: localhost)
            model: Model to use (default: llama3.2)
        """
        self.base_url = base_url
        self.model = model
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'].startswith(self.model) for m in models)
            return False
        except Exception:
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate text using local LLM
        
        Args:
            prompt: User prompt
            system_prompt: System instructions (optional)
        
        Returns:
            Generated text response
        """
        if not self.available:
            return "AI assistant unavailable. Please install and run Ollama."
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            return f"Error: {response.status_code}"
        
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"


class AICensusHelper:
    """AI-powered helper for census data management"""
    
    def __init__(self, model: str = "llama3.2"):
        """Initialize with specified model"""
        self.ollama = OllamaHelper(model=model)
    
    def is_available(self) -> bool:
        """Check if AI assistant is available"""
        return self.ollama.available
    
    def match_species_name(self, input_name: str, known_species: List[Dict]) -> Dict:
        """
        Use AI to match user input to known species names

        Args:
            input_name: Species name from user input
            known_species: List of known species dicts with 'name' and 'scientific_name'

        Returns:
            Dict with matched species and confidence
        """
        if not self.ollama.available:
            return {
                'matched': False,
                'species': None,
                'confidence': 0,
                'reason': 'AI unavailable'
            }

        # First try simple string matching without AI
        simple_match = self._simple_species_match(input_name, known_species)
        if simple_match['matched']:
            return simple_match

        # If no simple match, try AI matching
        species_list = "\n".join([
            f"- {s['name']} ({s['scientific_name']})"
            for s in known_species[:100]  # Increased limit for better matching
        ])

        prompt = f"""Given this bird species name from user input: "{input_name}"

I need you to match it to one of these known bird species. Be flexible with spelling and partial names:

{species_list}

Rules:
- Match partial names (e.g., "egret" could match "Chinese Egret")
- Be case-insensitive
- Consider common variations
- If no good match, return matched: false

Respond ONLY with JSON:
{{
  "matched": true/false,
  "species_name": "exact name from the list above",
  "confidence": 0.0-1.0,
  "reason": "brief explanation of the match"
}}"""

        system_prompt = "You are a bird species identification expert. Match user input to known species names, being flexible with partial names and common variations."

        response = self.ollama.generate(prompt, system_prompt)

        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                result = json.loads(response[json_start:json_end])

                # Find matching species from known list
                if result.get('matched'):
                    matched_species = next(
                        (s for s in known_species
                         if s['name'].lower() == result.get('species_name', '').lower()),
                        None
                    )
                    if matched_species:
                        result['species'] = matched_species
                    else:
                        result['species'] = None

                return result
        except Exception as e:
            return {
                'matched': False,
                'species': None,
                'confidence': 0,
                'reason': f'Parse error: {str(e)}'
            }

        return {
            'matched': False,
            'species': None,
            'confidence': 0,
            'reason': 'No valid response'
        }

    def _simple_species_match(self, input_name: str, known_species: List[Dict]) -> Dict:
        """
        Try simple string matching first before using AI
        """
        input_lower = input_name.lower().strip()

        for species in known_species:
            species_name_lower = species['name'].lower()

            # Exact match
            if input_lower == species_name_lower:
                return {
                    'matched': True,
                    'species': species,
                    'confidence': 1.0,
                    'reason': 'Exact match'
                }

            # Partial match (input is contained in species name)
            if input_lower in species_name_lower:
                return {
                    'matched': True,
                    'species': species,
                    'confidence': 0.8,
                    'reason': f'Partial match: "{input_name}" found in "{species["name"]}"'
                }

            # Scientific name match
            if 'scientific_name' in species and input_lower in species['scientific_name'].lower():
                return {
                    'matched': True,
                    'species': species,
                    'confidence': 0.9,
                    'reason': f'Scientific name match: "{input_name}" found in "{species["scientific_name"]}"'
                }

        return {
            'matched': False,
            'species': None,
            'confidence': 0,
            'reason': 'No simple match found'
        }
    
    def validate_census_data(self, data: Dict) -> Dict:
        """
        Use AI to validate census data entry
        
        Args:
            data: Census data dict with site, date, species, count, etc.
        
        Returns:
            Validation result with suggestions
        """
        if not self.ollama.available:
            return {
                'valid': True,
                'warnings': ['AI validation unavailable'],
                'suggestions': []
            }
        
        prompt = f"""Validate this bird census observation data:

Site: {data.get('site_name', 'Unknown')}
Date: {data.get('census_date', 'Unknown')}
Species: {data.get('species_name', 'Unknown')}
Count: {data.get('count', 0)}
Weather: {data.get('weather', 'Not specified')}

Check for:
1. Unusual bird counts (too high/low for species)
2. Date issues (future dates, weird patterns)
3. Missing important information
4. Potential data entry errors

Respond ONLY with JSON:
{{
  "valid": true/false,
  "warnings": ["list of warnings"],
  "suggestions": ["list of improvement suggestions"],
  "confidence": 0.0-1.0
}}"""
        
        system_prompt = "You are a wildlife census data quality expert."
        
        response = self.ollama.generate(prompt, system_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except Exception:
            pass
        
        return {
            'valid': True,
            'warnings': [],
            'suggestions': [],
            'confidence': 0.5
        }
    
    def interpret_excel_row(self, row_data: Dict, row_num: int) -> str:
        """
        Use AI to help interpret ambiguous Excel data
        
        Args:
            row_data: Row data from Excel
            row_num: Row number
        
        Returns:
            Interpretation/suggestion text
        """
        if not self.ollama.available:
            return "AI interpretation unavailable"
        
        prompt = f"""This is row {row_num} from a bird census Excel file:

{json.dumps(row_data, indent=2)}

Help interpret this data. Check for:
1. Are the species names correct?
2. Is the date format valid?
3. Are there any obvious errors?
4. What improvements would you suggest?

Provide a brief, helpful response (2-3 sentences)."""
        
        system_prompt = "You are a helpful assistant for wildlife census data entry."
        
        return self.ollama.generate(prompt, system_prompt)
    
    def suggest_data_corrections(self, errors: List[str]) -> List[str]:
        """
        Use AI to suggest corrections for import errors
        
        Args:
            errors: List of error messages
        
        Returns:
            List of suggested corrections
        """
        if not self.ollama.available or not errors:
            return []
        
        errors_text = "\n".join(errors[:10])  # Limit to first 10 errors
        
        prompt = f"""These errors occurred during census data import:

{errors_text}

For each error, suggest a specific fix. Be concise.

Format:
1. Error: [error message]
   Fix: [specific solution]"""
        
        system_prompt = "You are an expert at troubleshooting data import issues."
        
        response = self.ollama.generate(prompt, system_prompt)
        
        # Split response into suggestions
        suggestions = [
            line.strip() 
            for line in response.split('\n') 
            if line.strip().startswith('Fix:')
        ]
        
        return suggestions[:len(errors)]  # Return same number as errors
    
    def summarize_import_results(self, results: Dict) -> str:
        """
        Generate a natural language summary of import results
        
        Args:
            results: Import results dict
        
        Returns:
            Human-friendly summary
        """
        if not self.ollama.available:
            return f"Imported {results.get('successful', 0)} observations successfully."
        
        prompt = f"""Summarize these census data import results in a friendly way:

Total rows: {results.get('total_rows', 0)}
Successful: {results.get('successful', 0)}
Skipped: {results.get('skipped', 0)}
Census records created: {results.get('created_census', 0)}
Observations created: {results.get('created_observations', 0)}
Errors: {len(results.get('errors', []))}

Write a 2-3 sentence summary for the user."""
        
        system_prompt = "You are a helpful assistant explaining data import results."
        
        return self.ollama.generate(prompt, system_prompt)


# Singleton instance
_ai_helper = None


def get_ai_helper(model: str = "llama3.2") -> AICensusHelper:
    """Get or create AI helper singleton"""
    global _ai_helper
    if _ai_helper is None:
        _ai_helper = AICensusHelper(model=model)
    return _ai_helper


