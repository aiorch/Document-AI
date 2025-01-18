import os

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain_openai import ChatOpenAI

from agents.sql_agent.utils import SQL_QA_TEMPLATE

script_dir = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(script_dir, ".env")
load_dotenv(ENV_PATH)

DB_PATH = os.getenv("SQL_DB_PATH", os.path.join(script_dir, "batch_data.db"))

LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-instruct")


class SQLQAAgent:
    def __init__(self, db_path, llm_model="gpt-3.5-turbo-instruct", temperature=0):
        """
        Initializes the SQL Q&A Agent.
        Args:
            db_path (str): Path to the database file.
            llm_model (str): Model name for OpenAI.
            temperature (float): Temperature for LLM response generation.
        """
        # Initialize database
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

        # Initialize LLM
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)

        # Prompt template for SQL Agent
        prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
        system_message = prompt_template.format(dialect="SQLite", top_k=50)

        # SQL toolkit and agent creation
        # self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="tool-calling",
            top_k=50,
            system_message=system_message,
            verbose=True,
            agent_executor_kwargs={"handle_parsing_errors": True},
        )

        print("SQL Q&A Agent initialized successfully!")

    def ask_question(self, question):
        """
        Processes the user's question and returns the SQL Q&A Agent's response.
        Args:
            question (str): User's natural language question.

        Returns:
            str: Agent's response.
        """
        prompt = f"""
        Format your response in a clean, structured way:
        1. If returning tabular data, format it as a list of objects with clear headers
        2. For text responses, use clear paragraphs with proper line breaks
        3. Highlight important information using bold markdown (**text**)
        4. If showing steps or lists, use proper markdown numbering
        The user's query is: {question}. 
        Answer it based on the previous system instruction you recevied.
        """

        prompt += "\n" + SQL_QA_TEMPLATE

        try:
            result = self.agent_executor.invoke({"input": prompt})
            return result["output"]
        except Exception as e:
            return str(e)


if __name__ == "__main__":
    # Initialize SQL Q&A Agent
    agent = SQLQAAgent(db_path=DB_PATH, llm_model=LLM_MODEL)

    print("\nAsk questions about your SQL database!")
    while True:
        user_input = input("Your Question (type 'q' to quit): ")
        if user_input.lower() == "q":
            print("Exiting. Goodbye!")
            break
        response = agent.ask_question(user_input)  # ["output"]
        # response = response.strip("```").lstrip("json").strip()
        print("\nResponse:")
        # print(response)
        print(response)
