from loguru import logger
from typing import List, Dict, Optional, TypedDict

class ResearchState(TypedDict):
    # Original query as input 
    initial_query: str 

    # Planning output
    research_plan: Optional[List[str]] # NEW: List of sub-queries/keywords
    # Purpose: Stores the list of focused questions generated by the planner.
    # Populated by: The plan_research_node.
    # Used by: The research_node to guide searches.
    
    search_results: Optional[Dict[str, str]]
    # Purpose: Stores the actual results obtained by Tavily 
    # Populated by: The search node after calling CachedTavilyTool and parsing the JSON.
    # Used by: The drafting node to generate the answer.

    # Error Handling
    error: Optional[str]
    
    # Final output
    final_answer: Optional[str]
    # Populated by: The drafting node
    # Used by: The final output of the graph execution 

        
    
