import os
from dotenv import load_dotenv
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, END

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("🚨 Missing GEMINI_API_KEY in .env")
if not TAVILY_API_KEY:
    raise ValueError("🚨 Missing TAVILY_API_KEY in .env")

# Initialize Gemini Pro
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro-latest",
    temperature=0.7,
    google_api_key=GEMINI_API_KEY,
)

# Initialize Tavily tool
tavily_tool = TavilySearchResults(api_key=TAVILY_API_KEY)

# LangGraph state type
class GraphState(TypedDict):
    query: str
    research: str
    answer: str

# Research agent using Tavily
def research_agent(state: GraphState) -> dict:
    query = state["query"]
    print("[🔍] Research Agent is collecting data...")
    results = tavily_tool.invoke({"query": query})

    content = "\n\n".join([r["content"] for r in results])
    return {"research": content}

# Drafting agent using Gemini Pro
def answer_agent(state: GraphState) -> dict:
    query = state["query"]
    research = state["research"]

    print("[✍️] Drafting Agent is generating the answer...")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant. Use the research below to answer the query."),
        ("human", f"Query: {query}\n\nResearch:\n{research}")
    ])

    try:
        messages = prompt.format_messages()  # ✅ Format to list of BaseMessages
        response = llm.invoke(messages)      # ✅ Pass to Gemini-Pro
        return {"answer": response.content}
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return {"answer": "⚠️ Error generating response."}

# Build LangGraph
workflow = StateGraph(GraphState)
workflow.add_node("Research", research_agent)
workflow.add_node("Drafting", answer_agent)

workflow.set_entry_point("Research")
workflow.add_edge("Research", "Drafting")
workflow.add_edge("Drafting", END)

graph = workflow.compile()

# Run the full pipeline
if __name__ == "__main__":
    print("🤖 Deep Research Agentic System (Tavily + Gemini Pro)")
    query = input("📝 Enter your research query: ")

    result = graph.invoke({"query": query})
    print("\n✅ Final Answer:\n")
    print(result["answer"])
