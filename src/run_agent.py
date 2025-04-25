from loguru import logger
from src.research_agent.states import ResearchState
from src.research_agent.nodes import plan_research_node, research_node, draft_node
from langgraph.graph import StateGraph, END

workflow = StateGraph(ResearchState)
workflow.add_node("plan", plan_research_node)
workflow.add_node("search", research_node)
workflow.add_node("draft", draft_node)

# Set entry points
workflow.set_entry_point("plan")

# Add edges
workflow.add_edge("plan", "search")
workflow.add_edge("search", "draft")
workflow.add_edge("draft", END)

app = workflow.compile()

# --- Testing ----
if __name__ == "__main__":
    query = input("Enter your query: ")
    initial_state = {"initial_query": query}
    
    logger.info(f"Starting Research")
    final_state = app.invoke(initial_state)

    print("\n--- Final State ---")
    import pprint
    # pprint.pprint(final_state)

    if final_state.get('error'):
        print("\n--- ERROR ---")
        print(final_state['error'])
    elif final_state.get('final_answer'):
        print("\n--- FINAL ANSWER ---")
        print(final_state['final_answer'])
    else:
        print("\n--- No final answer or error produced ---")

    output_filename = input("Enter a name for markdown file to save: ")
    # Save report as markdown
    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(final_state['final_answer'])
