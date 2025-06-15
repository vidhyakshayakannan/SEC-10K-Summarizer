import streamlit as st
import re
from sec_api import ExtractorApi
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

SEC_API_KEY = os.getenv("SEC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# Configure the Google Gemini client
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Function to clean text
def clean_text(text):
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

# Function to split text into smaller chunks
def split_text(text, chunk_size):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Function to summarize text chunks
def summarize_text_chunks(text_chunks):
    summaries = []
    for i, chunk in enumerate(text_chunks):
        prompt = (
            f"I collected some SEC filing data and want to summarize it. "
            f"Please summarize and output 10 bullet points only. "
            f"Do not say 'bullet points' in your answer. Make sure it's well formatted and easy to understand. "
            f"The relevant information is below:\n\n{chunk}"
        )
        print(f"Generating summary for Chunk {i + 1}")
        try:
            response = model.generate_content(prompt)
            summaries.append(response.text.strip())
        except Exception as e:
            summaries.append(f"[Error generating summary: {e}]")
    return summaries

# Initialize SEC Extractor API
extractorApi = ExtractorApi(SEC_API_KEY)

# Streamlit UI
st.title("SEC Filing Summarization App")

# User input for filing URL
filing_url = st.text_input("Enter the SEC filing URL:")

# Section selection
sections_dict = {
    "1": "Business",
    "1A": "Risk Factors",
    "1B": "Unresolved Staff Comments",
    "6": "Selected Financial Data",
    "7": "Management's Discussion and Analysis",
    "7A": "Market Risk Disclosures",
    "8": "Financial Statements",
    "9": "Accounting Disagreements"
}

# Create a list of "Section X: Name" labels for display
section_labels = [f"Section {k}: {v}" for k, v in sections_dict.items()]
section_keys = list(sections_dict.keys())

# Display the dropdown and get the index of the selected item
selected_index = st.selectbox("Select SEC filing section:", range(len(section_labels)), format_func=lambda i: section_labels[i])

# Retrieve actual section key and label
selected_key = section_keys[selected_index]
selected_label = sections_dict[selected_key]

if st.button("Summarize"):
    if filing_url:
        try:
            section_text = extractorApi.get_section(filing_url, selected_key, 'text')
            cleaned_text = clean_text(section_text)
            chunk_size = 40000
            text_chunks = split_text(cleaned_text, chunk_size)

            summaries = summarize_text_chunks(text_chunks)

            st.subheader(f"Summary of Section {selected_key} - {selected_label}")
            for i, summary in enumerate(summaries, 1):
                st.markdown(f"**Chunk {i}:**")
                st.write(summary)
        except Exception as e:
            st.error(f"Error occurred while processing: {e}")
    else:
        st.warning("Please enter a valid SEC filing URL.")
