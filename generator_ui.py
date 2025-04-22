import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import torch

# === Load Hugging Face Models ===
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model_name = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer)
# === Streamlit App ===
st.title("📦 TariffHunterGPT Dashboard")
st.subheader("🔍 Analyze or Create Product CSVs with AI Assistance")

option = st.radio("Select Mode:", ("Upload CSV", "Type Product Ideas"))

if option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload a classified CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        col1, col2 = st.columns(2)
        with col1:
            made_in_china_filter = st.selectbox("Filter by Made in China:", ["All", "Yes", "No", "Unclear"])
        with col2:
            vulnerability_filter = st.selectbox("Filter by Tariff Vulnerability:", ["All", "High", "Medium", "Low"])

        filtered_df = df.copy()
        if made_in_china_filter != "All":
            filtered_df = filtered_df[filtered_df["made_in_china"] == made_in_china_filter]
        if vulnerability_filter != "All":
            filtered_df = filtered_df[filtered_df["tariff_vulnerability"] == vulnerability_filter]

        st.dataframe(filtered_df)
        st.download_button("📥 Download Filtered Results", filtered_df.to_csv(index=False).encode('utf-8'), file_name="filtered_products.csv", mime='text/csv')

elif option == "Type Product Ideas":
    product_input = st.text_area("Enter product titles and descriptions (one per line):", height=250)
    process_btn = st.button("Analyze Products with AI")

    if process_btn and product_input:
        st.info("Running AI classification...")
        lines = product_input.strip().split("\n")
        results = []

        for line in lines:
            title = line.strip().split(" - ")[0] if " - " in line else line.strip()
            description = line.strip()
            price = 14.99  # default placeholder price

            # Step 1: Determine if it's made in China
            text = f"{title}. {description}"
            score = util.cos_sim(embedder.encode("Made in China"), embedder.encode(text)).item()

            if score > 0.6:
                made_in_china = "Yes"
                vulnerability = "High"
            elif 0.4 < score <= 0.6:
                made_in_china = "Unclear"
                vulnerability = "Medium"
            else:
                made_in_china = "No"
                vulnerability = "Low"

            # Step 2: Ask AI for sourcing suggestions
            prompt = f"Suggest 2 countries (not China) that could manufacture the following product cost-effectively:\n{title}\n{description}"
            alt_sourcing = generator(prompt, max_new_tokens=100)[0]['generated_text'].strip()

            results.append({
                "title": title,
                "description": description,
                "price": price,
                "made_in_china": made_in_china,
                "tariff_vulnerability": vulnerability,
                "alt_sourcing": alt_sourcing
            })

        df = pd.DataFrame(results)
        st.success("AI analysis complete!")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, file_name="ai_generated_products.csv", mime="text/csv")
