import json
from typing import Dict, List, Optional, Any
import streamlit as st
from agno.team.team import Team
from agno.agent import Agent
from agno.utils.log import logger

# Custom CSS for styling the app
CUSTOM_CSS = """
<style>
    .main-title {
        color: #1E3A8A;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0;
        padding-bottom: 0;
        text-align: center;
    }
    
    .subtitle {
        color: #4B5563;
        font-size: 1.2rem;
        font-weight: 400;
        margin-top: 0;
        padding-top: 0;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    
    div[data-testid="stToolbar"] {
        visibility: hidden;
        height: 0;
        position: fixed;
    }
    
    div[data-testid="stDecoration"] {
        visibility: hidden;
        height: 0;
        position: fixed;
    }
    
    .stTextInput > div > div > input {
        color: #1f1f1f;
    }
    
    .tool-calls {
        background-color: #f7fafc;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 3px solid #3182ce;
    }
    
    .tool-call-name {
        font-weight: bold;
        color: #2c5282;
    }
    
    .tool-call-args {
        font-family: monospace;
        white-space: pre-wrap;
        background-color: #edf2f7;
        padding: 5px;
        border-radius: 3px;
        margin-top: 5px;
    }
    
    .tool-call-result {
        border-top: 1px solid #e2e8f0;
        padding-top: 5px;
        margin-top: 5px;
        white-space: pre-wrap;
    }
</style>
"""

def add_message(role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
    """Add a message to the chat history
    
    Args:
        role: The role of the message sender (user or assistant)
        content: The content of the message
        tool_calls: Optional list of tool calls made during response generation
    """
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    message = {"role": role, "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    
    st.session_state["messages"].append(message)


def display_tool_calls(container, tool_calls: List[Dict[str, Any]]) -> None:
    """Display tool calls in a formatted way
    
    Args:
        container: The Streamlit container to render the tool calls in
        tool_calls: List of tool calls to display
    """
    tool_calls_html = ""
    for idx, tool_call in enumerate(tool_calls):
        tool_name = tool_call.get("name", "Unknown Tool")
        args = tool_call.get("arguments", {})
        
        # Format arguments as pretty JSON if possible
        try:
            if isinstance(args, str):
                args_obj = json.loads(args)
                args_str = json.dumps(args_obj, indent=2)
            elif isinstance(args, dict):
                args_str = json.dumps(args, indent=2)
            else:
                args_str = str(args)
        except:
            args_str = str(args)
        
        result = tool_call.get("result", "")
        
        tool_calls_html += f"""
        <div class="tool-calls">
            <div class="tool-call-name">🔧 {tool_name}</div>
            <div class="tool-call-args">{args_str}</div>
            <div class="tool-call-result">Result: {result}</div>
        </div>
        """
    
    if tool_calls_html:
        container.markdown(tool_calls_html, unsafe_allow_html=True)


def export_chat_history() -> str:
    """Export the chat history as a markdown string
    
    Returns:
        str: The chat history formatted as markdown
    """
    if "messages" not in st.session_state or not st.session_state["messages"]:
        return "# No chat history to export"
    
    export_text = "# InvestorIQ Chat History\n\n"
    
    for msg in st.session_state["messages"]:
        role = msg["role"]
        content = msg.get("content", "")
        
        if role == "user":
            export_text += f"## 🙋 User\n\n{content}\n\n"
        elif role == "assistant":
            export_text += f"## 💼 InvestorIQ\n\n{content}\n\n"
            
            # Add tool calls if any
            if "tool_calls" in msg and msg["tool_calls"]:
                export_text += "### Tool Calls\n\n"
                for tool in msg["tool_calls"]:
                    tool_name = tool.get("name", "Unknown Tool")
                    args = tool.get("arguments", {})
                    result = tool.get("result", "")
                    
                    export_text += f"**{tool_name}**\n\n"
                    export_text += f"Arguments:\n```json\n{json.dumps(args, indent=2)}\n```\n\n"
                    export_text += f"Result:\n```\n{result}\n```\n\n"
    
    return export_text


def session_selector_widget(agent: Agent, model_id: str) -> None:
    """Widget for selecting different agent sessions
    
    Args:
        agent: The agent or team to manage sessions for
        model_id: The model identifier being used
    """
    st.sidebar.markdown("#### 💾 Sessions")
    
    try:
        # Get available sessions
        sessions = agent.storage.get_all_sessions(agent_id=agent.agent_id)
        
        # Filter sessions for the current model
        if sessions:
            session_ids = [session.session_id for session in sessions]
            session_names = [session.name or f"Session {i+1}" for i, session in enumerate(sessions)]
            
            # Create selectbox for sessions
            selected_index = 0
            if agent.session_id in session_ids:
                selected_index = session_ids.index(agent.session_id)
            
            selected_session_name = st.sidebar.selectbox(
                "Select Session",
                options=session_names,
                index=selected_index,
                key="session_selector"
            )
            
            selected_session_id = session_ids[session_names.index(selected_session_name)]
            
            # Load selected session if different from current
            if selected_session_id != agent.session_id:
                st.session_state["investor_iq_session_id"] = selected_session_id
                st.rerun()
            
            # Add button to create new session
            if st.sidebar.button("Create New Session"):
                st.session_state["investor_iq_session_id"] = None
                st.rerun()
        else:
            st.sidebar.info("No saved sessions found")
    
    except Exception as e:
        logger.error(f"Error loading sessions: {e}")
        st.sidebar.warning("Error loading sessions")


def rename_session_widget(agent: Agent) -> None:
    """Widget to rename the current session
    
    Args:
        agent: The agent or team to rename session for
    """
    st.sidebar.markdown("#### ✏️ Rename Current Session")
    
    if agent.session_id:
        new_name = st.sidebar.text_input("Session Name", key="session_name_input")
        
        if st.sidebar.button("Save Name"):
            try:
                agent.storage.rename_session(agent.session_id, new_name)
                st.sidebar.success(f"Session renamed to: {new_name}")
                st.rerun()
            except Exception as e:
                logger.error(f"Error renaming session: {e}")
                st.sidebar.error(f"Error renaming session: {str(e)}")


def about_widget() -> None:
    """Display information about the application"""
    with st.sidebar.expander("ℹ️ About InvestorIQ"):
        st.markdown("""
        **InvestorIQ** is a private equity financial assistant designed to help:
        
        - Process and analyze financial reports
        - Answer investor questions using knowledge base
        - Extract insights from Excel, CSV, and PDF documents
        - Organize and structure financial data
        
        Built with [Agno](https://agno.com/) and [Streamlit](https://streamlit.io/)
        """)
