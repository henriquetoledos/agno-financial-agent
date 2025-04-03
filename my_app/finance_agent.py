from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
# from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.playground import Playground, serve_playground_app
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.team.team import Team
from agno.tools.file import FileTools
import streamlit as st
from typing import Iterator
from agno.utils.pprint import pprint_run_response
import os
from dotenv import load_dotenv

load_dotenv()


# --------- LOAD API KEY ---------
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

# --------------- TITLE AND INFO SECTION -------------------
st.title("🗽 NYC News Reporter Bot")
st.write("Your sassy AI news buddy with that authentic New York attitude!")


# --------------- SIDEBAR CONTROLS -------------------
with st.sidebar:
    st.subheader("Try These NYC Prompts:")
    st.markdown("""
    - Central Park latest scoop
    - Wall Street breaking story
    - Yankees game update
    - New Broadway show buzz
    - Brooklyn food trend
    - Subway peculiar incident
    """)
    st.markdown("---")
    # st.caption(f"Queries processed: {st.session_state.get('counter', 0)}")

# Initialize session state for query counter
with st.sidebar:
    counter_placeholder = st.empty()
if "counter" not in st.session_state:
    st.session_state["counter"] = 0
st.session_state["counter"] += 1
with st.sidebar:
    counter_placeholder.caption(f"Queries processed: {st.session_state['counter']}")

stream = st.sidebar.checkbox("Stream")

# --------------- AGENT INITIALIZATION -------------------
agent_storage: str = "tmp/agents.db"

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
knowledge_base = PDFKnowledgeBase(
    path="data/knowledge",
    vector_db=PgVector(
        table_name="companies_reports",
        db_url=db_url,
    ),
)
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

# Load the knowledge base: Comment after first run
# knowledge_base.load(upsert=True)

question_intaker = Agent(
    name = "Question Intaker",
    model=OpenAIChat(id="gpt-4o"),
    role="Intakes the user's question.",
    description=
        """
        You are a Private Equity Financial Expert,",
        "You will receive a list of questions from the user. You will need to parse them and ask the search agent to find the answers.
        "You might receive the question in a single message, multiple lines, or with Excel files, Words, or PDFs. Use your tools to read the files and parse the questions.
        """,
    tools=[FileTools()], show_tool_calls=True
)

searcher = Agent(
    name="Searcher",
    model=OpenAIChat(id="gpt-4o"),
    role="Searches the documents to find the answer to the user's question.",
    description="You are a Private Equity Financial Expert. You have access to a knowledge base of financial reports and can search the web for additional information.",
    
    instructions=[
        "Search your knowledge base for reports about the companies performance.", 
        "Answer the questions posed by the user.",
    ],
    knowledge=knowledge_base,
    # Enable RAG by adding references from AgentKnowledge to the user prompt.
    add_references=True,
    # Set as False because Agents default to `search_knowledge=True`
    search_knowledge=False,
    markdown=True,
    # debug_mode=True,
)

coordinator = Team(
    name="Editor",
    mode="coordinate",
    model=OpenAIChat("gpt-4o"),
    members=[searcher, question_intaker],
    description="You are a senior Private Equity Financial Expert. Given the questions from the user, your goal is to provide the most accurate and relevant answers.",
    instructions=[
        "If the question is simple and direct, ask the searcher to find the answer in the knowledge base.",
        "If the user sends multiple questions or a file with questions, ask the question_intaker to parse the questions. Then ask the searcher to find the answers.",
        "You are going to request the searcher to find the answers to the questions within the knowledge base only, not searching the web.",
        "You must answer the user's question. in a structured manner, all in the same message ",
        # "Then ask the writer to get an engaging draft of the article.",
        # "Edit, proofread, and refine the article to ensure it meets the high standards of the New York Times.",
        # "The article should be extremely articulate and well written. "
        # "Focus on clarity, coherence, and overall quality.",
        # "Remember: you are the final gatekeeper before the article is published, so make sure the article is perfect.",
    ],
    add_datetime_to_instructions=True,
    # send_team_context_to_members=True,
    show_members_responses=True,
    markdown=True,
)

# # app = Playground(agents=[coordinator,question_intaker,searcher]).get_app()

# app = Playground(teams=[coordinator], agents=[searcher,question_intaker]).get_app()


# if __name__ == "__main__":
#     serve_playground_app("finance_agent:app", reload=True)
# --------------- USER INPUT HANDLING -------------------
prompt = st.text_input("What's your NYC news question? (e.g., 'Times Square breaking news')")

if prompt:
    st.session_state["counter"] = 1
    
    with st.spinner("🕵️♂️ Sniffing out the story..."):
        # stream = True
        if stream:
            response_stream: Iterator[RunResponse] = coordinator.run(prompt, stream=True)
            response_text = ""
            placeholder = st.empty()
            
            for chunk in response_stream:
                response_text += chunk.content
                placeholder.markdown(response_text + "▌")
                st.session_state["counter"] += 1
                with st.sidebar:
                    counter_placeholder.caption(f"Queries processed: {st.session_state['counter']}")
            
            placeholder.markdown(response_text)
        else:
            response = coordinator.run(prompt, stream=False)
            st.markdown(response.content)
            st.session_state["counter"] += 1
            with st.sidebar:
                counter_placeholder.caption(f"Queries processed: {st.session_state['counter']}")

# --------------- FOOTER & INFO -------------------
st.markdown("---")
st.caption("""
**NYC Reporter Bot Features:**
- 100% authentic attitude 🇺🇸
- Certified bodega-approved news 🌃
- Guaranteed to mention pizza at least once 🍕
""")

if __name__ == "__main__":
    coordinator.print_response("What was Ericsson's revenue in 2024?")
    
#     questions = """
#     What was Ericsson's revenue in 2024?
#     What was Ericsson's revenue in 2023?
#     Who is Ericson's CEO?
#     What is the company strategy?"""

#     # coordinator.print_response("What was Ericsson's revenue in 2024?")
#     response: RunResponse = coordinator.run(questions, show_tool_calls=True)
#     # Run agent and return the response as a stream
#     response_stream: Iterator[RunResponse] = coordinator.run(questions, stream=True)


#     # Print the response in markdown format
#     # pprint_run_response(response, markdown=True)
#     # Print the response stream in markdown format
#     pprint_run_response(response_stream, markdown=True)

#     # coordinator.print_response(questions)
#     # coordinator.



