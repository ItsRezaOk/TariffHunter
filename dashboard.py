import streamlit as st
import pandas as pd

# === Load Data ===
st.title("📦 TariffHunterGPT Dashboard")
st.subheader("🧠 AI Analysis of Product Tariff Vulnerability")

uploaded_file = st.file_uploader("Upload a classified CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        made_in_china_filter = st.selectbox(
            "Filter by Made in China:", ["All", "Yes", "No", "Unclear"]
        )

    with col2:
        vulnerability_filter = st.selectbox(
            "Filter by Tariff Vulnerability:", ["All", "High", "Medium", "Low"]
        )

    filtered_df = df.copy()

    if made_in_china_filter != "All":
        filtered_df = filtered_df[filtered_df["made_in_china"] == made_in_china_filter]

    if vulnerability_filter != "All":
        filtered_df = filtered_df[filtered_df["tariff_vulnerability"] == vulnerability_filter]

    # Table View
    st.dataframe(filtered_df)

    # Download Button
    st.download_button(
        "📥 Download Filtered Results",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name="filtered_products.csv",
        mime='text/csv'
    )
