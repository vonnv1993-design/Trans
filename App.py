# app.py
import streamlit as st
import requests
import json
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Vietnamese-English Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextArea textarea {
        font-size: 16px;
    }
    .output-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 10px 0;
    }
    .title-text {
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle-text {
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="title-text">🌐 Vietnamese-English Translator</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Translate and Summarize Content with AI</p>', unsafe_allow_html=True)

# API Configuration
API_ENDPOINT = "https://llm.blackbox.ai/chat/completions"
API_HEADERS = {
    "customerId": "cus_T4SotOIhxreJbK",
    "Content-Type": "application/json",
    "Authorization": "Bearer xxx"
}
MODEL_NAME = "openrouter/claude-sonnet-4"

def call_llm_api(prompt, system_prompt):
    """Call the LLM API for translation or summarization"""
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(
            API_ENDPOINT,
            headers=API_HEADERS,
            json=payload,
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"Error: API returned status code {response.status_code}"
    
    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

def translate_text(text, source_lang, target_lang):
    """Translate text between Vietnamese and English"""
    system_prompt = f"""You are a professional translator specializing in {source_lang} to {target_lang} translation.
    Provide accurate, natural-sounding translations that preserve the meaning and tone of the original text.
    Only return the translated text without any explanations or additional comments."""
    
    user_prompt = f"Translate the following text from {source_lang} to {target_lang}:\n\n{text}"
    
    return call_llm_api(user_prompt, system_prompt)

def summarize_text(text, language):
    """Summarize the given text"""
    system_prompt = f"""You are an expert at summarizing content in {language}.
    Create concise, informative summaries that capture the key points and main ideas.
    Only return the summary without any explanations or additional comments."""
    
    user_prompt = f"Summarize the following text in {language}:\n\n{text}"
    
    return call_llm_api(user_prompt, system_prompt)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    translation_direction = st.radio(
        "Translation Direction",
        ["Vietnamese → English", "English → Vietnamese"],
        index=0
    )
    
    st.divider()
    
    enable_summary = st.checkbox("Enable Summarization", value=True)
    
    if enable_summary:
        summary_language = st.selectbox(
            "Summary Language",
            ["Same as target language", "Same as source language", "Both languages"]
        )
    
    st.divider()
    
    st.markdown("### 📚 Instructions")
    st.markdown("""
    1. Select translation direction
    2. Enter or paste your text
    3. Click 'Translate' button
    4. View translation and summary
    5. Export results as needed
    """)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Input Text")
    
    # Determine source and target languages
    if translation_direction == "Vietnamese → English":
        source_lang = "Vietnamese"
        target_lang = "English"
        placeholder_text = "Nhập văn bản tiếng Việt tại đây..."
    else:
        source_lang = "English"
        target_lang = "Vietnamese"
        placeholder_text = "Enter English text here..."
    
    input_text = st.text_area(
        f"Enter text in {source_lang}",
        height=300,
        placeholder=placeholder_text,
        key="input_text"
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
    
    with col_btn1:
        translate_button = st.button("🔄 Translate", type="primary", use_container_width=True)
    
    with col_btn2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    with col_btn3:
        if input_text:
            st.download_button(
                label="💾 Save Input",
                data=input_text,
                file_name=f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

with col2:
    st.subheader("🎯 Translation Result")
    
    # Initialize session state
    if 'translated_text' not in st.session_state:
        st.session_state.translated_text = ""
    if 'summary_text' not in st.session_state:
        st.session_state.summary_text = ""
    
    # Clear functionality
    if clear_button:
        st.session_state.translated_text = ""
        st.session_state.summary_text = ""
        st.rerun()
    
    # Translation logic
    if translate_button and input_text.strip():
        with st.spinner("🔄 Translating..."):
            st.session_state.translated_text = translate_text(input_text, source_lang, target_lang)
        
        if enable_summary:
            with st.spinner("📋 Generating summary..."):
                if summary_language == "Same as target language":
                    st.session_state.summary_text = summarize_text(
                        st.session_state.translated_text, 
                        target_lang
                    )
                elif summary_language == "Same as source language":
                    st.session_state.summary_text = summarize_text(
                        input_text, 
                        source_lang
                    )
                else:  # Both languages
                    summary_source = summarize_text(input_text, source_lang)
                    summary_target = summarize_text(st.session_state.translated_text, target_lang)
                    st.session_state.summary_text = f"**Summary in {source_lang}:**\n{summary_source}\n\n**Summary in {target_lang}:**\n{summary_target}"
    
    # Display translation
    if st.session_state.translated_text:
        st.markdown(f"**Translation ({target_lang}):**")
        st.markdown(f'<div class="output-box">{st.session_state.translated_text}</div>', unsafe_allow_html=True)
        
        col_export1, col_export2 = st.columns(2)
        with col_export1:
            st.download_button(
                label="💾 Save Translation",
                data=st.session_state.translated_text,
                file_name=f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_export2:
            st.button("📋 Copy Translation", use_container_width=True, on_click=lambda: st.toast("Click the text to copy!"))

# Summary section (full width)
if enable_summary and st.session_state.summary_text:
    st.divider()
    st.subheader("📊 Content Summary")
    st.markdown(f'<div class="output-box">{st.session_state.summary_text}</div>', unsafe_allow_html=True)
    
    col_sum1, col_sum2, col_sum3 = st.columns([1, 1, 2])
    with col_sum1:
        st.download_button(
            label="💾 Save Summary",
            data=st.session_state.summary_text,
            file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col_sum2:
        # Export all results
        if st.session_state.translated_text:
            combined_text = f"""ORIGINAL TEXT ({source_lang}):
{input_text}

{'='*80}

TRANSLATION ({target_lang}):
{st.session_state.translated_text}

{'='*80}

SUMMARY:
{st.session_state.summary_text}

{'='*80}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            st.download_button(
                label="💾 Export All",
                data=combined_text,
                file_name=f"complete_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Powered by AI Translation Technology | Built with Streamlit</p>
    <p style='font-size: 0.9rem;'>Support: Vietnamese ↔ English Translation & Summarization</p>
</div>
""", unsafe_allow_html=True)
