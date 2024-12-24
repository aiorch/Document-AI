from typing import Any, Literal, TypedDict


class ControllerState(TypedDict):
    user_input: str
    intent: Literal[
        "create_workflow", "run_workflow", "regular_sql", "regular_kg", "unknown"
    ]
    workflow_name: str
    final_answer: str
    final_result: str


async def parse_intent(state: ControllerState, config: Any):
    """Parse user intent."""
    text = state["user_input"].lower()
    if "create a workflow" in text:
        return {"intent": "create_workflow"}
    elif "run workflow" in text:
        workflow_name = text.split("workflow")[-1].strip().split()[0]
        return {"intent": "run_workflow", "workflow_name": workflow_name}
    elif "knowledge graph" in text or "kg" in text:
        return {"intent": "regular_kg"}
    return {"intent": "regular_sql"}


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
    controller_tool,
    workflow_notify_tool,
):
    """Handle workflow execution."""
    workflow_name = state.get("workflow_name", "low_quantity_check")
    workflow_prompt = workflow_prompt_tool(workflow_name)
    if workflow_prompt == "Workflow not found.":
        return {"final_result": "Workflow not found."}

    sql_response = await sql_agent_tool.ainvoke(workflow_prompt, config)
    decision_prompt = f"""
    The following response was received:
    {sql_response}
    Does this indicate a failure? Respond with NOTIFY or NO.
    """
    decision = await controller_tool.ainvoke(decision_prompt, config)
    if "NOTIFY" in decision:
        notification = workflow_notify_tool(workflow_name)
        return {"final_result": f"Workflow failed.\n{notification}"}
    return {"final_result": "Workflow executed successfully."}


async def sql_node(state: ControllerState, config: Any, sql_agent_tool):
    """Handle SQL queries."""
    response = await sql_agent_tool.ainvoke(state["user_input"], config)
    return {"final_answer": response}


async def kg_node(state: ControllerState, config: Any, kg_agent_tool):
    """Handle KG queries."""
    response = await kg_agent_tool.ainvoke(state["user_input"], config)
    return {"final_answer": response}
