import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List
from constants import TrendDirections, TREND_INDICATORS

try:
    from constants import validate_trend_constants
except ImportError:
    st.error("Failed to import trend direction validation")
except ValueError as e:
    st.error(f"Trend direction constants validation failed: {e}")
    st.stop()

st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv('API_URL', 'http://localhost:8080/api/v1')

if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None

def make_api_request(endpoint: str, method: str = 'GET', data: Dict = None):
    """Make authenticated API request"""
    headers = {}
    if st.session_state.token:
        headers['Authorization'] = f'Bearer {st.session_state.token}'
    
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        if response.status_code == 401:
            if st.session_state.token and not endpoint.startswith('/auth/'):
                st.session_state.token = None
                st.session_state.user = None
                st.error("Session expired. Please log in again.")
                return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def login_page():
    """Login/Register page"""
    st.title("💰 Personal Finance Tracker")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if email and password:
                    response = make_api_request('/auth/login', 'POST', {
                        'email': email,
                        'password': password
                    })
                    
                    if response and 'token' in response:
                        st.session_state.token = response['token']
                        st.session_state.user = response['user']
                        st.success("Login successful!")
                        try:
                            st.rerun()
                        except AttributeError:
                            st.experimental_rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Register")
        
        with st.form("register_form"):
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            submit = st.form_submit_button("Register")
            
            if submit:
                if email and password and first_name and last_name:
                    response = make_api_request('/auth/register', 'POST', {
                        'email': email,
                        'password': password,
                        'first_name': first_name,
                        'last_name': last_name
                    })
                    
                    if response and 'token' in response:
                        st.session_state.token = response['token']
                        st.session_state.user = response['user']
                        st.success("Registration successful!")
                        try:
                            st.rerun()
                        except AttributeError:
                            st.experimental_rerun()
                    else:
                        st.error("Registration failed")
                else:
                    st.error("Please fill in all fields")

def get_analytics_summary(start_date: str, end_date: str):
    """Get analytics summary from API"""
    endpoint = f"/analytics/summary?start_date={start_date}&end_date={end_date}"
    return make_api_request(endpoint)

def get_spending_analytics(start_date: str, end_date: str):
    """Get spending analytics from API"""
    endpoint = f"/analytics/spending?start_date={start_date}&end_date={end_date}"
    return make_api_request(endpoint)

def get_spending_trends(period: str, date: str):
    """Get spending trends from API"""
    endpoint = f"/analytics/trends?period={period}&date={date}"
    return make_api_request(endpoint)

def get_transactions_from_api(start_date: str = None, end_date: str = None, limit: int = 100):
    """Get transactions from API"""
    params = []
    if start_date:
        params.append(f"start_date={start_date}")
    if end_date:
        params.append(f"end_date={end_date}")
    if limit:
        params.append(f"limit={limit}")
    
    query_string = "&".join(params)
    endpoint = f"/transactions?{query_string}" if query_string else "/transactions"
    return make_api_request(endpoint)

def dashboard_page():
    """Main dashboard page"""
    st.title("💰 Personal Finance Dashboard")
    
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.user['first_name']}!")
        
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.user = None
            st.cache_data.clear()
            st.cache_resource.clear()
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        
        st.divider()
        
        date_range = st.date_input(
            "Select Date Range",
            value=[datetime.now() - timedelta(days=30), datetime.now()],
            max_value=datetime.now()
        )
    
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Spending Trends", "💳 Transactions"])
    
    with tab1:
        show_overview_tab(date_range)
    
    with tab2:
        show_spending_trends_tab()
        
    with tab3:
        show_transactions_tab(date_range)

def show_overview_tab(date_range):
    """Show overview dashboard"""
    col1, col2, col3, col4 = st.columns(4)
    
    if len(date_range) == 2:
        summary_data = get_analytics_summary(
            start_date=date_range[0].strftime('%Y-%m-%d'),
            end_date=date_range[1].strftime('%Y-%m-%d')
        )
        
        if summary_data:
            total_income = summary_data.get('total_income', 0)
            total_expenses = summary_data.get('total_expenses', 0)
            net_income = summary_data.get('net_income', 0)
            account_balance = summary_data.get('account_balance', 0)
            
            col1.metric("Total Income", f"${total_income:,.2f}")
            col2.metric("Total Expenses", f"${total_expenses:,.2f}")
            col3.metric("Net Income", f"${net_income:,.2f}", delta=f"{net_income:,.2f}")
            col4.metric("Account Balance", f"${account_balance:,.2f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Spending by Category")
        
        if len(date_range) == 2:
            spending_data = get_spending_analytics(
                start_date=date_range[0].strftime('%Y-%m-%d'),
                end_date=date_range[1].strftime('%Y-%m-%d')
            )
            
            if spending_data and len(spending_data) > 0:
                df_spending = pd.DataFrame(spending_data)
                
                fig = px.pie(
                    df_spending, 
                    values='amount', 
                    names='category_name',
                    title="Spending Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending data available for the selected period.")
        else:
            st.info("Please select a date range.")
    
    with col2:
        st.subheader("Expense Trends")
        
        if len(date_range) == 2:
            spending_data = get_spending_analytics(
                start_date=date_range[0].strftime('%Y-%m-%d'),
                end_date=date_range[1].strftime('%Y-%m-%d')
            )
            
            if spending_data and len(spending_data) > 0:
                df_spending = pd.DataFrame(spending_data)
                
                fig = px.bar(
                    df_spending, 
                    x='category_name', 
                    y='amount',
                    title="Spending by Category"
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending data available for the selected period.")
        else:
            st.info("Please select a date range.")

def show_spending_trends_tab():
    """Show spending trends with predictions"""
    st.subheader("📈 Daily Spending Trends & Predictions")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        period = st.selectbox(
            "Time Period",
            options=["day", "week", "month"],
            index=1,
            format_func=lambda x: x.title()
        )
    
    with col2:
        if period == "day":
            selected_date = st.date_input("Select Day", value=datetime.now().date())
            date_str = selected_date.strftime('%Y-%m-%d')
        elif period == "week":
            selected_date = st.date_input("Select Week (any day in the week)", value=datetime.now().date())
            date_str = selected_date.strftime('%Y-%m-%d')
        else:
            col_month, col_year = st.columns(2)
            with col_month:
                month = st.selectbox("Month", range(1, 13), index=datetime.now().month - 1,
                                   format_func=lambda x: datetime(2024, x, 1).strftime('%B'))
            with col_year:
                year = st.selectbox("Year", range(2020, 2030), index=datetime.now().year - 2020)
            date_str = f"{year}-{month:02d}-01"
    
    trends_data = get_spending_trends(period, date_str)
    
    if trends_data and 'trends' in trends_data:
        trends = trends_data['trends']
        
        if trends:
            df = pd.DataFrame(trends)
            
            st.info(f"Showing trends for {period} of {trends_data['date']}")
            
            st.subheader("Spending Trends Table")
            
            display_df = df.copy()
            display_df['current_spend'] = display_df['current_spend'].apply(lambda x: f"${x:,.2f}")
            display_df['predicted_spend'] = display_df['predicted_spend'].apply(lambda x: f"${x:,.2f}")
            display_df['change_percent'] = display_df['change_percent'].apply(lambda x: f"{x:+.1f}%")
            
            display_df['trend'] = display_df['trend_direction'].map(TREND_INDICATORS)
            
            display_df = display_df[['category_name', 'current_spend', 'predicted_spend', 'change_percent', 'trend']]
            display_df.columns = ['Category', f'Current {period.title()}', f'Predicted Next {period.title()}', 'Change %', 'Trend']
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Current vs Predicted Spending")
                
                chart_df = df[['category_name', 'current_spend', 'predicted_spend']].head(10)
                
                fig = go.Figure(data=[
                    go.Bar(name=f'Current {period.title()}', x=chart_df['category_name'], y=chart_df['current_spend']),
                    go.Bar(name=f'Predicted Next {period.title()}', x=chart_df['category_name'], y=chart_df['predicted_spend'])
                ])
                
                fig.update_layout(
                    barmode='group',
                    title=f"Spending Comparison - Top 10 Categories",
                    xaxis_tickangle=-45
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Trend Direction Distribution")
                
                trend_counts = df['trend_direction'].value_counts()
                
                fig = px.pie(
                    values=trend_counts.values,
                    names=trend_counts.index,
                    title="Distribution of Spending Trends"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("💡 Insights")
            
            total_current = df['current_spend'].sum()
            total_predicted = df['predicted_spend'].sum()
            change = ((total_predicted - total_current) / total_current * 100) if total_current > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    f"Total Current {period.title()}", 
                    f"${total_current:,.2f}"
                )
            
            with col2:
                st.metric(
                    f"Predicted Next {period.title()}", 
                    f"${total_predicted:,.2f}",
                    delta=f"{change:+.1f}%"
                )
                
            with col3:
                trending_up = len(df[df['trend_direction'] == TrendDirections.UP])
                trending_down = len(df[df['trend_direction'] == TrendDirections.DOWN])
                
                if trending_up > trending_down:
                    trend_summary = "📈 Mostly Increasing"
                elif trending_down > trending_up:
                    trend_summary = "📉 Mostly Decreasing"
                else:
                    trend_summary = "➡️ Mixed Trends"
                
                st.metric("Overall Trend", trend_summary)
            
            if not df.empty:
                biggest_increase = df.loc[df['change_percent'].idxmax()]
                biggest_decrease = df.loc[df['change_percent'].idxmin()]
                
                st.markdown("### 📊 Key Insights")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if biggest_increase['change_percent'] > 0:
                        st.success(f"📈 **Biggest Increase**: {biggest_increase['category_name']} (+{biggest_increase['change_percent']:.1f}%)")
                    
                with col2:
                    if biggest_decrease['change_percent'] < 0:
                        st.error(f"📉 **Biggest Decrease**: {biggest_decrease['category_name']} ({biggest_decrease['change_percent']:.1f}%)")
        
        else:
            st.info("No spending trends data available for the selected period.")
    else:
        st.error("Failed to load spending trends data.")

def show_transactions_tab(date_range):
    """Show transactions list"""
    st.subheader("💳 Recent Transactions")
    
    if len(date_range) == 2:
        transactions = get_transactions_from_api(
            start_date=date_range[0].strftime('%Y-%m-%d'),
            end_date=date_range[1].strftime('%Y-%m-%d')
        )
        
        if transactions and len(transactions) > 0:
            df_transactions = pd.DataFrame(transactions)
            
            df_transactions['amount'] = df_transactions['amount'].apply(lambda x: f"${x:.2f}")
            df_transactions['date'] = pd.to_datetime(df_transactions['date']).dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                df_transactions[['date', 'description', 'amount', 'type']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No transactions found.")
    else:
        st.info("No transactions found.")

def main():
    """Main application"""
    if st.session_state.token is None:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
