# tariffhunter/ui/components/product_card.py
import streamlit as st
from typing import Dict

#OLD
def render(product: Dict):
    """Render a detailed product card with key metrics"""
    with st.container():
        st.subheader("Product Overview")
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Price", f"${product.get('price', 0):.2f}")
        with col2:
            st.metric("China Origin", 
                     product.get('made_in_china', 'Unknown'),
                     f"{product.get('confidence', 0)*100:.1f}% conf")
        with col3:
            st.metric("Tariff Risk", 
                     product.get('tariff_vulnerability', 'Unknown'),
                     "High risk" if product.get('made_in_china') == "Yes" else "Low risk")
        
        # Description section
        with st.expander("Product Description"):
            st.write(product.get('description', 'No description available'))
        
        # Origin details
        if product.get('made_in_china') == "Yes":
            st.warning("**China-Sourced Product** - High tariff vulnerability")
            if product.get('likely_province'):
                st.write(f"**Likely Production Region:** {product['likely_province'].title()}")
            if product.get('origin_phrases'):
                st.caption(f"Origin mentions: {product['origin_phrases']}")
        else:
            st.success("**Non-China Sourced** - Lower tariff risk")
            if product.get('likely_country'):
                st.write(f"**Likely Origin:** {product['likely_country']}")