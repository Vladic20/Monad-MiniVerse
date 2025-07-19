import sqlite3
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import config

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                balance_usd REAL DEFAULT 1000.0,
                balance_eur REAL DEFAULT 0.0,
                balance_rub REAL DEFAULT 0.0,
                balance_btc REAL DEFAULT 0.0,
                balance_eth REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                from_currency TEXT,
                to_currency TEXT,
                amount REAL,
                rate REAL,
                fee REAL,
                total_amount REAL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_type TEXT, -- 'buy' or 'sell'
                currency_pair TEXT,
                amount REAL,
                price REAL,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Exchange rates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_currency TEXT,
                to_currency TEXT,
                rate REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, 
                   balance_usd, balance_eur, balance_rub, balance_btc, balance_eth,
                   created_at, is_active
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'balance_usd': row[4],
                'balance_eur': row[5],
                'balance_rub': row[6],
                'balance_btc': row[7],
                'balance_eth': row[8],
                'created_at': row[9],
                'is_active': bool(row[10])
            }
        return None
    
    def create_user(self, user_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> bool:
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def update_balance(self, user_id: int, currency: str, amount: float) -> bool:
        """Update user balance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            balance_column = f"balance_{currency.lower()}"
            cursor.execute(f'''
                UPDATE users SET {balance_column} = {balance_column} + ?
                WHERE user_id = ?
            ''', (amount, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False
    
    def create_transaction(self, user_id: int, from_currency: str, to_currency: str,
                          amount: float, rate: float, fee: float, total_amount: float) -> bool:
        """Create transaction record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions (user_id, from_currency, to_currency, 
                                        amount, rate, fee, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, from_currency, to_currency, amount, rate, fee, total_amount))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return False
    
    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user transaction history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, from_currency, to_currency, amount, rate, fee, total_amount,
                   status, created_at
            FROM transactions 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'from_currency': row[1],
            'to_currency': row[2],
            'amount': row[3],
            'rate': row[4],
            'fee': row[5],
            'total_amount': row[6],
            'status': row[7],
            'created_at': row[8]
        } for row in rows]
    
    def update_exchange_rate(self, from_currency: str, to_currency: str, rate: float):
        """Update exchange rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO exchange_rates (from_currency, to_currency, rate, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (from_currency, to_currency, rate))
        
        conn.commit()
        conn.close()
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get current exchange rate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT rate FROM exchange_rates 
            WHERE from_currency = ? AND to_currency = ?
            ORDER BY updated_at DESC LIMIT 1
        ''', (from_currency, to_currency))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None