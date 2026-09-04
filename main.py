from dotenv import load_dotenv

from src.filesystem_agent.filesystem_agent import FilesystemAgent


def main():
    env_loaded = load_dotenv()
    if not env_loaded:
        raise Exception("Environment variables file `.env` not found.")

    agent = FilesystemAgent()
    question = input("Enter your question: ")
    agent.ask(question=question)


if __name__ == "__main__":
    main()
