import pandas as pd
import psycopg2
import os
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransactionImporter:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database=os.getenv('DB_NAME', 'finance_tracker')
        )
    
    def import_csv(self, file_path: str, user_id: int, account_id: int) -> int:
        """Import transactions from CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            # Standardize column names (adjust based on your bank's CSV format)
            column_mapping = {
                'Date': 'date',
                'Description': 'description',
                'Amount': 'amount',
                'Type': 'type',
                'Category': 'category'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Data cleaning
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df = df.dropna(subset=['date', 'amount'])
            
            # Determine transaction type based on amount
            df['type'] = df['amount'].apply(lambda x: 'income' if x > 0 else 'expense')
            df['amount'] = df['amount'].abs()
            
            imported_count = 0
            cursor = self.conn.cursor()
            
            for _, row in df.iterrows():
                try:
                    # Get or create category
                    category_id = self._get_or_create_category(
                        cursor, user_id, row.get('category', 'Other'), row['type']
                    )
                    
                    # Insert transaction
                    cursor.execute("""
                        INSERT INTO transactions (user_id, account_id, category_id, amount, type, description, date, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """, (
                        user_id, account_id, category_id, row['amount'],
                        row['type'], row['description'], row['date']
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    logger.error(f"Error importing row: {e}")
                    continue
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Successfully imported {imported_count} transactions")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            self.conn.rollback()
            return 0
    
    def _get_or_create_category(self, cursor, user_id: int, category_name: str, category_type: str) -> int:
        """Get existing category or create new one"""
        cursor.execute(
            "SELECT id FROM categories WHERE user_id = %s AND name = %s AND type = %s",
            (user_id, category_name, category_type)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new category
        cursor.execute("""
            INSERT INTO categories (user_id, name, type, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW()) RETURNING id
        """, (user_id, category_name, category_type))
        
        return cursor.fetchone()[0]
    
    def auto_categorize_transactions(self, user_id: int) -> int:
        """Auto-categorize transactions based on description patterns"""
        categorization_rules = {
            'groceries': ['grocery', 'supermarket', 'food', 'market'],
            'gas': ['gas station', 'fuel', 'petrol'],
            'restaurant': ['restaurant', 'cafe', 'dining'],
            'utilities': ['electric', 'water', 'gas bill', 'internet'],
            'shopping': ['amazon', 'store', 'retail'],
            'transport': ['uber', 'taxi', 'bus', 'train'],
            'healthcare': ['pharmacy', 'doctor', 'hospital', 'medical']
        }
        
        cursor = self.conn.cursor()
        updated_count = 0
        
        try:
            # Get uncategorized transactions
            cursor.execute("""
                SELECT t.id, t.description, c.name as current_category
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.user_id = %s AND c.name = 'Other'
            """, (user_id,))
            
            transactions = cursor.fetchall()
            
            for trans_id, description, _ in transactions:
                description_lower = description.lower()
                
                for category, keywords in categorization_rules.items():
                    if any(keyword in description_lower for keyword in keywords):
                        # Get or create category
                        category_id = self._get_or_create_category(
                            cursor, user_id, category.title(), 'expense'
                        )
                        
                        # Update transaction
                        cursor.execute(
                            "UPDATE transactions SET category_id = %s, updated_at = NOW() WHERE id = %s",
                            (category_id, trans_id)
                        )
                        updated_count += 1
                        break
            
            self.conn.commit()
            logger.info(f"Auto-categorized {updated_count} transactions")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error auto-categorizing: {e}")
            self.conn.rollback()
            return 0
        finally:
            cursor.close()
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    importer = TransactionImporter()
    
    # Example usage
    importer.import_csv('bank_export.csv', user_id=1, account_id=1)
    importer.auto_categorize_transactions(user_id=1)
    
    importer.close()
