# Deep Reserach Agent
A Deep Research AI Agentic System

### Tech Stack 
```
Python 3.11+
langchain
langgraph
redis
pydantic
```
# Details 
This is a `langgraph` based Agentic system, consisting of 3 agents - 

## Agents 
1. **Planner Agent** 
- Takes the initial user query and generates sub query using LLM call. 
- The sub-queries provide more context while being closely aligned with the original query.

2. **Research Agent**
- Reserach agent takes the List of sub-queries and iterate through it.
- For each iteration calls the Cached Tavily Search tool and either gets the cached response or calls the tavily tool to get new response.

3. **Drafter Agent** 
- Drafter agent takes takes `search_results` from research agent as context and creates a readable markdown report.

# Setup & Usage
- Clone the repo: git clone
