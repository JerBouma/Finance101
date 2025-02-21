import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# Set default lump sum amount (used for both strategies)
DEFAULT_LUMP_SUM = 10000.0

# Well-known ETFs, including diversified options beyond just the S&P 500
etfs = {
    "SPDR S&P 500 ETF Trust": "SPY",
    "Vanguard Total Stock Market ETF": "VTI",
    "Vanguard FTSE Developed Markets ETF": "VEA",
    "Vanguard FTSE Emerging Markets ETF": "VWO",
    "iShares Core US Aggregate Bond ETF": "AGG",
}

# Radio button to select which ETF to use for the simulation
ticker_label = st.sidebar.radio("Select ETF for Simulation", list(etfs.keys()))
selected_ticker = etfs[ticker_label]

# If not already in session state, download and store historical data for all ETFs
if "historical_data_all" not in st.session_state:
    st.session_state["historical_data_all"] = {}
    for name, ticker in etfs.items():
        data = yf.download(ticker, period="max", actions=True)
        data = data.xs(ticker, axis=1, level=1)
        st.session_state["historical_data_all"][ticker] = data

# Set the simulation data to the selected ETF's data
st.session_state["historical_data"] = st.session_state["historical_data_all"][
    selected_ticker
]
st.session_state["ticker"] = selected_ticker

st.title("Investment Strategy Comparison")
st.markdown(
    """
Investing in different ETFs presents distinct risk and return profiles. For example, Equity ETFs
such as SPDR S&P 500 ETF Trust and Vanguard Total Stock Market ETF, which track major stock indices,
typically exhibit higher volatility caused by the dynamic nature of the equity markets. This
increased volatility means that while investors have the potential to achieve substantial
returns over time, there are also greater swings in portfolio value over the short term.
Such ETFs are generally better suited for those with a higher risk tolerance, as the
potential for significant capital appreciation comes alongside the possibility of
steep declines during market downturns.

In contrast, Bond ETFs like iShares Core US Aggregate Bond ETF are designed to offer
lower volatility and steadier returns by focusing on fixed income securities. This
more conservative approach helps to maintain portfolio stability and offers capital
preservation benefits, particularly in turbulent market conditions. Additionally,
international equity ETFs such as Vanguard FTSE Developed Markets ETF and Vanguard
FTSE Emerging Markets ETF provide broader geographical diversification but may also
be affected by factors like currency fluctuations and geopolitical events. Together,
these differences in risk and return highlight the importance of aligning ETF selection
with an investor’s overall risk profile, investment goals, and market outlook.

Below plots the cumulative returns for all available ETFs.
"""
)

# Sidebar inputs for simulation parameters
st.sidebar.header("Simulation Parameters")

# Prepare and display cumulative returns for all ETFs
cumulative_returns_all = {}
for ticker, data in st.session_state["historical_data_all"].items():
    if not data.empty:
        monthly_series = data["Close"].resample("ME").last().dropna()
        if monthly_series.empty:
            continue
        etf_label = [name for name, sym in etfs.items() if sym == ticker][0]
        cumulative_returns_all[etf_label] = (
            monthly_series / monthly_series.iloc[0] - 1
        ) * 100  # in percentage

if cumulative_returns_all:
    cumulative_returns_df = pd.DataFrame(cumulative_returns_all).dropna()

    st.line_chart(cumulative_returns_df, use_container_width=True)

    st.markdown(
        """
    The following metrics are calculated for each ETF:
    - Annualized Return (%): The average yearly return over the sample period, accounting for compounding.
    - Annualized Volatility (%): The standard deviation of daily returns scaled to an annual basis, reflecting risk.
    - Maximum Drawdown (%): The largest peak-to-trough decline during the investment period, indicating worst-case loss.
    - Sharpe Ratio: A risk-adjusted return measure, calculated as the annualized return divided by annualized volatility.
    - Calmar Ratio: The ratio of annualized return to maximum drawdown, emphasizing return relative to downside risk.
    """
    )

    etf_stats = {}
    for name, ticker in etfs.items():
        data = st.session_state["historical_data_all"][ticker]
        if data.empty or "Close" not in data.columns:
            continue
        # Ensure data is sorted by date
        price = data["Close"].sort_index()
        # Daily returns
        daily_returns = price.pct_change().dropna()
        # Annualized Return: using the geometric return formula
        total_period = (price.index[-1] - price.index[0]).days
        annualized_return = (
            (price.iloc[-1] / price.iloc[0]) ** (365 / total_period) - 1
            if total_period > 0
            else np.nan
        )
        # Annualized Volatility
        annualized_vol = daily_returns.std() * np.sqrt(252)
        # Maximum Drawdown
        running_max = price.cummax()
        drawdown = (price - running_max) / running_max
        max_drawdown = drawdown.min()
        sharpe_ratio = (
            (annualized_return / annualized_vol) if annualized_vol != 0 else np.nan
        )
        calmar_ratio = (
            (annualized_return / abs(max_drawdown)) if max_drawdown != 0 else np.nan
        )

        etf_stats[name] = {
            "Annualized Return (%)": annualized_return * 100,
            "Annualized Volatility (%)": annualized_vol * 100,
            "Maximum Drawdown (%)": max_drawdown * 100,
            "Sharpe Ratio": sharpe_ratio,
            "Calmar Ratio": calmar_ratio,
        }

    if etf_stats:
        stats_df = pd.DataFrame(etf_stats).T
        st.dataframe(stats_df.style.format("{:.2f}"))

# Date inputs: use available data range as bounds
data_index = st.session_state["historical_data"].index
min_date = data_index.min().date()
max_date = data_index.max().date()
start_date = st.sidebar.date_input(
    "Select start date",
    value=datetime.date(2010, 1, 1),
    min_value=min_date,
    max_value=max_date,
)

# Amount input: one amount is used for both strategies
lump_sum = st.sidebar.number_input(
    "Total Investment Amount (€)", min_value=0.0, value=DEFAULT_LUMP_SUM, step=100.0
)

# Use adjusted close prices and resample monthly (take last trading day)
monthly_data = (
    st.session_state["historical_data"]["Close"].resample("ME").last().dropna()
)

# Filter data from the starting date onward
monthly_data = monthly_data[monthly_data.index >= pd.to_datetime(start_date)]

if len(monthly_data) < 2:  # noqa
    st.error("Not enough data points after the start date to run the simulation.")
    st.stop()

# Prepare DataFrame for simulation results
simulation = pd.DataFrame(index=monthly_data.index)
simulation["Price"] = monthly_data

# Lists to track which simulation(s) we run
simulation_labels = []
plot_data = {}

# Lump Sum Simulation: invest the lump sum on the first month
if lump_sum > 0:
    lump_shares = lump_sum / simulation["Price"].iloc[0]
    simulation["LumpSum Value"] = lump_shares * simulation["Price"]
    simulation_labels.append("Lump Sum Investing")
    plot_data["Lump Sum Investing"] = simulation["LumpSum Value"]

# Monthly Investing Simulation: invest an amount each month so that the total equals lump_sum
if lump_sum > 0:
    n_months = len(simulation)
    computed_monthly = lump_sum / n_months
    simulation["Monthly Shares Bought"] = computed_monthly / simulation["Price"]
    simulation["Cumulative Shares"] = simulation["Monthly Shares Bought"].cumsum()
    simulation["Monthly Value"] = simulation["Cumulative Shares"] * simulation["Price"]
    simulation_labels.append("Monthly Investing")
    plot_data["Monthly Investing"] = simulation["Monthly Value"]

if not simulation_labels:
    st.error("Please enter a positive investment amount.")
    st.stop()

# Savings simulation: regular monthly deposits with a defined savings rate
savings_rate = st.sidebar.number_input(
    "Savings Rate (%)", min_value=0.0, value=2.0, step=0.1
)
monthly_rate = savings_rate / 12 / 100
monthly_investment = lump_sum / len(simulation)
savings_values = []
savings_accumulated = 0.0
for _ in simulation.index:
    savings_accumulated = (savings_accumulated + monthly_investment) * (
        1 + monthly_rate
    )
    savings_values.append(savings_accumulated)
simulation["Savings Value"] = savings_values
plot_data["Savings Account"] = simulation["Savings Value"]

# Calculate cumulative returns for each strategy
cumulative_returns = pd.DataFrame(index=simulation.index)
for label, series in plot_data.items():
    if label == "Lump Sum Investing":
        # For lump sum, the full amount is invested at once (baseline is lump_sum)
        cumulative_returns[label] = (series - lump_sum) / lump_sum * 100
    elif label in ["Monthly Investing", "Savings Account"]:
        # For monthly investing and savings account, calculate cumulative invested amount up to each month
        cumulative_invested = monthly_investment * pd.Series(
            range(1, len(simulation) + 1), index=simulation.index
        )
        cumulative_returns[label] = (
            (series - cumulative_invested) / cumulative_invested * 100
        )

# Display cumulative returns using Streamlit's built-in line chart
st.subheader("Cumulative Return Over Time (%)")
st.markdown(
    """
Investment strategies differ in risk and return profiles. Lump Sum Investing involves
investing the entire amount at once, which can lead to substantial gains if the
market is trending upwards immediately after the investment, but also carries
the risk of significant losses if the market takes a downturn.

Dollar Cost Averaging (Monthly Investing) involves investing equal amounts
at regular intervals, thereby averaging out the purchase price.

A Savings Account strategy simulates depositing money regularly in a savings
account with a fixed annual interest rate, representing a conservative,
interest-bearing alternative.
"""
)
cumulative_returns["Profit Line"] = 0
st.line_chart(cumulative_returns, use_container_width=True)


# Summary stats: final portfolio values, total invested, and return
st.sidebar.subheader("Summary Statistics")
summary_lines = []
final_date = simulation.index[-1]
if "Lump Sum Investing" in simulation_labels:
    final_lump = simulation["LumpSum Value"].iloc[-1]
    total_invested_lump = lump_sum
    roi_lump = ((final_lump - total_invested_lump) / total_invested_lump) * 100
    summary_lines.append(
        f"**Lump Sum Investing (as of {final_date.date()}):** Invested "
        f"€{total_invested_lump:,.2f}, Final Value €{final_lump:,.2f} (ROI: {roi_lump:,.2f}%)"
    )

if "Monthly Investing" in simulation_labels:
    final_monthly = simulation["Monthly Value"].iloc[-1]
    # Total invested is exactly the lump_sum for monthly strategy.
    total_invested_monthly = lump_sum
    roi_monthly = (
        (final_monthly - total_invested_monthly) / total_invested_monthly
    ) * 100
    summary_lines.append(
        f"**Monthly Investing (as of {final_date.date()}):** Invested "
        f"€{total_invested_monthly:,.2f} evenly over {len(simulation)} "
        f"months, Final Value €{final_monthly:,.2f} (ROI: {roi_monthly:,.2f}%)"
    )

final_savings = simulation["Savings Value"].iloc[-1]
total_invested_savings = lump_sum
roi_savings = ((final_savings - total_invested_savings) / total_invested_savings) * 100
summary_lines.append(
    f"**Savings Account (as of {final_date.date()}):** Invested €{total_invested_savings:,.2f}, Final Value €{final_savings:,.2f} (ROI: {roi_savings:,.2f}%)"
)

st.sidebar.markdown("\n\n".join(summary_lines))
