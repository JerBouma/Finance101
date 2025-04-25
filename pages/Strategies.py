import datetime

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

# Set default lump sum amount (used for all strategies)
DEFAULT_LUMP_SUM = 10000.0
DEFAULT_TRANSACTION_COST = 5.0 # Default transaction cost

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
        # Download data, handling potential errors
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period="max", actions=True)
            # Check if data was downloaded and has expected columns
            if not data.empty and 'Close' in data.columns:
                 # No need for xs if downloading single ticker
                st.session_state["historical_data_all"][ticker] = data
            else:
                st.warning(f"Could not download or process data for {ticker}")
                st.session_state["historical_data_all"][ticker] = pd.DataFrame() # Store empty df
        except Exception as e:
            st.error(f"Error downloading data for {ticker}: {e}")
            st.session_state["historical_data_all"][ticker] = pd.DataFrame() # Store empty df


# Set the simulation data to the selected ETF's data
# Check if data for selected ticker exists and is not empty
if selected_ticker in st.session_state["historical_data_all"] and not st.session_state["historical_data_all"][selected_ticker].empty:
    st.session_state["historical_data"] = st.session_state["historical_data_all"][
        selected_ticker
    ]
    st.session_state["ticker"] = selected_ticker
else:
    st.error(f"No data available for the selected ETF: {ticker_label} ({selected_ticker}). Please select another ETF or check data source.")
    st.stop() # Stop execution if data is missing


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
    if not data.empty and 'Close' in data.columns:
        # Ensure we are working with a Series, even if data["Close"] somehow returned a DataFrame
        monthly_series = data["Close"].squeeze().resample("ME").last().dropna()
        if monthly_series.empty or len(monthly_series) < 2:
            continue
        etf_label = [name for name, sym in etfs.items() if sym == ticker][0]
        # Ensure first price is not zero and not NaN before calculating returns
        try:
            first_price = monthly_series.iloc[0]
            # Ensure first_price is a scalar, using .item() if necessary for Series/array-like objects
            if hasattr(first_price, 'item'):
                first_price = first_price.item()

            # Check the scalar value
            if pd.notna(first_price) and first_price != 0:
                cumulative_returns_all[etf_label] = (
                    monthly_series / first_price - 1
                ) * 100  # in percentage
            elif pd.isna(first_price):
                 st.warning(f"Initial price for {etf_label} is NaN, cannot calculate cumulative returns.")
            else: # Handles the case where first_price is 0
                 st.warning(f"Initial price for {etf_label} is zero, cannot calculate cumulative returns.")
        except IndexError:
            # This handles the case where monthly_series might be empty despite earlier checks
            st.warning(f"Could not get initial price for {etf_label} (IndexError). Skipping calculation.")
        except ValueError as e:
            # Catch error if .item() is called on multi-element Series or wrong type
            st.warning(f"Error processing initial price for {etf_label}: {e}. Skipping calculation.")


if cumulative_returns_all:
    cumulative_returns_df = pd.DataFrame(cumulative_returns_all).dropna(how='all') # Drop rows/cols where all are NaN

    if not cumulative_returns_df.empty:
        st.line_chart(cumulative_returns_df, use_container_width=True)

        st.markdown(
            """
        The following metrics are calculated for each ETF:
        - Annualized Return (%): The average yearly return over the sample period, accounting for compounding.
        - Annualized Volatility (%): The standard deviation of daily returns scaled to an annual basis, reflecting risk.
        - Maximum Drawdown (%): The largest peak-to-trough decline during the investment period, indicating worst-case loss.
        - Sharpe Ratio: A risk-adjusted return measure, calculated as the annualized return divided by annualized volatility (assuming risk-free rate = 0).
        - Calmar Ratio: The ratio of annualized return to maximum drawdown, emphasizing return relative to downside risk.
        """
        )

        etf_stats = {}
        for name, ticker in etfs.items():
            data = st.session_state["historical_data_all"].get(ticker) # Use .get for safety
            if data is None or data.empty or "Close" not in data.columns:
                st.warning(f"Skipping stats calculation for {name} due to missing or invalid base data.")
                continue

            # Ensure 'Close' column is treated as a Series
            close_col = data["Close"]
            if isinstance(close_col, pd.DataFrame):
                # If 'Close' is a DataFrame (e.g., multi-index issue), try to extract Series
                if close_col.shape[1] == 1:
                    close_col = close_col.iloc[:, 0] # Select first column
                else:
                    st.warning(f"Skipping stats calculation for {name}: Unexpected structure for 'Close' column (DataFrame).")
                    continue
            elif not isinstance(close_col, pd.Series):
                 st.warning(f"Skipping stats calculation for {name}: 'Close' column is not a Series.")
                 continue

            # Ensure data is sorted by date and drop NaNs in Close price
            price = close_col.sort_index().dropna()

            # Check for sufficient data points after cleaning
            if len(price) < 2:
                 st.warning(f"Skipping stats calculation for {name} due to insufficient data points after cleaning (need at least 2).")
                 continue

            # Daily returns - now guaranteed to work on a Series
            daily_returns = price.pct_change().dropna()
            if daily_returns.empty:
                st.warning(f"Skipping stats calculation for {name} as daily returns could not be calculated (e.g., constant price).")
                continue

            # Annualized Return: using the geometric return formula
            start_price = price.iloc[0]
            end_price = price.iloc[-1]
            if start_price == 0: # Avoid division by zero
                st.warning(f"Skipping annualized return for {name} due to zero start price.")
                annualized_return = np.nan
            else:
                total_period_years = (price.index[-1] - price.index[0]).days / 365.25
                if total_period_years <= 0:
                    annualized_return = np.nan # Avoid invalid power
                else:
                    annualized_return = (end_price / start_price) ** (1 / total_period_years) - 1


            # Annualized Volatility
            annualized_vol = daily_returns.std() * np.sqrt(252) # Assuming 252 trading days

            # Maximum Drawdown
            running_max = price.cummax()
            drawdown = (price - running_max) / running_max
            max_drawdown = drawdown.min() # This will be negative or zero

            # Sharpe Ratio (Risk-Free Rate assumed to be 0)
            # Check for NaN or zero volatility, or NaN return
            if pd.isna(annualized_vol) or annualized_vol == 0 or pd.isna(annualized_return):
                sharpe_ratio = np.nan
            else:
                sharpe_ratio = annualized_return / annualized_vol

            # Calmar Ratio
            # Check for NaN or zero max drawdown, or NaN return
            if pd.isna(max_drawdown) or max_drawdown == 0 or pd.isna(annualized_return):
                calmar_ratio = np.nan
            else:
                # Use abs() for max_drawdown as it's negative
                calmar_ratio = annualized_return / abs(max_drawdown)


            etf_stats[name] = {
                "Annualized Return (%)": annualized_return * 100 if pd.notna(annualized_return) else np.nan,
                "Annualized Volatility (%)": annualized_vol * 100 if not np.isnan(annualized_vol) else np.nan,
                "Maximum Drawdown (%)": max_drawdown * 100 if not np.isnan(max_drawdown) else np.nan,
                "Sharpe Ratio": sharpe_ratio if not np.isnan(sharpe_ratio) else np.nan,
                "Calmar Ratio": calmar_ratio if not np.isnan(calmar_ratio) else np.nan,
            }

        if etf_stats:
            stats_df = pd.DataFrame(etf_stats).T.dropna(how='all') # Drop rows where all stats are NaN
            if not stats_df.empty:
                st.dataframe(stats_df.style.format("{:.2f}", na_rep="-")) # Display NaN as '-'
            else:
                st.info("No valid ETF statistics could be calculated.")
    else:
        st.info("No valid cumulative returns data to display.")
else:
    st.info("Could not calculate cumulative returns for any ETF.")


# Date inputs: use available data range as bounds
data_index = st.session_state["historical_data"].index
min_date = data_index.min().date()
max_date = data_index.max().date()

# Ensure default start date is within bounds
default_start_date = datetime.date(2010, 1, 1)
if default_start_date < min_date:
    default_start_date = min_date
elif default_start_date > max_date:
    default_start_date = max_date

start_date = st.sidebar.date_input(
    "Select start date",
    value=default_start_date,
    min_value=min_date,
    max_value=max_date,
)

# Amount input: one amount is used for both strategies
lump_sum = st.sidebar.number_input(
    "Total Investment Amount (€)", min_value=0.0, value=DEFAULT_LUMP_SUM, step=100.0
)

# Transaction cost input
transaction_cost = st.sidebar.number_input(
    "Transaction Cost per Purchase (€)", min_value=0.0, value=DEFAULT_TRANSACTION_COST, step=0.5
)


# Use adjusted close prices and resample monthly (take last trading day)
monthly_data = (
    st.session_state["historical_data"]["Close"].resample("ME").last().dropna()
)

# Filter data from the starting date onward
# Ensure start_date is timezone-aware if the index is
start_timestamp = pd.Timestamp(start_date)
if monthly_data.index.tz is not None:
    # Localize the start_timestamp to the index's timezone
    start_timestamp = start_timestamp.tz_localize(monthly_data.index.tz)

monthly_data = monthly_data[monthly_data.index >= start_timestamp]


if len(monthly_data) < 2:  # noqa
    st.error("Not enough data points after the start date to run the simulation.")
    st.stop()

# Prepare DataFrame for simulation results
simulation = pd.DataFrame(index=monthly_data.index)
simulation["Price"] = monthly_data

# Lists to track which simulation(s) we run
simulation_labels = []
plot_data = {}
summary_lines = [] # Initialize summary lines list

# --- Lump Sum Simulation ---
if lump_sum > 0:
    first_price = simulation["Price"].iloc[0]
    amount_to_invest_lump = lump_sum - transaction_cost # Deduct cost first
    lump_shares = 0.0
    total_cost_lump = 0.0

    if amount_to_invest_lump > 0 and first_price > 0:
        lump_shares = amount_to_invest_lump / first_price
        simulation["LumpSum Value"] = lump_shares * simulation["Price"]
        simulation_labels.append("Lump Sum Investing")
        plot_data["Lump Sum Investing"] = simulation["LumpSum Value"]
        total_cost_lump = transaction_cost # Only one transaction

        # Summary for Lump Sum
        final_lump = simulation["LumpSum Value"].iloc[-1]
        # Total invested is the initial lump sum amount allocated
        total_invested_lump = lump_sum
        # ROI is calculated based on the total allocated capital
        roi_lump = ((final_lump - total_invested_lump) / total_invested_lump) * 100 if total_invested_lump else 0
        final_date_str = simulation.index[-1].strftime('%Y-%m-%d')
        summary_lines.append(
            f"**Lump Sum Investing (as of {final_date_str}):** Allocated "
            f"€{total_invested_lump:,.2f} (incl. €{total_cost_lump:,.2f} cost), "
            f"Final Value €{final_lump:,.2f} (ROI: {roi_lump:,.2f}%)"
        )
    elif amount_to_invest_lump <= 0:
         st.warning(f"Lump Sum simulation skipped: Investment amount (€{lump_sum:,.2f}) is less than or equal to transaction cost (€{transaction_cost:,.2f}).")
    else: # first_price is zero
        st.warning("Lump Sum simulation skipped: Initial price is zero.")


# --- Periodic Investment Simulations (DCA) ---
investment_periods = {
    "Monthly": 1,
    "Quarterly": 3,
    "Half-Yearly": 6,
    "Yearly": 12,
}

if lump_sum > 0:
    n_total_months = len(simulation)
    simulation_start_month = simulation.index[0].month
    simulation_start_year = simulation.index[0].year

    for freq_label, months_in_period in investment_periods.items():
        strategy_label = f"{freq_label} Investing"
        value_col = f"{freq_label} Value"
        shares_col = f"{freq_label} Shares Bought"
        cum_shares_col = f"{freq_label} Cumulative Shares"

        # Determine investment dates based on frequency
        investment_dates = []
        for i, date in enumerate(simulation.index):
            # Calculate months elapsed since start (0-indexed)
            months_elapsed = (date.year - simulation_start_year) * 12 + (date.month - simulation_start_month)
            # Invest at the *end* of the period (e.g., month 3 for quarterly, month 12 for yearly)
            # Check if the *next* month starts a new period
            if (months_elapsed + 1) % months_in_period == 0 or i == n_total_months - 1: # Invest in last month too if needed
                 investment_dates.append(date)

        # Filter out potential duplicate investment dates if period ends exactly at simulation end
        investment_dates = sorted(list(set(investment_dates)))

        num_investments = len(investment_dates)
        if num_investments == 0:
            st.warning(f"Skipping {strategy_label}: No investment periods found within the selected date range.")
            continue

        periodic_investment_amount = lump_sum / num_investments
        amount_to_invest_periodic = periodic_investment_amount - transaction_cost # Amount available after cost

        if amount_to_invest_periodic <= 0:
            st.warning(f"Skipping {strategy_label}: Periodic amount (€{periodic_investment_amount:,.2f}) is less than or equal to transaction cost (€{transaction_cost:,.2f}).")
            continue

        simulation[shares_col] = 0.0
        simulation[cum_shares_col] = 0.0
        simulation[value_col] = 0.0
        cumulative_shares = 0.0
        actual_investments_made = 0

        # Calculate shares bought on investment dates
        for inv_date in investment_dates:
            price_on_inv_date = simulation.loc[inv_date, "Price"]
            if price_on_inv_date > 0:
                shares_bought = amount_to_invest_periodic / price_on_inv_date
                simulation.loc[inv_date, shares_col] = shares_bought
                actual_investments_made += 1
            else:
                 st.warning(f"Skipping investment for {strategy_label} on {inv_date.strftime('%Y-%m-%d')} due to zero price.")


        # Calculate cumulative shares and value for all months
        simulation[cum_shares_col] = simulation[shares_col].cumsum()
        simulation[value_col] = simulation[cum_shares_col] * simulation["Price"]

        simulation_labels.append(strategy_label)
        plot_data[strategy_label] = simulation[value_col]

        # Summary for Periodic Strategy
        final_value = simulation[value_col].iloc[-1]
        # Total allocated capital is lump_sum by design for DCA strategies here
        total_allocated = lump_sum
        total_transaction_costs = actual_investments_made * transaction_cost
        # ROI is calculated based on the total allocated capital
        roi = ((final_value - total_allocated) / total_allocated) * 100 if total_allocated else 0
        final_date_str = simulation.index[-1].strftime('%Y-%m-%d')
        summary_lines.append(
            f"**{strategy_label} (as of {final_date_str}):** Allocated "
            f"€{total_allocated:,.2f} ({actual_investments_made} installments, "
            f"total costs €{total_transaction_costs:,.2f}), "
            f"Final Value €{final_value:,.2f} (ROI: {roi:,.2f}%)"
        )


if not simulation_labels:
    st.error("Please enter a positive investment amount or check data availability/transaction costs.")
    st.stop()

# --- Savings Simulation ---
# Savings simulation does not incur transaction costs for buying assets
savings_rate = st.sidebar.number_input(
    "Savings Rate (% Annual)", min_value=0.0, value=2.0, step=0.1
)
monthly_rate = (1 + savings_rate / 100)**(1/12) - 1 # More accurate monthly rate from annual

# Use the monthly investment amount calculated for the "Monthly Investing" strategy
# Need to ensure Monthly Investing ran successfully
if "Monthly Investing" in simulation_labels and "Monthly Shares Bought" in simulation.columns:
    # Calculate the intended monthly investment amount (before costs)
    # This assumes the Monthly strategy was calculated based on the total lump sum / total months
    num_investments_monthly = len(simulation) # Each month is an investment period for monthly
    monthly_investment_amount = lump_sum / num_investments_monthly if num_investments_monthly > 0 else 0

    if monthly_investment_amount > 0:
        savings_values = []
        savings_accumulated = 0.0
        for _ in simulation.index:
            # Add investment first, then apply interest for the month
            savings_accumulated += monthly_investment_amount
            savings_accumulated *= (1 + monthly_rate)
            savings_values.append(savings_accumulated)

        simulation["Savings Value"] = savings_values
        plot_data["Savings Account"] = simulation["Savings Value"]

        # Summary for Savings
        final_savings = simulation["Savings Value"].iloc[-1]
        # Total principal invested is the sum of monthly investments
        total_invested_savings = monthly_investment_amount * len(simulation)
        # Ensure total invested isn't zero to avoid division error
        roi_savings = ((final_savings - total_invested_savings) / total_invested_savings) * 100 if total_invested_savings else 0
        final_date_str = simulation.index[-1].strftime('%Y-%m-%d')
        summary_lines.append(
            f"**Savings Account (as of {final_date_str}):** Deposited €{total_invested_savings:,.2f} monthly, "
            f"Final Value €{final_savings:,.2f} (ROI: {roi_savings:,.2f}%)"
        )
    else:
        st.warning("Savings account simulation skipped as monthly deposit amount is zero.")

elif lump_sum > 0 and len(simulation) > 0:
    # Fallback if Monthly Investing didn't run but we have a lump sum and duration
    st.warning("Monthly Investing strategy did not run (check transaction costs vs. monthly amount). Calculating savings based on simple monthly allocation.")
    num_investments_monthly = len(simulation)
    monthly_investment_amount = lump_sum / num_investments_monthly

    if monthly_investment_amount > 0:
        savings_values = []
        savings_accumulated = 0.0
        for _ in simulation.index:
            savings_accumulated += monthly_investment_amount
            savings_accumulated *= (1 + monthly_rate)
            savings_values.append(savings_accumulated)

        simulation["Savings Value"] = savings_values
        plot_data["Savings Account"] = simulation["Savings Value"]

        final_savings = simulation["Savings Value"].iloc[-1]
        total_invested_savings = monthly_investment_amount * len(simulation)
        roi_savings = ((final_savings - total_invested_savings) / total_invested_savings) * 100 if total_invested_savings else 0
        final_date_str = simulation.index[-1].strftime('%Y-%m-%d')
        summary_lines.append(
            f"**Savings Account (as of {final_date_str}):** Deposited €{total_invested_savings:,.2f} monthly, "
            f"Final Value €{final_savings:,.2f} (ROI: {roi_savings:,.2f}%)"
        )
    else:
         st.warning("Savings account simulation skipped as monthly deposit amount is zero.")

else:
    st.warning("Savings account simulation skipped as required data is unavailable.")


# --- Calculate Cumulative Returns for Plotting ---
cumulative_returns = pd.DataFrame(index=simulation.index)
# Calculate the intended monthly investment amount once (used for Savings baseline)
n_total_months = len(simulation)
monthly_investment_amount = lump_sum / n_total_months if n_total_months > 0 else 0

for label, series in plot_data.items():
    if label == "Lump Sum Investing":
        # Baseline is the initial lump sum investment allocated
        if lump_sum > 0:
            cumulative_returns[label] = (series - lump_sum) / lump_sum * 100
        else:
            cumulative_returns[label] = 0.0
    elif "Investing" in label: # Handle Monthly, Quarterly, Half-Yearly, Yearly
        # Determine the frequency for calculating cumulative invested amount
        freq_label_part = label.split(" ")[0] # e.g., "Monthly", "Quarterly"
        months_in_period = investment_periods.get(freq_label_part, 1) # Default to 1 (monthly) if not found

        cumulative_invested = pd.Series(0.0, index=simulation.index)
        invested_so_far = 0.0
        num_investments_for_freq = 0
        # Recalculate investment dates for this specific frequency
        investment_dates_freq = []
        for i, date in enumerate(simulation.index):
             months_elapsed = (date.year - simulation_start_year) * 12 + (date.month - simulation_start_month)
             if (months_elapsed + 1) % months_in_period == 0 or i == n_total_months - 1:
                 investment_dates_freq.append(date)
        investment_dates_freq = sorted(list(set(investment_dates_freq)))
        num_investments_for_freq = len(investment_dates_freq)

        if num_investments_for_freq > 0:
            # Base cumulative investment on the allocated amount *before* costs
            amount_per_investment = lump_sum / num_investments_for_freq
            investment_occurred = pd.Series(False, index=simulation.index)
            investment_occurred.loc[investment_dates_freq] = True

            cumulative_invested = (investment_occurred.cumsum() * amount_per_investment).reindex(simulation.index, method='ffill').fillna(0)

            # Calculate return relative to cumulative allocated amount
            # Avoid division by zero if cumulative_invested is 0 (at the start)
            cumulative_returns[label] = (
                (series - cumulative_invested) / cumulative_invested.replace(0, np.nan) * 100
            )
        else:
             cumulative_returns[label] = 0.0 # No investments, no return

    elif label == "Savings Account":
        # Calculate cumulative principal deposited for savings (monthly deposits)
        if monthly_investment_amount > 0:
            cumulative_invested_savings = pd.Series(
                range(1, n_total_months + 1), index=simulation.index
            ) * monthly_investment_amount
            # Avoid division by zero
            cumulative_returns[label] = (
                (series - cumulative_invested_savings) / cumulative_invested_savings.replace(0, np.nan) * 100
            )
        else:
            cumulative_returns[label] = 0.0


# Display cumulative returns using Streamlit's built-in line chart
st.subheader("Cumulative Return Over Time (%)")
st.markdown(
    f"""
This chart shows the percentage return over time for each strategy, relative to the total amount *allocated* up to that point. Transaction costs of €{transaction_cost:,.2f} per purchase are included in the investment strategy calculations, reducing the amount used to buy shares.

- **Lump Sum Investing:** Allocates the entire amount at the start (minus one transaction cost). Return is relative to the initial total allocation.
- **Periodic Investing (Monthly, Quarterly, etc.):** Allocates equal amounts at regular intervals (Dollar Cost Averaging - DCA). A transaction cost is deducted from each installment before buying shares. Return is relative to the cumulative amount allocated so far.
- **Savings Account:** Simulates depositing the equivalent periodic amount into a savings account earning a fixed interest rate (no transaction costs applied here). Return is relative to the cumulative principal deposited.
"""
)
# Add a zero line for reference
cumulative_returns["Profit Line"] = 0
# Drop columns that might be all NaN if a strategy failed
cumulative_returns = cumulative_returns.dropna(axis=1, how='all')
if not cumulative_returns.drop(columns=["Profit Line"], errors='ignore').empty:
    st.line_chart(cumulative_returns, use_container_width=True)
else:
    st.info("Could not calculate cumulative returns for plotting.")


# Display Summary stats in the sidebar
st.sidebar.subheader("Summary Statistics")
if summary_lines:
    st.sidebar.markdown("\n\n".join(summary_lines))
else:
    st.sidebar.warning("No simulation results to summarize.")

# Display raw simulation data (optional)
# st.subheader("Simulation Data")
# st.dataframe(simulation.style.format("{:,.2f}", na_rep="-"))
