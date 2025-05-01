from typing import Optional, Tuple

import numpy as np
import pandas as pd


def get_financing_burden_pct(
    gross_income: float, interest_rate: float, financing_burden_df: pd.DataFrame
) -> float:
    """Calculates the financing burden percentage based on income and interest rate."""
    # Find the correct interest rate bracket (column)
    interest_bracket = None
    for interval in financing_burden_df.columns:
        # Assuming columns are pd.Interval objects or tuples (left, right)
        if isinstance(interval, pd.Interval):
            if interval.left <= interest_rate <= interval.right:
                interest_bracket = interval
                break
        elif isinstance(interval, tuple) and len(interval) == 2:  # noqa
            left, right = interval
            if left <= interest_rate <= right:
                interest_bracket = interval
                break
    else:
        # Fallback to the last bracket if rate is outside defined ranges
        interest_bracket = financing_burden_df.columns[-1]

    # Find the nearest income level (row index)
    incomes = financing_burden_df.index
    nearest_income_idx = (np.abs(incomes - gross_income)).argmin()
    nearest_income = incomes[nearest_income_idx]

    # Get the financing burden percentage
    burden_pct = financing_burden_df.loc[nearest_income]
    burden_pct = burden_pct[interest_bracket]

    return float(burden_pct)  # Ensure return type is float


def calculate_maximum_mortgage(
    gross_income: float,
    interest_rate: float,
    term_years: int,
    financing_burden_pct: float,
    energy_label_surplus: float,
) -> Tuple[float, float]:
    """Calculates the maximum mortgage amount and the base monthly payment."""
    if term_years <= 0:
        return 0.0, 0.0

    annual_payment_base = financing_burden_pct * gross_income
    monthly_payment_base = annual_payment_base / 12
    months = term_years * 12

    if interest_rate > 0:
        monthly_interest = interest_rate / 12
        # Annuity factor calculation: P = A / [r / (1 - (1 + r)^-n)]
        try:
            annuity_factor = monthly_interest / (1 - (1 + monthly_interest) ** -months)
        except ZeroDivisionError:
            # Should not happen if months > 0 and monthly_interest > 0
            return 0.0, monthly_payment_base

        maximum_mortgage_base = (
            0.0 if not annuity_factor else monthly_payment_base / annuity_factor
        )
    else:
        # Simple calculation for 0% interest
        maximum_mortgage_base = monthly_payment_base * months

    maximum_mortgage = maximum_mortgage_base + energy_label_surplus
    return maximum_mortgage, monthly_payment_base


def calculate_annuity_factor(interest_rate: float, term_years: int) -> Optional[float]:
    """Calculates the annuity factor."""
    if term_years <= 0 or interest_rate < 0:
        return None
    if interest_rate == 0:
        return None  # Annuity factor not applicable for 0%

    monthly_interest = interest_rate / 12
    months = term_years * 12
    try:
        denominator = 1 - (1 + monthly_interest) ** -months
        if denominator == 0:
            return None  # Avoid division by zero
        return monthly_interest / denominator
    except OverflowError:
        # Handle potential overflow for very large terms/rates (unlikely)
        return None


def calculate_monthly_payments(
    maximum_mortgage: float,
    interest_rate: float,
    term_years: int,
    tax_deduction_rate: float,
) -> Tuple[float, float, float, float]:
    """Calculates gross/net monthly payments and first month's interest/deduction."""
    if term_years <= 0 or maximum_mortgage <= 0:
        return 0.0, 0.0, 0.0, 0.0

    total_months = term_years * 12

    if interest_rate > 0:
        annuity_factor = calculate_annuity_factor(interest_rate, term_years)
        if annuity_factor is None:
            return 0.0, 0.0, 0.0, 0.0

        gross_monthly_payment = maximum_mortgage * annuity_factor
        # Calculate the interest portion for tax deduction (using first month's interest)
        first_month_interest = maximum_mortgage * (interest_rate / 12)
        tax_deduction = first_month_interest * tax_deduction_rate
        net_monthly_payment = gross_monthly_payment - tax_deduction
    else:
        # Handle 0% interest rate case
        gross_monthly_payment = maximum_mortgage / total_months
        net_monthly_payment = gross_monthly_payment  # No interest, so no deduction
        first_month_interest = 0.0
        tax_deduction = 0.0

    return (
        gross_monthly_payment,
        net_monthly_payment,
        first_month_interest,
        tax_deduction,
    )


def run_payment_simulation(
    maximum_mortgage: float,
    interest_rate: float,
    term_years: int,
    tax_deduction_rate: float,
) -> Optional[pd.DataFrame]:
    """Runs the month-by-month payment simulation."""
    if term_years <= 0 or maximum_mortgage <= 0 or interest_rate < 0:
        return None

    total_months = term_years * 12
    monthly_interest_rate = interest_rate / 12

    # Calculate the constant gross monthly payment
    if interest_rate > 0:
        annuity_factor = calculate_annuity_factor(interest_rate, term_years)
        if annuity_factor is None:
            return None
        gross_payment = maximum_mortgage * annuity_factor
    else:
        gross_payment = maximum_mortgage / total_months

    # Initialize arrays
    outstanding_principal = np.zeros(total_months + 1)
    interest_payment = np.zeros(total_months)
    principal_payment = np.zeros(total_months)
    net_payment_sim = np.zeros(total_months)
    tax_deduction_sim = np.zeros(total_months)

    outstanding_principal[0] = maximum_mortgage

    # Simulation loop
    for i in range(total_months):
        current_interest = outstanding_principal[i] * monthly_interest_rate
        current_tax_deduction = current_interest * tax_deduction_rate

        # Ensure principal repayment doesn't exceed remaining balance or payment
        current_principal_paid = gross_payment - current_interest
        current_principal_paid = max(
            0, min(current_principal_paid, outstanding_principal[i])
        )

        # Adjust gross payment if principal was capped (e.g., near end of term)
        actual_gross_payment = current_principal_paid + current_interest
        current_net_payment = actual_gross_payment - current_tax_deduction

        interest_payment[i] = current_interest
        principal_payment[i] = current_principal_paid
        net_payment_sim[i] = current_net_payment
        tax_deduction_sim[i] = current_tax_deduction
        outstanding_principal[i + 1] = outstanding_principal[i] - current_principal_paid

    # Ensure the last balance is non-negative
    outstanding_principal[-1] = max(0, outstanding_principal[-1])

    # Create DataFrame
    start_date = pd.Timestamp.now().normalize().replace(day=1)
    date_index = pd.date_range(start=start_date, periods=total_months, freq="MS")
    months_array = np.arange(1, total_months + 1)

    simulation_data = pd.DataFrame(
        {
            "Date": date_index,
            "Month": months_array,
            "Outstanding Principal": outstanding_principal[1:],
            "Gross Monthly Payment": gross_payment,
            "Net Monthly Payment": net_payment_sim,
            "Interest Payment": interest_payment,
            "Principal Payment": principal_payment,
            "Tax Deduction": tax_deduction_sim,
            "Net Interest Payment": interest_payment - tax_deduction_sim,
        }
    )
    simulation_data["Cumulative Interest"] = simulation_data[
        "Interest Payment"
    ].cumsum()
    simulation_data["Cumulative Principal"] = simulation_data[
        "Principal Payment"
    ].cumsum()
    simulation_data["Total Paid (Net)"] = simulation_data[
        "Net Monthly Payment"
    ].cumsum()

    return simulation_data
