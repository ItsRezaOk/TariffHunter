# tariffhunter/core/origin_analyzer.py
import re
import numpy as np
from geotext import GeoText
from sentence_transformers import SentenceTransformer, util
from typing import Dict, Optional

class OriginAnalyzer:
    def __init__(self):
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
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
        
        # Calculate similarity scores
        embeddings = self.embedder.encode([text] + china_phrases)
        similarities = util.cos_sim(embeddings[0], embeddings[1:])
        max_similarity = max(similarities).item()
        
        # Additional keyword indicators
        keyword_score = sum(1 for kw in china_phrases if kw in text) / len(china_phrases)
        
        # Combined score (weighted average)
        combined_score = 0.7 * max_similarity + 0.3 * keyword_score
        
        # Determine result
        if combined_score > 0.65:
            return {"made_in_china": "Yes", "confidence": combined_score}
        elif combined_score > 0.4:
            return {"made_in_china": "Unclear", "confidence": combined_score}
        return {"made_in_china": "No", "confidence": 1-combined_score}
    
    def _detect_chinese_details(self, text: str) -> Dict:
        """Extract specific details about Chinese origin"""
        # Detect province
        places = GeoText(text)
        province = next(
            (p.lower() for p in places.countries.get('cn', []) 
            if p.lower() in self.china_provinces
        ), None)
        
        # Detect factory/supplier mentions
        factory_mentioned = any(kw in text for kw in self.factory_keywords)
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
        countries = GeoText(text).countries
        if countries:
            # Return the first mentioned country that's not China
            for country, cities in countries.items():
                if country.lower() != 'cn':
                    return {
                        "likely_country": country,
                        "likely_cities": cities
                    }
        return {"likely_country": "Unknown"}
    
    def _extract_origin_phrases(self, text: str) -> Optional[str]:
        """Extract specific origin-related phrases from text"""
        patterns = [
            r"made in ([\w\s]+)", r"manufactured in ([\w\s]+)",
            r"produced in ([\w\s]+)", r"factory in ([\w\s]+)",
            r"origin:? ([\w\s]+)", r"sourced from ([\w\s]+)"
        ]
        matches = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, text, re.IGNORECASE))
        return "; ".join(set(matches)) if matches else None
    
    def _detect_production_type(self, text: str) -> str:
        """Estimate production relationship type"""
        if "oem" in text:
            return "OEM"
        if "odm" in text:
            return "ODM"
        if any(kw in text for kw in ["private label", "white label"]):
            return "Private Label"
        return "Unknown"
    
    def _estimate_supplier_tier(self, text: str) -> str:
        """Estimate supplier tier based on keywords"""
        if any(kw in text for kw in ["manufacturer", "factory"]):
            return "Tier 1 (Manufacturer)"
        if any(kw in text for kw in ["trading company", "export company"]):
            return "Tier 2 (Trading Company)"
        if any(kw in text for kw in ["distributor", "wholesaler"]):
            return "Tier 3 (Distributor)"
        return "Unknown"