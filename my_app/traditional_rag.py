from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.pgvector import PgVector, SearchType

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
knowledge_base.load(upsert=True)

question_intaker = Agent(
    name = "Question Intaker",
    model=OpenAIChat(id="gpt-4o"),
    role="Intakes the user's question.",
    description=(
        "You are a Private Equity Financial Expert,",
        "You will receive a question from the user.",
    ),
)

search_agent = Agent(
    name="Searcher",
    model=OpenAIChat(id="gpt-4o"),
    role="Searches the documents to find the answer to the user's question.",
    description=(
        "You are a Private Equity Financial Expert,",
        " You have access to a knowledge base of financial reports and can search the web for additional information.",
    ),
    
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
search_agent.print_response("What was Ericsson's revenue in 2024?")
