import pandas as pd
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline

# === Load Models ===
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
generator = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2", device_map="auto")

# === Output List ===
results = []

# === Stream CSV in Chunks ===
for chunk in pd.read_csv("products.csv", chunksize=10):
    for _, row in chunk.iterrows():
        title = str(row['title'])
        description = str(row['description'])
        price = float(row['price'])

        # Classify origin
        text = f"{title}. {description}"
        china_score = util.cos_sim(embedder.encode("Made in China"), embedder.encode(text)).item()

        if china_score > 0.6:
            made_in_china = "Yes"
            vulnerability = "High"
        elif 0.4 < china_score <= 0.6:
            made_in_china = "Unclear"
            vulnerability = "Medium"
        else:
            made_in_china = "No"
            vulnerability = "Low"

        # Recommend alternative sourcing countries
        prompt = f"""Product:
Title: {title}
Description: {description}

Suggest 2 countries (not China) that could manufacture this item cost-effectively.

Answer:"""
        suggestion = generator(prompt, max_new_tokens=100)[0]["generated_text"].split("Answer:")[-1].strip()

        results.append({
            "title": title,
            "price": price,
            "description": description,
            "made_in_china": made_in_china,
            "tariff_vulnerability": vulnerability,
            "alt_sourcing": suggestion
        })

# === Save to CSV ===
df = pd.DataFrame(results)
print(df)
df.to_csv("classified_products.csv", index=False)
print("\n✅ Results saved to classified_products.csv")
