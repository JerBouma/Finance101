from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from pages.mortgages import mortgages_model

# --- Constants ---
SCRIPT_DIR = Path(__file__).resolve().parent
FINANCING_BURDEN_FILE = "pages/mortgages/datasets/financing_burden_2025.pickle"
ENERGY_LABELS_FILE = "pages/mortgages/datasets/energy_labels.pickle"
DEFAULT_INCOME_1 = 60000.0
DEFAULT_INCOME_2 = 40000.0
DEFAULT_INTEREST_RATE_PCT = 4.0
DEFAULT_TERM_YEARS = 30
DEFAULT_ENERGY_LABEL_INDEX = 4
MORTGAGE_INTEREST_TAX_DEDUCTION_RATE = 0.3750  # 37.50%

# Plotting Colors
COLOR_PRINCIPAL = "#2E86C1"  # Blue
COLOR_INTEREST_GROSS = "#F39C12"  # Orange
COLOR_INTEREST_NET = "#F5B041"  # Lighter Orange
COLOR_MAX_PAYMENT_LINE = "red"
COLOR_AFFORDABLE_MORTGAGE_LINE = "green"
COLOR_INTERSECTION_MARKER = "red"

# CSS Styling
APP_STYLE = """
<style>
    .main-header {
        font-size: 2.5rem; font-weight: 700; color: #1E88E5; margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem; font-weight: 600; color: #555; padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
    .card {
        background-color: #f8f9fa; border-radius: 10px; padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 1rem;
    }
    .mortgage-result {
        background: linear-gradient(135deg, #1E88E5, #0D47A1); color: white;
        padding: 1.5rem; border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); text-align: center;
    }
    .stMetric {
        background-color: white; padding: 1rem; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .stSlider [data-baseweb="slider"] { margin-top: 0.5rem; }
    .stNumberInput [data-baseweb="input"] { border-radius: 8px; }
    .chart-container {
        background-color: white; border-radius: 10px; padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
"""


# --- Data Loading ---
@st.cache_data
def load_data(burden_file: str, labels_file: str) -> Tuple[pd.DataFrame, pd.Series]:
    """Loads financing burden and energy label data from pickle files."""
    try:
        burden_path = Path(burden_file)
        labels_path = Path(labels_file)

        if not burden_path.exists():
            st.error(f"Error: Financing burden file not found: {burden_file}")
            st.stop()
        if not labels_path.exists():
            st.error(f"Error: Energy labels file not found: {labels_file}")
            st.stop()

        financing_burden_df = pd.read_pickle(burden_path)
        energy_labels_series = pd.read_pickle(labels_path)
        return financing_burden_df, energy_labels_series
    except Exception as e:
        st.error(f"Error loading data files: {e}")
        st.stop()


# --- Streamlit App UI ---

st.set_page_config(layout="wide")
st.markdown(APP_STYLE, unsafe_allow_html=True)
st.markdown(
    '<p class="main-header">Maximum Mortgage Calculator</p>', unsafe_allow_html=True
)

st.markdown(
    """
    This calculator helps estimate the maximum mortgage amount you might be able to borrow
    based on your income, the current interest rate, the loan term, and potentially the
    energy label of the property. It also simulates the monthly payments over the
    lifetime of the mortgage, showing the breakdown between principal and interest,
    both gross and net of potential tax deductions.

    While the core principles of annuity mortgage calculations (principal and interest
    payments over time) are universal, the maximum amount you can borrow and the exact
    net costs can vary significantly in other countries due to different regulations,
    tax laws, and lending criteria. Use this calculator as an illustrative tool, but
    always consult with a local financial advisor for accurate advice specific to your
    region and circumstances.

    <strong>Important Note:</strong> The specific calculations, particularly the
    `financing burden' (woonquote) percentages and the impact of the energy label,
    are based on regulations and standards prevalent in the <strong>Dutch mortgage market
    (using 2025 data)</strong>. The mortgage interest tax deduction rate is also specific
    to the Dutch system.
    """,
    unsafe_allow_html=True,
)

# Load data once
financing_burden_2025, energy_labels = load_data(
    FINANCING_BURDEN_FILE, ENERGY_LABELS_FILE
)

st.markdown('<p class="sub-header">Input Parameters</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    income_1 = st.number_input(
        "Gross annual income 1 (€)",
        min_value=0.0,
        value=DEFAULT_INCOME_1,
        step=1000.0,
        key="income1",
    )
    interest_rate_pct = st.slider(
        "Mortgage interest rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_INTEREST_RATE_PCT,
        step=0.1,
        format="%.1f",
        key="interest_rate_slider",
    )
    energy_label_value = st.selectbox(
        "Energy label",
        options=energy_labels.index,
        index=DEFAULT_ENERGY_LABEL_INDEX,
        key="energy_label_select",
    )

with col2:
    income_2 = st.number_input(
        "Gross annual income 2 (€)",
        min_value=0.0,
        value=DEFAULT_INCOME_2,
        step=1000.0,
        key="income2",
    )
    term_years = st.slider(
        "Term (years)",
        min_value=1,
        max_value=50,
        value=DEFAULT_TERM_YEARS,
        key="term_slider",
    )
    st.number_input(
        "Tax deduction rate (%)",
        value=MORTGAGE_INTEREST_TAX_DEDUCTION_RATE * 100,
        disabled=True,
        format="%.2f",
        key="tax_rate_display",
    )

# --- Core Calculations ---
gross_income = income_1 + income_2
interest_rate = interest_rate_pct / 100.0

financing_burden_pct = mortgages_model.get_financing_burden_pct(
    gross_income, interest_rate, financing_burden_2025
)
# Ensure energy_label_value is valid before accessing .loc
if energy_label_value in energy_labels.index:
    energy_label_surplus = float(energy_labels.loc[energy_label_value])
else:
    st.warning(
        f"Selected energy label '{energy_label_value}' not found. Using 0 surplus."
    )
    energy_label_surplus = 0.0


maximum_mortgage, monthly_payment_base = mortgages_model.calculate_maximum_mortgage(
    gross_income,
    interest_rate,
    term_years,
    financing_burden_pct,
    energy_label_surplus,
)

# Calculate gross/net payments based *only* on the final maximum mortgage
(
    gross_monthly_payment,
    net_monthly_payment,
    first_month_interest,
    first_month_tax_deduction,
) = mortgages_model.calculate_monthly_payments(
    maximum_mortgage,
    interest_rate,
    term_years,
    MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
)

# Calculate the portion of the gross payment attributed to the energy surplus
additional_monthly_payment = 0.0
if energy_label_surplus > 0 and term_years > 0:
    if interest_rate > 0:
        annuity_factor_surplus = mortgages_model.calculate_annuity_factor(
            interest_rate, term_years
        )
        if annuity_factor_surplus:
            additional_monthly_payment = energy_label_surplus * annuity_factor_surplus
    else:
        additional_monthly_payment = energy_label_surplus / (term_years * 12)


# --- Results Section ---
st.markdown('<p class="sub-header">Results</p>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="mortgage-result">
    <h2 style="margin:0;">Maximum Mortgage (for {term_years} years)</h2>
    <h1 style="font-size:3.5rem; margin:0.5rem 0;">€{maximum_mortgage:,.0f}</h1>
    <p style="font-size:1.2rem; margin:0;">
        Est. Net Monthly Payment: €{net_monthly_payment:,.2f}
    </p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
col_res1, col_res2 = st.columns(2)
with col_res1:
    st.metric("Total gross income", f"€{gross_income:,.2f}")
    st.metric(
        "Est. Gross Monthly Payment",
        f"€{gross_monthly_payment:,.2f}",
        # delta=f"€{additional_monthly_payment:,.2f} from energy label",
        # delta_color="off",
    )

with col_res2:
    st.metric("Financing burden", f"{financing_burden_pct:.1%}")
    st.metric("Energy label surplus", f"€{energy_label_surplus:,.2f}")
st.markdown("</div>", unsafe_allow_html=True)


# --- Payment Simulation Section ---
st.markdown(
    '<p class="sub-header">Mortgage Payment Simulation</p>', unsafe_allow_html=True
)

if maximum_mortgage <= 0:
    st.warning("Cannot simulate payments for a zero or negative mortgage amount.")
elif term_years <= 0:
    st.warning("Please select a valid term (greater than 0) for simulation.")
elif interest_rate == 0:
    st.info(
        "For 0% interest rate, payments are constant principal repayments (€"
        f"{gross_monthly_payment:,.2f}/month) with no interest. Net and Gross payments"
        " are identical."
    )
    simulation_data = mortgages_model.run_payment_simulation(
        maximum_mortgage,
        interest_rate,
        term_years,
        MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
    )
    if simulation_data is not None:
        st.dataframe(
            simulation_data[
                ["Date", "Month", "Outstanding Principal", "Principal Payment"]
            ]
            .rename(columns={"Principal Payment": "Monthly Payment"})
            .style.format(
                {
                    "Outstanding Principal": "€{:,.2f}",
                    "Monthly Payment": "€{:,.2f}",
                    "Date": "{:%Y-%m}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

else:  # interest_rate > 0 and term_years > 0 and maximum_mortgage > 0
    simulation_data = mortgages_model.run_payment_simulation(
        maximum_mortgage,
        interest_rate,
        term_years,
        MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
    )

    if simulation_data is None:
        st.error("Failed to run payment simulation.")
    else:
        const_gross_payment = simulation_data["Gross Monthly Payment"].iloc[0]
        st.markdown(
            f"""
        The simulation below illustrates how your monthly payments are allocated over
        the {term_years}-year term. Your total gross monthly payment is consistently
        €{const_gross_payment:,.2f}. The chart breaks this down: the
        <span style='color:{COLOR_PRINCIPAL}; font-weight:bold;'>blue area</span>
        shows the principal repayment (increases over time), while the
        <span style='color:{COLOR_INTEREST_GROSS}; font-weight:bold;'>orange area</span>
        shows the interest payment (decreases over time). Select 'Net' view to see the
        impact of the estimated tax deduction.
        """,
            unsafe_allow_html=True,
        )

        payment_view = st.radio(
            "Select payment view for the chart:",
            ("Gross", "Net"),
            index=0,
            horizontal=True,
            key="payment_view_radio",
        )

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        if payment_view == "Gross":
            fig_sim = px.area(
                simulation_data,
                x="Date",
                y=["Principal Payment", "Interest Payment"],
                title="Monthly Payment Breakdown (Gross)",
                labels={"value": "Amount (€)", "variable": "Payment Type"},
                color_discrete_map={
                    "Principal Payment": COLOR_PRINCIPAL,
                    "Interest Payment": COLOR_INTEREST_GROSS,
                },
            )
            hover_template = (
                "<b>Date:</b> %{x|%Y-%m}<br>"
                "<b>%{data.name}:</b> €%{y:,.2f}<br>"
                f"<b>Total Gross:</b> €{const_gross_payment:,.2f}"
                "<extra></extra>"
            )
            fig_sim.update_traces(hovertemplate=hover_template)

        else:  # Net view
            fig_sim = px.area(
                simulation_data,
                x="Date",
                y=["Principal Payment", "Net Interest Payment"],
                title="Monthly Payment Breakdown (Net)",
                labels={"value": "Amount (€)", "variable": "Payment Type"},
                color_discrete_map={
                    "Principal Payment": COLOR_PRINCIPAL,
                    "Net Interest Payment": COLOR_INTEREST_NET,
                },
            )
            hover_template = (
                "<b>Date:</b> %{x|%Y-%m}<br>"
                "<b>%{data.name}:</b> €%{y:,.2f}<br>"
                "<b>Total Net:</b> €%{customdata:,.2f}<extra></extra>"
            )
            fig_sim.update_traces(
                customdata=simulation_data["Net Monthly Payment"],
                hovertemplate=hover_template,
            )

        fig_sim.update_xaxes(title_text="Date", tickformat="%Y-%m")
        fig_sim.update_yaxes(title_text="Amount (€)")
        fig_sim.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            font=dict(family="Arial, sans-serif"),
        )
        st.plotly_chart(
            fig_sim, use_container_width=True, config={"displayModeBar": False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Simulation Summary Metrics ---
        st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        total_interest = simulation_data["Interest Payment"].sum()
        total_net_paid = simulation_data["Net Monthly Payment"].sum()
        total_tax_benefit = (maximum_mortgage + total_interest) - total_net_paid

        with summary_col1:
            st.metric("Total Principal Paid", f"€{maximum_mortgage:,.2f}")
        with summary_col2:
            st.metric("Total Gross Interest Paid", f"€{total_interest:,.2f}")
        with summary_col3:
            st.metric(
                "Total Net Cost (Principal + Net Interest)",
                f"€{total_net_paid:,.2f}",
                delta=f"€{total_tax_benefit:,.2f} total tax benefit",
                delta_color="inverse",
            )
        st.markdown("</div>", unsafe_allow_html=True)

# --- User Input for Maximum Payment ---
st.markdown(
    '<p class="sub-header">Find Affordable Mortgage by Maximum Payment</p>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    This section helps you determine an affordable mortgage amount based on your desired
    maximum *monthly* payment, rather than solely on income limits. Enter your maximum
    affordable payment (either Gross or Net). This provides an alternative perspective on
    affordability, focusing on your monthly budget.
    """,
    unsafe_allow_html=True,
)
col_max1, col_max2 = st.columns(2)
with col_max1:
    max_payment_type = st.radio(
        "Maximum payment based on:",
        ("Net", "Gross"),
        index=0,
        key="max_payment_type_radio",
        horizontal=True,
    )
with col_max2:
    # Dynamically set default based on calculated payments
    default_max_payment = (
        net_monthly_payment if max_payment_type == "Net" else gross_monthly_payment
    )
    max_payment_input = st.number_input(
        f"Enter maximum {max_payment_type.lower()} monthly payment (€)",
        min_value=0.0,
        value=max(0.0, default_max_payment),  # Ensure non-negative default
        step=50.0,
        key="max_payment_input_num",
    )

# --- Affordability Calculation & Comparison Chart ---
if term_years <= 0:
    st.warning(
        "Please select a valid term (greater than 0) for the affordability analysis."
    )
else:
    affordable_mortgage: Optional[float] = None
    annuity_factor_comp = mortgages_model.calculate_annuity_factor(
        interest_rate, term_years
    )

    # Calculate affordable mortgage based on user input
    if max_payment_input > 0:
        if max_payment_type == "Gross":
            if interest_rate > 0:
                if annuity_factor_comp and annuity_factor_comp > 0:
                    affordable_mortgage = max_payment_input / annuity_factor_comp
            else:  # 0% interest
                affordable_mortgage = max_payment_input * term_years * 12

        elif max_payment_type == "Net":
            if interest_rate > 0:
                # Estimate based on first month's deduction: Net = Gross - Interest * TaxRate
                # Net = M*AF - (M*i * TaxRate) = M * (AF - i*TaxRate)
                # => M = Net / (AF - i*TaxRate)
                # Note: This is an approximation as tax deduction decreases over time.
                monthly_interest_comp = interest_rate / 12
                if annuity_factor_comp:
                    denominator = annuity_factor_comp - (
                        monthly_interest_comp * MORTGAGE_INTEREST_TAX_DEDUCTION_RATE
                    )
                    if denominator > 0:
                        affordable_mortgage = max_payment_input / denominator
            else:  # 0% interest, Net = Gross
                affordable_mortgage = max_payment_input * term_years * 12

    # Define the range of mortgage amounts to compare dynamically
    min_comp_mortgage = 50_000
    max_comp_mortgage = max(
        min_comp_mortgage * 2,
        (
            round(max(maximum_mortgage, affordable_mortgage or 0) * 1.5 / 50000) * 50000
            if affordable_mortgage or maximum_mortgage > 0
            else 1_000_000
        ),  # Default max if no other info
    )
    step_comp_mortgage = max(
        5000, round((max_comp_mortgage - min_comp_mortgage) / 20 / 5000) * 5000
    )  # Aim for ~20 points
    mortgage_amounts_to_compare = np.arange(
        min_comp_mortgage, max_comp_mortgage + step_comp_mortgage, step_comp_mortgage
    )

    # Calculate comparison data points
    comparison_data = []
    for mortgage_amount in mortgage_amounts_to_compare:
        gross_m_comp, net_m_comp, _, _ = mortgages_model.calculate_monthly_payments(
            mortgage_amount,
            interest_rate,
            term_years,
            MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
        )
        comparison_data.append(
            {
                "Mortgage Amount (€)": mortgage_amount,
                "Gross Monthly Payment (€)": gross_m_comp,
                "Net Monthly Payment (€)": net_m_comp,
            }
        )

    comparison_df = pd.DataFrame(comparison_data)

    # Add a graph for the comparison data
    st.markdown(
        '<div class="chart-container" style="margin-top: 1rem;">',
        unsafe_allow_html=True,
    )
    comparison_df_melted = comparison_df.melt(
        id_vars=["Mortgage Amount (€)"],
        value_vars=["Gross Monthly Payment (€)", "Net Monthly Payment (€)"],
        var_name="Payment Type",
        value_name="Monthly Payment (€)",
    )

    fig_comp_title = (
        f"Monthly Payments vs. Mortgage Amount "
        f"(Interest: {interest_rate_pct:.1f}%, Term: {term_years} years)"
    )
    fig_comp = px.line(
        comparison_df_melted,
        x="Mortgage Amount (€)",
        y="Monthly Payment (€)",
        color="Payment Type",
        title=fig_comp_title,
        markers=False,
        color_discrete_map={
            "Gross Monthly Payment (€)": COLOR_INTEREST_GROSS,
            "Net Monthly Payment (€)": COLOR_PRINCIPAL,
        },
    )

    # Add Horizontal Line for Max Payment
    if max_payment_input > 0:
        hline_annotation_text = (
            f"Max {max_payment_type} Payment: €{max_payment_input:,.2f}"
        )
        fig_comp.add_hline(
            y=max_payment_input,
            line_dash="dot",
            line_color=COLOR_MAX_PAYMENT_LINE,
            annotation_text=hline_annotation_text,
            annotation_position="bottom right",
            annotation_font_color=COLOR_MAX_PAYMENT_LINE,
        )

        # Add vertical line and annotation for affordable mortgage if calculated
        if affordable_mortgage is not None and affordable_mortgage > 0:
            vline_annotation_text = f"Affordable Mortgage: €{affordable_mortgage:,.0f}"
            # Ensure VLine is within the plotted x-range for visibility
            plot_affordable_mortgage = max(
                mortgage_amounts_to_compare.min(),
                min(mortgage_amounts_to_compare.max(), affordable_mortgage),
            )

            fig_comp.add_vline(
                x=plot_affordable_mortgage,
                line_dash="dot",
                line_color=COLOR_AFFORDABLE_MORTGAGE_LINE,
                annotation_text=vline_annotation_text,
                annotation_position="top left",
                annotation_font_color=COLOR_AFFORDABLE_MORTGAGE_LINE,
            )

            # Add intersection marker
            intersect_y = max_payment_input
            intersect_x = affordable_mortgage
            y_min_plot = comparison_df_melted["Monthly Payment (€)"].min()
            y_max_plot = comparison_df_melted["Monthly Payment (€)"].max()

            if (
                mortgage_amounts_to_compare.min()
                <= intersect_x
                <= mortgage_amounts_to_compare.max()
                and y_min_plot <= intersect_y <= y_max_plot
            ):
                fig_comp.add_trace(
                    go.Scatter(
                        x=[intersect_x],
                        y=[intersect_y],
                        mode="markers",
                        marker=dict(
                            color=COLOR_INTERSECTION_MARKER, size=10, symbol="x"
                        ),
                        name="Affordable Point",
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

    fig_comp.update_layout(
        xaxis_title="Mortgage Amount (€)",
        yaxis_title="Monthly Payment (€)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        font=dict(family="Arial, sans-serif"),
        xaxis_tickformat=",.0f",
        yaxis_tickformat=",.0f",
    )
    fig_comp_hovertemplate = (
        "<b>Mortgage:</b> €%{x:,.0f}<br>"
        "<b>%{fullData.name}:</b> €%{y:,.2f}<extra></extra>"
    )
    fig_comp.update_traces(hovertemplate=fig_comp_hovertemplate)

    st.plotly_chart(
        fig_comp, use_container_width=True, config={"displayModeBar": False}
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if max_payment_type == "Net" and interest_rate > 0:
        st.caption(
            "Note: The 'Affordable Mortgage' calculation based on Net payment is an "
            "estimate using the first month's tax deduction. The actual affordable "
            "amount might be slightly lower as the tax benefit decreases over time."
        )

# --- Fixed Interest Rate Period Comparison ---
st.markdown(
    '<p class="sub-header">Fixed Interest Rate Period Comparison</p>',
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    This section helps you compare different interest rates, which are typically
    associated with various fixed-rate periods (e.g., an interest rate for a 10-year
    fixed period, another for a 20-year fixed period).

    For your calculated maximum mortgage of **€{maximum_mortgage:,.0f}** over a
    total loan term of **{term_years} years** (as set in the main input parameters),
    you can input these different interest rates below.

    The table will then show the financial outcomes (monthly payments, total interest,
    principal repaid at key milestones, etc.) as if that specific interest rate
    were applied for the *entire* **{term_years}-year** loan duration. This allows for a
    side-by-side comparison of how different interest rate levels impact your mortgage.

    Please note that it is of course unrealistic to assume the same interest rate for the
    entire {term_years} year period and the therefore the most important aspect is to compare
    Principal Repaid at 5 and 10 years.
    """,
    unsafe_allow_html=True,
)

if maximum_mortgage <= 0:
    st.warning(
        "Cannot perform interest rate comparison for a zero or negative mortgage amount."
    )
elif term_years <= 0:
    st.warning(
        "Cannot perform interest rate comparison because the main loan term is not "
        "greater than zero. Please set a valid term in the main input parameters."
    )
else:
    # These are labels for different fixed-rate periods, for which users will input rates
    fixed_rate_periods_to_label_rates = [10, 15, 20, 30]
    # Default rate increments for initial display, user can change these
    default_rate_increments_pct = [0.0, 0.1, 0.2, 0.3]  # Relative to main interest rate

    st.markdown("**Enter Annual Interest Rates for Each Scenario:**")
    cols_rates = st.columns(len(fixed_rate_periods_to_label_rates))
    input_rates_pct = {}

    for i, fixed_period_label_yr in enumerate(fixed_rate_periods_to_label_rates):
        with cols_rates[i]:
            default_rate = round(interest_rate_pct + default_rate_increments_pct[i], 2)
            input_rates_pct[fixed_period_label_yr] = st.number_input(
                label=f"Rate for {fixed_period_label_yr}-Yr Fix (%)",
                min_value=0.0,
                max_value=20.0,
                value=default_rate,
                step=0.01,
                format="%.2f",
                key=f"rate_scenario_input_{fixed_period_label_yr}",
            )

    comparison_data_list = []

    for fixed_period_label_yr in fixed_rate_periods_to_label_rates:
        current_scenario_rate_pct = input_rates_pct[fixed_period_label_yr]
        current_scenario_rate_annual = current_scenario_rate_pct / 100.0

        # Calculate payments and simulation using the main `term_years` for loan duration
        (
            gross_monthly,
            net_monthly,
            _,
            _,
        ) = mortgages_model.calculate_monthly_payments(
            maximum_mortgage,
            current_scenario_rate_annual,  # The rate for this scenario
            term_years,  # Main loan term from page inputs
            MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
        )

        # Run simulation using the main `term_years` for loan duration
        simulation_df_scenario = mortgages_model.run_payment_simulation(
            maximum_mortgage,
            current_scenario_rate_annual,  # The rate for this scenario
            term_years,  # Main loan term from page inputs
            MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
        )

        total_gross_interest_paid = float("nan")
        total_net_cost = float("nan")
        total_gross_paid = float("nan")
        repaid_at_5_years = float("nan")
        repaid_at_10_years = float("nan")

        if simulation_df_scenario is not None and not simulation_df_scenario.empty:
            total_gross_interest_paid = simulation_df_scenario["Interest Payment"].sum()
            total_net_cost = simulation_df_scenario["Net Monthly Payment"].sum()
            if not np.isnan(total_gross_interest_paid):
                total_gross_paid = maximum_mortgage + total_gross_interest_paid

            # Principal Repaid at 5 Years (Month 60)
            # Check against the actual loan term (`term_years`)
            if term_years * 12 < 60:  # Actual loan term is less than 5 years
                repaid_at_5_years = maximum_mortgage  # Fully repaid
            else:  # Actual loan term is 5 years or more
                month_60_data = simulation_df_scenario[
                    simulation_df_scenario["Month"] == 60
                ]
                if not month_60_data.empty:
                    outstanding_at_5_years = month_60_data[
                        "Outstanding Principal"
                    ].iloc[0]
                    repaid_at_5_years = maximum_mortgage - outstanding_at_5_years
                elif term_years * 12 == 60:  # Loan term is exactly 5 years
                    outstanding_at_5_years = simulation_df_scenario[
                        "Outstanding Principal"
                    ].iloc[-1]
                    repaid_at_5_years = maximum_mortgage - outstanding_at_5_years

            # Principal Repaid at 10 Years (Month 120)
            # Check against the actual loan term (`term_years`)
            if term_years * 12 < 120:  # Actual loan term is less than 10 years
                repaid_at_10_years = maximum_mortgage  # Fully repaid
            else:  # Actual loan term is 10 years or more
                month_120_data = simulation_df_scenario[
                    simulation_df_scenario["Month"] == 120
                ]
                if not month_120_data.empty:
                    outstanding_at_10_years = month_120_data[
                        "Outstanding Principal"
                    ].iloc[0]
                    repaid_at_10_years = maximum_mortgage - outstanding_at_10_years
                elif term_years * 12 == 120:  # Loan term is exactly 10 years
                    outstanding_at_10_years = simulation_df_scenario[
                        "Outstanding Principal"
                    ].iloc[-1]
                    repaid_at_10_years = maximum_mortgage - outstanding_at_10_years
        else:
            st.error(
                f"Failed to run simulation for {term_years}-year loan "
                f"at {current_scenario_rate_pct:.2f}%. Principal: €{maximum_mortgage:,.0f}."
            )

        scenario_data_dict = {
            "Rate Scenario (Fixed Period)": f"{fixed_period_label_yr} Years Fix",  # Label for the rate
            "Gross Monthly Payment (€)": gross_monthly,
            "Net Monthly Payment (€)": net_monthly,
            "Principal Repaid at 5 Years (€)": repaid_at_5_years,
            "Principal Repaid at 10 Years (€)": repaid_at_10_years,
            "Total Principal Paid (€)": maximum_mortgage,  # Over the full term_years
            "Total Gross Interest Paid (€)": total_gross_interest_paid,  # Over term_years
            "Total Gross Paid (Principal + Gross Interest) (€)": total_gross_paid,  # Over term_years
            "Total Net Cost (Principal + Net Interest) (€)": total_net_cost,  # Over term_years
        }
        comparison_data_list.append(scenario_data_dict)

    if comparison_data_list:
        results_df = pd.DataFrame(comparison_data_list)

        # Format currency and percentage columns
        currency_columns = [col for col in results_df.columns if "(€)" in col]
        percentage_columns = [col for col in results_df.columns if "(%)" in col]

        for col_name in currency_columns:
            if col_name in results_df.columns:
                results_df[col_name] = results_df[col_name].round(2)
        for col_name in percentage_columns:
            if col_name in results_df.columns:
                results_df[col_name] = results_df[col_name].round(2)

        results_df = results_df.set_index("Rate Scenario (Fixed Period)")
        transposed_df = results_df.T  # Metrics as rows, scenarios as columns

        st.markdown(
            '<div class="chart-container" style="margin-top: 1rem;">',
            unsafe_allow_html=True,
        )

        # Define formatting for the transposed DataFrame
        format_dict_transposed = {}
        for (
            col_header_scenario_label
        ) in transposed_df.columns:  # Columns are "10 Years Fix", etc.
            # Each row (metric) needs specific formatting
            # Default to general number, then override for currency/percentage
            format_dict_transposed[col_header_scenario_label] = "{:,.2f}"  # Default

        # Apply specific formatting based on row index (metric name)
        # This requires iterating through the index of transposed_df
        final_formatters = {}
        for metric_name in transposed_df.columns:
            final_formatters[metric_name] = lambda x: (
                f"€{x:,.2f}" if pd.notnull(x) else "-"
            )

        st.dataframe(
            transposed_df.style.format(formatter=final_formatters, na_rep="-"),
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No interest rate scenario data to display.")

# --- Detailed Monthly Payment Schedule ---
st.markdown(
    '<p class="sub-header">Detailed Monthly Payment Schedule</p>',
    unsafe_allow_html=True,
)

if maximum_mortgage <= 0:
    st.info(
        "A detailed monthly payment schedule cannot be generated because the "
        "calculated maximum mortgage amount is zero or negative."
    )
elif term_years <= 0:
    st.warning(
        "A detailed monthly payment schedule cannot be generated because the "
        "loan term is not greater than zero. Please select a valid term."
    )
else:
    # Allow user to select/override interest rate for this specific schedule
    schedule_interest_rate_pct = st.number_input(
        "Annual interest rate for this schedule (%)",
        min_value=0.0,
        max_value=25.0,  # Reasonable upper limit
        value=interest_rate_pct,  # Default to the main interest rate
        step=0.01,
        format="%.2f",
        key="schedule_specific_interest_rate",
        help=(
            "Adjust this rate to see how the detailed monthly payments change. "
            "This will not affect other calculations on the page."
        ),
    )
    schedule_interest_rate_annual = schedule_interest_rate_pct / 100.0

    show_payment_percentages = st.checkbox(
        "Show Principal/Interest Percentages of Gross Payment",
        value=False,  # Default to not showing
        key="show_percentages_checkbox",
        help="If checked, the table will include columns showing the percentage of each gross monthly payment allocated to principal and interest.",
    )

    # Recalculate simulation data for this specific schedule and interest rate
    schedule_simulation_data = None
    if maximum_mortgage > 0 and term_years > 0:
        schedule_simulation_data = mortgages_model.run_payment_simulation(
            maximum_mortgage=maximum_mortgage,
            interest_rate=schedule_interest_rate_annual,
            term_years=term_years,
            tax_deduction_rate=MORTGAGE_INTEREST_TAX_DEDUCTION_RATE,
        )

    if schedule_simulation_data is not None and not schedule_simulation_data.empty:
        st.markdown(
            f"""
            Below is the detailed month-by-month breakdown for your primary mortgage of
            <b>€{maximum_mortgage:,.0f}</b> over <b>{term_years} years</b>
            at an annual interest rate of <b>{schedule_interest_rate_pct:.2f}%</b>.
            The table shows the principal repayment, gross interest, gross and net monthly payments,
            the tax deduction applied, and the outstanding mortgage balance after each payment.
            """,
            unsafe_allow_html=True,
        )

        # Define base columns and their new names
        base_columns_map = {
            "Date": "Payment Date",
            "Principal Payment": "Principal Repaid (€)",
            "Interest Payment": "Interest Paid (Gross) (€)",
            "Gross Monthly Payment": "Gross Monthly Payment (€)",
            "Tax Deduction": "Tax Deduction (€)",
            "Net Monthly Payment": "Net Monthly Payment (€)",
            "Outstanding Principal": "Remaining Mortgage Balance (€)",
        }
        schedule_df = schedule_simulation_data[list(base_columns_map.keys())].copy()
        schedule_df.rename(columns=base_columns_map, inplace=True)

        # Initialize formatters and columns to display
        formatters = {
            "Payment Date": "{:%Y-%m}",
            "Principal Repaid (€)": "€{:,.2f}",
            "Interest Paid (Gross) (€)": "€{:,.2f}",
            "Gross Monthly Payment (€)": "€{:,.2f}",
            "Tax Deduction (€)": "€{:,.2f}",
            "Net Monthly Payment (€)": "€{:,.2f}",
            "Remaining Mortgage Balance (€)": "€{:,.2f}",
        }
        columns_to_display = list(base_columns_map.values())

        if show_payment_percentages:
            gross_payment_col_name = "Gross Monthly Payment (€)"
            principal_repaid_col_name = "Principal Repaid (€)"
            interest_paid_col_name = "Interest Paid (Gross) (€)"

            # Calculate percentage columns, handling potential division by zero
            schedule_df["Principal % of Gross"] = np.where(
                schedule_df[gross_payment_col_name].ne(0)
                & pd.notna(schedule_df[gross_payment_col_name]),
                (
                    schedule_df[principal_repaid_col_name]
                    / schedule_df[gross_payment_col_name]
                )
                * 100,
                0.0,
            )
            schedule_df["Interest % of Gross"] = np.where(
                schedule_df[gross_payment_col_name].ne(0)
                & pd.notna(schedule_df[gross_payment_col_name]),
                (
                    schedule_df[interest_paid_col_name]
                    / schedule_df[gross_payment_col_name]
                )
                * 100,
                0.0,
            )

            # Add new percentage columns to the display list and formatters
            # Insert after "Gross Monthly Payment (€)"
            try:
                gross_payment_index = columns_to_display.index(gross_payment_col_name)
                columns_to_display.insert(
                    gross_payment_index + 1, "Interest % of Gross"
                )
                columns_to_display.insert(
                    gross_payment_index + 1, "Principal % of Gross"
                )
            except ValueError:  # Should not happen if base_columns_map is correct
                columns_to_display.extend(
                    ["Principal % of Gross", "Interest % of Gross"]
                )

            formatters["Principal % of Gross"] = "{:.2f}%"
            formatters["Interest % of Gross"] = "{:.2f}%"

        # Display the formatted DataFrame
        st.dataframe(
            schedule_df[columns_to_display].style.format(formatters, na_rep="-"),
            use_container_width=True,
            height=500,  # Set a fixed height for the table with a scrollbar
            hide_index=True,
        )
    elif maximum_mortgage > 0:
        st.warning(
            "The detailed monthly payment schedule could not be generated for the "
            f"selected interest rate of {schedule_interest_rate_pct:.2f}%. "
            "This might occur if the simulation did not produce valid results. "
            "Please check the main input parameters or the selected interest rate for this schedule."
        )
