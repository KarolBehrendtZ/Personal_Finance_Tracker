import pandas as pd
import psycopg2
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database=os.getenv('DB_NAME', 'finance_db')
        )
        
        self.sample_users = [
            {"email": "john.doe@example.com", "first_name": "John", "last_name": "Doe", "password": "password123"},
            {"email": "jane.smith@example.com", "first_name": "Jane", "last_name": "Smith", "password": "password123"},
            {"email": "mike.johnson@example.com", "first_name": "Mike", "last_name": "Johnson", "password": "password123"},
        ]
        
        self.account_types = ["checking", "savings", "credit", "investment"]
        
        self.expense_categories = [
            {"name": "Groceries", "color": "#ff6b6b"},
            {"name": "Transportation", "color": "#4ecdc4"},
            {"name": "Entertainment", "color": "#45b7d1"},
            {"name": "Utilities", "color": "#f9ca24"},
            {"name": "Healthcare", "color": "#6c5ce7"},
            {"name": "Shopping", "color": "#a29bfe"},
            {"name": "Restaurants", "color": "#fd79a8"},
            {"name": "Gas", "color": "#fdcb6e"},
            {"name": "Insurance", "color": "#e17055"},
            {"name": "Other", "color": "#74b9ff"}
        ]
        
        self.income_categories = [
            {"name": "Salary", "color": "#00b894"},
            {"name": "Freelance", "color": "#00cec9"},
            {"name": "Investment", "color": "#55a3ff"},
            {"name": "Gift", "color": "#ff7675"},
            {"name": "Other Income", "color": "#81ecec"}
        ]
        
        self.transaction_templates = {
            "Groceries": [
                "Walmart Supercenter", "Target", "Costco", "Kroger", "Safeway",
                "Whole Foods Market", "Trader Joe's", "Aldi", "Food Lion"
            ],
            "Transportation": [
                "Uber", "Lyft", "Metro Transit", "Gas Station", "Parking Meter",
                "Car Repair Shop", "Auto Parts Store", "Public Transport"
            ],
            "Entertainment": [
                "Netflix", "Spotify", "Movie Theater", "Concert Venue",
                "Video Game Store", "Bookstore", "Museum", "Theme Park"
            ],
            "Utilities": [
                "Electric Company", "Water Department", "Gas Company",
                "Internet Provider", "Phone Company", "Trash Service"
            ],
            "Healthcare": [
                "Doctor Visit", "Pharmacy", "Dental Clinic", "Hospital",
                "Urgent Care", "Vision Center", "Medical Lab"
            ],
            "Shopping": [
                "Amazon", "Best Buy", "Home Depot", "Macy's", "Nike Store",
                "Apple Store", "Furniture Store", "Clothing Store"
            ],
            "Restaurants": [
                "McDonald's", "Starbucks", "Pizza Hut", "Local Restaurant",
                "Food Truck", "Cafe", "Fast Food", "Fine Dining"
            ],
            "Gas": [
                "Shell", "BP", "Exxon", "Chevron", "Mobil",
                "Marathon", "Sunoco", "Speedway"
            ],
            "Insurance": [
                "Car Insurance", "Health Insurance", "Home Insurance",
                "Life Insurance", "Dental Insurance"
            ],
            "Salary": [
                "Company Payroll", "Direct Deposit", "Salary Payment"
            ],
            "Freelance": [
                "Client Payment", "Project Completion", "Consulting Fee"
            ],
            "Investment": [
                "Dividend Payment", "Stock Sale", "Bond Interest", "Crypto Gain"
            ]
        }
    
    def generate_users(self) -> List[int]:
        """Generate sample users and return their IDs"""
        import bcrypt
        
        cursor = self.conn.cursor()
        user_ids = []
        
        for user_data in self.sample_users:
            try:
                password_bytes = user_data["password"].encode('utf-8')
                hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
                hashed_password = hashed.decode('utf-8')
                
                cursor.execute("""
                    INSERT INTO users (email, password_hash, first_name, last_name, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (email) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    user_data["email"],
                    hashed_password,
                    user_data["first_name"],
                    user_data["last_name"]
                ))
                
                user_id = cursor.fetchone()[0]
                user_ids.append(user_id)
                logger.info(f"Created/updated user: {user_data['email']} (ID: {user_id})")
                
            except Exception as e:
                logger.error(f"Error creating user {user_data['email']}: {e}")
        
        self.conn.commit()
        cursor.close()
        return user_ids
    
    def generate_accounts(self, user_ids: List[int]) -> List[int]:
        """Generate sample accounts for users"""
        cursor = self.conn.cursor()
        account_ids = []
        
        for user_id in user_ids:
            for i, account_type in enumerate(self.account_types):
                try:
                    balance = random.uniform(100, 50000) if account_type != "credit" else random.uniform(-5000, 0)
                    
                    cursor.execute("""
                        INSERT INTO accounts (user_id, name, type, balance, currency, description, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        RETURNING id
                    """, (
                        user_id,
                        f"{account_type.title()} Account {i+1}",
                        account_type,
                        round(balance, 2),
                        "USD",
                        f"Sample {account_type} account for testing"
                    ))
                    
                    account_id = cursor.fetchone()[0]
                    account_ids.append(account_id)
                    logger.info(f"Created account: {account_type} for user {user_id} (ID: {account_id})")
                    
                except Exception as e:
                    logger.error(f"Error creating account for user {user_id}: {e}")
        
        self.conn.commit()
        cursor.close()
        return account_ids
    
    def generate_categories(self, user_ids: List[int]) -> Dict[int, Dict[str, List[int]]]:
        """Generate sample categories for users"""
        cursor = self.conn.cursor()
        user_categories = {}
        
        for user_id in user_ids:
            user_categories[user_id] = {"expense": [], "income": []}
            
            for category_data in self.expense_categories:
                try:
                    cursor.execute("""
                        SELECT id FROM categories 
                        WHERE user_id = %s AND name = %s AND type = %s
                    """, (user_id, category_data["name"], "expense"))
                    
                    existing = cursor.fetchone()
                    if existing:
                        category_id = existing[0]
                        cursor.execute("""
                            UPDATE categories 
                            SET color = %s, icon = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (category_data["color"], category_data["icon"], category_id))
                    else:
                        cursor.execute("""
                            INSERT INTO categories (user_id, name, type, color, icon, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                        """, (
                            user_id,
                            category_data["name"],
                            "expense",
                            category_data["color"],
                            category_data["icon"]
                        ))
                        category_id = cursor.fetchone()[0]
                    
                    user_categories[user_id]["expense"].append(category_id)
                    
                except Exception as e:
                    logger.error(f"Error creating expense category for user {user_id}: {e}")
            
            for category_data in self.income_categories:
                try:
                    cursor.execute("""
                        SELECT id FROM categories 
                        WHERE user_id = %s AND name = %s AND type = %s
                    """, (user_id, category_data["name"], "income"))
                    
                    existing = cursor.fetchone()
                    if existing:
                        category_id = existing[0]
                        cursor.execute("""
                            UPDATE categories 
                            SET color = %s, icon = %s, updated_at = NOW()
                            WHERE id = %s
                        """, (category_data["color"], category_data["icon"], category_id))
                    else:
                        cursor.execute("""
                            INSERT INTO categories (user_id, name, type, color, icon, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                            RETURNING id
                        """, (
                            user_id,
                            category_data["name"],
                            "income",
                            category_data["color"],
                            category_data["icon"]
                        ))
                        category_id = cursor.fetchone()[0]
                    
                    user_categories[user_id]["income"].append(category_id)
                    
                except Exception as e:
                    logger.error(f"Error creating income category for user {user_id}: {e}")
        
        self.conn.commit()
        cursor.close()
        logger.info(f"Created categories for {len(user_ids)} users")
        return user_categories
    
    def generate_transactions(self, user_ids: List[int], account_ids: List[int], 
                            user_categories: Dict[int, Dict[str, List[int]]], 
                            num_transactions: int = 500) -> int:
        """Generate sample transactions"""
        cursor = self.conn.cursor()
        created_count = 0
        
        cursor.execute("SELECT id, user_id FROM accounts")
        account_user_map = {account_id: user_id for account_id, user_id in cursor.fetchall()}
        
        for _ in range(num_transactions):
            try:
                account_id = random.choice(account_ids)
                user_id = account_user_map[account_id]
                
                trans_type = "expense" if random.random() < 0.8 else "income"
                
                if user_categories[user_id][trans_type]:
                    category_id = random.choice(user_categories[user_id][trans_type])
                    
                    cursor.execute("SELECT name FROM categories WHERE id = %s", (category_id,))
                    category_name = cursor.fetchone()[0]
                    
                    if category_name in self.transaction_templates:
                        description = random.choice(self.transaction_templates[category_name])
                    else:
                        description = f"{category_name} Transaction"
                    
                    if trans_type == "expense":
                        amount = round(random.uniform(5, 500), 2)
                    else:
                        if category_name == "Salary":
                            amount = round(random.uniform(2000, 8000), 2)
                        else:
                            amount = round(random.uniform(50, 2000), 2)
                    
                    start_date = datetime.now() - timedelta(days=180)
                    random_days = random.randint(0, 180)
                    transaction_date = start_date + timedelta(days=random_days)
                    
                    cursor.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, type, description, date, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        user_id, account_id, category_id, amount, trans_type, 
                        description, transaction_date.date()
                    ))
                    
                    created_count += 1
                    
            except Exception as e:
                logger.error(f"Error creating transaction: {e}")
                continue
        
        self.conn.commit()
        cursor.close()
        logger.info(f"Created {created_count} sample transactions")
        return created_count
    
    def generate_budget_rules(self, user_ids: List[int], user_categories: Dict[int, Dict[str, List[int]]]) -> int:
        """Generate sample budget rules"""
        cursor = self.conn.cursor()
        created_count = 0
        
        budget_amounts = {
            "Groceries": 800,
            "Transportation": 300,
            "Entertainment": 200,
            "Utilities": 400,
            "Healthcare": 300,
            "Shopping": 500,
            "Restaurants": 400,
            "Gas": 200,
        }
        
        for user_id in user_ids:
            for category_id in user_categories[user_id]["expense"]:
                try:
                    cursor.execute("SELECT name FROM categories WHERE id = %s", (category_id,))
                    category_name = cursor.fetchone()[0]
                    
                    if category_name in budget_amounts:
                        amount = budget_amounts[category_name] * random.uniform(0.7, 1.3)
                        
                        cursor.execute("""
                            INSERT INTO budget_rules (user_id, category_id, amount, period, start_date, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        """, (
                            user_id, category_id, round(amount, 2), "monthly", 
                            datetime.now().replace(day=1).date()
                        ))
                        
                        created_count += 1
                        
                except Exception as e:
                    logger.error(f"Error creating budget rule: {e}")
                    continue
        
        self.conn.commit()
        cursor.close()
        logger.info(f"Created {created_count} budget rules")
        return created_count
    
    def generate_all_sample_data(self, num_transactions: int = 500):
        """Generate complete sample dataset"""
        logger.info("🚀 Starting sample data generation...")
        
        try:
            logger.info("📝 Creating sample users...")
            user_ids = self.generate_users()
            
            logger.info("🏦 Creating sample accounts...")
            account_ids = self.generate_accounts(user_ids)
            
            logger.info("📋 Creating sample categories...")
            user_categories = self.generate_categories(user_ids)
            
            logger.info("💰 Creating sample transactions...")
            transaction_count = self.generate_transactions(user_ids, account_ids, user_categories, num_transactions)
            
            logger.info("📊 Creating sample budget rules...")
            budget_count = self.generate_budget_rules(user_ids, user_categories)
            
            logger.info("✅ Sample data generation completed!")
            logger.info(f"Created: {len(user_ids)} users, {len(account_ids)} accounts, {transaction_count} transactions, {budget_count} budget rules")
            
            return {
                "users": len(user_ids),
                "accounts": len(account_ids),
                "transactions": transaction_count,
                "budget_rules": budget_count
            }
            
        except Exception as e:
            logger.error(f"Error during sample data generation: {e}")
            self.conn.rollback()
            return None
    
    def clear_all_data(self):
        """Clear all data from database (use with caution!)"""
        cursor = self.conn.cursor()
        
        tables = ["budget_rules", "transactions", "categories", "accounts", "users"]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            logger.info(f"Cleared table: {table}")
        
        self.conn.commit()
        cursor.close()
        logger.info("🗑️ All data cleared from database")
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    generator = SampleDataGenerator()
    
    
    result = generator.generate_all_sample_data(num_transactions=1000)
    
    if result:
        print(f"\n✅ Sample data generation completed!")
        print(f"📊 Generated: {result['users']} users, {result['accounts']} accounts, {result['transactions']} transactions, {result['budget_rules']} budget rules")
        print(f"\n👥 Sample users created:")
        print(f"  - john.doe@example.com (password: password123)")
        print(f"  - jane.smith@example.com (password: password123)")
        print(f"  - mike.johnson@example.com (password: password123)")
        print(f"\n🌐 You can now log in to the dashboard at: http://localhost:8501")
    else:
        print("❌ Sample data generation failed!")
    
    generator.close()
