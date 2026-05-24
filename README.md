# COVID-19 Data Agent

This is a command-line interface (CLI) application that allows you to get insights and analytics on publicly available COVID-19 data.

The application uses the Gemini API to understand your questions and provide answers based on the Our World in Data (OWID) COVID-19 dataset.

## Features

- **Natural Language Interface:** Ask questions in plain English.
- **Latest Data:** Get the latest summary of cases, deaths, and vaccinations for any country.
- **Trend Analysis:** Analyze the trend of a metric for a country over a given time window.
- **Country Comparison:** Compare a metric for multiple countries.
- **Vaccination Progress:** Get the vaccination progress for any country.
- **Conversational Context:** The agent remembers the context of your conversation, so you can ask follow-up questions.
- **Off-Topic Reminder:** The agent will gently guide you back to COVID-19 related questions if you go off-topic.
- **Cool Animation:** A retro-style boot-up animation to get you started.
- **API Key Rotation:** The application can use multiple API keys to avoid rate limiting issues.

## Installation

1.  **Clone the repository:**
    ```
    git clone <repository-url>
    ```
2.  **Install the dependencies:**
    ```
    pip install -r requirements.txt
    ```
3.  **Set up your Gemini API key(s):**
    - Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). You can get multiple keys to avoid rate limiting issues.
    - Set the API key(s) as an environment variable.

      **For a single API key:**

      *   **Windows Command Prompt:**
          ```
          set GEMINI_API_KEY=<your-api-key>
          ```

      *   **Windows PowerShell:**
          ```
          $env:GEMINI_API_KEY="<your-api-key>"
          ```

      *   **Linux and macOS:**
          ```
          export GEMINI_API_KEY=<your-api-key>
          ```

      **For multiple API keys (comma-separated):**

      *   **Windows Command Prompt:**
          ```
          set GEMINI_API_KEY=<key1>,<key2>,<key3>
          ```

      *   **Windows PowerShell:**
          ```
          $env:GEMINI_API_KEY="<key1>,<key2>,<key3>"
          ```

      *   **Linux and macOS:**
          ```
          export GEMINI_API_KEY=<key1>,<key2>,<key3>
          ```

## Usage

1.  **Run the application:**
    ```
    python -m src.covid_cli.main
    ```
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
- **Gemini API:** The application uses the Gemini API to understand user queries and generate responses.
- **pandas:** The application uses the pandas library to process the COVID-19 data.
- **requests:** The application uses the requests library to download the COVID-19 data.

When you ask a question, the application sends a single, comprehensive prompt to the Gemini API. This prompt instructs the model to:
1.  Determine if the query is on-topic or off-topic.
2.  If it's off-topic, politely decline the request.
3.  If it's on-topic, determine which data analysis function to call and with what arguments.
4.  Call the function to get the raw data.
5.  Generate a natural language response based on the data.

The application uses a `ChatSession` object to maintain the context of the conversation, which allows it to understand follow-up questions. It also rotates through a list of API keys to avoid rate limiting issues.

## A note on warnings

You may see a warning that says `ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.`. This is a standard warning from Google's API client library when not running on the Google Cloud Platform. It is safe to ignore this warning.
