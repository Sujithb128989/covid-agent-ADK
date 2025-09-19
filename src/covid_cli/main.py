import os
from dotenv import load_dotenv
from .animation import play_animation
from .agent import root_agent

# Suppress the ALTS warning by setting the GRPC_VERBOSITY environment variable
os.environ['GRPC_VERBOSITY'] = 'ERROR'

def main():
    """
    The main function of the COVID-19 CLI application.
    """
    load_dotenv()
    play_animation()

    print("Agent: Welcome to the COVID-19 Data Agent!")
    print("Agent: You can ask me questions about COVID-19 data.")
    print("Agent: Type 'exit' to quit.")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break

        try:
            response = root_agent.run(query)
            print(f"Agent: {response}")
        except Exception as e:
            if "ResourceExhausted" in str(e):
                print("Agent: I'm sorry, I've hit my request limit for the day. Please try again tomorrow.")
            else:
                print(f"Agent: I'm sorry, I had trouble understanding that. Error: {e}")
                print("Agent: Please try rephrasing your question.")


if __name__ == "__main__":
    main()
