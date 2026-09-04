from dotenv import load_dotenv

from logging_config import setup_logging
from src.filesystem_agent.filesystem_agent import FilesystemAgent


def main():
    setup_logging()

    env_loaded = load_dotenv()
    if not env_loaded:
        raise RuntimeError("Environment variables file `.env` not found.")

    agent = FilesystemAgent()
    question = input("Enter your question: ")
    agent.ask(question=question)


if __name__ == "__main__":
    main()
