import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import plotly.express as px
from prophet import Prophet
from sklearn.ensemble import IsolationForest
from scipy import stats
from jinja2 import Template
from xhtml2pdf import pisa
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from google.genai import Client

from .data import get_covid_data

OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_layer_size=50, output_size=1):
        super().__init__()
        self.hidden_layer_size = hidden_layer_size
        self.lstm = nn.LSTM(input_size, hidden_layer_size)
        self.linear = nn.Linear(hidden_layer_size, output_size)
        self.hidden_cell = (torch.zeros(1,1,self.hidden_layer_size),
                            torch.zeros(1,1,self.hidden_layer_size))

    def forward(self, input_seq):
        lstm_out, self.hidden_cell = self.lstm(input_seq.view(len(input_seq), 1, -1), self.hidden_cell)
        predictions = self.linear(lstm_out.view(len(input_seq), -1))
        return predictions[-1]

def create_inout_sequences(input_data, tw):
    inout_seq = []
    L = len(input_data)
    for i in range(L-tw):
        train_seq = input_data[i:i+tw]
        train_label = input_data[i+tw:i+tw+1]
        inout_seq.append((train_seq, train_label))
    return inout_seq

def forecast_lstm(data, days: int = 30):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    scaler = MinMaxScaler(feature_range=(-1, 1))
    data_normalized = scaler.fit_transform(data.reshape(-1, 1))
    data_normalized = torch.FloatTensor(data_normalized).view(-1)

    train_window = 30
    train_inout_seq = create_inout_sequences(data_normalized, train_window)

    model = LSTMModel().to(device)
    loss_function = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    epochs = 50
    for i in range(epochs):
        for seq, labels in train_inout_seq:
            seq, labels = seq.to(device), labels.to(device)
            optimizer.zero_grad()
            model.hidden_cell = (torch.zeros(1, 1, model.hidden_layer_size).to(device),
                            torch.zeros(1, 1, model.hidden_layer_size).to(device))
            y_pred = model(seq)
            single_loss = loss_function(y_pred, labels)
            single_loss.backward()
            optimizer.step()

    fut_pred = len(data)
    test_inputs = data_normalized[-train_window:].tolist()

    model.eval()
    for i in range(days):
        seq = torch.FloatTensor(test_inputs[-train_window:]).to(device)
        with torch.no_grad():
            model.hidden = (torch.zeros(1, 1, model.hidden_layer_size).to(device),
                            torch.zeros(1, 1, model.hidden_layer_size).to(device))
            test_inputs.append(model(seq).item())

    actual_predictions = scaler.inverse_transform(np.array(test_inputs[train_window:]).reshape(-1, 1))
    return actual_predictions.flatten()

def forecast_cases(country: str, days: int) -> dict:
    """
    Uses Prophet and LSTM to forecast new cases for a given country, compares them, and saves a plot.
    """
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return {"error": f"No data found for {country}."}

    country_df['date'] = pd.to_datetime(country_df['date'])
    country_df = country_df.sort_values(by='date')
    country_df = country_df.dropna(subset=['new_cases_smoothed'])

    # Prophet Forecast
    prophet_df = country_df[['date', 'new_cases_smoothed']].rename(columns={'date': 'ds', 'new_cases_smoothed': 'y'})
    m = Prophet(yearly_seasonality=True, daily_seasonality=False)
    m.fit(prophet_df)
    future = m.make_future_dataframe(periods=days)
    forecast = m.predict(future)
    prophet_forecast = forecast.iloc[-days:]['yhat'].values

    # LSTM Forecast
    lstm_forecast = forecast_lstm(country_df['new_cases_smoothed'].values, days)

    # Plotting
    plt.figure(figsize=(12, 6))
    plt.plot(country_df['date'], country_df['new_cases_smoothed'], label='Historical')
    future_dates = pd.date_range(start=country_df['date'].iloc[-1] + pd.Timedelta(days=1), periods=days)
    plt.plot(future_dates, prophet_forecast, label='Prophet Forecast', color='orange')
    plt.plot(future_dates, lstm_forecast, label='LSTM Forecast', color='green')
    plt.title(f'COVID-19 Case Forecast for {country}: Prophet vs LSTM')
    plt.xlabel('Date')
    plt.ylabel('New Cases Smoothed')
    plt.legend()
    plot_path = os.path.join(OUTPUT_DIR, f"{country}_forecast_comparison.png")
    plt.savefig(plot_path)
    plt.close()

    return {
        "country": country,
        "forecast_days": days,
        "plot_path": plot_path,
        "average_forecasted_daily_cases_prophet": round(np.mean(prophet_forecast), 2),
        "average_forecasted_daily_cases_lstm": round(np.mean(lstm_forecast), 2)
    }

def detect_anomalies(country: str, metric: str) -> dict:
    """
    Uses Isolation Forest to detect anomalies in outbreak patterns and saves a plot.
    """
    df = get_covid_data()
    country_df = df[df['country'] == country].copy()
    if country_df.empty:
        return {"error": f"No data found for {country}."}

    country_df['date'] = pd.to_datetime(country_df['date'])
    country_df = country_df.sort_values(by='date').dropna(subset=[metric])

    if len(country_df) < 50:
         return {"error": "Not enough data points for anomaly detection."}

    X = country_df[[metric]].values
    clf = IsolationForest(contamination=0.05, random_state=42)
    country_df['anomaly'] = clf.fit_predict(X)

    anomalies = country_df[country_df['anomaly'] == -1]

    plt.figure(figsize=(10, 6))
    plt.plot(country_df['date'], country_df[metric], label=metric)
    plt.scatter(anomalies['date'], anomalies[metric], color='red', label='Anomaly')
    plt.title(f'Anomaly Detection in {metric} for {country}')
    plt.xlabel('Date')
    plt.ylabel(metric)
    plt.legend()
    plot_path = os.path.join(OUTPUT_DIR, f"{country}_{metric}_anomalies.png")
    plt.savefig(plot_path)
    plt.close()

    return {
        "country": country,
        "metric": metric,
        "plot_path": plot_path,
        "total_anomalies": len(anomalies)
    }

def compare_countries_statistically(country_a: str, country_b: str, metric: str) -> dict:
    """
    Performs a Mann-Whitney U test and T-test for cross-country metric comparisons.
    """
    df = get_covid_data()

    df_a = df[df['country'] == country_a].copy()
    df_b = df[df['country'] == country_b].copy()

    if df_a.empty or df_b.empty:
        return {"error": "Data missing for one or both countries."}

    df_a = df_a.dropna(subset=[metric])
    df_b = df_b.dropna(subset=[metric])

    # Simple T-test
    t_stat, p_val_t = stats.ttest_ind(df_a[metric], df_b[metric], equal_var=False)

    # Mann-Whitney U test (non-parametric)
    u_stat, p_val_u = stats.mannwhitneyu(df_a[metric], df_b[metric], alternative='two-sided')

    # Visualization using Plotly
    combined_df = pd.concat([df_a, df_b])
    fig = px.box(combined_df, x="country", y=metric, title=f"Comparison of {metric}: {country_a} vs {country_b}")
    plot_path = os.path.join(OUTPUT_DIR, f"{country_a}_vs_{country_b}_{metric}_comparison.html")
    fig.write_html(plot_path)

    return {
        "country_a": country_a,
        "country_b": country_b,
        "metric": metric,
        "t_test_p_value": round(p_val_t, 4),
        "mann_whitney_p_value": round(p_val_u, 4),
        "significant_difference_t_test": p_val_t < 0.05,
        "significant_difference_mann_whitney": p_val_u < 0.05,
        "plot_path": plot_path
    }

def generate_report(country: str) -> dict:
    """
    Compiles automated insights, anomalies, and statistical comparisons into a structured HTML/PDF report.
    """
    forecast_info = forecast_cases(country, 30)
    anomaly_info = detect_anomalies(country, "new_cases")

    if "error" in forecast_info or "error" in anomaly_info:
        return {"error": "Failed to generate report due to missing data."}

    client = Client(api_key=os.environ.get("GOOGLE_API_KEY", "dummy_key"))
    prompt = f"""
    Analyze the following findings for COVID-19 in {country}:
    - The Prophet model forecasts an average of {forecast_info['average_forecasted_daily_cases_prophet']} daily cases over the next {forecast_info['forecast_days']} days.
    - The LSTM model forecasts an average of {forecast_info['average_forecasted_daily_cases_lstm']} daily cases over the next {forecast_info['forecast_days']} days.
    - The Isolation Forest model detected {anomaly_info['total_anomalies']} anomalous outbreaks in the new cases data.

    Provide a succinct, insightful 2-paragraph summary of these automated findings, highlighting any non-obvious patterns or implications.
    """
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        automated_insight_text = response.text
    except Exception as e:
        automated_insight_text = "Could not generate automated insight due to API error."

    html_out = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>COVID-19 Data Science Report: {country}</title>
        <style>
            body {{ font-family: sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ccc; margin-top: 10px;}}
            .insight {{ background-color: #f9f9f9; padding: 15px; border-left: 5px solid #007bff; margin-bottom: 20px;}}
        </style>
    </head>
    <body>
        <h1>COVID-19 Data Science Report: {country}</h1>
        <div class="insight">
            <h2>Data Science Insights</h2>
            <div>{automated_insight_text.replace(chr(10), '<br>')}</div>
        </div>
        <h2>Time Series Forecast (Prophet vs LSTM)</h2>
        <img src="{os.path.abspath(forecast_info['plot_path'])}" alt="Forecast Plot" width="600" />
        <h2>Outbreak Anomaly Detection (Isolation Forest)</h2>
        <img src="{os.path.abspath(anomaly_info['plot_path'])}" alt="Anomaly Plot" width="600" />
    </body>
    </html>
    """

    report_html_path = os.path.join(OUTPUT_DIR, f"{country}_report.html")
    with open(report_html_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    # Generate PDF
    report_pdf_path = os.path.join(OUTPUT_DIR, f"{country}_report.pdf")
    with open(report_pdf_path, "w+b") as result_file:
        pisa.CreatePDF(html_out, dest=result_file)

    return {
        "report_html": report_html_path,
        "report_pdf": report_pdf_path
    }
