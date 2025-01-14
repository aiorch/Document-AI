import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# script_dir = os.path.dirname(os.path.abspath(__file__))
# ENV_PATH = os.path.join(script_dir, "../.env")
# load_dotenv(ENV_PATH, override=True)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


def initialize_llm():
    """Initialize the LLM for general use."""
    return ChatOpenAI(model=OPENAI_MODEL, temperature=0)


def invoke_llm_with_prompt(llm, prompt):
    """Send a prompt to the LLM and return its response."""
    messages = [HumanMessage(content=prompt)]
    return llm.invoke(messages).content
