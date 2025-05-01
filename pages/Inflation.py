import pandas as pd
import streamlit as st

# --- Constants ---
INFLATION_TARGET = 2.0
LOW_INFLATION_THRESHOLD = 1.0

DATA_URLS = {
    "fed_rate": "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=EFFR&scale=left&cosd=1900-02-19&coed=2025-02-19&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Daily&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2025-02-20&revision_date=2025-02-20&nd=2000-07-03",
    "ecb_rate": "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=off&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=ECBDFR&scale=left&cosd=1900-02-20&coed=2025-02-20&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Daily%2C%207-Day&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2025-02-20&revision_date=2025-02-20&nd=1999-01-01",
    "euro_area_inflation": "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=off&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CP0000EZ19M086NEST&scale=left&cosd=1997-01-01&coed=2024-12-01&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=pc1&vintage_date=2025-02-20&revision_date=2025-02-20&nd=1996-01-01",
    "us_inflation": "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CPIAUCSL&scale=left&cosd=1947-01-01&coed=2025-01-01&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=pc1&vintage_date=2025-02-20&revision_date=2025-02-20&nd=1947-01-01",
    "us_savings_rate": "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=SNDR&scale=left&cosd=1900-04-01&coed=2025-02-01&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2021-04-01&line_index=1&transformation=lin&vintage_date=2025-02-21&revision_date=2025-02-21&nd=1947-01-01",
    "us_mortgage_rate": "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=MORTGAGE30US&scale=left&cosd=1971-04-02&coed=2025-02-20&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Weekly%2C%20Ending%20Thursday&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2025-02-21&revision_date=2025-02-21&nd=1971-04-02",
}


# --- Data Loading ---
@st.cache_data
def load_fred_data(url: str) -> pd.DataFrame:
    """Loads data from a FRED CSV URL and formats it."""
    data_df = pd.read_csv(url, index_col=0)
    data_df.index = pd.to_datetime(data_df.index)
    # Handle potential non-numeric values represented as '.'
    for col in data_df.columns:
        data_df[col] = pd.to_numeric(data_df[col], errors="coerce")
    return data_df


with st.spinner("Loading data..."):
    for key, url in DATA_URLS.items():
        if key not in st.session_state:
            st.session_state[key] = load_fred_data(url)

# --- Page Content ---
st.subheader("Understanding Inflation and Central Bank Policies")

explanation = """
Inflation is the rate at which the overall price level for goods and services rises, leading
to a decrease in purchasing power.
In a healthy economy, a moderate and steady inflation rate is normal and even desirable, as
it encourages spending and investment.

Central banks, such as the European Central Bank and the Federal Reserve, influence inflation
by adjusting policy rates.
By increasing rates, borrowing becomes more expensive, which can slow down spending and
investment, thereby reducing inflationary pressures.
Conversely, lowering rates makes borrowing cheaper, stimulating economic activity and
potentially increasing inflation.

**A commonly targeted inflation rate is around 2%.** This rate is considered optimal as
it balances the goals of maintaining price stability,
providing confidence in the economy, and allowing enough room for monetary policy adjustments.
Maintaining inflation close to 2% avoids the risks
associated with deflation or negative inflation, which can lead to decreased consumer
spending and investment, and may trigger an economic slowdown
as people delay purchases in anticipation of lower prices.
"""

st.markdown(explanation)

# --- Euro Area Section ---
st.subheader("Inflation and Interest Rates in the Euro Area")

# Get the latest readings
latest_eu_inflation = st.session_state["euro_area_inflation"].iloc[-1, 0]

# Build dynamic commentary
if pd.isna(latest_eu_inflation):
    text_eu = "Latest Euro Area inflation data is not available."
elif latest_eu_inflation > INFLATION_TARGET:
    text_eu = (
        "Recent data indicates that inflation in the Euro Area is running above the "
        f"{INFLATION_TARGET:.1f}% target level. This growing price pressure suggests that the "
        "European Central Bank might be inclined to raise its policy rates to cool down inflation."
    )
elif latest_eu_inflation < LOW_INFLATION_THRESHOLD:
    text_eu = (
        "The latest figures show that inflation in the Euro Area is quite subdued (below "
        f"{LOW_INFLATION_THRESHOLD:.1f}%). With low price pressures, the European Central Bank is "
        "likely to maintain or even lower interest rates to foster economic growth."
    )
else:
    text_eu = (
        "Inflation in the Euro Area appears moderate at present. In this balanced scenario, "
        "the European Central Bank may continue to carefully adjust interest rates to sustain "
        "price stability while supporting the economy."
    )

st.markdown(text_eu)

# Prepare and plot data
combined_eu = (
    st.session_state["euro_area_inflation"]
    .merge(
        st.session_state["ecb_rate"],
        left_index=True,
        right_index=True,
        how="outer",  # Use outer merge to keep all dates
    )
    .ffill()  # Forward fill missing values after merge
)
combined_eu.columns = ["Inflation Rate", "ECB Rate"]
st.line_chart(
    combined_eu.dropna(), use_container_width=True
)  # Drop rows with NaN before plotting

# --- United States Section ---
st.subheader("Inflation and Interest Rates in the United States")

# Get the latest readings
latest_us_inflation = st.session_state["us_inflation"].iloc[-1, 0]

# Build dynamic commentary
if pd.isna(latest_us_inflation):
    text_us = "Latest US inflation data is not available."
elif latest_us_inflation > INFLATION_TARGET:
    text_us = (
        "Recent data indicates that inflation in the United States is running above the "
        f"{INFLATION_TARGET:.1f}% target level. This rising price pressure suggests that the "
        "Federal Reserve might be inclined to raise its policy rates to combat inflation."
    )
elif latest_us_inflation < LOW_INFLATION_THRESHOLD:
    text_us = (
        "The latest figures show that inflation in the United States is quite subdued (below "
        f"{LOW_INFLATION_THRESHOLD:.1f}%). With low price pressures, the Federal Reserve is "
        "likely to maintain or even lower interest rates to stimulate economic activity."
    )
else:
    text_us = (
        "Inflation in the United States appears moderate at present. In this balanced scenario, "
        "the Federal Reserve may continue to adjust interest rates carefully to sustain "
        "price stability while supporting economic growth."
    )
st.markdown(text_us)

# Prepare and plot data
combined_us = (
    st.session_state["us_inflation"]
    .merge(
        st.session_state["fed_rate"],
        left_index=True,
        right_index=True,
        how="outer",
    )
    .ffill()
)
combined_us.columns = ["Inflation Rate", "Federal Funds Rate"]
st.line_chart(combined_us.dropna(), use_container_width=True)

# --- US Savings and Mortgage Rates Section ---
st.subheader("The Central Bank's Influence on Savings and Mortgage Rates")

# Savings Rate Explanation and Plot
text_savings = (
    "Analysis indicates a direct correlation between the US Savings Rate and the Federal Funds Rate. "
    "When the Federal Reserve adjusts its benchmark rate, savings behavior often adjusts correspondingly. "
    "Higher rates typically encourage saving, while lower rates may reduce the incentive."
)
st.markdown(text_savings)

# Note: Dividing fed_rate by 10 might be for scaling purposes on the chart
savings_rate_combined = (
    st.session_state["us_savings_rate"]
    .merge(
        st.session_state["fed_rate"] / 10,  # Keep scaling if intended
        left_index=True,
        right_index=True,
        how="outer",
    )
    .ffill()
)
savings_rate_combined.columns = ["Savings Rate", "Federal Funds Rate (Scaled)"]
st.line_chart(savings_rate_combined.dropna(), use_container_width=True)

# Mortgage Rate Explanation and Plot
text_mortgage = (
    "The US Mortgage Rate is closely tied to the Federal Funds Rate, although other market factors also play a role. "
    "When the Federal Reserve adjusts its benchmark rate, mortgage rates tend to follow suit over time. "
    "Higher rates generally lead to increased borrowing costs, potentially slowing the housing market, "
    "while lower rates can stimulate demand."
)
st.markdown(text_mortgage)

# Resample to monthly frequency using the last observation of the month
mortgage_rate_monthly = st.session_state["us_mortgage_rate"].resample("ME").last()
fed_rate_monthly = st.session_state["fed_rate"].resample("ME").last()

mortgage_rate_combined = mortgage_rate_monthly.merge(
    fed_rate_monthly,
    left_index=True,
    right_index=True,
    how="outer",  # Use outer merge before forward fill
).ffill()
mortgage_rate_combined.columns = ["Mortgage Rate", "Federal Funds Rate"]
st.line_chart(mortgage_rate_combined.dropna(), use_container_width=True)
