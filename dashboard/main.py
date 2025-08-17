import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime, timedelta
import psycopg2
from typing import Dict, List

# Page configuration
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        database=os.getenv('DB_NAME', 'finance_tracker')
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

def get_data_from_db(query: str, params: tuple = None) -> pd.DataFrame:
    """Execute SQL query and return DataFrame"""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

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
    
    # Get summary data
    summary_query = """
    SELECT 
        SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as total_income,
        SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as total_expenses,
        COUNT(*) as total_transactions
    FROM transactions 
    WHERE user_id = %s AND date >= %s AND date <= %s
    """
    
    if len(date_range) == 2:
        summary_df = get_data_from_db(summary_query, (user_id, date_range[0], date_range[1]))
        
        if not summary_df.empty:
            total_income = summary_df.iloc[0]['total_income'] or 0
            total_expenses = summary_df.iloc[0]['total_expenses'] or 0
            net_income = total_income - total_expenses
            total_transactions = summary_df.iloc[0]['total_transactions'] or 0
            
            col1.metric("Total Income", f"${total_income:,.2f}")
            col2.metric("Total Expenses", f"${total_expenses:,.2f}")
            col3.metric("Net Income", f"${net_income:,.2f}", delta=f"{net_income:,.2f}")
            col4.metric("Transactions", f"{total_transactions}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Spending by Category")
        
        category_query = """
        SELECT c.name, SUM(t.amount) as total
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = %s AND t.type = 'expense' 
        AND t.date >= %s AND t.date <= %s
        GROUP BY c.name
        ORDER BY total DESC
        """
        
        if len(date_range) == 2:
            category_df = get_data_from_db(category_query, (user_id, date_range[0], date_range[1]))
            
            if not category_df.empty:
                fig = px.pie(category_df, values='total', names='name')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data available for the selected period.")
    
    with col2:
        st.subheader("Daily Spending Trend")
        
        daily_query = """
        SELECT date, SUM(amount) as daily_total
        FROM transactions
        WHERE user_id = %s AND type = 'expense'
        AND date >= %s AND date <= %s
        GROUP BY date
        ORDER BY date
        """
        
        if len(date_range) == 2:
            daily_df = get_data_from_db(daily_query, (user_id, date_range[0], date_range[1]))
            
            if not daily_df.empty:
                fig = px.line(daily_df, x='date', y='daily_total')
                fig.update_layout(xaxis_title="Date", yaxis_title="Amount ($)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No spending data available for the selected period.")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    transactions_query = """
    SELECT t.date, t.description, t.amount, t.type, c.name as category
    FROM transactions t
    JOIN categories c ON t.category_id = c.id
    WHERE t.user_id = %s
    ORDER BY t.date DESC, t.created_at DESC
    LIMIT 10
    """
    
    transactions_df = get_data_from_db(transactions_query, (user_id,))
    
    if not transactions_df.empty:
        # Format the dataframe for display
        transactions_df['amount'] = transactions_df['amount'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(
            transactions_df,
            column_config={
                "date": "Date",
                "description": "Description",
                "amount": "Amount",
                "type": "Type",
                "category": "Category"
            },
            hide_index=True,
            use_container_width=True
        )
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
