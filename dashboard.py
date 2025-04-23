# tariffhunter/ui/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict
from pathlib import Path

# Import our core analyzers
from tariffhunter.core.origin_analyzer import OriginAnalyzer
from tariffhunter.core.sales_analyzer import SalesAnalyzer
from tariffhunter.core.sourcing_advisor import SourcingAdvisor

# Set page config
st.set_page_config(
    page_title="TariffHunterGPT",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize analyzers
    origin_analyzer = OriginAnalyzer()
    sales_analyzer = SalesAnalyzer()
    sourcing_advisor = SourcingAdvisor()
    
    # Page header
    st.title("🛡️ TariffHunterGPT")
    st.markdown("### AI-powered Product Sourcing Risk Analysis")
    
    # Sidebar with filters and info
    with st.sidebar:
        st.header("Analysis Options")
        analysis_mode = st.radio(
            "Analysis Mode",
            ["Single Product", "Bulk CSV"],
            help="Analyze one product at a time or upload a CSV for bulk analysis"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        TariffHunterGPT helps identify products vulnerable to tariffs 
        and suggests alternative sourcing strategies.
        """)
    
    # Main content area
    if analysis_mode == "Single Product":
        analyze_single_product(origin_analyzer, sales_analyzer, sourcing_advisor)
    else:
        analyze_bulk_products(origin_analyzer, sales_analyzer, sourcing_advisor)

def analyze_single_product(origin_analyzer, sales_analyzer, sourcing_advisor):
    """Interface for analyzing a single product"""
    with st.expander("📝 Enter Product Details", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Product Title", placeholder="Bluetooth Wireless Earbuds")
            price = st.number_input("Price (USD)", min_value=0.0, value=19.99)
            url = st.text_input("Product URL (optional)", placeholder="https://www.amazon.com/...")
        
        with col2:
            description = st.text_area(
                "Product Description",
                placeholder="High-quality stereo earbuds with noise cancellation...",
                height=150
            )
            categories = ["Electronics", "Apparel", "Home Goods", "Toys", "Other"]
            category = st.selectbox("Product Category (optional)", ["Auto-detect"] + categories)
    
    if st.button("Analyze Product", type="primary"):
        with st.spinner("🔍 Analyzing product..."):
            # Prepare product data
            product_data = {
                "title": title,
                "description": description,
                "price": price,
                "url": url,
                "category": category if category != "Auto-detect" else None
            }
            
            # Run all analyses
            origin = origin_analyzer.analyze_origin(title, description)
            sales = sales_analyzer.estimate_metrics(product_data)
            sourcing = sourcing_advisor.get_sourcing_suggestions(title, description, price)
            
            # Combine results
            result = {
                **product_data,
                **origin,
                **sales,
                **sourcing,
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Display results
            display_product_results(result)

def analyze_bulk_products(origin_analyzer, sales_analyzer, sourcing_advisor):
    """Interface for bulk CSV analysis"""
    st.info("📁 Upload a CSV file with product data. Required columns: title, description, price")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        accept_multiple_files=False
    )
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success(f"Successfully loaded {len(df)} products")
        
        # Show sample of the data
        with st.expander("View Uploaded Data"):
            st.dataframe(df.head())
        
        if st.button("Analyze All Products", type="primary"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, row in df.iterrows():
                # Update progress
                progress = int((i + 1) / len(df) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Analyzing product {i + 1} of {len(df)}...")
                
                # Run analyses
                origin = origin_analyzer.analyze_origin(row['title'], row['description'])
                sales = sales_analyzer.estimate_metrics(row.to_dict())
                sourcing = sourcing_advisor.get_sourcing_suggestions(
                    row['title'], 
                    row['description'], 
                    row.get('price', 0)
                )
                
                # Combine results
                result = {
                    **row.to_dict(),
                    **origin,
                    **sales,
                    **sourcing,
                    "analyzed_at": datetime.now().isoformat()
                }
                results.append(result)
            
            # Analysis complete
            progress_bar.empty()
            status_text.empty()
            st.success("Analysis complete!")
            
            # Convert to DataFrame
            results_df = pd.DataFrame(results)
            
            # Show summary stats
            show_summary_statistics(results_df)
            
            # Show full results
            with st.expander("View Full Analysis Results"):
                st.dataframe(results_df)
            
            # Download button
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Full Analysis",
                data=csv,
                file_name="tariffhunter_analysis.csv",
                mime="text/csv"
            )

def display_product_results(result: Dict):
    """Display detailed results for a single product"""
    st.markdown("---")
    st.markdown(f"## 📋 Analysis Report: {result['title']}")
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("China Origin Likelihood", 
                 f"{result.get('made_in_china', 'Unknown')}",
                 f"{result.get('confidence', 0)*100:.1f}% confidence")
    with col2:
        st.metric("Tariff Risk", 
                 "High" if result.get('made_in_china') == "Yes" else "Low",
                 "Consider alternatives" if result.get('made_in_china') == "Yes" else "Low risk")
    with col3:
        st.metric("Estimated Monthly Sales", 
                 f"{result.get('estimated_monthly_sales', 'N/A')}",
                 f"BSR: {result.get('best_seller_rank', 'N/A')}")
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🛃 Origin Analysis", 
        "📊 Sales Metrics", 
        "🌍 Sourcing Alternatives",
        "📈 Full Data"
    ])
    
    with tab1:
        display_origin_analysis(result)
    
    with tab2:
        display_sales_metrics(result)
    
    with tab3:
        display_sourcing_alternatives(result)
    
    with tab4:
        st.json(result, expanded=False)
        
    # Download button for this product
    csv = pd.DataFrame([result]).to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download This Analysis",
        data=csv,
        file_name=f"tariffhunter_{result['title'][:20]}.csv",
        mime="text/csv"
    )

def display_origin_analysis(result: Dict):
    """Display origin analysis details"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Origin Details")
        if result.get('made_in_china') == "Yes":
            st.success("**Likely Manufactured in China**")
            if result.get('likely_province'):
                st.markdown(f"**Probable Province:** {result['likely_province'].title()}")
            if result.get('factory_mentioned'):
                st.markdown("✅ Factory/supplier mentioned in description")
            if result.get('origin_phrases'):
                st.markdown("**Origin Phrases Found:**")
                st.write(result['origin_phrases'])
        else:
            st.info("**Not Likely Manufactured in China**")
            if result.get('likely_country') and result['likely_country'] != "Unknown":
                st.markdown(f"**Possible Origin:** {result['likely_country']}")
    
    with col2:
        st.markdown("### Production Details")
        if result.get('production_type'):
            st.markdown(f"**Production Type:** {result['production_type']}")
        if result.get('supplier_tier'):
            st.markdown(f"**Supplier Tier:** {result['supplier_tier']}")
        
        # Confidence indicator
        confidence = result.get('confidence', 0)
        st.markdown(f"**Analysis Confidence:** {confidence*100:.1f}%")
        st.progress(int(confidence * 100))

def display_sales_metrics(result: Dict):
    """Display sales and performance metrics"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Sales Performance")
        st.metric("Current Price", f"${result.get('price', 0):.2f}")
        st.metric("Estimated Monthly Sales", result.get('estimated_monthly_sales', 'N/A'))
        st.metric("Best Seller Rank", result.get('best_seller_rank', 'N/A'))
    
    with col2:
        st.markdown("### Customer Feedback")
        st.metric("Average Rating", 
                 f"{result.get('average_rating', 'N/A')} ⭐",
                 f"{result.get('review_count', 0)} reviews")
        
        # Price history chart would go here
        if result.get('price_history'):
            st.markdown("**Price History (Last 6 Months)**")
            price_df = pd.DataFrame(result['price_history'])
            st.line_chart(price_df.set_index('date')['price'])

def display_sourcing_alternatives(result: Dict):
    """Display sourcing recommendations"""
    st.markdown("### Recommended Alternative Sourcing Countries")
    
    if result.get('made_in_china') != "Yes":
        st.info("This product doesn't appear to be China-sourced. No alternatives needed.")
        return
    
    # Show country comparisons
    if result.get('country_comparisons'):
        st.markdown("#### Cost Comparison")
        comparisons = []
        for country, data in result['country_comparisons'].items():
            comparisons.append({
                "Country": country,
                "Estimated Cost": f"${data['estimated_cost']:.2f}",
                "Lead Time": data['lead_time'],
                "Labor Cost Index": f"{data['labor_cost_index']*100:.0f}% of China"
            })
        st.table(pd.DataFrame(comparisons))
    
    # Show AI analysis
    if result.get('ai_analysis'):
        st.markdown("#### Detailed Analysis")
        st.write(result['ai_analysis'])
    
    # Show key considerations
    if result.get('key_considerations'):
        st.markdown("#### Key Considerations")
        for consideration in result['key_considerations']:
            st.markdown(f"- {consideration}")

def show_summary_statistics(df: pd.DataFrame):
    """Show summary stats for bulk analysis"""
    st.markdown("## 📊 Analysis Summary")
    
    # Calculate stats
    total_products = len(df)
    china_products = len(df[df['made_in_china'] == "Yes"])
    high_risk = len(df[(df['made_in_china'] == "Yes") & (df['tariff_vulnerability'] == "High")])
    
    # Display stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Products", total_products)
    col2.metric("China-Sourced", china_products, f"{china_products/total_products*100:.1f}%")
    col3.metric("High Tariff Risk", high_risk, f"{high_risk/china_products*100:.1f}%" if china_products else "N/A")
    
    # Show charts
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Origin Breakdown")
        origin_counts = df['made_in_china'].value_counts()
        st.bar_chart(origin_counts)
    
    with col2:
        st.markdown("### Risk Profile")
        if 'tariff_vulnerability' in df:
            risk_counts = df['tariff_vulnerability'].value_counts()
            st.bar_chart(risk_counts)

if __name__ == "__main__":
    main()