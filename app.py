import locale
import json
from datetime import datetime, timedelta
import numpy_financial as npf
import pandas as pd
import streamlit as st

# Set locale to handle formatting as currency
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def format_as_currency(amount):
    return locale.currency(amount, grouping=True)

# File path for saving/loading data
file_path = "debt_data.json"


def load_data():
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return pd.DataFrame(data)
    except FileNotFoundError:
        return pd.DataFrame(
            columns=["Name", "Type", "Amount", "APR", "Minimum Payment"]
        )


def save_data(df):
    with open(file_path, "w") as file:
        json.dump(df.to_dict(orient="records"), file)


def get_user_input():
    st.sidebar.header("Debt Input")
    name = st.sidebar.text_input("Debt Name")
    debt_type = st.sidebar.selectbox(
        "Type of Debt", ["Credit Card", "Car Loan", "Loan"]
    )
    amount = st.sidebar.number_input("Amount Owed", value=0.0)
    apr = st.sidebar.number_input("APR (%)", value=0.0)
    min_payment = st.sidebar.number_input("Minimum Monthly Payment", value=0.0)
    return name, debt_type, amount, apr, min_payment

def calculate_payoff_date_and_payments(amount, apr, min_payment, current_date):
    monthly_rate = apr / 12 / 100
    num_payments = npf.nper(monthly_rate, -min_payment, amount)
    payoff_date = current_date + timedelta(days=int(num_payments * 30))  # Assuming 30 days in a month
    return payoff_date, round(float(num_payments))

def calculate_total_interest_and_payments(amount, apr, min_payment):
    monthly_rate = apr / 12 / 100
    num_payments = npf.nper(monthly_rate, -min_payment, amount)
    total_paid = num_payments * min_payment
    total_interest = total_paid - amount
    return total_interest, round(float(num_payments))

def main():
    st.title("Debt Management App")

    user_df = load_data()

    name, debt_type, amount, apr, min_payment = get_user_input()

    if st.sidebar.button('Add Debt'):
        new_data = pd.DataFrame({
            'Name': [name],
            'Type': [debt_type],
            'Amount': [amount],
            'APR': [apr],
            'Minimum Payment': [min_payment]
        })
        user_df = pd.concat([user_df, new_data], ignore_index=True)
        save_data(user_df)


    # Calculate payoff date, total interest, and number of payments for all debts
    user_df[['Payoff Date', 'Payments']] = user_df.apply(
        lambda row: calculate_payoff_date_and_payments(row['Amount'], row['APR'], row['Minimum Payment'], datetime.today()), 
        axis=1, result_type='expand'
    )
    user_df[['Total Interest', 'Payments']] = user_df.apply(
        lambda row: calculate_total_interest_and_payments(row['Amount'], row['APR'], row['Minimum Payment']), 
        axis=1, result_type='expand'
    )

    # Calculate and display total debt and overall payoff date
    total_debt = user_df["Amount"].sum()
    overall_payoff_date = user_df["Payoff Date"].max().strftime("%Y-%m-%d")
    total_debt_payments_per_month = user_df['Minimum Payment'].sum()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Debt", format_as_currency(total_debt))
    with col2:
        st.metric("Overall Payoff Date:", overall_payoff_date)    
    with col3:
        st.metric('Monthly Debt Payments',format_as_currency(total_debt_payments_per_month))


    # Create and display prioritized payoff list
    prioritized_df = user_df.sort_values(by="Total Interest", ascending=False)
    st.markdown("## Prioritized Payoff List:")
    st.table(prioritized_df)

    # Add delete buttons for each debt
    for index, row in user_df.iterrows():
        if st.button(f'Delete {row["Name"]}', key=f'btn_{row["Name"]}'):
            user_df = user_df.drop(index)
            save_data(user_df)

if __name__ == "__main__":
    main()
