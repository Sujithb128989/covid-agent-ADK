import requests
import pandas as pd
import io
from typing import List

def get_covid_data():
    """
    Downloads the OWID COVID-19 compact dataset and returns it as a pandas DataFrame.
    """
    url = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
    response = requests.get(url)
    data = response.text
    df = pd.read_csv(io.StringIO(data))
    return df

def get_latest_summary(country: str) -> dict:
    """
    Returns a summary of the latest COVID-19 data for a given country.
    """
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return {"error": f"No data found for {country}."}

    def get_latest_value(df, metric):
        latest_date = df.dropna(subset=[metric])['date'].max()
        value = df[df['date'] == latest_date][metric].values[0]
        return latest_date, value

    latest_date_cases, new_cases = get_latest_value(country_df, 'new_cases')
    latest_date_deaths, new_deaths = get_latest_value(country_df, 'new_deaths')
    latest_date_vaccinations, new_vaccinations = get_latest_value(country_df, 'new_vaccinations')

    return {
        "country": country,
        "latest_date_cases": latest_date_cases,
        "new_cases": new_cases,
        "latest_date_deaths": latest_date_deaths,
        "new_deaths": new_deaths,
        "latest_date_vaccinations": latest_date_vaccinations,
        "new_vaccinations": new_vaccinations,
    }

def get_trend(country: str, metric: str, window: int) -> dict:
    """
    Analyzes the trend of a metric over a given time window.
    """
    metric = metric.replace(" ", "_")
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return {"error": f"No data found for {country}."}

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

    return {
        "country": country,
        "metric": metric,
        "window": window,
        "trend": trend,
    }

def compare_countries(countries: List[str], metric: str) -> dict:
    """
    Compares a metric for a list of countries.
    """
    metric = metric.replace(" ", "_")
    df = get_covid_data()
    df = df[df['country'].isin(countries)]

    results = []
    for country in countries:
        country_df = df[df['country'] == country]
        if country_df.empty:
            results.append({"country": country, "error": "No data found"})
            continue
        latest_date = country_df.dropna(subset=[metric])['date'].max()
        value = country_df[country_df['date'] == latest_date][metric].values[0]
        results.append({"country": country, "latest_date": latest_date, "value": value})

    return {
        "metric": metric,
        "comparison": results,
    }

def get_vaccination_progress(country: str) -> dict:
    """
    Returns the vaccination progress for a given country.
    """
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return {"error": f"No data found for {country}."}

    def get_latest_value(df, metric):
        latest_date = df.dropna(subset=[metric])['date'].max()
        value = df[df['date'] == latest_date][metric].values[0]
        return latest_date, value

    latest_date_vaccinated, people_vaccinated = get_latest_value(country_df, 'people_vaccinated')
    latest_date_fully_vaccinated, people_fully_vaccinated = get_latest_value(country_df, 'people_fully_vaccinated')
    latest_date_boosters, total_boosters = get_latest_value(country_df, 'total_boosters')
    population = country_df['population'].iloc[-1]

    return {
        "country": country,
        "people_vaccinated": people_vaccinated,
        "people_vaccinated_date": latest_date_vaccinated,
        "people_vaccinated_percent": f"{people_vaccinated / population:.2%}",
        "people_fully_vaccinated": people_fully_vaccinated,
        "people_fully_vaccinated_date": latest_date_fully_vaccinated,
        "people_fully_vaccinated_percent": f"{people_fully_vaccinated / population:.2%}",
        "total_boosters": total_boosters,
        "total_boosters_date": latest_date_boosters,
        "total_boosters_percent": f"{total_boosters / population:.2%}",
    }

from google.adk.agents import Agent

root_agent = Agent(
    name="covid_agent",
    model="gemini-1.5-flash",
    description="An agent that can answer questions about COVID-19 data.",
    instruction=(
        "You are a helpful agent who can answer user questions about COVID-19 data. "
        "Use the provided tools to answer the user's questions. "
        "If the user's query is off-topic (not related to COVID-19 data), "
        "politely decline the request and remind them of your purpose."
    ),
    tools=[
        get_latest_summary,
        get_trend,
        compare_countries,
        get_vaccination_progress,
    ],
)
