import pandas as pd
import streamlit as st

fed_rate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=EFFR&scale=left&cosd=1900-02-19&coed=2025-02-19&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Daily&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2025-02-20&revision_date=2025-02-20&nd=2000-07-03"
ecb_rate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=off&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=ECBDFR&scale=left&cosd=1900-02-20&coed=2025-02-20&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Daily%2C%207-Day&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2025-02-20&revision_date=2025-02-20&nd=1999-01-01"
euro_area_inflation_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=off&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CP0000EZ19M086NEST&scale=left&cosd=1997-01-01&coed=2024-12-01&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=pc1&vintage_date=2025-02-20&revision_date=2025-02-20&nd=1996-01-01"
us_inflation_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CPIAUCSL&scale=left&cosd=1947-01-01&coed=2025-01-01&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=pc1&vintage_date=2025-02-20&revision_date=2025-02-20&nd=1947-01-01"
us_savings_rate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=SNDR&scale=left&cosd=1900-04-01&coed=2025-02-01&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2021-04-01&line_index=1&transformation=lin&vintage_date=2025-02-21&revision_date=2025-02-21&nd=1947-01-01"
us_mortgage_rate_url = "https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23ebf3fb&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1320&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=MORTGAGE30US&scale=left&cosd=1971-04-02&coed=2025-02-20&line_color=%230073e6&link_values=false&line_style=solid&mark_type=none&mw=3&lw=3&ost=-99999&oet=99999&mma=0&fml=a&fq=Weekly%2C%20Ending%20Thursday&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2025-02-21&revision_date=2025-02-21&nd=1971-04-02"

with st.spinner("Loading data..."):
    if "fed_rate" not in st.session_state:
        st.session_state["fed_rate"] = pd.read_csv(fed_rate_url, index_col=0)
        st.session_state["fed_rate"].index = pd.to_datetime(
            st.session_state["fed_rate"].index
        )
    if "us_inflation" not in st.session_state:
        st.session_state["us_inflation"] = pd.read_csv(us_inflation_url, index_col=0)
        st.session_state["us_inflation"].index = pd.to_datetime(
            st.session_state["us_inflation"].index
        )
    if "ecb_rate" not in st.session_state:
        st.session_state["ecb_rate"] = pd.read_csv(ecb_rate_url, index_col=0)
        st.session_state["ecb_rate"].index = pd.to_datetime(
            st.session_state["ecb_rate"].index
        )
    if "euro_area_inflation" not in st.session_state:
        st.session_state["euro_area_inflation"] = pd.read_csv(
            euro_area_inflation_url, index_col=0
        )
        st.session_state["euro_area_inflation"].index = pd.to_datetime(
            st.session_state["euro_area_inflation"].index
        )
    if "us_savings_rate" not in st.session_state:
        st.session_state["us_savings_rate"] = pd.read_csv(us_savings_rate_url, index_col=0)
        st.session_state["us_savings_rate"].index = pd.to_datetime(
            st.session_state["us_savings_rate"].index
        )
    if "us_mortgage_rate" not in st.session_state:
        st.session_state["us_mortgage_rate"] = pd.read_csv(us_mortgage_rate_url, index_col=0)
        st.session_state["us_mortgage_rate"].index = pd.to_datetime(
            st.session_state["us_mortgage_rate"].index
        )

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

st.subheader("Inflation and Interest Rates in the Euro Area")
# Get the latest readings and calculate recent changes
latest_eu_inflation = st.session_state["euro_area_inflation"].iloc[-1, 0]

# Build a dynamic commentary based on the latest inflation figures
if latest_eu_inflation > 2:  # noqa
    text = (
        "Recent data indicates that inflation in the Euro Area is running above the "
        "usual target level. This growing price pressure suggests that the European Central Bank "
        "might be inclined to raise its policy rates to cool down inflation."
    )
elif latest_eu_inflation < 1:  # noqa
    text = (
        "The latest figures show that inflation in the Euro Area is quite subdued. With low price pressures, "
        "the European Central Bank is likely to maintain or even lower interest rates to foster economic growth."
    )
else:
    text = (
        "Inflation in the Euro Area appears moderate at present. In this balanced scenario, the European Central Bank "
        "may continue to carefully adjust interest rates to sustain price stability while supporting the economy."
    )

st.markdown(text)
combined = st.session_state["euro_area_inflation"].merge(
    st.session_state["ecb_rate"],
    left_index=True,
    right_index=True,
)

combined = combined.ffill()
combined.columns = ["Inflation Rate", "ECB Rate"]

st.line_chart(combined, use_container_width=True)

st.subheader("Inflation and Interest Rates in the United States")

# Get the latest readings and calculate recent changes
latest_us_inflation = st.session_state["us_inflation"].iloc[-1, 0]

# Build a dynamic commentary based on the latest inflation figures
if latest_us_inflation > 2:  # noqa
    text = (
        "Recent data indicates that inflation in the United States is running above the "
        "target level. This rising price pressure suggests that the Federal Reserve "
        "might be inclined to raise its policy rates to combat inflation."
    )
elif latest_us_inflation < 1:  # noqa
    text = (
        "The latest figures show that inflation in the United States is quite subdued. With low price pressures, "
        "the Federal Reserve is likely to maintain or even lower interest rates to stimulate economic activity."
    )
else:
    text = (
        "Inflation in the United States appears moderate at present. In this balanced scenario, the Federal Reserve "
        "may continue to adjust interest rates carefully to sustain price stability while supporting economic growth."
    )
st.markdown(text)

combined = st.session_state["us_inflation"].merge(
    st.session_state["fed_rate"],
    left_index=True,
    right_index=True,
)

combined = combined.ffill()
combined.columns = ["Inflation Rate", "Federal Funds Rate"]

st.line_chart(combined, use_container_width=True)


st.subheader("The Central Bank's Influence on Savings and Mortgage Rates")

# Get the latest readings and calculate recent changes
# Explain the relationship between the US Savings Rate and the Federal Funds Rate
text = (
    "Analysis indicates a direct correlation between the US Savings Rate and the Federal Funds Rate. "
    "When the Federal Reserve adjusts its benchmark rate, it appears that the savings behavior adjusts correspondingly. "
    "Higher rates often promote increased savings, as borrowing costs rise, while lower rates may reduce the incentive to save."
)
st.markdown(text)

savings_rate_combined = st.session_state["us_savings_rate"].merge(
    st.session_state["fed_rate"] / 10,
    left_index=True,
    right_index=True,
)

savings_rate_combined = savings_rate_combined.ffill()

savings_rate_combined.columns = ["Savings Rate", "Federal Funds Rate"]

st.line_chart(savings_rate_combined, use_container_width=True)

# Get the latest readings and calculate recent changes
# Explain the relationship between the US Mortgage Rate and the Federal Funds Rate
text = (
    "The US Mortgage Rate is closely tied to the Federal Funds Rate. "
    "When the Federal Reserve adjusts its benchmark rate, mortgage rates tend to follow suit. "
    "Higher rates can lead to increased borrowing costs, which may slow down the housing market, while lower rates can stimulate demand."
)

st.markdown(text)

mortgage_rate_monthly = st.session_state["us_mortgage_rate"].resample("ME").last()
fed_rate_monthly = st.session_state["fed_rate"].resample("ME").last()

mortgage_rate_combined = mortgage_rate_monthly.merge(
    fed_rate_monthly,
    left_index=True,
    right_index=True,
)
mortgage_rate_combined.columns = ["Mortgage Rate", "Federal Funds Rate"]

st.line_chart(mortgage_rate_combined, use_container_width=True)