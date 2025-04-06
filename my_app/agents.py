from pathlib import Path
from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.anthropic import Claude
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.csv import CSVKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.team.team import Team
from agno.tools.file import FileTools
from agno.tools.csv_toolkit import CsvTools
from agno.tools.local_file_system import LocalFileSystemTools
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.email import EmailTools
# from custom_tools.excel_tools import ExcelTools, 

import os
from dotenv import load_dotenv

# --------- LOAD API KEY ---------
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")


# csv_dir_final = Path("data/knowledge/csv/Extract_database_Absolute_data.csv")

# csv_analyzer_agent = Agent(
#         #  model=Claude(id="claude-3-5-sonnet-20241022"),
#         model=OpenAIChat(id="gpt-4o"),
#         markdown=True,
#         show_tool_calls=True,
#         tools=[CsvTools(csvs=[csv_dir_final]),LocalFileSystemTools()],
#         instructions=[
#             "You are a Private Equity Financial Expert. You have access to a knowledge base of financial reports and other informations about the companies",
#             "You are going to answer the questions based on the csv files provided",
#             "All of the numerical values, unless explained otherwise, are in M€ (Million Euros)",
#         ],

#     )



# Database connection
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

def get_financial_team(model_id: str = "openai:gpt-4o", session_id: Optional[str] = None) -> Team:
    """Initialize the financial agent team with all necessary components
    
    Args:
        model_id (str): Model identifier in format "provider:model_name"
        session_id (Optional[str]): Optional session ID for loading existing team
        
    Returns:
        Team: The initialized financial agent team
    """
    # Parse model ID to get provider and model name
    provider, model_name = model_id.split(":", 1)
    
    # Initialize model based on provider
    if provider == "openai":
        model = OpenAIChat(id=model_name)
    elif provider == "anthropic":
        model = Claude(id=model_name)
    else:
        raise ValueError(f"Unsupported model provider: {provider}")
    
    # Initialize knowledge bases
    # PDF Knowledge Base
    pdf_kb = PDFKnowledgeBase(
        path="data/knowledge/pdf",
        vector_db=PgVector(
            table_name="companies_reports",
            db_url=db_url,
        ),
    )

    # CSV Knowledge Base
    csv_kb = CSVKnowledgeBase(
        path="data/knowledge/csv",
        vector_db=PgVector(
            table_name="csv_documents",
            db_url=db_url,
        ),
    )

    # Combine knowledge bases
    knowledge_base = CombinedKnowledgeBase(
        sources=[
            csv_kb,
            # pdf_kb,
        ],
        vector_db=PgVector(
            table_name="combined_documents",
            db_url=db_url,
        ),
    )
    
    # Initialize agents with storage for persistence
    storage = PostgresAgentStorage(table_name="financial_agent_sessions", db_url=db_url)
    
    # Excel directory for Excel tools
    excel_dir = Path("data/knowledge")
    excel_files = list(excel_dir.glob("*.xlsx"))
    
    # Create Question Intaker Agent
    question_intaker = Agent(
        name="Question Intaker",
        model=model,
        role="Intakes the user's question(s).",
        description="""
            You are a Private Equity Financial Expert.
            You will receive questions from the user. You will need to parse them and ask the Searcher to find the answers.
            You might receive the question in a single message, multiple lines, or embedded in Excel files, Word documents, or PDFs.
            Use your tools to read the files and parse the questions.
        """,
        tools=[FileTools()],
        # storage=storage,
        show_tool_calls=True,
        markdown=True,
    )
    
    # Create the Excel Processor Agent
    excel_processor = Agent(
        name="Excel Processor",
        model=model,
        role="Processes Excel files to extract and analyze data.",
        description="""
            You are an Excel processing expert for financial data.
            You can convert Excel files to CSV format, analyze sheets and extract relevant information.
            You help organize financial data for the knowledge base.
        """,
        tools=[
            LocalFileSystemTools(),
            CsvTools()
        ],
        # storage=storage,
        show_tool_calls=True,
        markdown=True,
        instructions=[
            "Convert Excel files to CSV format when needed.",
            "Analyze Excel sheets to identify relevant columns and data.",
            "Help structure financial data for the knowledge base.",
            "Extract questions from Excel files when they contain investor questions."
        ]
    )


    csv_dir = Path("data/knowledge/csv/Extract_database_Absolute_data.csv")

    # Create agent with the custom tools and PandasTools
    csv_parser_agent = Agent(
        #  model=Claude(id="claude-3-5-sonnet-20241022"),
        name = "CSV Parser Agent",
        model=model,
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

    csv_dir_final = Path("data/knowledge/csv/Extract_database_Absolute_data.csv")

    csv_analyzer_agent = Agent(
        #  model=Claude(id="claude-3-5-sonnet-20241022"),
        name = "CSV Analyzer Agent",
        role="Analyzes CSV files to extract and analyze data.",
        model=OpenAIChat(id="gpt-4o"),
        markdown=True,
        show_tool_calls=True,
        tools=[CsvTools(csvs=[csv_dir_final]),LocalFileSystemTools()],
        description="""
            You are a Private Equity Financial Expert. You have access to a knowledge base of financial reports and other informations about the companies.
            You are going to answer the questions based on the csv files provided.""",
        instructions=[
            "First always get the list of files",
            "Then check the columns in the file",
            "Then run the query to answer the question",
            # "You are going to act as a text-to-sql agent, creating the necessary query to answer the user question"
            "All of the numerical values, unless explained otherwise, are in M€ (Million Euros)",
            "OPEX is Operational Expenditure, and it's percentual",
        ],

    )
    
    # Create Searcher Agent
    searcher = Agent(
        name="Searcher",
        model=model,
        role="Searches documents to find answers to financial questions",
        description="""
            You are a Private Equity Financial Expert. 
            You have access to a knowledge base of reports and other information about companies.
            Your role is to find accurate answers to investor questions by searching the knowledge base.
            "You never retrieve numerical data from the knowledge base to the coordinator because you work with text embeddings",
        """,
        instructions=[
            "Search the knowledge base for information about company performance and financial details.",
            "Provide accurate answers based on the available information.",
            "Look for textual content like Code NACE (what the company does) ESG policies, and security measures.",
            "You never retrieve numerical data from the knowledge base because you work with text embeddings",
            "If information is missing or uncertain, clearly indicate this."
        ],
        knowledge=csv_kb,
        add_references=True,
        search_knowledge=True,
        # storage=storage,
        markdown=True,
        show_tool_calls=True,
    )

    # Create Sanity Checker Agent
    sanity_checker = Agent(
        name="Sanity Checker",
        model=model,
        role="Verifies the accuracy and completeness of answers.",
        description="""
            You are a verification expert for financial information.
            You check answers for accuracy, completeness, and confidence level.
            You ensure that the information provided is reliable and backed by evidence.
        """,
        instructions=[
            "Review answers for accuracy and completeness.",
            "Assess confidence level based on available evidence.",
            "Verify that numerical data is correctly represented.",
            "Flag any potential inconsistencies or uncertainties.",
            "Suggest improvements or additional information needed."
        ],
        storage=storage,
        markdown=True,
    )

    receiver_email = "<henrique.toledo@artefact.com>"
    sender_email = "<agent@investoriq.com>"
    sender_name = "InvestorIQ Agent"
    sender_passkey = "test_passkey"

    email_sender = Agent(
        tools=[
            EmailTools(
                receiver_email=receiver_email,
                sender_email=sender_email,
                sender_name=sender_name,
                sender_passkey=sender_passkey,
            )
        ]
    )
    
    # Create Coordinator Team
    coordinator = Team(
        name="Financial Expert Team",
        mode="coordinate",
        model=model,
        members=[question_intaker, searcher, excel_processor, sanity_checker,csv_analyzer_agent],
        description="""
            You are a senior Private Equity Financial Expert leading a team of specialists.
            Your goal is to provide accurate, structured responses to investor questions by coordinating your team effectively.
            The questions might be about financial information, or ESG policies, or security measures.
        """,
        instructions=[
            "You are the coordinator of a team of financial experts.",

            "This is the flow you are going to follow:",
            "1. First, understand the user question with your knowledge.", 
            "2. If the user question involves a numerical output, ask the csv_analyzer_agent to analyze the csv file and end the response",
            "3. If the question is about a textual information, ask the Searcher to find the answer in the knowledge base. Never return numerical information ",
            "4. If a question is answered by the csv_analyzer_agent , do not ask Searcher to look for it",
            # # "For simple, direct questions, ask the Searcher to find the answer in the knowledge base.",
            # # "If the question involves retrieving numerical data, ask the searcher to use the CSV knowledge base.",
            # # "For questions involving Excel files or multiple questions, involve the Question Intaker and Excel Processor.",
            # # "4. Ask the sanity checker to verify the answers.",
            "Finally, compile the answers and provide a structured response to the user.",
            "Your answer must follow this structure: Question 1: Answer 1, Question 2: Answer 2, etc.",
            "Structure your responses clearly with headings, bullet points, and tables when appropriate.",
            # "For questions about ESG, cyber security, or other specialized topics, make sure to search for relevant documents.",
            # "If information is not available, clearly state this and suggest what additional data might be needed."
        ],
        # storage=storage,
        session_id=session_id,
        add_datetime_to_instructions=True,
        show_members_responses=True,
        markdown=True,
    )
    
    # Change back to coordinator, choose what agent you want to return
    return coordinator

if __name__ == "__main__":
    # Example usage
    team = get_financial_team()

    team.print_response("What is the Total value for Special Project 11? What is the OPEX?")
