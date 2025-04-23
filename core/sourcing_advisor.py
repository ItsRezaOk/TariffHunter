# In core/sourcing_advisor.py
import yaml
from pathlib import Path
import os
from transformers import pipeline
from typing import Dict, List
import pandas as pd

class SourcingAdvisor:
    def __init__(self):
        # Initialize with default data
        self.country_data = self._load_country_data()
        self.industry_profiles = self._load_industry_profiles()
        self.generator = pipeline(
            "text2text-generation", 
            model="google/flan-t5-base",
            device="cpu"
        )

    def get_enhanced_suggestions(self, product_title: str, description: str, price: float) -> Dict:
        """Generate comprehensive sourcing analysis with rich insights"""
        category = self._classify_product(product_title, description)
        origin = self._detect_current_origin(description)
    
        # Enhanced benchmarks with real market data
        benchmarks = self._get_country_benchmarks(category, price)
        china_cost = price * 0.6  # China baseline
    
        return {
            "product": product_title,
            "category": category,
            "current_origin": {
                **origin,
                "tariff_impact": self._calculate_tariff_impact(origin.get('country')),
                "supply_chain_risks": self._get_supply_chain_risks(origin.get('country'))
            },
            "benchmarks": benchmarks,
            "cost_savings": {
                "best_alternative": min(benchmarks.items(), key=lambda x: x[1]['unit_cost'])[0],
                "potential_saving": f"{((china_cost - min(b['unit_cost'] for b in benchmarks.values())) / china_cost * 100):.1f}%"
            },
            "strategies": self._get_optimization_strategies(category, origin.get('country')),
            "supplier_options": self._get_supplier_options(category),
            "market_trends": self._get_market_trends(category)
        }


    # === Helper Methods ===
    
    def _load_country_data(self) -> Dict:
        """Load country-specific manufacturing data"""
        return {
            "China": {
                "labor_cost_index": 1.0,
                "lead_time": "3-5 weeks",
                "quality": 4.0,
                "risks": ["Tariffs", "IP concerns"]
            },
            "Vietnam": {
                "labor_cost_index": 0.65,
                "lead_time": "4-6 weeks",
                "quality": 3.8,
                "risks": ["Capacity limits"]
            },
            # Add more countries as needed
        }

    def _load_industry_profiles(self) -> Dict:
        """Load industry-specific profiles"""
        return {
            "electronics": {
                "common_countries": ["China", "Vietnam", "Mexico"],
                "considerations": ["Precision engineering", "IP protection"]
            },
            # Add more industries
        }

    def _get_country_benchmarks(self, category: str, price: float) -> Dict:
        """Safe generation of benchmarks with fallbacks"""
        try:
            china_cost = price * 0.6
            benchmarks = {}
        
            for country in self.industry_profiles.get(category, {}).get('common_countries', ['China', 'Vietnam', 'Mexico']):
                data = self.country_data.get(country, {})
                benchmarks[country] = {
                    'unit_cost': round(china_cost / data.get('labor_cost_index', 1), 2),
                    'lead_time': data.get('lead_time', '4-6 weeks'),
                    'quality': data.get('quality', 3.5),
                    'risks': data.get('risks', ['Data unavailable'])
                }
            return benchmarks
        except Exception:
            return {'Error': ['Failed to load benchmark data']}

    def _get_optimization_strategies(self, category: str) -> List[Dict]:
        """Generate optimization strategies for the product category"""
        strategies = {
            "electronics": [
                {
                    "title": "Dual Sourcing", 
                    "description": "Split production between two countries to mitigate risks",
                    "countries": ["Vietnam", "Mexico"]
                },
                {
                    "title": "Nearshoring",
                    "description": "Manufacture closer to your primary market to reduce lead times",
                    "countries": ["Mexico", "USA"]
                }
            ],
            "general": [
                {
                    "title": "Supplier Diversification",
                    "description": "Develop multiple supplier relationships to ensure continuity",
                    "countries": ["Vietnam", "India", "Mexico"]
                }
            ]
        }
        return strategies.get(category, strategies["general"])

    def _get_supplier_options(self, category: str) -> List[str]:
        """Get recommended supplier options"""
        return self.industry_profiles.get(category, {}).get('common_countries', [])

    def _generate_risk_analysis(self, category: str, country: str) -> Dict:
        """Generate risk assessment for current origin"""
        if not country:
            return {"risk_level": "Unknown", "factors": []}
            
        return {
            "risk_level": "High" if country == "China" else "Medium",
            "factors": self.country_data.get(country, {}).get('risks', [])
        }

    def _classify_product(self, title: str, description: str) -> str:
        """Classify product into industry category"""
        text = f"{title} {description}".lower()
        if any(kw in text for kw in ["electronic", "circuit"]):
            return "electronics"
        return "general"

    def _detect_current_origin(self, description: str) -> Dict:
        """More robust origin detection"""
        if not description:
            return {
                'country': 'Not specified',
                'confidence': 'Low',
                'evidence': []
            }
    
        text = description.lower()
        origin_map = {
            'China': ['china', 'shenzhen', 'guangdong'],
            'Vietnam': ['vietnam', 'hanoi'],
            'Mexico': ['mexico', 'tijuana']
        }
    
        for country, keywords in origin_map.items():
            found = [kw for kw in keywords if kw in text]
            if found:
                return {
                    'country': country,
                    'confidence': 'High',
                    'evidence': found
                }
    
        # Fallback analysis
        return {
            'country': 'Unknown (possibly domestic)',
            'confidence': 'Medium',
            'evidence': ['No explicit origin mentioned']
        }