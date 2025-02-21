import streamlit as st
import yfinance as yf
import datetime

import matplotlib.pyplot as plt
import pandas_datareader as pdr
import altair as alt
import pandas as pd



st.set_page_config(page_title="Investing 101", layout="wide")

st.write("""
Investing is the act of allocating resources, usually money, with the expectation of generating income or profit. 
By investing, you can potentially grow your wealth over time, outpacing inflation and ensuring financial security.

It can help you achieve your financial goals, such as saving for retirement, buying a home, or funding your children's education.
Previous generations often relied on their savings account to grow their wealth but with the decreasing interest rates, this no longer
generates a steady passive income as it used to be.

This becomes visible when we compare the savings rate with the S&P 500 return. Note that the savings rate here is high, which is not the case in reality.
""")


if "savings_rate" not in st.session_state:
    # start = datetime.date(1986, 1, 1)
    # end = datetime.date(2020, 1, 1)

    # savings_rate = pdr.get_data_fred('PSAVERT', start, end)
    # st.session_state["savings_rate"] = savings_rate.resample('YE').mean()
    
    years = list(range(1980, 2025))
    rates = [
        10.5, 11.0, 10.8, 10.2, 9.8, 9.2, 8.5, 8.0, 7.5, 7.0, 9.0, 8.5, 8.0, 7.8, 6.5,
        6.0, 5.5, 5.0, 4.5, 3.5, 3.0, 3.0, 2.8, 2.5, 2.2, 2.0, 2.2, 3.0, 3.5, 1.5,
        1.2, 1.5, 1.2, 1.0, 0.8, 0.5, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.5, 1.5, 2.0
    ]

    df = pd.DataFrame({"Year": years, "Savings Rate": rates})
    df.set_index("Year", inplace=True)
    df.index = pd.to_datetime(df.index.astype(str)) + pd.offsets.YearEnd(0)
    st.session_state["savings_rate"] = df

    st.dataframe(st.session_state["savings_rate"])
        
if "sp500_return" not in st.session_state:
    data = yf.download("^GSPC", period="50y", interval="1mo")

    # Resample to get the last closing price of each year and compute annual returns.
    yearly_data = data['Close'].resample('YE').last()
    yearly_data.index = pd.to_datetime(yearly_data.index, format="%Y")
    st.session_state["sp500_return"] = yearly_data.pct_change().dropna() * 100
    

combined = st.session_state["savings_rate"].merge(
     st.session_state["sp500_return"], left_index=True, right_index=True, how="inner"
)

tab1, tab2, tab3 = st.tabs(["Combined", "Savings Rate", "S&P 500 Return"])

with tab1:
    st.bar_chart(combined, use_container_width=True, stack=False)
with tab2:
    st.bar_chart(st.session_state["savings_rate"], use_container_width=True)
with tab3:
    st.bar_chart(st.session_state["sp500_return"], use_container_width=True)

# Compute cumulative returns by converting annual percentage changes into growth factors.
savings = st.session_state["savings_rate"]
sp500 = st.session_state["sp500_return"]

cumulative_savings = (savings / 100 + 1).cumprod()
cumulative_sp500 = (sp500 / 100 + 1).cumprod()

cumulative_df = cumulative_savings.merge(cumulative_sp500, left_index=True, right_index=True, how="inner")
cumulative_df.columns = ["Savings", "S&P 500"]

final_savings = cumulative_df["Savings"].iloc[-1]
final_sp500 = cumulative_df["S&P 500"].iloc[-1]

if final_sp500 > final_savings:
    st.write(f"The S&P 500 accumulated to **{final_sp500:.2f}** compared to the savings account's **{final_savings:.2f}**. "
                "This indicates that, over the covered period, investing in the S&P 500 significantly outpaced the growth you would have seen by relying solely on traditional savings returns.")
else:
    st.write(f"The savings account accumulated to {final_savings:.2f} compared to the S&P 500's {final_sp500:.2f}. "
                "This shows that in this specific timeframe, saving provided higher cumulative returns than investing in the market.")
    
st.line_chart(cumulative_df, use_container_width=True)