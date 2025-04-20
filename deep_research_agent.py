from dotenv import load_dotenv
import os
from typing import TypedDict

from tavily import TavilyClient
from langchain_openai import ChatOpenAI  # ✅ Correct import
from langgraph.graph import StateGraph, END

# ------------------------
# 🔐 Load API keys
# ------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ------------------------
# 🔧 Clients
# ------------------------
tavily = TavilyClient(api_key=TAVILY_API_KEY)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, api_key=OPENAI_API_KEY)

# ------------------------
# 🧾 State Schema
# ------------------------
class ResearchState(TypedDict):
    query: str
    data: str

# ------------------------
# 🧠 Research Agent
# ------------------------
def research_agent(state: ResearchState) -> ResearchState:
    print("[🔹] Research Agent is collecting data...")
    results = tavily.search(state["query"], max_results=5)
    docs = [r["content"] for r in results["results"]]
    compiled = "\n\n".join(docs)
    return {"query": state["query"], "data": compiled}

# ------------------------
# ✍️ Answer Agent
# ------------------------
def answer_agent(state: ResearchState) -> str:
    print("[✍️] Drafting Agent is generating the answer...")
    prompt = f"""
    You are a research assistant. Based on the following data, write a detailed, well-researched response:

    {state['data']}
    """
    return llm.invoke(prompt)

# ------------------------
# 🔄 LangGraph Setup
# ------------------------
def create_graph():
    builder = StateGraph(ResearchState)  # ✅ Schema added here
    builder.add_node("Research", research_agent)
    builder.add_node("Drafting", answer_agent)
    builder.set_entry_point("Research")
    builder.add_edge("Research", "Drafting")
    builder.add_edge("Drafting", END)

    return builder.compile()

# ------------------------
# 🚀 Run
# ------------------------
if __name__ == "__main__":
    query = input("📝 Enter your research query: ")
    graph = create_graph()
    result = graph.invoke({"query": query})
    print("\n✅ Final Answer:\n")
    print(result)