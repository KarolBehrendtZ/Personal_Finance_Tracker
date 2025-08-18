import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_URL = os.getenv('API_URL', 'http://localhost:8080/api/v1')

# Authentication state
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
            # Only show session expired error if user was logged in and it's not a login/register request
            if st.session_state.token and not endpoint.startswith('/auth/'):
                st.session_state.token = None
                st.session_state.user = None
                st.error("Session expired. Please log in again.")
            return None
        
        if response.status_code == 400:
            # Handle validation errors
            try:
                error_data = response.json()
                if 'error' in error_data:
                    # Don't show error here - let the calling function handle it
                    pass
            except:
                pass
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server. Please check if the API is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        # Only show generic error if it's not an auth endpoint
        if not endpoint.startswith('/auth/'):
            st.error(f"API Error: {e}")
        return None

def login_page():
    """Login/Register page"""
    st.title("🏦 Personal Finance Tracker")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields!")
                else:
                    data = {"email": email, "password": password}
                    response = make_api_request("/auth/login", "POST", data)
                    
                    if response:
                        st.session_state.token = response['token']
                        st.session_state.user = response['user']
                        st.success("Logged in successfully!")
                        # Clear any error messages and force refresh
                        if 'error_message' in st.session_state:
                            del st.session_state.error_message
                        # Use experimental_rerun if rerun doesn't work
                        try:
                            st.rerun()
                        except AttributeError:
                            st.experimental_rerun()
                    else:
                        st.error("❌ Invalid email or password. Please try again.")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if not all([first_name, last_name, email, password, confirm_password]):
                    st.error("Please fill in all fields!")
                elif password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long!")
                else:
                    data = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "password": password
                    }
                    response = make_api_request("/auth/register", "POST", data)
                    
                    if response:
                        st.session_state.token = response['token']
                        st.session_state.user = response['user']
                        st.success("Registered successfully!")
                        # Clear any error messages and force refresh
                        if 'error_message' in st.session_state:
                            del st.session_state.error_message
                        # Use experimental_rerun if rerun doesn't work
                        try:
                            st.rerun()
                        except AttributeError:
                            st.experimental_rerun()
                    else:
                        st.error("❌ Registration failed. Email might already be taken or there was a server error.")

def get_analytics_summary(start_date: str = None, end_date: str = None) -> Dict:
    """Get analytics summary from API"""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    endpoint = "/analytics/summary"
    if params:
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint += f"?{query_string}"
    
    return make_api_request(endpoint)

def get_spending_analytics(start_date: str = None, end_date: str = None) -> List[Dict]:
    """Get spending analytics from API"""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    
    endpoint = "/analytics/spending"
    if params:
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint += f"?{query_string}"
    
    result = make_api_request(endpoint)
    return result if result else []

def get_transactions_from_api(limit: int = 10) -> List[Dict]:
    """Get transactions from API"""
    endpoint = f"/transactions?limit={limit}"
    result = make_api_request(endpoint)
    return result if result else []

def dashboard_page():
    """Main dashboard page"""
    st.title("💰 Personal Finance Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.write(f"Welcome, {st.session_state.user['first_name']}!")
        
        if st.button("Logout"):
            # Clear all session state
            st.session_state.token = None
            st.session_state.user = None
            # Clear any cached data
            st.cache_data.clear()
            st.cache_resource.clear()
            # Force immediate rerun to show login page
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        
        st.divider()
        
        # Date range selector
        date_range = st.date_input(
            "Select Date Range",
            value=[datetime.now() - timedelta(days=30), datetime.now()],
            max_value=datetime.now()
        )
    
    user_id = st.session_state.user['id']
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if len(date_range) == 2:
        # Use API to get analytics summary
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
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Spending by Category")
        
        if len(date_range) == 2:
            # Use API to get spending analytics
            spending_data = get_spending_analytics(
                start_date=date_range[0].strftime('%Y-%m-%d'),
                end_date=date_range[1].strftime('%Y-%m-%d')
            )
            
            if spending_data:
                # Convert to DataFrame for plotting
                category_df = pd.DataFrame(spending_data)
                if not category_df.empty and 'amount' in category_df.columns:
                    # Filter out zero amounts
                    category_df = category_df[category_df['amount'] > 0]
                    if not category_df.empty:
                        fig = px.pie(category_df, values='amount', names='category_name',
                                   title="Spending by Category")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No expense data available for the selected period.")
                else:
                    st.info("No expense data available for the selected period.")
            else:
                st.info("No expense data available for the selected period.")
    
    with col2:
        st.subheader("Daily Spending Trend")
        st.info("Daily spending trend feature coming soon!")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    # Get recent transactions from API
    transactions_data = get_transactions_from_api(limit=10)
    
    if transactions_data:
        # Convert to DataFrame for display
        transactions_df = pd.DataFrame(transactions_data)
        
        if not transactions_df.empty:
            # Format the dataframe for display
            if 'amount' in transactions_df.columns:
                transactions_df['amount'] = transactions_df['amount'].apply(lambda x: f"${x:,.2f}")
            
            # Select and rename columns for display
            display_columns = {}
            if 'date' in transactions_df.columns:
                display_columns['date'] = 'Date'
            if 'description' in transactions_df.columns:
                display_columns['description'] = 'Description'
            if 'amount' in transactions_df.columns:
                display_columns['amount'] = 'Amount'
            if 'type' in transactions_df.columns:
                display_columns['type'] = 'Type'
            
            st.dataframe(
                transactions_df,
                column_config=display_columns,
                hide_index=True,
                use_container_width=True
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
