from langchain_core.tools import tool

from agents.controller_agent.langgraph_components.helpers import invoke_llm_with_prompt


def initialize_tools(sql_agent, kg_agent, workflow_agent, llm):
    """Initialize LangGraph tools with agent dependencies."""

    @tool
    def sql_agent_tool(query: str) -> str:
        """Executes a query using the SQL Agent."""
        return sql_agent.ask_question(query)

    @tool
    def kg_agent_tool(query: str) -> str:
        """Executes a query using the Knowledge Graph Agent."""
        return kg_agent.ask_question(query)

    @tool
    def workflow_create_tool(user_text: str) -> str:
        """Creates a workflow based on the user-provided text."""
        name, msg = workflow_agent.parse_workflow_creation(user_text)
        return msg

    @tool
    def workflow_prompt_tool(workflow_name: str) -> str:
        """Retrieves the natural language prompt for a specific workflow."""
        return workflow_agent.get_prompt(workflow_name)

    @tool
    def workflow_notify_tool(workflow_name: str, message: str) -> str:
        """Notifies the user of a workflow condition trigger."""
        return workflow_agent.notify_user(workflow_name, message)

    @tool
    def controller_tool(input_text: str) -> str:
        """Uses the controller LLM to reason about the SQL Agent's response."""
        return invoke_llm_with_prompt(llm, input_text)

    return {
        "sql_agent_tool": sql_agent_tool,
        "kg_agent_tool": kg_agent_tool,
        "workflow_create_tool": workflow_create_tool,
        "workflow_prompt_tool": workflow_prompt_tool,
        "workflow_notify_tool": workflow_notify_tool,
        "controller_tool": controller_tool,
    }
