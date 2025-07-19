import sqlite3
import asyncio
from datetime import datetime, timedelta
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
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                account_id TEXT UNIQUE NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Wallets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                network TEXT NOT NULL,
                address TEXT NOT NULL,
                private_key TEXT NOT NULL,
                seed_phrase TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, network, address)
            )
        ''')
        
        # Withdrawal logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                from_address TEXT,
                to_address TEXT,
                amount REAL,
                token_type TEXT,
                network TEXT,
                status TEXT DEFAULT 'pending',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tx_hash TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Staking logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staking_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                wallet_address TEXT,
                amount REAL,
                asset TEXT,
                rate REAL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                accrued_reward REAL DEFAULT 0.0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, telegram_id, account_id, creation_date
            FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'telegram_id': row[1],
                'account_id': row[2],
                'creation_date': row[3]
            }
        return None
    
    def create_user(self, telegram_id: int) -> Optional[Dict]:
        """Create new user with random account_id"""
        import random
        
        # Generate 9-digit account_id
        account_id = str(random.randint(100000000, 999999999))
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (telegram_id, account_id)
                VALUES (?, ?)
            ''', (telegram_id, account_id))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'user_id': user_id,
                'telegram_id': telegram_id,
                'account_id': account_id,
                'creation_date': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def get_user_wallets(self, user_id: int) -> List[Dict]:
        """Get all wallets for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, network, address, created_at
            FROM wallets WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'network': row[1],
            'address': row[2],
            'created_at': row[3]
        } for row in rows]
    
    def get_wallet_by_address(self, user_id: int, address: str) -> Optional[Dict]:
        """Get wallet by address for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, network, address, private_key, seed_phrase
            FROM wallets WHERE user_id = ? AND address = ?
        ''', (user_id, address))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'network': row[1],
                'address': row[2],
                'private_key': row[3],
                'seed_phrase': row[4]
            }
        return None
    
    def create_wallet(self, user_id: int, network: str, address: str, 
                     private_key: str, seed_phrase: str) -> bool:
        """Create new wallet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO wallets (user_id, network, address, private_key, seed_phrase)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, network, address, private_key, seed_phrase))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating wallet: {e}")
            return False
    
    def create_withdrawal_log(self, user_id: int, from_address: str, to_address: str,
                            amount: float, token_type: str, network: str, 
                            status: str = 'pending', tx_hash: str = None) -> bool:
        """Create withdrawal log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO withdrawal_logs (user_id, from_address, to_address, 
                                           amount, token_type, network, status, tx_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, from_address, to_address, amount, token_type, network, status, tx_hash))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating withdrawal log: {e}")
            return False
    
    def create_staking_log(self, user_id: int, wallet_address: str, amount: float,
                          asset: str, rate: float, end_date: datetime) -> bool:
        """Create staking log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO staking_logs (user_id, wallet_address, amount, asset, 
                                        rate, end_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, wallet_address, amount, asset, rate, end_date))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating staking log: {e}")
            return False
    
    def get_user_stakes(self, user_id: int) -> List[Dict]:
        """Get all staking records for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, wallet_address, amount, asset, rate, start_date, end_date, 
                   status, accrued_reward
            FROM staking_logs WHERE user_id = ?
            ORDER BY start_date DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'wallet_address': row[1],
            'amount': row[2],
            'asset': row[3],
            'rate': row[4],
            'start_date': row[5],
            'end_date': row[6],
            'status': row[7],
            'accrued_reward': row[8]
        } for row in rows]
    
    def get_active_stakes_count(self, user_id: int) -> int:
        """Get count of active stakes for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM staking_logs 
            WHERE user_id = ? AND status = 'active'
        ''', (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def update_stake_status(self, stake_id: int, status: str, accrued_reward: float = None) -> bool:
        """Update staking status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if accrued_reward is not None:
                cursor.execute('''
                    UPDATE staking_logs SET status = ?, accrued_reward = ?
                    WHERE id = ?
                ''', (status, accrued_reward, stake_id))
            else:
                cursor.execute('''
                    UPDATE staking_logs SET status = ?
                    WHERE id = ?
                ''', (status, stake_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating stake status: {e}")
            return False
    
    def get_withdrawal_logs(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get withdrawal logs for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, from_address, to_address, amount, token_type, network, 
                   status, timestamp, tx_hash
            FROM withdrawal_logs WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'from_address': row[1],
            'to_address': row[2],
            'amount': row[3],
            'token_type': row[4],
            'network': row[5],
            'status': row[6],
            'timestamp': row[7],
            'tx_hash': row[8]
        } for row in rows]