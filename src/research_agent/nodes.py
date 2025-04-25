import re
import json
from loguru import logger
from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.settings import settings
from src.tavily.tavily_tool import CachedTavilyTool
from src.research_agent.states import ResearchState

llm = ChatGoogleGenerativeAI(
    google_api_key=settings.GEMINI_API_KEY,
    model=settings.LLM_MODEL,
    temperature=0,
)

# Helper functions
def remove_json_fences(text: str):
    """Removes the ```markdown ... ``` fences."""
    # Ensure input is a string
    text = str(text).strip()
    # Remove backtick markdown tags
    text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    return text


class ResearchPlan(BaseModel):
    "Structured plan for research"
    sub_questions: List[str] = Field(..., description="A list of 3-5 specific, factual questions or search terms derived from the main query.")


# --- Plannder Node ---
def plan_research_node(state: ResearchState):
    """Analyzes the initial query and generates a reserach plan (list of sub-questions)"""
    logger.info("--- PLANNER AGENT ---")
    query = state['initial_query']
    if not query: 
        logger.error('Initial query is missing for planning')
        return {"error": "Initial query is missing."}
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a research planning assistant. Your goal is to break down the user's main query into 3-5 specific, factual sub-questions or keywords suitable for web searches."
        "Focus on covering key aspects. Respond ONLY with a JSON object containing a single key 'sub_questions' which holds a list of strings."),
        ("human", "Please generate a JSON research plan for the query: {query}")
    ])

    chain = prompt_template | llm
    try: 
        raw_response = chain.invoke({'query': query})
        # logger.debug(f"Raw response: {raw_response}")
        # Remove the json fences
        cleaned_response = remove_json_fences(raw_response.content)
        # logger.debug(f"Cleaned Reponse:\n{cleaned_response}")
        # Parse the JSON output
        plan_json = json.loads(cleaned_response)
        # logger.debug(f"Parsed JSON: {plan_json}")
        validate_plan = ResearchPlan(**plan_json)
        plan = validate_plan.sub_questions

        logger.success(f"Generated research plan: {plan}")
        return {"research_plan": plan}
    except json.JSONDecodeError as e:
        logger.error(f"Planner Node: Failed to parse LLM json output: {str(e)}")
        return {"error": f"Planner node failed to generate valid JSON respnose: {str(e)}"}


# --- Research Node ---
def research_node(state: ResearchState):
    """
    Performs web searches based on the research plan using Tavily.
    """
    logger.info("--- RESEARCH AGENT ---")
    plan = state.get('research_plan')
    initial_query = state.get('initial_query')
    # Error handling
    if not plan:
        logger.warning("Research Node: No research plan recieved. Falling back to initial query")
        if not initial_query:
            logger.error("Research Node: Cannot proceed without a plan or initial query.")
            return {"error": "Research plan and initial query both missing."}
    
    tool = CachedTavilyTool()
    all_search_results = [] # Accumulates search results for each sub-query

    for sub_query in plan:
        logger.info(f"Research Node: Researching sub-query - {sub_query}")
        tool_response = tool._invoke(query=sub_query)

        if tool_response['status'] == "error":
            error = tool_response.get('details', 'Unkown Tavily Error')
            logger.warning(f'Tavily serach failed for sub-query: {sub_query}: {error}')
            # # Update error field in state
            # state['error'] = f"Tavily search failed: {error}"
            # # Return a dictionary with error details 
            # return {"error": f"Tavily search failed: {error}"}
            continue # Skip to the next query 

        elif tool_response['status'] == "success":
            # get JSON string from dictionary 
            tavily_response_json = tool_response['tavily_response']
            # Parse and store JSON in dict like object
            if tavily_response_json:
                try:
                    tavily_response_dict = json.loads(tavily_response_json)
                    # Update the search_results in state
                    # state['search_results'] = tavily_response_dict
                    # logger.debug(type(tavily_response_dict))
                    results_list = tavily_response_dict.get('results', [])
                    if isinstance(results_list, list):
                        all_search_results.extend(results_list) # Add results from this sub-query
                        logger.success(f"Successfully added {len(results_list)} results from sub-query:{sub_query}")
                    else:
                        logger.warning(f"Tavily response for '{sub_query}' did not contain a list under 'results' key")
                except json.JSONDecodeError as e:
                    logger.error(f"Json decoder error: {str(e)}")
                    continue
            else:
                logger.warning(f"Tavily call succeeded for '{sub_query}' but response was empty.")

        if not all_search_results:
            logger.warning("Research Node: No search results gathered after processing the plan.")
            return {"search_results": []}
        
        logger.info(f"Accumaulated a total number of {len(all_search_results)} search results.")

        # Finally return the dict object 
    return {"search_results": all_search_results}

# --- Drafting Node ---
def draft_node(state: ResearchState):
    """
    Drafts the final answer based on accumulated search results
    """
    logger.info("--- DRAFTING AGENT ---")
    initial_query = state.get('initial_query')
    search_results = state.get('search_results')

    # logger.debug(f"drafting_node: type of {type(search_results)}")
    # logger.debug(f"context string:\n\n{search_results}")
    if not search_results:
        logger.warning("Drafting Node: No search results available to draft an answer.")
        return {"final_answer": "I could not find sufficient information to process your request"}
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "Your are a Report Drafter. Organize the research summary into an easy to understand, professional and readable markdown format."
         "Attach all the relevant information as clickable links (e.g., url, blogs). Answer the query with the provided context only, if the context is"
         "insufficient, state that clearly. Do not use Outside knowledge."),
        ("human", "Context:\n{search_context}\n\nQuery: {query}\n\nAnswer:")
    ])

    chain = prompt_template | llm
   
    context_str = "\n\n".join(
        f"Source {i + 1}: (URL: {res.get('url', 'N/A')}):\n{res.get('content', 'N/A')}"
        for i, res in enumerate(search_results)
        if res.get('content')
    )

    if not context_str:
        logger.warning("Drafting Node: Search results were present but context string empty.")
        return {"final_answer": "Found sources, but could could not extract relevant content to answer the query."}
    
    logger.debug(f"context string:\n\n{context_str[:500]}...")

    try:
        response = chain.invoke({"search_context": context_str, "query": initial_query})
        final_answer = response.content
        return {"final_answer": final_answer}
    except Exception as e:
        logger.error(f"Error during LLM drafting: {str(e)}")
        return {"error": f"Failed to draft answer: {str(e)}"}