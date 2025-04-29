# In core/sourcing_advisor.py
import yaml   #easily editable, readable, and clean data
from pathlib import Path #easier file paths
import os
from transformers import pipeline  #Hugging Face pre-trained AI models for Web Scraping
from typing import Dict, List
import pandas as pd  # For Data, Lists

class SourcingAdvisor:
    def __init__(self):
        # Initialize with default data
        self.country_data = self._load_country_data()
        self.industry_profiles = self._load_industry_profiles()
        self.generator = pipeline( #Use Hugging Face models
            "text2text-generation", 
            model="google/flan-t5-base",
            device="cpu"
        )


    def get_enhanced_suggestions(self, product_title: str, description: str, price: float) -> Dict:
        """Generate comprehensive sourcing suggestions"""
        self.current_category = self._classify_product(product_title, description) #gets product category
        origin = self._detect_current_origin(description) #country of origin
        category = self._classify_product(product_title, description) #reclassify - not optimized yet
    
        # Enhanced benchmarks with real market data
        benchmarks = self._get_country_benchmarks(category, price) #gets benchmarks of other places where product is made
        china_cost = price * 0.6  # China baseline - Shipping, tariffs, margins take 40% cost in China(avg)
    
        return {
            "product": product_title,
            "category": category,
            "current_origin": {
                **origin,
                "tariff_impact": self._calculate_tariff_impact(origin.get('country')), #how much tariffs might hurt the import
                "supply_chain_risks": self._get_supply_chain_risks(origin.get('country')) #possible instabilities
            },
            "benchmarks": benchmarks,
            "cost_savings": {
                "best_alternative": min(benchmarks.items(), key=lambda x: x[1]['unit_cost'])[0], #find lowest unit cost
                #savings by moving from china to an alternative as a %
                "potential_saving": f"{((china_cost - min(b['unit_cost'] for b in benchmarks.values())) / china_cost * 100):.1f}%"

            },
            "strategies": self._get_optimization_strategies(category, origin.get('country')), #AI generate actionable stratgies
            "supplier_options": self._get_supplier_options(category),
            # "market_trends": self._get_market_trends(category) ADD THIS
        }
##Final output example
# {
#   "product": "Smartphone Wireless Charger",
#   "category": "Electronics",
#   "current_origin": {
#     "country": "China",
#     "cities": ["Shenzhen"],
#     "tariff_impact": "High",
#     "supply_chain_risks": ["Tariffs", "Political Tensions"]
#   },
#   "benchmarks": {
#     "Vietnam": {"unit_cost": 12.0, "labor_score": 7.0},
#     "Mexico": {"unit_cost": 13.5, "labor_score": 6.5}
#   },
#   "cost_savings": {
#     "best_alternative": "Vietnam",
#     "potential_saving": "20.0%"
#   },
#   "strategies": ["Diversify suppliers across Vietnam", "Negotiate contracts for lower risk exposure"],
#   "supplier_options": ["OEM wireless charger manufacturers"]
# }


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
            #working on making this AI automated
        }

    def _load_industry_profiles(self) -> Dict:
        """Load industry-specific profiles"""
        return {
            "electronics": {
                "common_countries": ["China", "Vietnam", "Mexico"],
                "considerations": ["Precision engineering", "IP protection"]
            },
            # Working on making this AI automated
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

    def _get_optimization_strategies(self, category, country: str) -> List[Dict]:
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
        return self.industry_profiles.get(category, {}).get('common_countries', []) #Get industry category from YAML
    #common_countries from category info

    def _generate_risk_analysis(self, category: str, country: str) -> Dict:
        """Generate risk assessment for current origin"""
        if not country:
            return {"risk_level": "Unknown", "factors": []}
         #WILL UPDATE: for now this is very simple and just give higher risk to china. As tariffs settle, this will be updated
        return {
            "risk_level": "High" if country == "China" else "Medium",
            "factors": self.country_data.get(country, {}).get('risks', [])
        }

    def _classify_product(self, title: str, description: str) -> str:
        """Classify product into industry category"""
        text = f"{title} {description}".lower() #title description in lowercase
        if any(kw in text for kw in ["electronic", "circuit"]): #finds keywords
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
    
    def _calculate_tariff_impact(self, country: str) -> str:
        """Calculate tariff impact based on country and product type"""
        if not country:
            return "Unknown (origin not specified)"
    
        # Basic tariff rates by country
        tariff_rates = {
            "China": {"electronics": 0.25, "textiles": 0.15, "default": 0.20},
            "Vietnam": {"electronics": 0.10, "textiles": 0.05, "default": 0.07},
            "Mexico": {"electronics": 0.00, "textiles": 0.00, "default": 0.00},
            "default": 0.10
        }
    
        #Get the appropriate rate
        country_rates = tariff_rates.get(country, tariff_rates["default"])
        if isinstance(country_rates, dict):
            rate = country_rates.get(self.current_category, country_rates["default"])
        else:
            rate = country_rates
    
        return f"{rate*100:.1f}% estimated tariff"
    
    def _get_supply_chain_risks(self, country: str) -> List[str]:
        """Get supply chain risks for a country"""
        risk_db = {
            "China": ["Tariff volatility", "IP protection concerns"],
            "Vietnam": ["Capacity constraints", "Port congestion"],
            "Mexico": ["Border delays", "Cartel activity"],
            "default": ["Standard international shipping risks"]
        }
        return risk_db.get(country, risk_db["default"])

    def _classify_product(self, title: str, description: str) -> str:
        """Enhanced product categorization"""
        text = f"{title} {description}".lower()
        if any(kw in text for kw in ["electronic", "circuit", "battery"]):
            return "electronics"
        if any(kw in text for kw in ["fabric", "textile", "garment"]):
            return "textiles"
        return "general"