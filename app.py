import streamlit as st
import os
import asyncio
import nest_asyncio

# Apply nest_asyncio for async support
nest_asyncio.apply()

# Set page config
st.set_page_config(
    page_title="🌿 Plant Disease Diagnosis AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 2rem;
        padding-top: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #388E3C;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #FF9800;
        margin: 1rem 0;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        border: none;
    }
    .stButton button:hover {
        background-color: #388E3C;
    }
    .chat-user {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
    }
    .chat-assistant {
        background-color: #F1F8E9;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #8BC34A;
    }
    .example-query {
        background-color: #F5F5F5;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        cursor: pointer;
        border: 1px solid #E0E0E0;
    }
    .example-query:hover {
        background-color: #E8F5E9;
        border-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🌿 Plant Disease Diagnosis AI</h1>', unsafe_allow_html=True)
st.markdown("""
<div class="info-box">
<strong>🤖 AI-Powered Plant Pathology Assistant</strong><br>
Diagnose plant diseases and identify affected plants using Google's Gemini AI with web search.
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent_initialized' not in st.session_state:
    st.session_state.agent_initialized = False
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # API Key
    st.markdown("#### 🔑 Gemini API Key")
    st.markdown("""
    <div class="info-box" style="padding: 1rem; margin-bottom: 1rem;">
    <small>Get free API key:<br>
    <a href="https://aistudio.google.com/app/apikeys" target="_blank">Google AI Studio</a></small>
    </div>
    """, unsafe_allow_html=True)
    
    api_key = st.text_input(
        "Enter your Gemini API Key:",
        type="password",
        value=st.session_state.api_key
    )
    
    if api_key:
        st.session_state.api_key = api_key
    
    # Initialize Agent
    if st.button("🚀 Initialize AI Agent", use_container_width=True, type="primary"):
        if api_key:
            with st.spinner("Initializing AI Agent..."):
                try:
                    os.environ["GOOGLE_API_KEY"] = api_key
                    
                    from google.adk.agents import Agent
                    from google.adk.models.google_llm import Gemini
                    from google.adk.runners import InMemoryRunner
                    from google.adk.tools import google_search
                    
                    plant_disease_agent = Agent(
                        name="plant_disease_diagnostician",
                        model=Gemini(model="gemini-2.5-flash-lite"),
                        description="AI agent for plant disease diagnosis",
                        instruction="""You are a plant pathology expert. Help diagnose plant diseases and identify affected plants. Use Google Search for current information. Provide symptoms, prevention methods, and practical advice.""",
                        tools=[google_search],
                    )
                    
                    runner = InMemoryRunner(agent=plant_disease_agent)
                    
                    st.session_state.agent = plant_disease_agent
                    st.session_state.runner = runner
                    st.session_state.agent_initialized = True
                    
                    st.success("✅ AI Agent initialized!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter API key")
    
    st.markdown("---")
    
    # Examples
    st.markdown("### 💡 Examples")
    
    examples = {
        "🌱 Plant Diagnosis": [
            "What diseases affect tomato plants?",
            "Why are my rose leaves turning yellow?",
        ],
        "🦠 Disease Info": [
            "Which plants get powdery mildew?",
            "What is early blight?",
        ],
        "🔍 Symptoms": [
            "Brown spots on plant leaves?",
            "White powder on cucumber leaves?",
        ]
    }
    
    for category, items in examples.items():
        with st.expander(category):
            for item in items:
                if st.button(item, key=f"ex_{hash(item)}", use_container_width=True):
                    st.session_state.prefilled_query = item
                    st.rerun()
    
    st.markdown("---")
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.conversation_history = []
        st.rerun()

# Main Content
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<div class="sub-header">💬 Ask Your Plant Question</div>', unsafe_allow_html=True)
    
    # Query input
    if 'prefilled_query' in st.session_state:
        default_query = st.session_state.prefilled_query
        del st.session_state.prefilled_query
    else:
        default_query = ""
    
    user_query = st.text_area(
        "Describe your plant issue:",
        height=120,
        placeholder="Example: 'My tomato plants have yellow leaves with black spots'",
        value=default_query,
        key="query_input"
    )
    
    # Submit
    submit_disabled = not (st.session_state.get('agent_initialized', False) and user_query.strip())
    if st.button("🔍 Analyze with AI", disabled=submit_disabled, type="primary"):
        if not st.session_state.get('agent_initialized', False):
            st.warning("⚠️ Initialize agent first")
        elif not user_query.strip():
            st.warning("⚠️ Enter a question")
        else:
            with st.spinner("🌿 AI is analyzing..."):
                try:
                    # Add to history
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": user_query
                    })
                    
                    # Display user message
                    with st.chat_message("user"):
                        st.markdown(f"**You:** {user_query}")
                    
                    # Get response
                    async def get_response():
                        return await st.session_state.runner.run_debug(user_query)
                    
                    response = asyncio.run(get_response())
                    
                    # Clean response
                    response_text = str(response)
                    if "plant_disease_diagnostician >" in response_text:
                        lines = response_text.split('\n')
                        cleaned = []
                        for line in lines:
                            if line.startswith('plant_disease_diagnostician >'):
                                line = line.replace('plant_disease_diagnostician >', '').strip()
                            if line and not line.startswith('User >'):
                                cleaned.append(line)
                        response_text = '\n'.join(cleaned)
                    
                    # Add to history
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": response_text
                    })
                    
                    # Display response
                    with st.chat_message("assistant"):
                        st.markdown(f"**🌿 Plant Doctor:** {response_text}")
                    
                    # Clear input
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

with col2:
    st.markdown('<div class="sub-header">📊 Status</div>', unsafe_allow_html=True)
    
    if st.session_state.get('agent_initialized', False):
        st.markdown("""
        <div class="success-box">
        <strong>✅ Active</strong><br>
        • Gemini AI<br>
        • Google Search<br>
        • Ready
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box">
        <strong>⏳ Setup Required</strong><br>
        Enter API key and initialize agent.
        </div>
        """, unsafe_allow_html=True)

# Chat History
if st.session_state.conversation_history:
    st.markdown("---")
    st.markdown('<div class="sub-header">📜 Conversation</div>', unsafe_allow_html=True)
    
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.markdown(f'<div class="chat-user"><strong>You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant"><strong>🌿 Plant Doctor:</strong> {message["content"]}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
<p>🌱 Built with Google ADK & Gemini AI | Streamlit Cloud</p>
<p>⚠️ For educational purposes</p>
</div>
""", unsafe_allow_html=True)
