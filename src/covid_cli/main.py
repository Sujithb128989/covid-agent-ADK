import requests
import pandas as pd
import io
import os
import google.generativeai as genai
from .animation import play_animation
import logging
import ast
import re

# Suppress the ALTS warning by setting the GRPC_VERBOSITY environment variable
os.environ['GRPC_VERBOSITY'] = 'ERROR'

def get_covid_data():
    """
    Downloads the OWID COVID-19 compact dataset and returns it as a pandas DataFrame.
    """
    url = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
    response = requests.get(url)
    data = response.text
    df = pd.read_csv(io.StringIO(data))
    return df

def get_latest_summary(country: str) -> str:
    """
    Returns a summary of the latest COVID-19 data for a given country.
    """
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return f"No data found for {country}."

    def get_latest_value(df, metric):
        latest_date = df.dropna(subset=[metric])['date'].max()
        value = df[df['date'] == latest_date][metric].values[0]
        return latest_date, value

    latest_date_cases, new_cases = get_latest_value(country_df, 'new_cases')
    latest_date_deaths, new_deaths = get_latest_value(country_df, 'new_deaths')
    latest_date_vaccinations, new_vaccinations = get_latest_value(country_df, 'new_vaccinations')


    return (
        f"Latest COVID-19 data for {country}:\n"
        f"- New cases on {latest_date_cases}: {new_cases}\n"
        f"- New deaths on {latest_date_deaths}: {new_deaths}\n"
        f"- New vaccinations on {latest_date_vaccinations}: {new_vaccinations}"
    )

def get_trend(country: str, metric: str, window: int) -> str:
    """
    Analyzes the trend of a metric over a given time window.
    """
    metric = metric.replace(" ", "_")
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return f"No data found for {country}."

    country_df['date'] = pd.to_datetime(country_df['date'])
    country_df = country_df.sort_values(by='date')
    country_df[f'{metric}_trend'] = country_df[metric].rolling(window=window).mean()

    latest_trend = country_df[f'{metric}_trend'].iloc[-1]
    previous_trend = country_df[f'{metric}_trend'].iloc[-2]

    if latest_trend > previous_trend:
        trend = "increasing"
    elif latest_trend < previous_trend:
        trend = "decreasing"
    else:
        trend = "stable"

    return f"The trend of {metric} in {country} over the last {window} days is {trend}."

def compare_countries(countries: list[str], metric: str) -> str:
    """
    Compares a metric for a list of countries.
    """
    metric = metric.replace(" ", "_")
    df = get_covid_data()
    df = df[df['country'].isin(countries)]

    result = f"Comparison of {metric}:\n"
    for country in countries:
        country_df = df[df['country'] == country]
        latest_date = country_df.dropna(subset=[metric])['date'].max()
        value = country_df[country_df['date'] == latest_date][metric].values[0]
        result += f"- {country} on {latest_date}: {value}\n"

    return result

def get_vaccination_progress(country: str) -> str:
    """
    Returns the vaccination progress for a given country.
    """
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return f"No data found for {country}."

    def get_latest_value(df, metric):
        latest_date = df.dropna(subset=[metric])['date'].max()
        value = df[df['date'] == latest_date][metric].values[0]
        return latest_date, value

    latest_date_vaccinated, people_vaccinated = get_latest_value(country_df, 'people_vaccinated')
    latest_date_fully_vaccinated, people_fully_vaccinated = get_latest_value(country_df, 'people_fully_vaccinated')
    latest_date_boosters, total_boosters = get_latest_value(country_df, 'total_boosters')
    population = country_df['population'].iloc[-1]


    return (
        f"Vaccination progress for {country}:\n"
        f"- People vaccinated on {latest_date_vaccinated}: {people_vaccinated} ({people_vaccinated / population:.2%})\n"
        f"- People fully vaccinated on {latest_date_fully_vaccinated}: {people_fully_vaccinated} ({people_fully_vaccinated / population:.2%})\n"
        f"- Total boosters on {latest_date_boosters}: {total_boosters} ({total_boosters / population:.2%})"
    )

def main():
    """
    The main function of the COVID-19 CLI application.
    """
    play_animation()
    api_keys = os.environ["GEMINI_API_KEY"].split(',')
    key_index = 0

    print("Agent: Welcome to the COVID-19 Data Agent!")
    print("Agent: You can ask me questions about COVID-19 data.")
    print("Agent: Type 'exit' to quit.")

    chat = None
    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break

        # Rotate API key
        key_index = (key_index + 1) % len(api_keys)
        genai.configure(api_key=api_keys[key_index])
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Preserve chat history
        if chat:
            history = chat.history
            chat = model.start_chat(history=history)
        else:
            chat = model.start_chat(history=[])


        # Send a single, more sophisticated prompt to the model
        response = chat.send_message(
            "You are a helpful assistant that determines the user's intent. "
            "If the user's query is off-topic (not related to COVID-19 data), respond with 'off-topic'. "
            "If it is on-topic, determine which of the following functions should be called and with what arguments: "
            "get_latest_summary(country: str), "
            "get_trend(country: str, metric: str, window: int), "
            "compare_countries(countries: list[str], metric: str), "
            "get_vaccination_progress(country: str). "
            "Respond with ONLY the function call. For example: get_latest_summary(country='United States')"
            f"\n\nHere is the user's query: '{query}'"
        )

        try:
            response_text = response.text.strip()
            if "off-topic" in response_text.lower():
                print("Agent: I am a COVID-19 data agent. Please ask me questions about COVID-19 data.")
                continue

            if "get_latest_summary" in response_text or "get_trend" in response_text or "compare_countries" in response_text or "get_vaccination_progress" in response_text:
                function_call_str = response_text
                if "(" in function_call_str and ")" in function_call_str:
                    function_name, args_str = function_call_str.split("(", 1)
                    args_str = args_str[:-1]
                    args = {}
                    for match in re.finditer(r"(\w+)=('.*?'|\".*?\"|\d+)", args_str):
                        key, value = match.groups()
                        args[key] = ast.literal_eval(value)

                    if function_name == "get_latest_summary":
                        data = get_latest_summary(**args)
                    elif function_name == "get_trend":
                        data = get_trend(**args)
                    elif function_name == "compare_countries":
                        data = compare_countries(**args)
                    elif function_name == "get_vaccination_progress":
                        data = get_vaccination_progress(**args)
                    else:
                        data = "I'm sorry, I don't know how to do that."

                    # Send the data to Gemini to get a natural language response
                    final_response = chat.send_message(
                        f"Here is the data you requested:\n{data}\n\nPlease explain this to the user in a natural, conversational, and concise way."
                    )
                    print(f"Agent: {final_response.text}")

                else:
                    print("Agent: I'm sorry, I had trouble understanding that. Please try rephrasing your question.")
            else:
                print(f"Agent: {response_text}")


        except genai.types.generation_types.StopCandidateException as e:
            print(f"Agent: I'm sorry, I had to stop generating the response. This can happen for a variety of reasons. Please try again.")
        except Exception as e:
            if "ResourceExhausted" in str(e):
                print("Agent: I'm sorry, I've hit my request limit for the day. Please try again tomorrow.")
            else:
                print(f"Agent: I'm sorry, I had trouble understanding that. Error: {e}")
                print("Agent: Please try rephrasing your question.")


if __name__ == "__main__":
    main()
