from agno.agent import Agent, AgentKnowledge
from agno.models.openai import OpenAIChat
from agno.playground import Playground, serve_playground_app
# from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
# from agno.tools.yfinance import YFinanceTools
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.embedder.openai import OpenAIEmbedder
from agno.vectordb.pgvector import PgVector

agent_storage: str = "tmp/agents.db"


agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    description="You are a Private Equity Financial Expert. You have access to a knowledge base of financial reports and can search the web for additional information.",
    name="Finance Agent",
    instructions=[
        "Search your knowledge base for reports about the companies performance.", 
        "Answer the questions posed by the user.",
    ],
    knowledge=PDFUrlKnowledgeBase(
        urls=["./knowledge/ericsson_2024_full_year_report.pdf"],
        vector_db=LanceDb(
            uri="tmp/lancedb",
            table_name="recipes",
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        ),
    ),
    # tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True
)

# Comment out after the knowledge base is loaded
if agent.knowledge is not None:
    agent.knowledge.load()

app = Playground(agents=[agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("playground:app", reload=True)
