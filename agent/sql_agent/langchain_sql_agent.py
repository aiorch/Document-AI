import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.llms import OpenAI
from langchain.sql_database import SQLDatabase
from langchain import hub

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "batch_data.db")
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
system_message = prompt_template.format(dialect="SQLite", top_k=5)
llm=OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    system_message=system_message,
    verbose=True
)

print("Ask a question about the data in your database:")
while True:
    query = input("Your question (or 'q' to quit): ")
    if query.lower() == "q":
        break
    print("Answer:")
    print(agent_executor.run(query))
