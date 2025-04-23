import streamlit as st
import pandas as pd
from core.origin_analyzer import OriginAnalyzer
from core.sales_analyzer import SalesAnalyzer
from core.sourcing_advisor import SourcingAdvisor
from ui.components import product_card, comparison_chart
# In tariffhunter/ui/dashboard.py


def main():
    st.set_page_config(layout="wide")
    
    # Initialize services
    origin_analyzer = OriginAnalyzer()
    sales_analyzer = SalesAnalyzer()
    sourcing_advisor = SourcingAdvisor()
    
    st.title("🛡️ TariffHunterGPT - Product Intelligence Dashboard")
    st.markdown("### AI-powered supply chain risk analysis")
    
    # Input section
    with st.expander("📥 Add Products", expanded=True):
        input_method = st.radio(
            "Input method:",
            ["Upload CSV", "Enter Manually", "Import from Amazon"],
            horizontal=True
        )
        
        if input_method == "Upload CSV":
            uploaded_file = st.file_uploader("Upload product CSV", type=["csv"])
            if uploaded_file:
                products = pd.read_csv(uploaded_file).to_dict('records')
        
        elif input_method == "Enter Manually":
            product_input = st.text_area("Enter product details (one per line)")
            if st.button("Analyze"):
                products = [{"title": line, "description": line} for line in product_input.split("\n")]
        
        elif input_method == "Import from Amazon":
            urls = st.text_area("Enter Amazon product URLs (one per line)")
            if st.button("Fetch"):
                products = [{"url": url} for url in urls.split("\n")]
    
    # Analysis section
    if 'products' in locals():
        with st.spinner("🔍 Analyzing products..."):
            results = []
            for product in products:
                # Run all analyses
                origin = origin_analyzer.analyze_origin(product.get('title', ''), product.get('description', ''))
                sales = sales_analyzer.estimate_metrics(product)
                sourcing = sourcing_advisor.get_sourcing_suggestions(
                    product.get('title', ''),
                    product.get('description', ''),
                    product.get('price', 0)
                )
                
                # Combine results
                result = {
                    **product,
                    **origin,
                    **sales,
                    **sourcing,
                    "tariff_risk": self._calculate_tariff_risk(origin, sales)
                }
                results.append(result)
        
        # Display results
        st.success("Analysis complete!")
        
        # Summary view
        st.subheader("Product Summary")
        cols = st.columns(3)
        cols[0].metric("Products Analyzed", len(results))
        cols[1].metric("High Risk", len([r for r in results if r['tariff_risk'] == "High"]))
        cols[2].metric("Recommended Alternatives", len([r for r in results if r['made_in_china'] == "Yes"]))
        
        # Detailed product views
        for product in results:
            with st.expander(f"📦 {product.get('title', 'Untitled Product')}"):
                product_card.render(product)
                
                # Comparison section
                st.subheader("China vs Alternative Sourcing")
                comparison_chart.render(product)
                
                # Sourcing recommendations
                st.subheader("Recommended Sourcing Strategy")
                st.write(product['ai_suggestions'])
                
                # Download button for individual product
                st.download_button(
                    label=f"Download {product.get('title', 'product')} Report",
                    data=pd.DataFrame([product]).to_csv(index=False),
                    file_name=f"tariffhunter_{product.get('title', 'product')}.csv"
                )
        
        # Bulk download
        st.download_button(
            "Download All Results",
            pd.DataFrame(results).to_csv(index=False),
            "tariffhunter_full_report.csv"
        )

if __name__ == "__main__":
    main()