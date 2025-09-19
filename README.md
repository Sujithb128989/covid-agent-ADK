# COVID-19 Data Agent

This is a command-line interface (CLI) application that allows you to get insights and analytics on publicly available COVID-19 data.

The application uses the Google Agent Development Kit (ADK) to understand your questions and provide answers based on the Our World in Data (OWID) COVID-19 dataset.

## Features

- **Natural Language Interface:** Ask questions in plain English.
- **Latest Data:** Get the latest summary of cases, deaths, and vaccinations for any country.
- **Trend Analysis:** Analyze the trend of a metric for a country over a given time window.
- **Country Comparison:** Compare a metric for multiple countries.
- **Vaccination Progress:** Get the vaccination progress for any country.
- **Conversational Context:** The agent remembers the context of your conversation, so you can ask follow-up questions.
- **Off-Topic Reminder:** The agent will gently guide you back to COVID-19 related questions if you go off-topic.
- **Cool Animation:** A retro-style boot-up animation to get you started.

## Installation

1.  **Clone the repository:**
    ```
    git clone <repository-url>
    ```
2.  **Install the dependencies:**
    ```
    pip install -r requirements.txt
    ```
3.  **Set up your Gemini API key:**
    - Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
    - Create a file named `.env` in the root of the project.
    - Add the following line to the `.env` file, replacing `YOUR_GEMINI_API_KEY` with your actual key:
      ```
      GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
      ```
    - An example is provided in the `.env.example` file.

## Usage

1.  **Run the application:**
    ```
    python -m src.covid_cli.main
    ```
    This will start an interactive session with the agent.

2.  **Ask questions:**
    - "What is the latest summary for the United States?"
    - "What is the trend of new cases in Germany over the last 30 days?"
    - "Compare the new cases in France and Germany."
    - "What is the vaccination progress for Canada?"
    - "How about Japan?" (follow-up question)

3.  **Exit the application:**
    - Type "exit" to quit.

## How it works

The application uses the following technologies:
- **Python:** The application is written in Python.
- **Google Agent Development Kit (ADK):** The application uses the ADK to create a tool-using agent.
- **Gemini API:** The agent uses the Gemini API to understand user queries and generate responses.
- **pandas:** The application uses the pandas library to process the COVID-19 data.
- **requests:** The application uses the requests library to download the COVID-19 data.

The application is built around an ADK `Agent`. The data-fetching functions (`get_latest_summary`, `get_trend`, etc.) are provided to the agent as tools. When you ask a question, the ADK handles:
1.  Sending the user's query to the Gemini model.
2.  Determining which tool to call based on the model's response.
3.  Executing the tool with the correct arguments.
4.  Sending the tool's output back to the model to generate a natural language response.
5.  Maintaining the conversational history.

This approach is more robust and maintainable than the previous implementation, which relied on manual prompt engineering and response parsing.

## A note on warnings

You may see a warning that says `ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.`. This is a standard warning from Google's API client library when not running on the Google Cloud Platform. It is safe to ignore this warning. You may also see experimental warnings from the ADK, which can also be safely ignored.
