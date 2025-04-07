import streamlit as st
from agno.team import Team
from agents import get_financial_team
from agno.utils.log import logger
from utils import add_message, display_tool_calls  # Removed sidebar_widget

# Configure the Streamlit page
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

def main():
    ####################################################################
    # App header
    ####################################################################
    st.markdown("<h1 class='main-title'>InvestorIQ</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Private Equity Financial Assistant powered by AI</p>", unsafe_allow_html=True)
    st.markdown("---")

    ####################################################################
    # Model selector
    ####################################################################
    model_options = {
        "GPT-4o": "openai:gpt-4o",
        "GPT-4o-mini": "openai:gpt-4o-mini",
        "Claude 3.5 Sonnet": "anthropic:claude-3-5-sonnet-20241022",
    }
    selected_model = st.sidebar.selectbox(
        "Select a model",
        options=list(model_options.keys()),
        index=0,
        key="model_selector",
    )
    model_id = model_options[selected_model]

    ####################################################################
    # Initialize Financial Team
    ####################################################################
    financial_team: Team
    if (
        "financial_team" not in st.session_state
        or st.session_state["financial_team"] is None
        or st.session_state.get("current_model") != model_id
    ):
        logger.info("---*--- Creating new Financial Team ---*---")
        try:
            financial_team = get_financial_team(model_id=model_id)
            st.session_state["financial_team"] = financial_team
            st.session_state["current_model"] = model_id
            st.success("AI team initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize the AI team: {str(e)}")
            return
    else:
        financial_team = st.session_state["financial_team"]

    ####################################################################
    # Initialize messages if not exists
    ####################################################################
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    ####################################################################
    # Sidebar
    ####################################################################
    st.sidebar.title("Settings")  # Placeholder for sidebar_widget functionality
    st.sidebar.markdown("Configure your preferences here.")  # Add any necessary sidebar content

    ####################################################################
    # Sidebar - File Input for Questions
    ####################################################################
    st.sidebar.markdown("#### 📄 Upload Questions File")
    uploaded_questions_file = st.sidebar.file_uploader(
        "Upload a file containing questions (.txt or .csv)", type=["txt", "csv"], key="questions_file"
    )

    if uploaded_questions_file:
        try:
            # Process the uploaded file
            file_type = uploaded_questions_file.name.split(".")[-1].lower()
            if file_type == "txt":
                # Read questions from a text file (one question per line)
                questions = uploaded_questions_file.read().decode("utf-8").splitlines()
            elif file_type == "csv":
                # Read questions from a CSV file (assuming one question per row)
                import csv
                questions = [row[0] for row in csv.reader(uploaded_questions_file.read().decode("utf-8").splitlines())]
            else:
                st.sidebar.error("Unsupported file type!")
                questions = []

            # Add each question to the chat history
            for question in questions:
                if question.strip():  # Ensure the question is not empty
                    add_message("user", question.strip())
            st.sidebar.success(f"Successfully added {len(questions)} questions!")
        except Exception as e:
            st.sidebar.error(f"Error processing file: {str(e)}")


    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("Ask me any investor question..."):
        add_message("user", prompt)

    ####################################################################
    # Display chat history
    ####################################################################
    for message in st.session_state["messages"]:
        if message["role"] in ["user", "assistant"]:
            with st.chat_message(message["role"]):
                if "tool_calls" in message and message["tool_calls"]:
                    display_tool_calls(st.empty(), message["tool_calls"])
                st.markdown(message["content"])

    ####################################################################
    # Generate response for user message
    ####################################################################
    last_message = (
        st.session_state["messages"][-1] if st.session_state["messages"] else None
    )
    if last_message and last_message.get("role") == "user":
        question = last_message["content"]
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner("🤔 Thinking..."):
                try:
                    # Run the financial team and get response
                    run_response = financial_team.run(question)
                    response_content = run_response.content

                    # Display response
                    st.markdown(response_content)

                    # Store the formatted response for chat history
                    add_message("assistant", response_content, run_response.tools)

                    # Display tool calls if available
                    if run_response.tools and len(run_response.tools) > 0:
                        display_tool_calls(tool_calls_container, run_response.tools)

                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    add_message("assistant", error_message)
                    st.error(error_message)


if __name__ == "__main__":
    main()
