import requests
import pandas as pd
import io
import functools

@functools.lru_cache(maxsize=1)
def get_covid_data():
    """
    Downloads the OWID COVID-19 compact dataset and returns it as a pandas DataFrame.
    """
    url = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
    response = requests.get(url)
    data = response.text
    df = pd.read_csv(io.StringIO(data))
    return df
