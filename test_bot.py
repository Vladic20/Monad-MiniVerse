#!/usr/bin/env python3
"""
Tests for Crypto Wallet Telegram Bot
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wallet_generator import generate_wallet, generate_multiple_wallets
from utils import validate_address, validate_amount, escape_markdown
from config import SUPPORTED_NETWORKS, STAKING_PERIODS

class TestWalletGenerator(unittest.TestCase):
    """Test wallet generation functionality"""
    
    def test_generate_ethereum_wallet(self):
        """Test Ethereum wallet generation"""
        address, private_key, seed_phrase = generate_wallet('ETH')
        
        self.assertIsInstance(address, str)
        self.assertIsInstance(private_key, str)
        self.assertIsInstance(seed_phrase, str)
        
        # Check address format
        self.assertTrue(address.startswith('0x'))
        self.assertEqual(len(address), 42)
        
        # Check private key format
        self.assertTrue(private_key.startswith('0x'))
        self.assertEqual(len(private_key), 66)
        
        # Check seed phrase
        words = seed_phrase.split()
        self.assertEqual(len(words), 12)

    def test_generate_multiple_wallets(self):
        """Test multiple wallet generation"""
        wallets = generate_multiple_wallets('ETH', 3)
        
        self.assertEqual(len(wallets), 3)
        
        for wallet in wallets:
            self.assertIn('address', wallet)
            self.assertIn('private_key', wallet)
            self.assertIn('seed_phrase', wallet)
            
            # Check address format
            self.assertTrue(wallet['address'].startswith('0x'))
            self.assertEqual(len(wallet['address']), 42)

    def test_unsupported_network(self):
        """Test unsupported network error"""
        with self.assertRaises(ValueError):
            generate_wallet('UNSUPPORTED')

class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_validate_address(self):
        """Test address validation"""
        # Valid addresses
        self.assertTrue(validate_address('0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6', 'ETH'))
        self.assertTrue(validate_address('TJRabPrwbZy45sbavfcjinPJC18kjpRTv8', 'TRX'))
        
        # Invalid addresses
        self.assertFalse(validate_address('invalid_address', 'ETH'))
        self.assertFalse(validate_address('0x123', 'ETH'))
        self.assertFalse(validate_address('TJRabPrwbZy45sbavfcjinPJC18kjpRTv8', 'ETH'))

    def test_validate_amount(self):
        """Test amount validation"""
        # Valid amounts
        self.assertEqual(validate_amount('1.5'), 1.5)
        self.assertEqual(validate_amount('0.001'), 0.001)
        self.assertEqual(validate_amount('100'), 100.0)
        
        # Invalid amounts
        self.assertIsNone(validate_amount('0'))
        self.assertIsNone(validate_amount('-1'))
        self.assertIsNone(validate_amount('invalid'))
        self.assertIsNone(validate_amount(''))

    def test_escape_markdown(self):
        """Test markdown escaping"""
        text = "Hello *world* with _emphasis_ and [links](url)"
        escaped = escape_markdown(text)
        
        # Check that special characters are escaped
        self.assertIn('\\*', escaped)
        self.assertIn('\\_', escaped)
        self.assertIn('\\[', escaped)
        self.assertIn('\\)', escaped)

class TestConfig(unittest.TestCase):
    """Test configuration"""
    
    def test_supported_networks(self):
        """Test supported networks configuration"""
        expected_networks = ['ETH', 'TRX', 'SOL', 'BNB', 'DOGE', 'AVAX', 'POL', 'XRP']
        self.assertEqual(SUPPORTED_NETWORKS, expected_networks)

    def test_staking_periods(self):
        """Test staking periods configuration"""
        self.assertIn('1_month', STAKING_PERIODS)
        self.assertIn('3_months', STAKING_PERIODS)
        self.assertIn('6_months', STAKING_PERIODS)
        self.assertIn('9_months', STAKING_PERIODS)
        
        # Check rates
        self.assertEqual(STAKING_PERIODS['1_month']['rate'], 16)
        self.assertEqual(STAKING_PERIODS['3_months']['rate'], 18)
        self.assertEqual(STAKING_PERIODS['6_months']['rate'], 20)
        self.assertEqual(STAKING_PERIODS['9_months']['rate'], 22)

class TestDatabase(unittest.TestCase):
    """Test database functionality"""
    
    @patch('database.get_db')
    def test_create_user(self, mock_get_db):
        """Test user creation"""
        from database import create_user, User
        
        # Mock database session
        mock_session = Mock()
        mock_get_db.return_value = iter([mock_session])
        
        # Mock user object
        mock_user = Mock()
        mock_user.id = 1
        mock_user.account_id = '123456789'
        mock_user.creation_date = '2024-01-01'
        
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None
        
        # Test user creation
        result = create_user(mock_session, 12345)
        
        # Verify user was added to session
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

class TestStakingManager(unittest.TestCase):
    """Test staking manager functionality"""
    
    def test_calculate_reward(self):
        """Test reward calculation"""
        from staking_manager import StakingManager
        
        manager = StakingManager()
        
        # Test reward calculation
        reward = manager.calculate_reward(100, 20, 365)  # 100 tokens, 20% rate, 365 days
        self.assertEqual(reward, 20.0)
        
        reward = manager.calculate_reward(50, 16, 180)  # 50 tokens, 16% rate, 180 days
        expected = 50 * (16 / 100) * (180 / 365)
        self.assertAlmostEqual(reward, expected, places=2)

    def test_get_staking_period_info(self):
        """Test staking period info"""
        from staking_manager import StakingManager
        
        manager = StakingManager()
        
        info = manager.get_staking_period_info('1_month')
        self.assertEqual(info['months'], 1)
        self.assertEqual(info['rate'], 16)
        self.assertEqual(info['days'], 30)
        
        # Test invalid period
        with self.assertRaises(ValueError):
            manager.get_staking_period_info('invalid_period')

def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestWalletGenerator))
    test_suite.addTest(unittest.makeSuite(TestUtils))
    test_suite.addTest(unittest.makeSuite(TestConfig))
    test_suite.addTest(unittest.makeSuite(TestDatabase))
    test_suite.addTest(unittest.makeSuite(TestStakingManager))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)