# In core/sourcing_advisor.py
import os
from pathlib import Path

class SourcingAdvisor:
    def __init__(self):
        # Get the directory of the current file
        current_dir = Path(__file__).parent
        
        # Define the path to the YAML file
        # In core/sourcing_advisor.py
        profiles_path = Path(__file__).resolve().parent.parent / 'data' / 'industry_profiles' / 'sourcing_profiles.yaml'
        
        # Create default profiles if file doesn't exist
        if not profiles_path.exists():
            os.makedirs(profiles_path.parent, exist_ok=True)
            self.industry_profiles = self._create_default_profiles()
            # Optionally save the default profiles
            # with open(profiles_path, 'w') as f:
            #     yaml.dump(self.industry_profiles, f)
        else:
            with open(profiles_path) as f:
                self.industry_profiles = yaml.safe_load(f) or {}
        
        # Rest of your __init__ code...

    def _create_default_profiles(self):
        """Create default industry profiles if YAML file doesn't exist"""
        return {
            "general": {
                "name": "General Products",
                "common_alternatives": ["Vietnam", "India", "Mexico"],
                "labor_cost_index": 0.8,
                "lead_time": "4-6 weeks",
                "considerations": [
                    "General manufacturing capabilities required",
                    "Moderate quality expectations"
                ]
            }
        }