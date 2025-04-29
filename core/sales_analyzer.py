# tariffhunter/core/sales_analyzer.py
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from bs4 import BeautifulSoup # Useful for scraping product data from Amazon pages
import requests #download Amazon product pages

#Estimate sales of products
class SalesAnalyzer:
    def __init__(self):
        # Amazon BSR to estimated sales mapping (simplified)
        self.bsr_to_sales = {
            (1, 100): 10000,
            (101, 1000): 5000,
            (1001, 5000): 2500,
            (5001, 10000): 1000,
            (10001, 50000): 500,
            (50001, 100000): 250,
            (100001, 500000): 100,
            (500001, float('inf')): 50
        }
        
    def estimate_metrics(self, product_data: Dict) -> Dict:
        """Estimate sales metrics with fallback to mock data"""
        if product_data.get('url', '').startswith(('http://', 'https://')): #try to get url from product_data dictionary
            try:
                return self._scrape_ecommerce_data(product_data['url']) #scrape the data
            except Exception as e:
                print(f"Scraping failed: {e}")
                
        return self._generate_mock_data(product_data) #For testing and Demos if product has no URL
    
    def _scrape_ecommerce_data(self, url: str) -> Dict:
        """Scrape e-commerce site for product metrics"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" #Fake Browser signature
        }
        response = requests.get(url, headers=headers, timeout=10) #Download HTML, use Fake Browser Headers
        soup = BeautifulSoup(response.text, 'html.parser') #Turn raw HTML into searchable data
        
        # Amazon-specific selectors (would need customization per site)
        price = self._extract_price(soup) #Extract Price
        bsr = self._extract_bsr(soup) #Extract BSR
        reviews = self._extract_reviews(soup) #Extract Reviews
        
        return {
            "current_price": price,
            "best_seller_rank": bsr,
            "estimated_monthly_sales": self._estimate_from_bsr(bsr),
            "review_count": reviews['count'],
            "average_rating": reviews['rating'],
            "price_history": self._generate_price_history(price),
            "in_stock": self._check_stock_status(soup)
        }
    
    def _generate_mock_data(self, product: Dict) -> Dict:
        """Generate realistic mock data based on product attributes"""
        # Base values influenced by product category
        #ONLY FOR DEMOS AND READIBILITY FOR NOW
        category = self._guess_category(product.get('title', ''), product.get('description', ''))
        base_bsr, price_multiplier = self._get_category_baselines(category)
        
        # Generate realistic values around the baseline
        bsr = max(1, int(np.random.normal(base_bsr, base_bsr/2)))
        price = product.get('price', random.uniform(10, 200) * price_multiplier)
        
        return {
            "current_price": round(price, 2),
            "best_seller_rank": bsr,
            "estimated_monthly_sales": self._estimate_from_bsr(bsr),
            "review_count": random.randint(0, 10000),
            "average_rating": round(random.uniform(3.0, 5.0), 1),
            "price_history": self._generate_price_history(price),
            "in_stock": random.choice([True, False])
        }
    
    def _guess_category(self, title: str, description: str) -> str:
        """Guess product category from text"""
        text = f"{title} {description}".lower()
        #Finds Keywords to get a category in mind
        if any(kw in text for kw in ["electronic", "cable", "charger"]):
            return "electronics"
        elif any(kw in text for kw in ["clothing", "shirt", "dress"]):
            return "apparel"
        elif any(kw in text for kw in ["home", "kitchen", "decor"]):
            return "home"
        elif any(kw in text for kw in ["toy", "game", "play"]):
            return "toys"
        return "general"
    
    def _get_category_baselines(self, category: str) -> tuple:
        """Return typical BSR and price multiplier for category"""
        baselines = {
            "electronics": (5000, 1.2),
            "apparel": (10000, 1.0),
            "home": (8000, 1.1),
            "toys": (15000, 0.9),
            "general": (20000, 1.0)
        }
        return baselines.get(category, (20000, 1.0))
    
    def _estimate_from_bsr(self, bsr: int) -> int:
        """Estimate monthly sales from best seller rank"""
        for (min_bsr, max_bsr), sales in self.bsr_to_sales.items():
            if min_bsr <= bsr <= max_bsr:
                return sales + random.randint(-sales//10, sales//10) #Randomizes + or - 10%... Yeah this has to be changed eventually
        return 50 #need to be more accurate for products not in BSR...
    
    def _generate_price_history(self, current_price: float) -> List[Dict]:
        """Generate realistic price history"""
        history = [] #each months price
        base_date = datetime.now() #Todays date
        
        for i in range(6, 0, -1):  # Last 6 months Price data
            date = (base_date - timedelta(days=30*i)).strftime("%Y-%m") #calculates days for each month
            # Price fluctuates ±20% with general trend... NEEDS TO BE REAL, just for demos for now
            fluctuation = random.uniform(0.8, 1.2)
            if i > 3:  # Older prices trend slightly different
                fluctuation *= random.uniform(0.9, 1.1)
            price = round(current_price * fluctuation, 2)
            history.append({"date": date, "price": price})
        
        # Add current price
        history.append({"date": base_date.strftime("%Y-%m"), "price": current_price})
        return history
    
    # Future (Better) Scraping Methods
    def _extract_price(self, soup: BeautifulSoup) -> float: ...
    def _extract_bsr(self, soup: BeautifulSoup) -> int: ...
    def _extract_reviews(self, soup: BeautifulSoup) -> Dict: ...
    def _check_stock_status(self, soup: BeautifulSoup) -> bool: ...