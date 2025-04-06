import os
import tempfile
from typing import List, Dict, Any
from pathlib import Path

import nest_asyncio
import requests
import streamlit as st
from agno.agent import Agent
from agno.document import Document
from agno.document.reader.csv_reader import CSVReader
from agno.document.reader.pdf_reader import PDFReader
from agno.document.reader.text_reader import TextReader
from agno.document.reader.website_reader import WebsiteReader
from agno.utils.log import logger
from agno.team.team import Team
from agno.media import File

from agents import get_financial_team
from utils import (
    CUSTOM_CSS,
    about_widget,
    add_message,
    display_tool_calls,
    export_chat_history,
    rename_session_widget,
    session_selector_widget,
)

# Apply the nest_asyncio patch to allow nested event loops
nest_asyncio.apply()

# Configure the Streamlit page with safe defaults that will render properly
st.set_page_config(
    page_title="InvestorIQ",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.agno.com',
        'Report a bug': 'https://github.com/yourusername/agno-financial-agent/issues',
        'About': "# InvestorIQ\nA private equity financial assistant powered by AI"
    }
)

# # Define simpler CSS that will render more reliably
# SIMPLE_CSS = """
# <style>
#     .main-title {
#         color: #1E3A8A;
#         font-size: 2.5rem;
#         font-weight: 700;
#         text-align: center;
#         margin-bottom: 0.5rem;
#     }
    
#     .subtitle {
#         color: #4B5563;
#         font-size: 1.2rem;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
    
#     .stButton button {
#         background-color: #1E88E5;
#         color: white;
#     }
    
#     .tool-call {
#         background-color: #f7fafc;
#         border-radius: 5px;
#         padding: 10px;
#         margin-bottom: 10px;
#         border-left: 3px solid #3182ce;
#     }
# </style>
# """

# # Add the simplified CSS
# st.markdown(SIMPLE_CSS, unsafe_allow_html=True)


def restart_agent():
    """Reset the agent and clear chat history"""
    logger.debug("---*--- Restarting agent ---*---")
    st.session_state["investor_iq_team"] = None
    st.session_state["investor_iq_session_id"] = None
    st.session_state["messages"] = []
    st.rerun()


def get_reader(file_type: str):
    """Return appropriate reader based on file type."""
    readers = {
        "pdf": PDFReader(),
        "csv": CSVReader(),
        "txt": TextReader(),
        # "xlsx": ExcelReader(),
        # "xls": ExcelReader(),
    }
    return readers.get(file_type.lower(), None)


def initialize_team(model_id: str):
    """Initialize or retrieve the Financial Team."""
    if (
        "investor_iq_team" not in st.session_state
        or st.session_state["investor_iq_team"] is None
    ):
        logger.info(f"---*--- Creating {model_id} Team ---*---")
        team: Team = get_financial_team(
            model_id=model_id,
            session_id=st.session_state.get("investor_iq_session_id"),
        )
        st.session_state["investor_iq_team"] = team
        st.session_state["investor_iq_session_id"] = team.session_id
    return st.session_state["investor_iq_team"]


def process_questions_file(file, team: Team):
    """Process Excel file with multiple questions and get answers"""
    try:
        file_type = file.name.split(".")[-1].lower()
        # Convert the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
        
        # Create a File object for the agent
        file_obj = File(filepath=Path(tmp_path))
        
        # Ask the team to process the questions file
        message = "I've uploaded an Excel file with questions. Please process all questions in this file and provide answers."
        response = team.run(message, files=[file_obj], stream=False)
        
        # Clean up the temporary file
        os.unlink(tmp_path)
        
        return response.content
    except Exception as e:
        logger.error(f"Error processing questions file: {e}")
        return f"Error processing questions file: {e}"


def main():
    # Initialize session state variables if they don't exist
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "loaded_files" not in st.session_state:
        st.session_state.loaded_files = set()
    if "knowledge_base_initialized" not in st.session_state:
        st.session_state.knowledge_base_initialized = False
    
    # App header - using basic HTML that renders reliably
    st.markdown("<h1 class='main-title'>InvestorIQ</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Private Equity Financial Assistant powered by AI</p>", unsafe_allow_html=True)

    # Simple divider
    st.markdown("---")

    # Model selector in the sidebar
    model_options = {
        "GPT-4o": "openai:gpt-4o",
        "GPT-4o-mini": "openai:gpt-4o-mini",
        "Claude 3.5 Sonnet": "anthropic:claude-3-5-sonnet-20241022",
    }
    
    # Adding a basic container for the sidebar content
    with st.sidebar:
        st.title("Settings")
        
        selected_model = st.selectbox(
            "Select a model",
            options=list(model_options.keys()),
            index=0,
            key="model_selector",
        )
        model_id = model_options[selected_model]

    # Initialize Team
    try:
        investor_iq_team: Team
        if (
            "investor_iq_team" not in st.session_state
            or st.session_state["investor_iq_team"] is None
            or st.session_state.get("current_model") != model_id
        ):
            with st.spinner("Initializing AI team..."):
                logger.info("---*--- Creating new InvestorIQ Team ---*---")
                investor_iq_team = get_financial_team(model_id=model_id)
                st.session_state["investor_iq_team"] = investor_iq_team
                st.session_state["current_model"] = model_id
                logger.info(f"Current model set to: {model_id}")

        else:
            investor_iq_team = st.session_state["investor_iq_team"]

        # Load Team Session from the database - commented out because of bugs
        # try:
        #     st.session_state["investor_iq_session_id"] = (
        #         investor_iq_team.load_session()
        #     )
        # except Exception as e:
        #     st.warning(f"Could not create Team session: {str(e)}. Is the database running?")
        #     logger.error(f"Database error: {str(e)}")
    except Exception as e:
        st.error(f"Failed to initialize the AI team: {str(e)}")
        logger.error(f"Team initialization error: {str(e)}")
        return

    # Load runs from memory - commented out because of bugs

    # agent_runs = investor_iq_team.memory.runs
    # if len(agent_runs) > 0:
    #     logger.debug("Loading run history")
    #     st.session_state["messages"] = []
    #     for _run in agent_runs:
    #         if _run.message is not None:
    #             add_message(_run.message.role, _run.message.content)
    #         if _run.response is not None:
    #             add_message("assistant", _run.response.content, _run.response.tools)
    # else:
    #     logger.debug("No run history found")
    #     if "messages" not in st.session_state:
    #         st.session_state["messages"] = []

    # Document Upload Section in sidebar
    with st.sidebar:
        st.markdown("### 📚 Knowledge Base")
        
        # Financial Report Upload
        uploaded_report = st.file_uploader(
            "Upload Financial Reports",
            key="report_upload",
            accept_multiple_files=False,
            type=["pdf", "csv", "xlsx", "xls"]
        )
        
        if uploaded_report:
            file_identifier = f"{uploaded_report.name}_{uploaded_report.size}"
            if file_identifier not in st.session_state.loaded_files:
                with st.spinner("Processing document..."):
                    file_type = uploaded_report.name.split(".")[-1].lower()
                    reader = get_reader(file_type)
                    
                    if reader:
                        try:
                            # Create a temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                                tmp_file.write(uploaded_report.getvalue())
                                tmp_path = tmp_file.name
                            
                            docs = reader.read(tmp_path)
                            
                            # Add to knowledge base
                            searcher = next((m for m in investor_iq_team.members if m.name == "Searcher"), None)
                            if searcher and hasattr(searcher, 'knowledge'):
                                searcher.knowledge.load_documents(docs, upsert=True)
                                st.session_state.loaded_files.add(file_identifier)
                                st.success(f"{uploaded_report.name} added to knowledge base")
                            else:
                                st.error("Searcher agent not found or doesn't have a knowledge base")
                            
                            # Clean up
                            os.unlink(tmp_path)
                        except Exception as e:
                            st.error(f"Error processing document: {str(e)}")
                    else:
                        st.error(f"Unsupported file type: {file_type}")
            else:
                st.info(f"{uploaded_report.name} already loaded in knowledge base")

        # Questions File Upload
        st.markdown("### ❓ Question Batch")
        questions_file = st.file_uploader(
            "Upload Questions File",
            key="questions_upload",
            accept_multiple_files=False,
            type=["xlsx", "csv"]
        )
        
        if questions_file and st.button("Process Questions"):
            with st.spinner("Processing questions file..."):
                response = process_questions_file(questions_file, investor_iq_team)
                add_message("user", f"Process questions from file: {questions_file.name}")
                add_message("assistant", response)

        # # Clear Knowledge Base Button
        # if st.button("Clear Knowledge Base"):
        #     searcher = next((m for m in investor_iq_team.members if m.name == "Searcher"), None)
        #     if searcher and hasattr(searcher, 'knowledge') and hasattr(searcher.knowledge, 'vector_db'):
        #         searcher.knowledge.vector_db.delete()
        #         st.session_state.loaded_files.clear()
        #         st.session_state.knowledge_base_initialized = False
        #         st.success("Knowledge base cleared")
        #     else:
        #         st.error("Could not clear knowledge base - structure not found")

        # Sample Questions
        st.markdown("### 📋 Sample Questions")
        
        sample_questions = {
            "Company Total Value": "What is the Commitment and Drawdowns for Special Project 11?",
            "ESG Policy": "Are there any Diversity, equity & inclusion initiatives on Project 5?",
            "Cyber Security": "Does Ericsson have a cyber/information security policy?"
        }
        
        for label, question in sample_questions.items():
            if st.button(label):
                add_message("user", question)
                st.rerun()

        # Utility buttons
        st.markdown("### 🛠️ Utilities")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("New Chat", use_container_width=True):
                restart_agent()
        with col2:
            if st.download_button(
                "Export Chat",
                export_chat_history(),
                file_name="investor_iq_chat_history.md",
                mime="text/markdown",
                use_container_width=True,
            ):
                st.success("Chat history exported!")

        # About widget
        about_widget()

    # Main chat area
    st.markdown("### Chat")
    
    # Simple container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state["messages"]:
            if message["role"] in ["user", "assistant"]:
                _content = message["content"]
                if _content is not None:
                    with st.chat_message(message["role"]):
                        # Display tool calls if they exist in the message
                        if "tool_calls" in message and message["tool_calls"]:
                            display_tool_calls(st.empty(), message["tool_calls"])
                        st.markdown(_content)

    # Chat input
    if prompt := st.chat_input("Ask me any investor question..."):
        add_message("user", prompt)
        st.rerun()

    # Generate response for user message
    last_message = (
        st.session_state["messages"][-1] if st.session_state["messages"] else None
    )
    if last_message and last_message.get("role") == "user":
        question = last_message["content"]
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner("Thinking..."):
                response = ""
                try:
                    # Run the team and stream the response
                    run_response = investor_iq_team.run(question, stream=True)
                    for _resp_chunk in run_response:
                        # Display tool calls if available
                        if _resp_chunk.tools and len(_resp_chunk.tools) > 0:
                            display_tool_calls(tool_calls_container, _resp_chunk.tools)

                        # Display response
                        if _resp_chunk.content is not None:
                            response += _resp_chunk.content
                            resp_container.markdown(response)

                    add_message(
                        "assistant", response, investor_iq_team.run_response.tools
                    )
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    add_message("assistant", error_message)
                    st.error(error_message)


    
    col1, col2 = st.columns(2)
    with col1:
        session_selector_widget(investor_iq_team, model_id)
    with col2:
        rename_session_widget(investor_iq_team)


if __name__ == "__main__":
    # Add error handling for the entire application
    try:
        main()
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logger.error(f"Application error: {str(e)}", exc_info=True)
