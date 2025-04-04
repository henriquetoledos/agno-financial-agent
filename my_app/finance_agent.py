# InvestorIQ
# What is goal of this application?
# This application is designed to assist private equity professionals in analyzing financial reports to answer questions from the Investors.
# The process is the following:
# 1. We have an already trained knowledge base, consisting of reports in xslx format (which we have an agent to convert to csv), and pdf files.
# 2. The user can ask questions about the reports, and the agent will search the knowledge base to find the answers.
# 3. Those questions can be submited individually, or in bulk, using an excel file. The agent must be capable of parsing the questions from the file, and then search the knowledge base to find the answers.

# We have a team of agents, each with a specific role:
# 1. **Question Intaker Agent**: This agent is responsible for receiving the questions from the user. It can handle multiple questions at once, and it can also read questions from Excel files.
# 2. **Searcher Agent**: This agent is responsible for searching the knowledge base to find the answers to the questions. It can also search the web for additional information if needed.
# 3. **Coordinator**: This agent is responsible for coordinating the work of the other agents. It decides which agent should handle each question, and it also formats the final answer to be sent back to the user.
# 4. **Excel Reader Agent**: This agent is responsible for converting Excel files to CSV format and analyzing the data. It can also handle multiple Excel files at once.
# 5. **CSV Analyzer Agent**: This agent is responsible for analyzing the CSV files and determining how to split them into different tables. It can also handle multiple CSV files at once.
# 6. ** Sanity Checker Agent**: This agent is responsible for checking if the answer provided by the Searcher is correct. It needs to ouptput the level of confidence in the answer, and if it is not confident enough, it should ask the Searcher to provide more information, or to answer that there is no suffience information
# 7. **Email Information Requester Agent**: This agent is responsible for sending an email for the private equity team to ask for more information about the question, in case there is no suffiecient or relevant information in the knowledge base

# For the interface, we have the following features:
# 1. The user can submit questions in the chat, or upload an excel file with multiple questions.
# 2. The user can submit new data for the knowledge base, be it Excel files, CSV files, or PDF files.


# 📄 Private Equity Investor Agent – Data Collection Guide

# This document outlines the structure, questions, and expected data fields for the agent designed to retrieve company information for private equity investors.


# ## 🏢 Company Fundamentals

# | ID          | Question                                                                 | Field               | Data Source / Hint             | Answer Format             |
# |-------------|--------------------------------------------------------------------------|---------------------|-------------------------------|---------------------------|
# | O.DES.NAM   | What is the name of your company?                                        | Company Name        | Project name                  | Text                      |
# | O.DES.REV   | What was the revenue of your company in the most recent financial year?  | Revenue             | Look at turnover              | Numeric                   |
# | O.DES.CUR   | Please state the currency and unit of the revenue above                  | Currency            | e.g., mEUR or tUSD            | Text                      |
# | O.DES.IND   | What is your company’s primary industry classification (GICS IIII)?      | GICS Sub-industry   | Cross-reference with NACE     | Text (GICS code or name)  |

# ---

# ## 🌱 ESG Governance

# | ID            | Question                                                                                     | Field                              | Data Source / Hint         | Answer Format               |
# |----------------|----------------------------------------------------------------------------------------------|------------------------------------|-----------------------------|-----------------------------|
# | O.POL.SUS      | Does your company have an overall policy on sustainability, ESG or similar?                 | Sustainability Policy              | Look at policies in place   | Yes/No + Optional Description |
# | G.PRO.RESB.a   | Does your company have ESG responsibility at board level (person/committee/etc.)?           | Board ESG Oversight                | Check governance documents  | Yes/No                      |
# | O.PRO.MAT      | Has your company assessed material ESG issues within the last 3 years?                      | Materiality Assessment             | ESG reports or policies     | Dropdown (Yes/No)           |
# | O.PRO.MAT.a    | If yes, did the assessment include stakeholder engagement?                                  | Stakeholder Consultation           | Linked to above             | Dropdown (Yes/No)           |
# | O.PRO.MAT.c    | If yes, list the topics assessed to be material.                                            | Material ESG Topics                | ESG reports or disclosures  | Text/list                   |

# ---

# ## 🔐 Cyber Security

# | ID            | Question                                                                                      | Field                             | Data Source / Hint            | Answer Format                 |
# |---------------|-----------------------------------------------------------------------------------------------|-----------------------------------|-------------------------------|-------------------------------|
# | G.POL.CIS     | Does your company have a cyber/information security policy?                                  | Cyber Security Policy             | Check IT/security docs        | Yes/No + Optional Description |
# | G.PRO.ITSM    | Does your company have an IT security management system in place?                            | IT Security Management System     | Cyber security documentation  | Yes/No                        |
# | G.PRO.ITSM.c  | If yes, describe the key elements (certification, coverage, etc.).                           | IT Security System Details        | Same as above                 | Text                          |
# | G.PRO.CIO     | Is there a CIO (or equivalent) responsible for information/cyber security?                   | Chief Information Officer         | Org chart or leadership page  | Yes/No + Optional Name/Title  |
# | G.PER.CYBAT   | Has your company had significant cyber attacks or data breaches in the last 3 years?        | Cyber Attacks or Breaches         | Incident reports              | Yes/No                        |
# | G.PER.CYBAT.a | If yes, briefly describe the incidents.                                                      | Cyber Attack Details              | Same as above                 | Text                          |

# ---

# ## 📝 Usage Guidelines

# - **Agent Logic**:
#   - Pull from structured documents (e.g., annual reports, sustainability reports, cyber policies).

# - **Answer Classification**:
#   - Use tags like `B` (Basic), `O` (Operational), `CA` (Compliance-Aligned), `CM` (Compliance-Missing), etc., for internal tracking of completeness and maturity.

# - **Fallback Strategy**:
#   - If data is missing, tag with “No data” and recommend outreach or clarification request from the company.

# ---




from agno.agent import Agent
from agno.models.openai import OpenAIChat
# from agno.models.anthropic import Claude
# from agno.models.openai.responses import OpenAIResponses
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.csv import CSVKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase

from agno.vectordb.pgvector import PgVector
from agno.team.team import Team
from agno.media import File
from agno.tools.file import FileTools
from agno.tools.local_file_system import LocalFileSystemTools
from custom_tools.read_excel_tool import excel_to_csv
from agno.tools.csv_toolkit import CsvTools
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()


# --------- LOAD API KEY ---------
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    # st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    # st.stop()
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# --------------- LOAD EXCEL FILES -------------------
# You can add your Excel files here or load them dynamically
# excel_to_csv()


# --------------- AGENT INITIALIZATION -------------------
# agent_storage: str = "tmp/agents.db"

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

## PDF Knowledge Base
pdf_kb = PDFKnowledgeBase(
    path="data/knowledge/pdf",
    vector_db=PgVector(
        table_name="companies_reports",
        db_url=db_url,
    ),
)

## CSV Knowledge Base
csv_kb = CSVKnowledgeBase(
    path="data/knowledge/csv",
    # Table name: ai.csv_documents
    vector_db=PgVector(
        table_name="csv_documents",
        db_url=db_url,
    ),
)

# Combine knowledge bases
knowledge_base = CombinedKnowledgeBase(
    sources=[
        csv_kb,
        pdf_kb,
    ],
    vector_db=PgVector(
        table_name="combined_documents",
        db_url=db_url,
    ),
)

# --------------- AGENT INITIALIZATION -------------------

csv_dir = Path("data/knowledge/csv/Extract_database_Absolute_data.csv")

# Create agent with the custom tools and PandasTools
csv_analyzer_agent = Agent(
    #  model=Claude(id="claude-3-5-sonnet-20241022"),
    model=OpenAIChat(id="gpt-4o"),
     markdown=True,
     show_tool_calls=True,
     tools=[CsvTools(csvs=[csv_dir]),LocalFileSystemTools()],
     instructions=[
        "You are a Private Equity Financial Expert. You have access to a knowledge base of financial reports and other informations about the companies",
        "First always get the list of files",
        "Then check the columns in the file",
        # "Then run the query to answer the question",
        "Your goal is to analyze the csv file to determine to what database it should be inserted."
        "You need to determine what is the unique identifier for the table. Example: Project Name, or Project Name + Fund.",
        "You should then split the csv file into 2 separate files; one for the numerical and boolean values (TRUE / FALSE, Yes / No / Blank), which will be inserted into a different csv, and the other which is the text values, which are going to be added to a vector database",
        "For the numerical and boolean values, create a new csv file with the same name as the original file, but with the suffix '_numerical' added to it, in the folder data/knowledge/csv/numerical, and for the text values, create a new csv file with the same name as the original file, but with the suffix '_text' added to it, in the folder data/knowledge/csv/text",
        "You should keep in both csv files the unique identifier column or composite key, and the column names should be the same as in the original file.",
        "Always wrap column names with double quotes if they contain spaces or special characters",
        "Remember to escape the quotes in the JSON string (use \")",
        "Use single quotes for string values"
    ],

)

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
        "You must answer the user's question. in a structured manner, all in the same message.",
    ],
    add_datetime_to_instructions=True,
    # send_team_context_to_members=True,
    show_members_responses=True,
    markdown=True,
)

# --------------- TESTING THE PLAYGROUND  -------------------
# app = Playground(agents=[coordinator,question_intaker,searcher]).get_app()
# app = Playground(teams=[coordinator], agents=[searcher,question_intaker]).get_app()


# --------------- TESTING IN THE PROMPT  -------------------
# if __name__ == "__main__":
#     coordinator.print_response("What was Ericsson's revenue in 2024? Who is Ericsson's CEO?")
