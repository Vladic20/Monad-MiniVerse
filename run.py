#!/usr/bin/env python3
"""
Crypto Wallet Telegram Bot Runner
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'TELEGRAM_TOKEN',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        return False
    
    logger.info("Environment variables check passed")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import telegram
        import sqlalchemy
        import web3
        import tronpy
        import solana
        import requests
        import bip_utils
        logger.info("All dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

def check_database():
    """Check database connection"""
    try:
        from database import init_db, get_db
        from sqlalchemy import text
        
        # Initialize database
        init_db()
        
        # Test connection
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        db.close()
        
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def main():
    """Main function to run the bot"""
    logger.info("Starting Crypto Wallet Telegram Bot...")
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database():
        sys.exit(1)
    
    # Import and run bot
    try:
        from bot import main as run_bot
        logger.info("Bot initialized successfully")
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()