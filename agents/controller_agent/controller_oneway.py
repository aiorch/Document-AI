import json
import os
from typing import Any, Dict, Union

from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.chains.base import Chain
from langchain.chains.router import LLMRouterChain, MultiRouteChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.base import BaseOutputParser
from pydantic import BaseModel, Field

from agents.knowledge_graph_agent.langchain_graph_agent import GraphQAAgent
from agents.sql_agent.langchain_sql_agent import SQLQAAgent

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")

load_dotenv(ENV_PATH, override=True)

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


#######################################
# Wrap each agent in a chain-like class
#######################################
class SQLQueryChain(Chain):
    """Wraps the SQLQAAgent in a LangChain Chain interface."""

    sql_agent: SQLQAAgent

    @property
    def input_keys(self) -> list:
        # The name(s) of keys this chain expects in the input dictionary
        return ["input"]

    @property
    def output_keys(self) -> list:
        # The name(s) of keys this chain returns in the output dictionary
        return ["output"]

    def _call(self, inputs: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        # This is what happens when another chain or the user calls .call(...)
        user_input = inputs["input"]
        answer = self.sql_agent.ask_question(user_input)
        return {"output": answer}


class KGQueryChain(Chain):
    """Wraps the GraphQAAgent in a LangChain Chain interface."""

    kg_agent: GraphQAAgent

    @property
    def input_keys(self) -> list:
        return ["input"]

    @property
    def output_keys(self) -> list:
        return ["output"]

    def _call(self, inputs: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        user_input = inputs["input"]
        answer = self.kg_agent.ask_question(user_input)
        return {"output": answer}


########################################
# Router LLM and Router Prompt
########################################
router_template = """
You are a routing model. Return valid JSON with exactly two keys: "destination" and "next_inputs".

Descriptions of available agents:
- "sql_chain": Handles questions about SQL databases. Use this for tasks like querying data, aggregations, or filtering records from a structured database.
- "kg_chain": Handles questions about the knowledge graph. Use this for tasks that require reasoning over relationships, entities, and their connections.

Rules:
- "destination" must be either "sql_chain" or "kg_chain".
- "next_inputs" must be a JSON object containing exactly one key: "input", whose value is the user's question.
- DO NOT include newlines or spaces in the JSON key names. 
- DO NOT add triple quotes, code fences, or any text outside the JSON.

User's question: {input}
"""


class RouterOutput(BaseModel):
    destination: str
    next_inputs: Dict[str, str] = Field(default_factory=dict)


router_output_parser = PydanticOutputParser(pydantic_object=RouterOutput)


class RouterOutputParser(BaseOutputParser):
    def parse(self, output: Union[str, Dict[str, Any]]) -> RouterOutput:
        if isinstance(output, str):
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                raise ValueError(f"Failed to parse output as JSON: {output}")
        elif isinstance(output, dict):
            parsed = output
        else:
            raise TypeError(f"Unsupported output type: {type(output)}")

        # Validate and convert to RouterOutput using Pydantic
        return RouterOutput(**parsed)

    def parse_with_prompt(
        self, completion: Dict[str, Any], prompt: str
    ) -> RouterOutput:
        return self.parse(completion["text"])


router_output_parser = RouterOutputParser()

router_prompt = PromptTemplate(
    template=router_template,
    input_variables=["input"],
    output_parser=router_output_parser,
)

router_llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)


class LLMRouterChain(LLMRouterChain):
    def _call(self, inputs: Dict[str, Any], run_manager=None) -> Dict[str, Any]:
        result = super()._call(inputs, run_manager=run_manager)
        if "text" in result and isinstance(result["text"], dict):
            text_dict = result["text"]
            result.update(text_dict)
            del result["text"]
        return dict(result)


router_llm_chain = LLMChain(llm=router_llm, prompt=router_prompt, verbose=True)

router_chain = LLMRouterChain(llm_chain=router_llm_chain, verbose=True)

# Build the Q&A agents
sql_agent = SQLQAAgent(
    db_path=os.getenv("SQL_DB_PATH", "batch_data.db"), llm_model=OPENAI_MODEL
)
kg_agent = GraphQAAgent(
    uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "neo4j"),
    llm_model=OPENAI_MODEL,
)

sql_query_chain = SQLQueryChain(sql_agent=sql_agent)
kg_query_chain = KGQueryChain(kg_agent=kg_agent)

# Define a fallback chain for when the router doesn't return one of the agent options
fallback_prompt = PromptTemplate(
    template="Sorry, I cannot determine the right chain for: {input}",
    input_variables=["input"],
)
fallback_chain = LLMChain(llm=router_llm, prompt=fallback_prompt)

########################################
# Assemble the high-level RouterChain
########################################

multi_route_chain = MultiRouteChain(
    router_chain=router_chain,
    destination_chains={"sql_chain": sql_query_chain, "kg_chain": kg_query_chain},
    default_chain=fallback_chain,
    verbose=True,
)


def main():
    print("Welcome to the new MultiRouteChain!\n")
    while True:
        user_question = input("Ask anything (type 'q' to quit): ")
        if user_question.lower() == "q":
            print("Exiting.")
            break

        answer_dict = multi_route_chain.invoke({"input": user_question})
        print(answer_dict)
        answer = answer_dict["output"]
        print(f"\nAnswer:\n{answer}\n{'-'*40}")


if __name__ == "__main__":
    main()
