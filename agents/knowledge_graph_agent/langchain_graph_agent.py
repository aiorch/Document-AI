import os

from dotenv import load_dotenv
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_openai import ChatOpenAI

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

# Neo4j credentials
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")

LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-instruct")


class GraphQAAgent:
    def __init__(self, uri, username, password, llm_model="gpt-4"):
        # Connect to Neo4j
        self.graph = Neo4jGraph(url=uri, username=username, password=password)
        self.graph.refresh_schema()  # Fetch graph schema
        self.llm = ChatOpenAI(model=llm_model, temperature=0)

        # Build QA Chain
        self.chain = GraphCypherQAChain.from_llm(
            graph=self.graph, llm=self.llm, verbose=True, allow_dangerous_requests=True
        )

    def ask_question(self, question):
        response = self.chain.invoke({"query": question})
        return response.get("result", "No result found.")


if __name__ == "__main__":
    # Initialize QA Agent
    agent = GraphQAAgent(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        llm_model=LLM_MODEL,
    )

    print("\nAsk questions about your graph database!")
    while True:
        user_input = input("Your Question (type 'q' to quit): ")
        if user_input.lower() == "q":
            print("Exiting. Goodbye!")
            break
        response = agent.ask_question(user_input)
        print("\nResponse:")
        print(response)
