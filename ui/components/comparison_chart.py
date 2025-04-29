# tariffhunter/ui/components/comparison_chart.py
import streamlit as st
import pandas as pd
from typing import Dict

#OLD
def render(product: Dict):
    """Render China vs. alternative sourcing comparison"""
    if product.get('made_in_china') != "Yes" or not product.get('country_comparisons'):
        st.info("No comparison available for non-China sourced products")
        return
    
    st.subheader("🇨🇳 China vs. Alternative Sourcing")
    
    # Prepare comparison data
    comparisons = []
    china_data = {
        "country": "China",
        "cost": product.get('price', 0) * 0.6,  # Assuming 60% of retail is COGS
        "lead_time": "2-4 weeks",
        "risk": "High"
    }
    comparisons.append(china_data)
    
    for country, data in product.get('country_comparisons', {}).items():
        comparisons.append({
            "country": country,
            "cost": data.get('estimated_cost', 0),
            "lead_time": data.get('lead_time', '4-6 weeks'),
            "risk": "Medium"
        })
    
    # Display comparison table
    df = pd.DataFrame(comparisons)
    st.dataframe(
        df.style.format({'cost': "${:.2f}"}),
        column_config={
            "country": "Country",
            "cost": "Unit Cost",
            "lead_time": "Lead Time",
            "risk": "Tariff Risk"
        },
        hide_index=True
    )
    
    # Visual comparison
    tab1, tab2 = st.tabs(["Cost Comparison", "Lead Time"])
    
    with tab1:
        st.bar_chart(df.set_index('country')['cost'])
    
    with tab2:
        # Convert lead time to numeric for visualization
        lead_time_df = df.copy()
        lead_time_df['lead_time_days'] = lead_time_df['lead_time'].apply(
            lambda x: int(x.split('-')[0]) * 7
        )
        st.bar_chart(lead_time_df.set_index('country')['lead_time_days'])