import streamlit as st
import os
import asyncio
import nest_asyncio
import re

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

def clean_agent_response(raw_response):
    """
    Clean the raw agent response to extract readable text.
    Handles both Event objects and plain text responses.
    """
    response_str = str(raw_response)
    
    # If response is empty or None
    if not response_str or response_str == "None":
        return "No response received from the agent."
    
    # Check if it's an Event object
    if 'Event(model_version=' in response_str:
        try:
            # Method 1: Extract text between triple quotes
            text_matches = re.findall(r'text="""(.*?)"""', response_str, re.DOTALL)
            if text_matches:
                cleaned_text = text_matches[0].strip()
                if cleaned_text:
                    return cleaned_text
            
            # Method 2: Look for content parts
            if 'Content(parts=[' in response_str:
                # Find the main text content
                pattern = r'Part\(.*?text="""(.*?)""".*?\)'
                matches = re.findall(pattern, response_str, re.DOTALL)
                if matches:
                    return matches[0].strip()
            
            # Method 3: Extract from plant_disease_diagnostician lines
            lines = response_str.split('\n')
            result_lines = []
            in_response = False
            
            for line in lines:
                if 'plant_disease_diagnostician >' in line:
                    in_response = True
                    # Extract text after the agent name
                    parts = line.split('plant_disease_diagnostician >')
                    if len(parts) > 1:
                        line = parts[1].strip()
                    else:
                        line = line.replace('plant_disease_diagnostician >', '').strip()
                
                # Skip debug lines and Event object lines
                if (in_response and line and 
                    not line.startswith('Event(') and 
                    not line.startswith('User >') and
                    not line.startswith('### Created') and
                    not line.startswith('### Continue')):
                    result_lines.append(line.strip())
            
            if result_lines:
                return '\n'.join(result_lines)
            
            # Method 4: Fallback - clean up the string
            cleaned = response_str.replace('Event(model_version=', '')
            cleaned = cleaned.replace('Content(parts=[Part(text="""', '')
            cleaned = cleaned.replace('""",)], role=', '')
            cleaned = cleaned.replace('model', '')
            
            # Remove excessive whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip()
            
        except Exception as e:
            return f"Error processing response: {str(e)}"
    
    # If it's already clean text with agent prefix
    elif 'plant_disease_diagnostician >' in response_str:
        lines = response_str.split('\n')
        cleaned_lines = []
        for line in lines:
            if 'plant_disease_diagnostician >' in line:
                line = line.split('plant_disease_diagnostician >')[-1].strip()
            if line and not line.startswith('User >'):
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    # If it's just regular text
    else:
        # Clean up any remaining artifacts
        cleaned = response_str
        # Remove common prefixes
        prefixes = ['### Created', '### Continue', 'User >']
        for prefix in prefixes:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove multiple newlines
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        return cleaned.strip()

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
        value=st.session_state.api_key,
        help="Your API key is only used for this session and not stored"
    )
    
    if api_key:
        st.session_state.api_key = api_key
    
    # Initialize Agent
    if st.button("🚀 Initialize AI Agent", use_container_width=True, type="primary"):
        if api_key:
            with st.spinner("Initializing AI Agent..."):
                try:
                    # Set API key
                    os.environ["GOOGLE_API_KEY"] = api_key
                    
                    # Import ADK components
                    from google.adk.agents import Agent
                    from google.adk.models.google_llm import Gemini
                    from google.adk.runners import InMemoryRunner
                    from google.adk.tools import google_search
                    
                    # Create agent
                    plant_disease_agent = Agent(
                        name="plant_disease_diagnostician",
                        model=Gemini(model="gemini-2.5-flash-lite"),
                        description="AI agent for plant disease diagnosis",
                        instruction="""You are a plant pathology expert assistant. Help diagnose plant diseases and identify affected plants. Use Google Search for current information. Provide symptoms, prevention methods, and practical advice. Format your response clearly with headings and bullet points when appropriate.""",
                        tools=[google_search],
                    )
                    
                    # Create runner
                    runner = InMemoryRunner(agent=plant_disease_agent)
                    
                    # Store in session state
                    st.session_state.agent = plant_disease_agent
                    st.session_state.runner = runner
                    st.session_state.agent_initialized = True
                    
                    st.success("✅ AI Agent initialized successfully!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error initializing agent: {str(e)}")
                    st.info("Make sure you have installed: pip install google-adk nest-asyncio")
        else:
            st.warning("⚠️ Please enter your API key first")
    
    st.markdown("---")
    
    # Examples
    st.markdown("### 💡 Example Questions")
    
    examples = {
        "🌱 Plant to Diseases": [
            "What diseases affect tomato plants?",
            "Common rose bush diseases?",
        ],
        "🦠 Disease to Plants": [
            "Which plants get powdery mildew?",
            "Plants affected by root rot?",
        ],
        "🔍 Symptom Analysis": [
            "Brown spots on plant leaves?",
            "Why are leaves turning yellow?",
        ]
    }
    
    for category, items in examples.items():
        with st.expander(category):
            for item in items:
                if st.button(item, key=f"ex_{hash(item)}", use_container_width=True):
                    st.session_state.prefilled_query = item
                    st.rerun()
    
    st.markdown("---")
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.conversation_history = []
        st.rerun()
    
    # Info
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Features:**
        - 🌿 Plant disease diagnosis
        - 🔍 Web search for current info
        - 📝 Conversation history
        
        **Note:** Educational use only.
        Consult experts for serious issues.
        """)

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
        placeholder="Example: 'What diseases affect tomato plants?' or 'Which plants get powdery mildew?'",
        value=default_query,
        key="query_input"
    )
    
    # Submit button
    submit_disabled = not (st.session_state.get('agent_initialized', False) and user_query.strip())
    
    if st.button("🔍 Analyze with AI", disabled=submit_disabled, type="primary", use_container_width=True):
        if not st.session_state.get('agent_initialized', False):
            st.warning("⚠️ Please initialize the AI agent first (sidebar)")
        elif not user_query.strip():
            st.warning("⚠️ Please enter a question")
        else:
            with st.spinner("🌿 AI is analyzing your question..."):
                try:
                    # Add user query to history
                    st.session_state.conversation_history.append({
                        "role": "user",
                        "content": user_query,
                        "timestamp": "Now"
                    })
                    
                    # Display user message
                    with st.chat_message("user"):
                        st.markdown(f"**You:** {user_query}")
                    
                    # Get agent response
                    async def get_agent_response():
                        return await st.session_state.runner.run_debug(user_query)
                    
                    # Run async function
                    raw_response = asyncio.run(get_agent_response())
                    
                    # Clean the response
                    response_text = clean_agent_response(raw_response)
                    
                    # Add agent response to history
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": "Now"
                    })
                    
                    # Display agent response
                    with st.chat_message("assistant"):
                        st.markdown(f"**🌿 Plant Doctor:** {response_text}")
                    
                    # Clear input by rerunning
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"❌ Error getting response: {str(e)}"
                    st.error(error_msg)
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": "Now"
                    })

with col2:
    st.markdown('<div class="sub-header">📊 Agent Status</div>', unsafe_allow_html=True)
    
    if st.session_state.get('agent_initialized', False):
        st.markdown("""
        <div class="success-box">
        <strong>✅ Active</strong><br>
        • Model: Gemini 2.5 Flash Lite<br>
        • Tools: Google Search<br>
        • Status: Ready<br>
        • API: Configured
        </div>
        """, unsafe_allow_html=True)
        
        # Quick stats
        total_messages = len(st.session_state.conversation_history)
        if total_messages > 0:
            st.caption(f"💬 {total_messages} messages in history")
    else:
        st.markdown("""
        <div class="info-box">
        <strong>⏳ Setup Required</strong><br>
        1. Enter API key<br>
        2. Initialize agent<br>
        3. Ask questions
        </div>
        """, unsafe_allow_html=True)

# Display conversation history
if st.session_state.conversation_history:
    st.markdown("---")
    st.markdown('<div class="sub-header">📜 Conversation History</div>', unsafe_allow_html=True)
    
    for i, message in enumerate(st.session_state.conversation_history):
        if message["role"] == "user":
            st.markdown(f'<div class="chat-user"><strong>👤 You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            # Check if it's an error message
            if message["content"].startswith("❌"):
                st.error(message["content"])
            else:
                st.markdown(f'<div class="chat-assistant"><strong>🌿 Plant Doctor:</strong> {message["content"]}</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
<p>🌱 Built with Google ADK & Gemini AI | Deployed on Streamlit Cloud</p>
<p>⚠️ For educational purposes | Always verify with agricultural experts</p>
<p>🔒 Your API key is not stored on our servers</p>
</div>
""", unsafe_allow_html=True)

# Add some debugging info in expander (hidden by default)
with st.expander("🔧 Debug Info (for troubleshooting)"):
    if st.session_state.get('agent_initialized', False):
        st.write("Agent Status: ✅ Initialized")
        st.write(f"Conversation History Length: {len(st.session_state.conversation_history)}")
        
        if st.session_state.conversation_history:
            st.write("Last 2 messages:")
            for msg in st.session_state.conversation_history[-2:]:
                st.write(f"{msg['role']}: {msg['content'][:100]}...")
    else:
        st.write("Agent Status: ❌ Not initialized")
    
    st.write(f"API Key Set: {'✅ Yes' if st.session_state.api_key else '❌ No'}")
    st.write(f"Environment API Key: {'✅ Set' if os.environ.get('GOOGLE_API_KEY') else '❌ Not set'}")
