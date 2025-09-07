import pandas as pd
import psycopg2
import os
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpendingAnalyzer:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database=os.getenv('DB_NAME', 'finance_tracker')
        )
    
    def detect_unusual_spending(self, user_id: int, days: int = 30) -> List[Dict]:
        """Detect unusual spending patterns"""
        query = """
        WITH monthly_spending AS (
            SELECT 
                category_id,
                c.name as category_name,
                DATE_TRUNC('month', date) as month,
                SUM(amount) as monthly_amount
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s 
                AND t.type = 'expense'
                AND t.date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY category_id, c.name, DATE_TRUNC('month', date)
        ),
        category_stats AS (
            SELECT 
                category_id,
                category_name,
                AVG(monthly_amount) as avg_monthly,
                STDDEV(monthly_amount) as stddev_monthly,
                COUNT(*) as months_count
            FROM monthly_spending
            GROUP BY category_id, category_name
            HAVING COUNT(*) >= 2
        ),
        current_month AS (
            SELECT 
                category_id,
                SUM(amount) as current_amount
            FROM transactions
            WHERE user_id = %s 
                AND type = 'expense'
                AND date >= DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY category_id
        )
        SELECT 
            cs.category_name,
            cs.avg_monthly,
            cs.stddev_monthly,
            cm.current_amount,
            (cm.current_amount - cs.avg_monthly) / NULLIF(cs.stddev_monthly, 0) as z_score
        FROM category_stats cs
        JOIN current_month cm ON cs.category_id = cm.category_id
        WHERE cm.current_amount > cs.avg_monthly + (2 * cs.stddev_monthly)
        ORDER BY z_score DESC
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (user_id, days, user_id))
        results = cursor.fetchall()
        cursor.close()
        
        unusual_spending = []
        for row in results:
            unusual_spending.append({
                'category': row[0],
                'average_monthly': float(row[1]) if row[1] else 0,
                'current_monthly': float(row[3]) if row[3] else 0,
                'z_score': float(row[4]) if row[4] else 0,
                'excess_amount': float(row[3] - row[1]) if row[3] and row[1] else 0
            })
        
        return unusual_spending
    
    def analyze_spending_trends(self, user_id: int, months: int = 6) -> Dict:
        """Analyze spending trends over time"""
        query = """
        SELECT 
            DATE_TRUNC('month', date) as month,
            c.name as category,
            SUM(amount) as total_amount
        FROM transactions t
        JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = %s 
            AND t.type = 'expense'
            AND t.date >= CURRENT_DATE - INTERVAL '%s months'
        GROUP BY DATE_TRUNC('month', date), c.name
        ORDER BY month, category
        """
        
        df = pd.read_sql_query(query, self.conn, params=(user_id, months))
        
        if df.empty:
            return {'trends': {}, 'summary': {}}
        
        pivot_df = df.pivot(index='month', columns='category', values='total_amount').fillna(0)
        
        trends = {}
        for category in pivot_df.columns:
            series = pivot_df[category]
            if len(series) > 1:
                trend = np.polyfit(range(len(series)), series, 1)[0]
                trends[category] = {
                    'trend': float(trend),
                    'avg_monthly': float(series.mean()),
                    'total': float(series.sum()),
                    'variance': float(series.var())
                }
        
        total_by_month = pivot_df.sum(axis=1)
        overall_trend = np.polyfit(range(len(total_by_month)), total_by_month, 1)[0] if len(total_by_month) > 1 else 0
        
        summary = {
            'overall_trend': float(overall_trend),
            'avg_monthly_total': float(total_by_month.mean()),
            'months_analyzed': len(total_by_month)
        }
        
        return {'trends': trends, 'summary': summary}
    
    def budget_variance_analysis(self, user_id: int) -> List[Dict]:
        """Analyze variance between budget and actual spending"""
        query = """
        SELECT 
            c.name as category,
            br.amount as budget_amount,
            br.period,
            COALESCE(SUM(t.amount), 0) as actual_amount,
            br.start_date,
            br.end_date
        FROM budget_rules br
        JOIN categories c ON br.category_id = c.id
        LEFT JOIN transactions t ON br.category_id = t.category_id 
            AND t.user_id = br.user_id
            AND t.type = 'expense'
            AND t.date >= br.start_date
            AND (br.end_date IS NULL OR t.date <= br.end_date)
            AND (
                (br.period = 'monthly' AND t.date >= DATE_TRUNC('month', CURRENT_DATE)) OR
                (br.period = 'weekly' AND t.date >= DATE_TRUNC('week', CURRENT_DATE)) OR
                (br.period = 'yearly' AND t.date >= DATE_TRUNC('year', CURRENT_DATE))
            )
        WHERE br.user_id = %s
        GROUP BY c.name, br.amount, br.period, br.start_date, br.end_date
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        
        variances = []
        for row in results:
            budget_amount = float(row[1])
            actual_amount = float(row[3])
            variance = actual_amount - budget_amount
            variance_percent = (variance / budget_amount * 100) if budget_amount > 0 else 0
            
            variances.append({
                'category': row[0],
                'budget_amount': budget_amount,
                'actual_amount': actual_amount,
                'variance': variance,
                'variance_percent': variance_percent,
                'period': row[2],
                'status': 'over_budget' if variance > 0 else 'under_budget'
            })
        
        return variances
    
    def income_vs_expenses_analysis(self, user_id: int, months: int = 12) -> Dict:
        """Analyze income vs expenses trends"""
        query = """
        SELECT 
            DATE_TRUNC('month', date) as month,
            type,
            SUM(amount) as total_amount
        FROM transactions
        WHERE user_id = %s 
            AND date >= CURRENT_DATE - INTERVAL '%s months'
        GROUP BY DATE_TRUNC('month', date), type
        ORDER BY month
        """
        
        df = pd.read_sql_query(query, self.conn, params=(user_id, months))
        
        if df.empty:
            return {}
        
        pivot_df = df.pivot(index='month', columns='type', values='total_amount').fillna(0)
        
        if 'income' not in pivot_df.columns:
            pivot_df['income'] = 0
        if 'expense' not in pivot_df.columns:
            pivot_df['expense'] = 0
        
        pivot_df['net_income'] = pivot_df['income'] - pivot_df['expense']
        pivot_df['savings_rate'] = (pivot_df['net_income'] / pivot_df['income'] * 100).replace([np.inf, -np.inf], 0)
        
        return {
            'monthly_data': pivot_df.to_dict('records'),
            'summary': {
                'avg_monthly_income': float(pivot_df['income'].mean()),
                'avg_monthly_expenses': float(pivot_df['expense'].mean()),
                'avg_net_income': float(pivot_df['net_income'].mean()),
                'avg_savings_rate': float(pivot_df['savings_rate'].mean()),
                'total_income': float(pivot_df['income'].sum()),
                'total_expenses': float(pivot_df['expense'].sum())
            }
        }
    
    def generate_spending_report(self, user_id: int, output_file: str = None) -> Dict:
        """Generate comprehensive spending report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'user_id': user_id,
            'unusual_spending': self.detect_unusual_spending(user_id),
            'spending_trends': self.analyze_spending_trends(user_id),
            'budget_variance': self.budget_variance_analysis(user_id),
            'income_vs_expenses': self.income_vs_expenses_analysis(user_id)
        }
        
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {output_file}")
        
        return report
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    analyzer = SpendingAnalyzer()
    
    report = analyzer.generate_spending_report(user_id=1, output_file='spending_report.json')
    print("Unusual spending detected:", analyzer.detect_unusual_spending(user_id=1))
    
    analyzer.close()
