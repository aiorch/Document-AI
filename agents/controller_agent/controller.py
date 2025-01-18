import asyncio
import os
from functools import partial

from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agents.controller_agent.langgraph_components.helpers import initialize_llm
from agents.controller_agent.langgraph_components.nodes import (
    ControllerState, create_workflow_node, kg_node, parse_intent,
    run_workflow_node, sql_node)
from agents.controller_agent.langgraph_components.tools import initialize_tools
from agents.controller_agent.utils.init_agents import (
    initialize_kg_agent, initialize_sql_agent, initialize_workflow_agent)

# Load environment variables
# script_dir = os.path.dirname(os.path.abspath(__file__))
# ENV_PATH = os.path.join(script_dir, ".env")
# load_dotenv(ENV_PATH, override=True)

# Initialize agents and tools
sql_agent = initialize_sql_agent()
kg_agent = initialize_kg_agent()
workflow_agent = initialize_workflow_agent()
llm = initialize_llm()

tools = initialize_tools(sql_agent, kg_agent, workflow_agent, llm)
workflow_create_tool = tools["workflow_create_tool"]
workflow_prompt_tool = tools["workflow_prompt_tool"]
workflow_notify_tool = tools["workflow_notify_tool"]
sql_agent_tool = tools["sql_agent_tool"]
kg_agent_tool = tools["kg_agent_tool"]
controller_tool = tools["controller_tool"]

# Build LangGraph
# Build Graph
graph = StateGraph(ControllerState)
graph.add_node("parse_intent", partial(parse_intent, llm=llm))
graph.add_node(
    "create_workflow_node",
    partial(create_workflow_node, workflow_create_tool=workflow_create_tool),
)
graph.add_node(
    "run_workflow_node",
    partial(
        run_workflow_node,
        workflow_prompt_tool=workflow_prompt_tool,
        sql_agent_tool=sql_agent_tool,
        kg_agent_tool=kg_agent_tool,
        controller_tool=controller_tool,
        workflow_notify_tool=workflow_notify_tool,
        llm=llm,
    ),
)
graph.add_node("sql_node", partial(sql_node, sql_agent_tool=sql_agent_tool))
graph.add_node("kg_node", partial(kg_node, kg_agent_tool=kg_agent_tool))

# Define edges
graph.add_edge(START, "parse_intent")


# Routing logic based on intent
def pick_next_node(state: ControllerState) -> str:
    return {
        "create_workflow": "create_workflow_node",
        "run_workflow": "run_workflow_node",
        "regular_sql": "sql_node",
        "regular_kg": "kg_node",
    }.get(
        state["intent"], "sql_node"
    )  # Default to SQL if intent is unknown


graph.add_conditional_edges("parse_intent", pick_next_node)
graph.add_edge("create_workflow_node", END)
graph.add_edge("run_workflow_node", END)
graph.add_edge("sql_node", END)
graph.add_edge("kg_node", END)

memory = MemorySaver()
app = graph.compile(checkpointer=memory)


# Main loop
async def main():
    config = {"configurable": {"thread_id": "workflow-thread"}}
    while True:
        user_input = input("Enter your query (type 'q' to quit): ")
        if user_input.lower() == "q":
            break
        if user_input == "":
            print("No query specified, Try again!")
            continue
        state = await app.ainvoke({"user_input": user_input}, config=config)
        print(f"Input: {state['user_input']}")
        if "final_answer" in state:
            print(f"Answer: {state['final_answer']}")
        if "final_result" in state:
            print(f"Result: {state['final_result']}")


if __name__ == "__main__":
    asyncio.run(main())
