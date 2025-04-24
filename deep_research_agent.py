# from dotenv import load_dotenv
# import os
# from typing import TypedDict

# from tavily import TavilyClient
# from langchain_openai import ChatOpenAI  # ✅ Correct import
# from langgraph.graph import StateGraph, END

# # ------------------------
# # 🔐 Load API keys
# # ------------------------
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# # ------------------------
# # 🔧 Clients
# # ------------------------
# tavily = TavilyClient(api_key=TAVILY_API_KEY)
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=OPENAI_API_KEY)

# # ------------------------
# # 🧾 State Schema
# # ------------------------
# class ResearchState(TypedDict):
#     query: str
#     data: str

# # ------------------------
# # 🧠 Research Agent
# # ------------------------
# def research_agent(state: ResearchState) -> ResearchState:
#     print("[🔹] Research Agent is collecting data...")
#     results = tavily.search(state["query"], max_results=5)
#     docs = [r["content"] for r in results["results"]]
#     compiled = "\n\n".join(docs)
#     return {"query": state["query"], "data": compiled}

# # ------------------------
# # ✍️ Answer Agent
# # ------------------------
# def answer_agent(state: ResearchState) -> str:
#     print("[✍️] Drafting Agent is generating the answer...")
#     prompt = f"""
#     You are a research assistant. Based on the following data, write a detailed, well-researched response:

#     {state['data']}
#     """
#     return llm.invoke(prompt)

# # ------------------------
# # 🔄 LangGraph Setup
# # ------------------------
# def create_graph():
#     builder = StateGraph(ResearchState)  # ✅ Schema added here
#     builder.add_node("Research", research_agent)
#     builder.add_node("Drafting", answer_agent)
#     builder.set_entry_point("Research")
#     builder.add_edge("Research", "Drafting")
#     builder.add_edge("Drafting", END)

#     return builder.compile()

# # ------------------------
# # 🚀 Run
# # ------------------------
# if __name__ == "__main__":
#     query = input("📝 Enter your research query: ")
#     graph = create_graph()
#     result = graph.invoke({"query": query})
#     print("\n✅ Final Answer:\n")
#     print(result)


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
