from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import random
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=False)
    account_id = Column(String(9), unique=True, nullable=False)
    creation_date = Column(DateTime, default=datetime.utcnow)

class Wallet(Base):
    __tablename__ = 'wallets'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    network = Column(String(10), nullable=False)
    address = Column(String(100), nullable=False)
    private_key = Column(Text, nullable=False)
    seed_phrase = Column(Text, nullable=False)

class WithdrawalLog(Base):
    __tablename__ = 'withdrawal_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    from_address = Column(String(100), nullable=False)
    to_address = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    token_type = Column(String(20), nullable=False)
    network = Column(String(10), nullable=False)
    status = Column(String(20), default='pending')
    timestamp = Column(DateTime, default=datetime.utcnow)
    tx_hash = Column(String(100))

class StakingLog(Base):
    __tablename__ = 'staking_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    wallet_address = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    asset = Column(String(10), nullable=False)
    rate = Column(Float, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default='active')
    accrued_reward = Column(Float, default=0.0)

# Database connection
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)

def generate_account_id():
    """Generate a random 9-digit account ID"""
    return str(random.randint(100000000, 999999999))

def create_user(db, telegram_id):
    """Create a new user"""
    account_id = generate_account_id()
    user = User(
        user_id=telegram_id,
        telegram_id=telegram_id,
        account_id=account_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_telegram_id(db, telegram_id):
    """Get user by telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def get_user_wallets(db, user_id):
    """Get all wallets for a user"""
    return db.query(Wallet).filter(Wallet.user_id == user_id).all()

def create_wallet(db, user_id, network, address, private_key, seed_phrase):
    """Create a new wallet"""
    wallet = Wallet(
        user_id=user_id,
        network=network,
        address=address,
        private_key=private_key,
        seed_phrase=seed_phrase
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

def get_active_stakes(db, user_id):
    """Get active stakes for a user"""
    return db.query(StakingLog).filter(
        StakingLog.user_id == user_id,
        StakingLog.status == 'active'
    ).all()

def create_stake(db, user_id, wallet_address, amount, asset, rate, end_date):
    """Create a new stake"""
    stake = StakingLog(
        user_id=user_id,
        wallet_address=wallet_address,
        amount=amount,
        asset=asset,
        rate=rate,
        end_date=end_date
    )
    db.add(stake)
    db.commit()
    db.refresh(stake)
    return stake

def log_withdrawal(db, user_id, from_address, to_address, amount, token_type, network, status='pending', tx_hash=None):
    """Log a withdrawal transaction"""
    withdrawal = WithdrawalLog(
        user_id=user_id,
        from_address=from_address,
        to_address=to_address,
        amount=amount,
        token_type=token_type,
        network=network,
        status=status,
        tx_hash=tx_hash
    )
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal