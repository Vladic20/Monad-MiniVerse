import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import config
from database import Database
from wallet_service import WalletService

class StakingService:
    def __init__(self, database: Database, wallet_service: WalletService):
        self.db = database
        self.wallet_service = wallet_service
    
    def calculate_staking_reward(self, amount: float, rate: float, days: int) -> float:
        """Calculate staking reward"""
        return amount * (rate / 100) * (days / 365)
    
    def calculate_current_reward(self, stake_data: Dict) -> float:
        """Calculate current reward for active stake"""
        if stake_data['status'] != 'active':
            return stake_data['accrued_reward']
        
        start_date = datetime.fromisoformat(stake_data['start_date'])
        end_date = datetime.fromisoformat(stake_data['end_date'])
        current_date = datetime.now()
        
        # If stake is completed
        if current_date >= end_date:
            return self.calculate_staking_reward(
                stake_data['amount'], 
                stake_data['rate'], 
                (end_date - start_date).days
            )
        
        # Calculate current reward
        days_passed = (current_date - start_date).days
        if days_passed <= 0:
            return 0.0
        
        return self.calculate_staking_reward(
            stake_data['amount'], 
            stake_data['rate'], 
            days_passed
        )
    
    async def create_stake(self, user_id: int, wallet_address: str, amount: float,
                          asset: str, period_key: str) -> Tuple[bool, str, Dict]:
        """Create new staking position"""
        try:
            # Validate period
            if period_key not in config.STAKING_PERIODS:
                return False, "Неверный период стейкинга", {}
            
            period_data = config.STAKING_PERIODS[period_key]
            
            # Check active stakes limit
            active_stakes = self.db.get_active_stakes_count(user_id)
            if active_stakes >= config.STAKING_LIMITS['max_active_stakes']:
                return False, f"Достигнут лимит активных стейков ({config.STAKING_LIMITS['max_active_stakes']})", {}
            
            # Validate amount
            min_amount = config.STAKING_LIMITS['min_usdt'] if asset == 'USDT' else config.STAKING_LIMITS['min_amount']
            if amount < min_amount:
                return False, f"Минимальная сумма для {asset}: {min_amount}", {}
            
            # Check wallet balance
            wallet = self.db.get_wallet_by_address(user_id, wallet_address)
            if not wallet:
                return False, "Кошелек не найден", {}
            
            # Get current balance
            current_balance = await self.wallet_service.get_balance(
                wallet_address, wallet['network'], asset
            )
            
            # Check staked amount
            staked_amount = await self.get_staked_amount(user_id, wallet_address, asset)
            available_balance = current_balance - staked_amount
            
            if amount > available_balance:
                return False, f"Недостаточно {asset}. Доступно: {available_balance:.6f}", {}
            
            # Calculate end date
            end_date = datetime.now() + timedelta(days=period_data['days'])
            
            # Create staking log
            success = self.db.create_staking_log(
                user_id, wallet_address, amount, asset, 
                period_data['rate'], end_date
            )
            
            if not success:
                return False, "Ошибка создания стейкинга", {}
            
            # Calculate expected reward
            expected_reward = self.calculate_staking_reward(
                amount, period_data['rate'], period_data['days']
            )
            
            result_data = {
                'amount': amount,
                'asset': asset,
                'rate': period_data['rate'],
                'period': period_key,
                'end_date': end_date.isoformat(),
                'expected_reward': expected_reward
            }
            
            return True, "Стейкинг успешно создан", result_data
            
        except Exception as e:
            print(f"Error creating stake: {e}")
            return False, "Ошибка создания стейкинга", {}
    
    async def get_staked_amount(self, user_id: int, wallet_address: str, asset: str) -> float:
        """Get total staked amount for wallet and asset"""
        stakes = self.db.get_user_stakes(user_id)
        total_staked = 0.0
        
        for stake in stakes:
            if (stake['wallet_address'] == wallet_address and 
                stake['asset'] == asset and 
                stake['status'] == 'active'):
                total_staked += stake['amount']
        
        return total_staked
    
    async def get_user_stakes_info(self, user_id: int) -> List[Dict]:
        """Get detailed staking information for user"""
        stakes = self.db.get_user_stakes(user_id)
        stakes_info = []
        
        for stake in stakes:
            current_reward = self.calculate_current_reward(stake)
            penalty_amount = current_reward * config.STAKING_LIMITS['early_withdrawal_penalty']
            
            stakes_info.append({
                'id': stake['id'],
                'wallet_address': stake['wallet_address'],
                'amount': stake['amount'],
                'asset': stake['asset'],
                'rate': stake['rate'],
                'start_date': stake['start_date'],
                'end_date': stake['end_date'],
                'status': stake['status'],
                'current_reward': current_reward,
                'penalty_amount': penalty_amount,
                'reward_after_penalty': current_reward - penalty_amount
            })
        
        return stakes_info
    
    async def early_withdraw_stake(self, user_id: int, stake_id: int) -> Tuple[bool, str, Dict]:
        """Early withdrawal with penalty"""
        try:
            stakes = self.db.get_user_stakes(user_id)
            target_stake = None
            
            for stake in stakes:
                if stake['id'] == stake_id and stake['status'] == 'active':
                    target_stake = stake
                    break
            
            if not target_stake:
                return False, "Стейк не найден или не активен", {}
            
            # Calculate current reward
            current_reward = self.calculate_current_reward(target_stake)
            penalty_amount = current_reward * config.STAKING_LIMITS['early_withdrawal_penalty']
            final_reward = current_reward - penalty_amount
            
            # Update stake status
            success = self.db.update_stake_status(
                stake_id, 'early_withdrawn', current_reward
            )
            
            if not success:
                return False, "Ошибка обновления статуса", {}
            
            # Create withdrawal log for reward
            self.db.create_withdrawal_log(
                user_id, target_stake['wallet_address'], target_stake['wallet_address'],
                final_reward, f"{target_stake['asset']} Staking Reward", 
                target_stake['wallet_address'][:3], 'completed'
            )
            
            result_data = {
                'amount': target_stake['amount'],
                'asset': target_stake['asset'],
                'reward': current_reward,
                'penalty': penalty_amount,
                'final_reward': final_reward
            }
            
            return True, "Досрочный вывод выполнен", result_data
            
        except Exception as e:
            print(f"Error early withdrawing stake: {e}")
            return False, "Ошибка досрочного вывода", {}
    
    async def complete_expired_stakes(self) -> List[Dict]:
        """Complete expired stakes and return rewards"""
        try:
            # This would typically be called by a background task
            # For now, we'll just return empty list
            return []
        except Exception as e:
            print(f"Error completing expired stakes: {e}")
            return []
    
    def get_staking_periods(self) -> Dict:
        """Get available staking periods"""
        return config.STAKING_PERIODS
    
    def get_staking_limits(self) -> Dict:
        """Get staking limits"""
        return config.STAKING_LIMITS
    
    async def validate_staking_request(self, user_id: int, wallet_address: str, 
                                     amount: float, asset: str) -> Tuple[bool, str]:
        """Validate staking request"""
        try:
            # Check wallet exists
            wallet = self.db.get_wallet_by_address(user_id, wallet_address)
            if not wallet:
                return False, "Кошелек не найден"
            
            # Check amount limits
            min_amount = config.STAKING_LIMITS['min_usdt'] if asset == 'USDT' else config.STAKING_LIMITS['min_amount']
            if amount < min_amount:
                return False, f"Минимальная сумма для {asset}: {min_amount}"
            
            # Check active stakes limit
            active_stakes = self.db.get_active_stakes_count(user_id)
            if active_stakes >= config.STAKING_LIMITS['max_active_stakes']:
                return False, f"Достигнут лимит активных стейков ({config.STAKING_LIMITS['max_active_stakes']})"
            
            # Check balance
            current_balance = await self.wallet_service.get_balance(
                wallet_address, wallet['network'], asset
            )
            staked_amount = await self.get_staked_amount(user_id, wallet_address, asset)
            available_balance = current_balance - staked_amount
            
            if amount > available_balance:
                return False, f"Недостаточно {asset}. Доступно: {available_balance:.6f}"
            
            return True, "OK"
            
        except Exception as e:
            print(f"Error validating staking request: {e}")
            return False, "Ошибка валидации"