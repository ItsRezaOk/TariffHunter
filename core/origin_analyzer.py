# tariffhunter/core/origin_analyzer.py
import re
import numpy as np
from geotext import GeoText
from sentence_transformers import SentenceTransformer, util
from typing import Dict, Optional
import torch
from sentence_transformers import util

class OriginAnalyzer:
    def __init__(self):

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu' #Use torch for GPU
    
        # Sentence transformer model to understand Human-English
        self.embedder = SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2',
            device=self.device
        )
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
        self.china_provinces = [
            'guangdong', 'zhejiang', 'jiangsu', 'shandong', 'fujian',
            'shanghai', 'beijing', 'tianjin', 'chongqing', 'sichuan'
        ]
        self.factory_keywords = ["factory", "manufacturer", "facility", "works", "plant"]
        self.supplier_keywords = ["supplier", "vendor", "distributor", "wholesaler"]
        
    def analyze_origin(self, title: str, description: str) -> Dict:
        """Comprehensive origin analysis with province/factory detection"""
        text = self._clean_text(f"{title} {description}")
        
        # 1. Enhanced China detection
        origin_result = self._detect_china_origin(text)
        
        # 2. Detect specific origin details
        details = {}
        if origin_result['made_in_china'] == "Yes":
            details.update(self._detect_chinese_details(text))
        else:
            details.update(self._detect_other_origin(text))
        
        return {**origin_result, **details}
    
    def _clean_text(self, text: str) -> str:
        """Normalize text for analysis"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text
    
    def _detect_china_origin(self, text: str) -> Dict:
        """Enhanced China detection with multiple indicators"""
        # Phrase-based detection
        china_phrases = [
            "made in china", "manufactured in china", "product of china",
            "shenzhen", "guangzhou", "yiwu", "chinese supplier",
            "factory in china", "produced in china"
        ]
    
        try:
            # Calculate similarity scores
            text_embedding = self.embedder.encode(text, convert_to_tensor=True)  # our text gets embedded using our Transformer
            phrase_embeddings = self.embedder.encode(china_phrases, convert_to_tensor=True) #phrases get embedded for comparason
        
            # Calculate cosine similarities
            similarities = util.cos_sim(text_embedding, phrase_embeddings)[0] # 1 if identical -1 if opposite
            max_similarity = float(torch.max(similarities)) #similatity becomes a list of the scores, picks the max score - closes china phrase matched
        
            # Backup Method - If Transformers dosnt work
            #Goes through phrases and looks for exact matches because they sometimes miss.
            keyword_score = sum(1 for kw in china_phrases if kw in text.lower()) / len(china_phrases)
        
            # Combined score (weighted average)
            combined_score = 0.7 * max_similarity + 0.3 * keyword_score #more importance on max_similarity
        
            # Determine result
            if combined_score > 0.65:
                return {"made_in_china": "Yes", "confidence": combined_score}
            elif combined_score > 0.4:
                return {"made_in_china": "Unclear", "confidence": combined_score}
            return {"made_in_china": "No", "confidence": 1-combined_score}
        
        except Exception as e:
            print(f"Error in similarity calculation: {e}")
            return {"made_in_china": "Unknown", "confidence": 0} #Error :(
    
   #Finding extra facts about our chinese products from (Title, description)
   #Main and more complex method of extraction, simpler detection of keywords is further below
    def _detect_chinese_details(self, text: str) -> Dict:
        """Extract specific details about Chinese origin"""
        # Detect province
        places = GeoText(text) #GeoText tries to find any country realted names in text
        province = next(
            (p.lower() for p in places.countries.get('cn', [])  #from results get places linked to cn (China)
            if p.lower() in self.china_provinces # make lowercase and find if its one of chinas main providences(from our list)
        ), None) #take first matching
        
        # Detect factory/supplier mentions
        factory_mentioned = any(kw in text for kw in self.factory_keywords) #checks out keyword lists if any supplier or factory is mentioned
        supplier_mentioned = any(kw in text for kw in self.supplier_keywords)
        
        # Extract origin phrases
        origin_phrases = self._extract_origin_phrases(text)
        
        # Estimate production type (OEM, ODM, etc.)
        production_type = self._detect_production_type(text)
        
        return {
            "likely_province": province,
            "factory_mentioned": factory_mentioned,
            "supplier_mentioned": supplier_mentioned,
            "origin_phrases": origin_phrases,
            "production_type": production_type,
            "supplier_tier": self._estimate_supplier_tier(text)
        }
    
    def _detect_other_origin(self, text: str) -> Dict:
        """Detect likely origin for non-China products"""
        countries = GeoText(text).countries #find any countries in the text
        if countries:
            # Return the first mentioned country that's not China IT: ["Milan"]
            for country, cities in countries.items(): # find country and city of this other supplier
                if country.lower() != 'cn':
                    return {
                        "likely_country": country,
                        "likely_cities": cities
                    }
        return {"likely_country": "Unknown"}
    
    def _extract_origin_phrases(self, text: str) -> Optional[str]:
        """Extract specific origin-related phrases from text"""
        patterns = [
            r"made in ([\w\s]+)", r"manufactured in ([\w\s]+)", #Regular Expression Patterns
            r"produced in ([\w\s]+)", r"factory in ([\w\s]+)", #([\w\s]+) multiple words, letters, and spaces
            r"origin:? ([\w\s]+)", r"sourced from ([\w\s]+)"
        ]
        matches = []
        for pattern in patterns: #for the 6 patterns
            matches.extend(re.findall(pattern, text, re.IGNORECASE)) #using regex find all the patterns, case insensetive
        return "; ".join(set(matches)) if matches else None #add all matches to the list seperated by ;
    

    #Simple detection for OEM and other keywords
    def _detect_production_type(self, text: str) -> str:
        """Estimate production relationship type"""
        if "oem" in text:
            return "OEM"
        if "odm" in text:
            return "ODM"
        if any(kw in text for kw in ["private label", "white label"]):
            return "Private Label"
        return "Unknown"
    
    #More simple detection
    def _estimate_supplier_tier(self, text: str) -> str:
        """Estimate supplier tier based on keywords"""
        if any(kw in text for kw in ["manufacturer", "factory"]):
            return "Tier 1 (Manufacturer)"
        if any(kw in text for kw in ["trading company", "export company"]):
            return "Tier 2 (Trading Company)"
        if any(kw in text for kw in ["distributor", "wholesaler"]):
            return "Tier 3 (Distributor)"
        return "Unknown"