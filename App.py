# app.py
import streamlit as st
import requests
import json
from datetime import datetime
import time
import io
import base64
from audio_recorder_streamlit import audio_recorder

# Page configuration
st.set_page_config(
    page_title="Vietnamese-English Translator with Voice",
    page_icon="🎙️",
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
    .recording-indicator {
        background-color: #ff4b4b;
        color: white;
        padding: 10px 20px;
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .transcription-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    .translation-box {
        background-color: #f0f8e8;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin: 10px 0;
    }
    .history-item {
        background-color: #fff;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 8px 0;
    }
    .success-badge {
        background-color: #4caf50;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .error-badge {
        background-color: #ff4b4b;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="title-text">🎙️ Voice Translation & Transcription</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Speak, Record, Translate - Vietnamese ↔ English</p>', unsafe_allow_html=True)

# API Configuration
LLM_ENDPOINT = "https://llm.blackbox.ai/chat/completions"
LLM_HEADERS = {
    "customerId": "cus_T4SotOIhxreJbK",
    "Content-Type": "application/json",
    "Authorization": "Bearer xxx"
}

STT_ENDPOINT = "https://elevenlabs-proxy-server-lipn.onrender.com/v1/speech-to-text"
STT_HEADERS = {
    "customerId": "cus_T4SotOIhxreJbK",
    "Authorization": "Bearer xxx"
}

MODEL_NAME = "openrouter/claude-sonnet-4"

# Initialize session state
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = ""
if 'translated_text' not in st.session_state:
    st.session_state.translated_text = ""
if 'summary_text' not in st.session_state:
    st.session_state.summary_text = ""
if 'audio_history' not in st.session_state:
    st.session_state.audio_history = []
if 'continuous_mode' not in st.session_state:
    st.session_state.continuous_mode = False
if 'current_source_lang' not in st.session_state:
    st.session_state.current_source_lang = ""
if 'current_target_lang' not in st.session_state:
    st.session_state.current_target_lang = ""

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
            LLM_ENDPOINT,
            headers=LLM_HEADERS,
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

def transcribe_audio(audio_bytes):
    """Transcribe audio using ElevenLabs STT API"""
    try:
        # Prepare the multipart form data
        files = {
            'file': ('audio.wav', audio_bytes, 'audio/wav')
        }
        data = {
            'model_id': 'scribe_v1'
        }
        
        # Make the request
        response = requests.post(
            STT_ENDPOINT,
            headers=STT_HEADERS,
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract transcription text
            if 'text' in result:
                return result['text']
            elif 'transcription' in result:
                return result['transcription']
            else:
                return str(result)
        else:
            return f"Error: STT API returned status code {response.status_code}"
    
    except requests.exceptions.Timeout:
        return "Error: Transcription timed out. Please try again with shorter audio."
    except Exception as e:
        return f"Error during transcription: {str(e)}"

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

def detect_language(text):
    """Detect if text is Vietnamese or English"""
    system_prompt = """You are a language detection expert. Analyze the given text and determine if it is Vietnamese or English.
    Reply with ONLY one word: either 'Vietnamese' or 'English'. No other text."""
    
    user_prompt = f"What language is this text: {text[:200]}"
    
    result = call_llm_api(user_prompt, system_prompt).strip()
    return result if result in ['Vietnamese', 'English'] else 'English'

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Mode selection
    mode = st.radio(
        "Input Mode",
        ["🎙️ Voice Recording", "⌨️ Text Input"],
        index=0
    )
    
    st.divider()
    
    translation_direction = st.radio(
        "Translation Direction",
        ["Vietnamese → English", "English → Vietnamese", "Auto-detect"],
        index=2
    )
    
    st.divider()
    
    enable_summary = st.checkbox("Enable Summarization", value=True)
    
    if enable_summary:
        summary_language = st.selectbox(
            "Summary Language",
            ["Same as target language", "Same as source language", "Both languages"]
        )
    
    st.divider()
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.audio_history = []
        st.session_state.transcribed_text = ""
        st.session_state.translated_text = ""
        st.session_state.summary_text = ""
        st.rerun()
    
    st.divider()
    
    st.markdown("### 📚 Instructions")
    if mode == "🎙️ Voice Recording":
        st.markdown("""
        1. Click microphone to start recording
        2. Speak clearly in your language
        3. Click again to stop recording
        4. Transcription appears automatically
        5. Translation follows transcription
        6. Export results as needed
        """)
    else:
        st.markdown("""
        1. Select translation direction
        2. Enter or paste your text
        3. Click 'Translate' button
        4. View translation and summary
        5. Export results as needed
        """)
    
    # Display statistics
    if st.session_state.audio_history:
        st.divider()
        st.markdown("### 📊 Statistics")
        st.metric("Total Recordings", len(st.session_state.audio_history))
        successful = sum(1 for item in st.session_state.audio_history if item.get('success', False))
        st.metric("Successful Translations", successful)

# Main content based on mode
if mode == "🎙️ Voice Recording":
    st.subheader("🎤 Voice Recording & Translation")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🎙️ Record Your Voice")
        st.info("Click the microphone button below to start/stop recording")
        
        # Audio recorder
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#ff4b4b",
            neutral_color="#1f77b4",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=2.0,
            sample_rate=44100
        )
        
        if audio_bytes:
            st.success("✅ Audio recorded successfully!")
            
            # Display audio player
            st.audio(audio_bytes, format='audio/wav')
            
            # Transcription section
            with st.spinner("🔄 Transcribing audio..."):
                transcription = transcribe_audio(audio_bytes)
                st.session_state.transcribed_text = transcription
            
            if transcription and not transcription.startswith("Error"):
                st.markdown("### 📝 Transcription")
                st.markdown(f'<div class="transcription-box">{transcription}</div>', unsafe_allow_html=True)
                
                # Auto-detect language or use selection
                if translation_direction == "Auto-detect":
                    detected_lang = detect_language(transcription)
                    source_lang = detected_lang
                    target_lang = "English" if detected_lang == "Vietnamese" else "Vietnamese"
                    st.info(f"🔍 Detected language: {source_lang}")
                elif translation_direction == "Vietnamese → English":
                    source_lang = "Vietnamese"
                    target_lang = "English"
                else:
                    source_lang = "English"
                    target_lang = "Vietnamese"
                
                st.session_state.current_source_lang = source_lang
                st.session_state.current_target_lang = target_lang
                
                # Translate
                with st.spinner(f"🔄 Translating to {target_lang}..."):
                    translation = translate_text(transcription, source_lang, target_lang)
                    st.session_state.translated_text = translation
                
                # Summarize if enabled
                if enable_summary:
                    with st.spinner("📋 Generating summary..."):
                        if summary_language == "Same as target language":
                            summary = summarize_text(translation, target_lang)
                        elif summary_language == "Same as source language":
                            summary = summarize_text(transcription, source_lang)
                        else:
                            summary_source = summarize_text(transcription, source_lang)
                            summary_target = summarize_text(translation, target_lang)
                            summary = f"**Summary in {source_lang}:**\n{summary_source}\n\n**Summary in {target_lang}:**\n{summary_target}"
                        st.session_state.summary_text = summary
                
                # Add to history
                history_item = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'transcription': transcription,
                    'translation': translation,
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'success': True
                }
                st.session_state.audio_history.append(history_item)
                
            else:
                st.error(f"❌ Transcription failed: {transcription}")
                history_item = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'error': transcription,
                    'success': False
                }
                st.session_state.audio_history.append(history_item)
    
    with col2:
        st.markdown("### 🌐 Translation Result")
        
        if st.session_state.translated_text:
            st.markdown(f"**Translation ({st.session_state.current_target_lang}):**")
            st.markdown(f'<div class="translation-box">{st.session_state.translated_text}</div>', unsafe_allow_html=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.download_button(
                    label="💾 Save Translation",
                    data=st.session_state.translated_text,
                    file_name=f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_btn2:
                combined = f"""TRANSCRIPTION ({st.session_state.current_source_lang}):
{st.session_state.transcribed_text}

{'='*60}

TRANSLATION ({st.session_state.current_target_lang}):
{st.session_state.translated_text}
"""
                st.download_button(
                    label="💾 Save Both",
                    data=combined,
                    file_name=f"voice_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("🎤 Record audio to see translation here")
    
    # Summary section (full width)
    if enable_summary and st.session_state.summary_text:
        st.divider()
        st.subheader("📊 Content Summary")
        st.markdown(f'<div class="output-box">{st.session_state.summary_text}</div>', unsafe_allow_html=True)
        
        col_sum1, col_sum2 = st.columns([1, 2])
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
            complete_text = f"""VOICE RECORDING TRANSCRIPTION
{'='*60}

TRANSCRIPTION ({st.session_state.current_source_lang}):
{st.session_state.transcribed_text}

{'='*60}

TRANSLATION ({st.session_state.current_target_lang}):
{st.session_state.translated_text}

{'='*60}

SUMMARY:
{st.session_state.summary_text}

{'='*60}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            st.download_button(
                label="💾 Export Complete Report",
                data=complete_text,
                file_name=f"complete_voice_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # History section
    if st.session_state.audio_history:
        st.divider()
        st.subheader("📜 Translation History")
        
        # Display last 5 items
        for idx, item in enumerate(reversed(st.session_state.audio_history[-5:])):
            with st.expander(f"🎙️ Recording {len(st.session_state.audio_history) - idx} - {item['timestamp']}"):
                if item.get('success', False):
                    st.markdown(f'<span class="success-badge">✓ Success</span>', unsafe_allow_html=True)
                    st.markdown(f"**Source ({item['source_lang']}):** {item['transcription'][:100]}...")
                    st.markdown(f"**Translation ({item['target_lang']}):** {item['translation'][:100]}...")
                else:
                    st.markdown(f'<span class="error-badge">✗ Failed</span>', unsafe_allow_html=True)
                    st.markdown(f"**Error:** {item.get('error', 'Unknown error')}")

elif mode == "⌨️ Text Input":
    st.subheader("⌨️ Text Translation")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 Input Text")
        
        # Determine source and target languages
        if translation_direction == "Vietnamese → English":
            source_lang = "Vietnamese"
            target_lang = "English"
            placeholder_text = "Nhập văn bản tiếng Việt tại đây..."
        elif translation_direction == "English → Vietnamese":
            source_lang = "English"
            target_lang = "Vietnamese"
            placeholder_text = "Enter English text here..."
        else:
            source_lang = "Auto-detect"
            target_lang = "Auto"
            placeholder_text = "Enter text in Vietnamese or English..."
        
        input_text = st.text_area(
            f"Enter text",
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
        st.markdown("### 🎯 Translation Result")
        
        # Clear functionality
        if clear_button:
            st.session_state.translated_text = ""
            st.session_state.summary_text = ""
            st.rerun()
        
        # Translation logic
        if translate_button and input_text.strip():
            # Auto-detect language if needed
            if translation_direction == "Auto-detect":
                with st.spinner("🔍 Detecting language..."):
                    detected_lang = detect_language(input_text)
                    source_lang = detected_lang
                    target_lang = "English" if detected_lang == "Vietnamese" else "Vietnamese"
                    st.info(f"Detected language: {source_lang}")
            
            with st.spinner(f"🔄 Translating to {target_lang}..."):
                st.session_state.translated_text = translate_text(input_text, source_lang, target_lang)
                st.session_state.current_source_lang = source_lang
                st.session_state.current_target_lang = target_lang
            
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
                    else:
                        summary_source = summarize_text(input_text, source_lang)
                        summary_target = summarize_text(st.session_state.translated_text, target_lang)
                        st.session_state.summary_text = f"**Summary in {source_lang}:**\n{summary_source}\n\n**Summary in {target_lang}:**\n{summary_target}"
        
        # Display translation
        if st.session_state.translated_text:
            st.markdown(f"**Translation ({st.session_state.current_target_lang}):**")
            st.markdown(f'<div class="translation-box">{st.session_state.translated_text}</div>', unsafe_allow_html=True)
            
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
                combined = f"""ORIGINAL ({st.session_state.current_source_lang}):
{input_text}

{'='*60}

TRANSLATION ({st.session_state.current_target_lang}):
{st.session_state.translated_text}
"""
                st.download_button(
                    label="💾 Save Both",
                    data=combined,
                    file_name=f"text_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("⌨️ Enter text and click translate to see results")
    
    # Summary section (full width)
    if enable_summary and st.session_state.summary_text:
        st.divider()
        st.subheader("📊 Content Summary")
        st.markdown(f'<div class="output-box">{st.session_state.summary_text}</div>', unsafe_allow_html=True)
        
        col_sum1, col_sum2 = st.columns([1, 2])
        with col_sum1:
            st.download_button(
                label="💾 Save Summary",
                data=st.session_state.summary_text,
                file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_sum2:
            if st.session_state.translated_text and input_text:
                complete_text = f"""TEXT TRANSLATION REPORT
{'='*60}

ORIGINAL TEXT ({st.session_state.current_source_lang}):
{input_text}

{'='*60}

TRANSLATION ({st.session_state.current_target_lang}):
{st.session_state.translated_text}

{'='*60}

SUMMARY:
{st.session_state.summary_text}

{'='*60}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                st.download_button(
                    label="💾 Export Complete Report",
                    data=complete_text,
                    file_name=f"complete_translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>🎙️ Voice Translation & Transcription System</strong></p>
    <p>Powered by AI Technology | Built with Streamlit</p>
    <p style='font-size: 0.9rem;'>Features: Voice Recording • Real-time Transcription • Translation • Summarization</p>
    <p style='font-size: 0.85rem; color: #999;'>Vietnamese ↔ English | Speech-to-Text | Export Capabilities</p>
</div>
""", unsafe_allow_html=True)
