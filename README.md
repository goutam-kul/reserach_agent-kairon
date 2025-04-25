# Deep Reserach Agent
A Deep Research AI Agentic System

# Details 
This is a `langgraph` based Agentic system, consisting of 3 agents. A Redis caching system is introduced to cache the Tavily search response. To save tavily credits. Whenever a new response is generated using Tavily API the reponse is stored inside redis database with a unique key. Whenever tavily tool is called by the agent, we first search the key in redis database, if the key exists we query the results from redis. 

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
- Clone the repo: `git clone https://github.com/goutam-kul/reserach_agent-kairon.git`
- Install Redis: Redis is a dependecy of the application. Please refer to this guide for redis installation [InstallRedis](https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/)
- Configure `.env` file:
  ```
  - GEMINI_API_KEY=YOUR_GEMINI_API_KEY
  - TAVILY_API_KEY=YOUR_TAVILY_API_KEY
  - REDIS_PASSWORD=YOUR_PASSWORD
  ```
- Install Dependencies: Install the required dependency using `pip install -r requirements.txt`
- Run the application: `python src/agent.py`


# Tech Stack 
```
Python 3.11+
langchain
langgraph
redis
pydantic
```
