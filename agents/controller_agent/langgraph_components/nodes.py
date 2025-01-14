from typing import Any, Literal, TypedDict

from agents.controller_agent.langgraph_components.helpers import \
    invoke_llm_with_prompt


class ControllerState(TypedDict):
    user_input: str
    intent: Literal[
        "create_workflow", "run_workflow", "regular_sql", "regular_kg", "unknown"
    ]
    workflow_name: str
    final_answer: str
    final_result: str


async def parse_intent(state: ControllerState, llm: Any):
    """Parse user intent using LLM for intuitive decision-making."""
    text = state["user_input"].lower()

    # Prompt LLM to decide the intent
    llm_prompt = """
    You are an intelligent agent capable of classifying user requests.
    Your task is to decide if the given user query relates to:
    1. Running a workflow.
    2. Answering a direct question using either the SQL Agent or the Knowledge Graph Agent.

    If the query is about workflows, specify:
      - "create_workflow" if it requests creating a workflow.
      - "run_workflow" if it requests running a workflow. Include the workflow name.

    If it's a direct question, 
    Two databases are available:
    1. **SQL Database**: Stores structured data in rows and columns. Best suited for:
    - Queries involving aggregation, filtering, or numeric operations.
    - Retrieving tabular data with exact conditions.
    - Questions about counts, averages, sums, or specific records.

    2. **Knowledge Graph**: Represents data as nodes and relationships. Best suited for:
    - Questions involving relationships between entities (especially where people are involved).
    - Understanding how entities are connected or hierarchical queries.
    - Exploring complex, interconnected data.
    You must specify:
      - "regular_sql" if you would like to use the SQL Database to answer the query.
      - "regular_kg" if you would like to use the Knowledge Graph to answer the query.

    Query: "{text}"

    Respond with the intent (e.g., "create_workflow", "run_workflow", "regular_sql", or "regular_kg").
    """

    llm_response = invoke_llm_with_prompt(llm, llm_prompt.format(text=text))
    print(f"Agent Decision: {llm_response}")
    intent, workflow_name = "unknown", None

    if "create_workflow" in llm_response:
        intent = "create_workflow"
    elif "run_workflow" in llm_response:
        intent = "run_workflow"
        workflow_name = llm_response.split("run_workflow")[-1].strip()
    elif "regular_kg" in llm_response:
        intent = "regular_kg"
    else:
        intent = "regular_sql"

    return {"intent": intent, "workflow_name": workflow_name}


async def create_workflow_node(
    state: ControllerState, config: Any, workflow_create_tool
):
    """Handle workflow creation."""
    msg = await workflow_create_tool.ainvoke(state["user_input"], config)
    return {"final_answer": msg}


async def run_workflow_node(
    state: ControllerState,
    config: Any,
    workflow_prompt_tool,
    sql_agent_tool,
    kg_agent_tool,
    controller_tool,
    workflow_notify_tool,
    llm: Any,
    recipient: str = None,
):
    """Handle workflow execution and decide between SQL or KG."""
    workflow_name = state.get("workflow_name", "low_quantity_check")
    workflow_prompt = workflow_prompt_tool(workflow_name)

    # Check if the workflow exists
    if workflow_prompt == "Workflow not found.":
        return {"final_result": "Workflow not found."}

    # Decide which agent to use (SQL or KG)
    agent_prompt = """
    Given the following workflow prompt:
    {workflow_prompt}

    Two databases are available:
        1. **SQL Database**: Stores structured data in rows and columns. Best suited for:
        - Queries involving aggregation, filtering, or numeric operations.
        - Retrieving tabular data with exact conditions.
        - Questions about counts, averages, sums, or specific records.

        2. **Knowledge Graph**: Represents data as nodes and relationships. Best suited for:
        - Questions involving relationships between entities.
        - Understanding how entities are connected or hierarchical queries.
        - Exploring complex, interconnected data.
        You must specify:
        - "use_sql" if you would like to use the SQL Database to answer the prompt.
        - "use_kg" if you would like to use the Knowledge Graph to answer the prompt.
    """
    agent_decision = invoke_llm_with_prompt(
        llm, agent_prompt.format(workflow_prompt=workflow_prompt)
    )

    print(f"Agent Decision: {agent_decision}")

    if "use_sql" in agent_decision:
        response = await sql_agent_tool.ainvoke(workflow_prompt, config)
    else:
        response = await kg_agent_tool.ainvoke(workflow_prompt, config)

    response_content = (
        response.get("output", "") if isinstance(response, dict) else str(response)
    )

    # Generate a decision prompt for the controller
    decision_prompt = f"""
    The following response was received from the query:
    {response_content}

    The workflow condition is as follows:
    {workflow_prompt}

    Does this response indicate a failure of the condition? Respond with:
    - NOTIFY: If it indicates a failure.
    - NO: If the workflow condition is satisfied.
    """
    decision = await controller_tool.ainvoke(decision_prompt, config)

    if "NOTIFY" in decision:
        notification_input = {
            "workflow_name": workflow_name,
            "message": response_content,
        }
        notification = workflow_notify_tool(notification_input)
        return {
            "final_result": f"Workflow '{workflow_name}' condition failed!\nDetails:\n{decision}\nNotification:\n{notification}"
        }

    return {
        "final_result": f"Workflow '{workflow_name}' executed successfully.\nDetails:\n{decision}"
    }


async def sql_node(state: ControllerState, config: Any, sql_agent_tool):
    """Handle SQL queries."""
    response = await sql_agent_tool.ainvoke(state["user_input"], config)
    return {"final_answer": response}


async def kg_node(state: ControllerState, config: Any, kg_agent_tool):
    """Handle KG queries."""
    response = await kg_agent_tool.ainvoke(state["user_input"], config)
    return {"final_answer": response}
