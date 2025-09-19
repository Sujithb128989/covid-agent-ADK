import os
import asyncio
import warnings
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

warnings.filterwarnings("ignore", message="There are non-text parts in the response")
warnings.filterwarnings("ignore", category=ResourceWarning, message="Unclosed client session")
warnings.filterwarnings("ignore", category=ResourceWarning, message="Unclosed connector")
from .animation import play_animation
from .agent import root_agent

from google.adk.runners import Runner
from google.adk.apps.app import App
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.genai import types
from google.adk.utils.context_utils import Aclosing

# Suppress the ALTS warning by setting the GRPC_VERBOSITY environment variable
os.environ['GRPC_VERBOSITY'] = 'ERROR'

async def main():
    """
    The main function of the COVID-19 CLI application.
    """
    colorama.init()
    load_dotenv()
    play_animation()

    print(f"{Fore.GREEN}Agent: Welcome to the COVID-19 Data Agent!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Agent: You can ask me questions about COVID-19 data.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Agent: Type 'exit' to quit.{Style.RESET_ALL}")

    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()
    credential_service = InMemoryCredentialService()

    app = App(name="covid_agent", root_agent=root_agent)
    runner = Runner(
        app=app,
        artifact_service=artifact_service,
        session_service=session_service,
        credential_service=credential_service,
    )

    user_id = "test_user"
    session = await session_service.create_session(app_name="covid_agent", user_id=user_id)

    while True:
        query = input(f"{Fore.YELLOW}You: {Style.RESET_ALL}")
        if query.lower() == "exit":
            break

        try:
            async with Aclosing(
                runner.run_async(
                    user_id=session.user_id,
                    session_id=session.id,
                    new_message=types.Content(
                        role='user', parts=[types.Part(text=query)]
                    ),
                )
            ) as agen:
              async for event in agen:
                if event.content and event.content.parts:
                  if text := ''.join(part.text or '' for part in event.content.parts):
                    print(f"{Fore.GREEN}Agent: {text}{Style.RESET_ALL}")
        except Exception as e:
            if "ResourceExhausted" in str(e):
                print(f"{Fore.RED}Agent: I'm sorry, I've hit my request limit for the day. Please try again tomorrow.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Agent: I'm sorry, I had trouble understanding that. Error: {e}{Style.RESET_ALL}")
                print(f"{Fore.RED}Agent: Please try rephrasing your question.{Style.RESET_ALL}")

    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
