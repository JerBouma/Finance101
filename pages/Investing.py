from typing import Dict, List, Union

import pandas as pd
import streamlit as st
import yfinance as yf

# --- Constants ---
SAVINGS_RATE_KEY: str = "savings_rate"
SP500_RETURN_KEY: str = "sp500_return"
START_YEAR: int = 1980
END_YEAR: int = 2025
YEARS: List[int] = list(range(START_YEAR, END_YEAR))
# Approximate historical savings rates (for illustration)
RATES: List[float] = [
    10.5,
    11.0,
    10.8,
    10.2,
    9.8,
    9.2,
    8.5,
    8.0,
    7.5,
    7.0,
    9.0,
    8.5,
    8.0,
    7.8,
    6.5,
    6.0,
    5.5,
    5.0,
    4.5,
    3.5,
    3.0,
    3.0,
    2.8,
    2.5,
    2.2,
    2.0,
    2.2,
    3.0,
    3.5,
    1.5,
    1.2,
    1.5,
    1.2,
    1.0,
    0.8,
    0.5,
    0.3,
    0.2,
    0.1,
    0.1,
    0.1,
    0.1,
    0.5,
    1.5,
    2.0,
]
SP500_TICKER: str = "^GSPC"
DATA_PERIOD: str = "50y"
DATA_INTERVAL: str = "1mo"


# --- Type Aliases ---
SessionStateData = Dict[str, Union[pd.DataFrame, pd.Series]]


# --- Helper Functions ---
def load_savings_rate_data() -> pd.DataFrame:
    """Loads or creates illustrative savings rate data."""
    data: Dict[str, List[Union[int, float]]] = {"Year": YEARS, "Savings Rate": RATES}
    savings_rate_df = pd.DataFrame(data)
    savings_rate_df = savings_rate_df.set_index("Year")
    # Ensure index is datetime at year end for proper merging
    savings_rate_df.index = pd.to_datetime(
        savings_rate_df.index.astype(str)
    ) + pd.offsets.YearEnd(0)
    return savings_rate_df


def load_sp500_data() -> pd.Series:
    """Downloads and processes S&P 500 yearly return data."""
    data: pd.DataFrame = yf.download(
        SP500_TICKER, period=DATA_PERIOD, interval=DATA_INTERVAL, progress=False
    )
    # Resample to get the last closing price of each year
    yearly_data: pd.Series = data["Close"].resample("YE").last()
    # Ensure index is datetime for proper merging
    yearly_data.index = pd.to_datetime(
        yearly_data.index.year.astype(str)
    ) + pd.offsets.YearEnd(0)
    # Compute annual returns as percentages
    yearly_returns: pd.Series = yearly_data.pct_change().dropna() * 100
    return yearly_returns


# --- Streamlit App ---
st.set_page_config(page_title="Investing 101", layout="wide")

st.write(
    """
Investing is the act of allocating resources, usually money, with the expectation
of generating income or profit. By investing, you can potentially grow your
wealth over time, outpacing inflation and ensuring financial security.

It can help you achieve your financial goals, such as saving for retirement,
buying a home, or funding your children's education. Previous generations often
relied on their savings account to grow their wealth but with the decreasing
interest rates, this no longer generates a steady passive income as it used to be.

This becomes visible when we compare the savings rate with the S&P 500 return.
Note that the savings rate here is illustrative and may not reflect actual historical rates accurately.
"""
)

# --- Data Loading and Caching ---
# Use functions to load data if not already in session state
if SAVINGS_RATE_KEY not in st.session_state:
    st.session_state[SAVINGS_RATE_KEY] = load_savings_rate_data()

if SP500_RETURN_KEY not in st.session_state:
    st.session_state[SP500_RETURN_KEY] = load_sp500_data()

# --- Data Preparation for Charts ---
# Type assertion for clarity, though Streamlit's session state is inherently Any
savings_rate_df: pd.DataFrame = st.session_state[SAVINGS_RATE_KEY]
sp500_return_series: pd.Series = st.session_state[SP500_RETURN_KEY]

# Ensure Series has a name for merging and legend clarity
sp500_return_series.name = "S&P 500 Return"

# Combine annual returns data using the .merge method
combined_df: pd.DataFrame = savings_rate_df.merge(
    sp500_return_series,
    left_index=True,
    right_index=True,
    how="inner",  # Use only years where both data points exist
)

# --- Annual Returns Visualization ---
st.subheader("Annual Returns Comparison")
tab1, tab2, tab3 = st.tabs(["Combined", "Savings Rate", "S&P 500 Return"])

with tab1:
    st.bar_chart(combined_df, use_container_width=True)
with tab2:
    st.bar_chart(savings_rate_df, use_container_width=True)
with tab3:
    st.bar_chart(sp500_return_series, use_container_width=True)

# --- Cumulative Growth Calculation ---
st.subheader("Cumulative Growth Comparison")

# Calculate cumulative growth factors (1 + rate/100)
cumulative_savings: pd.Series = (savings_rate_df["Savings Rate"] / 100 + 1).cumprod()
cumulative_sp500: pd.Series = (sp500_return_series / 100 + 1).cumprod()

# Combine cumulative growth data using the .merge method
# Convert Series to DataFrames before merging to use the method
cumulative_df: pd.DataFrame = cumulative_savings.to_frame(name="Savings Growth").merge(
    cumulative_sp500.to_frame(name="S&P 500 Growth"),
    left_index=True,
    right_index=True,
    how="inner",
)

# --- Cumulative Growth Results ---
# Check if data is available before accessing iloc[-1]
if not cumulative_df.empty:
    final_savings_growth: float = cumulative_df["Savings Growth"].iloc[-1]
    final_sp500_growth: float = cumulative_df["S&P 500 Growth"].iloc[-1]

    st.write(
        f"Starting with $1, investing in the S&P 500 would have grown to "
        f"**${final_sp500_growth:.2f}** compared to **${final_savings_growth:.2f}** "
        f"from the illustrative savings account over the same period."
    )
    if final_sp500_growth > final_savings_growth:
        st.write(
            "This indicates that, over the covered period, investing in the S&P 500 "
            "significantly outpaced the growth from savings returns."
        )
    else:
        st.write(
            "This shows that, according to this illustrative data, saving provided "
            "higher cumulative growth than investing in the market for this specific timeframe."
        )

    # --- Cumulative Growth Visualization ---
    st.line_chart(cumulative_df, use_container_width=True)
else:
    st.warning("Could not compute cumulative growth. Check data availability.")
