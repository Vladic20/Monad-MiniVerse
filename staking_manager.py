from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import StakingLog, get_active_stakes, create_stake
from sqlalchemy.orm import Session
from config import (
    STAKING_PERIODS, 
    MIN_STAKING_AMOUNTS, 
    MAX_ACTIVE_STAKES, 
    EARLY_WITHDRAWAL_PENALTY
)

class StakingManager:
    def __init__(self):
        pass

    def calculate_reward(self, amount: float, rate: float, days: int) -> float:
        """Calculate staking reward"""
        return amount * (rate / 100) * (days / 365)

    def get_staking_period_info(self, period_key: str) -> Dict:
        """Get staking period information"""
        if period_key not in STAKING_PERIODS:
            raise ValueError(f"Invalid staking period: {period_key}")
        
        period_info = STAKING_PERIODS[period_key]
        months = period_info['months']
        rate = period_info['rate']
        days = months * 30  # Approximate days
        
        return {
            'months': months,
            'rate': rate,
            'days': days,
            'period_key': period_key
        }

    def validate_staking_request(
        self, 
        db: Session, 
        user_id: int, 
        amount: float, 
        asset: str,
        wallet_address: str
    ) -> Tuple[bool, str]:
        """Validate staking request"""
        # Check minimum amount
        if asset not in MIN_STAKING_AMOUNTS:
            return False, f"Unsupported asset: {asset}"
        
        min_amount = MIN_STAKING_AMOUNTS[asset]
        if amount < min_amount:
            return False, f"Minimum staking amount for {asset}: {min_amount}"
        
        # Check maximum active stakes
        active_stakes = get_active_stakes(db, user_id)
        if len(active_stakes) >= MAX_ACTIVE_STAKES:
            return False, f"Maximum {MAX_ACTIVE_STAKES} active stakes allowed"
        
        # Check if wallet already has active stake
        for stake in active_stakes:
            if stake.wallet_address == wallet_address and stake.asset == asset:
                return False, f"Wallet {wallet_address} already has active {asset} stake"
        
        return True, "Valid"

    def create_staking(
        self, 
        db: Session, 
        user_id: int, 
        wallet_address: str, 
        amount: float, 
        asset: str, 
        period_key: str
    ) -> StakingLog:
        """Create a new staking"""
        period_info = self.get_staking_period_info(period_key)
        
        # Calculate end date
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=period_info['days'])
        
        # Create stake
        stake = create_stake(
            db=db,
            user_id=user_id,
            wallet_address=wallet_address,
            amount=amount,
            asset=asset,
            rate=period_info['rate'],
            end_date=end_date
        )
        
        return stake

    def get_user_stakes(self, db: Session, user_id: int) -> List[StakingLog]:
        """Get all stakes for user"""
        return get_active_stakes(db, user_id)

    def calculate_current_reward(self, stake: StakingLog) -> float:
        """Calculate current reward for active stake"""
        if stake.status != 'active':
            return 0.0
        
        days_passed = (datetime.utcnow() - stake.start_date).days
        total_days = (stake.end_date - stake.start_date).days
        
        if days_passed <= 0:
            return 0.0
        
        # Calculate proportional reward
        reward = self.calculate_reward(stake.amount, stake.rate, days_passed)
        return reward

    def get_stake_summary(self, stake: StakingLog) -> Dict:
        """Get summary information for stake"""
        current_reward = self.calculate_current_reward(stake)
        penalty_amount = current_reward * EARLY_WITHDRAWAL_PENALTY
        days_remaining = (stake.end_date - datetime.utcnow()).days
        
        return {
            'id': stake.id,
            'wallet_address': stake.wallet_address,
            'asset': stake.asset,
            'amount': stake.amount,
            'rate': stake.rate,
            'start_date': stake.start_date,
            'end_date': stake.end_date,
            'current_reward': current_reward,
            'penalty_amount': penalty_amount,
            'days_remaining': max(0, days_remaining),
            'status': stake.status
        }

    def process_completed_stakes(self, db: Session) -> List[StakingLog]:
        """Process completed stakes and return them"""
        completed_stakes = []
        active_stakes = db.query(StakingLog).filter(
            StakingLog.status == 'active'
        ).all()
        
        for stake in active_stakes:
            if datetime.utcnow() >= stake.end_date:
                # Calculate final reward
                final_reward = self.calculate_reward(
                    stake.amount, 
                    stake.rate, 
                    (stake.end_date - stake.start_date).days
                )
                
                # Update stake
                stake.status = 'completed'
                stake.accrued_reward = final_reward
                completed_stakes.append(stake)
        
        db.commit()
        return completed_stakes

    def early_withdraw_stake(self, db: Session, stake_id: int) -> Tuple[bool, str, float]:
        """Process early withdrawal of stake"""
        stake = db.query(StakingLog).filter(
            StakingLog.id == stake_id,
            StakingLog.status == 'active'
        ).first()
        
        if not stake:
            return False, "Stake not found or not active", 0.0
        
        # Calculate current reward and penalty
        current_reward = self.calculate_current_reward(stake)
        penalty_amount = current_reward * EARLY_WITHDRAWAL_PENALTY
        final_reward = current_reward - penalty_amount
        
        # Update stake
        stake.status = 'early_withdrawn'
        stake.accrued_reward = final_reward
        
        db.commit()
        
        return True, "Early withdrawal successful", final_reward

    def get_staking_stats(self, db: Session, user_id: int) -> Dict:
        """Get staking statistics for user"""
        active_stakes = get_active_stakes(db, user_id)
        
        total_staked = sum(stake.amount for stake in active_stakes)
        total_reward = sum(self.calculate_current_reward(stake) for stake in active_stakes)
        
        return {
            'total_stakes': len(active_stakes),
            'total_staked': total_staked,
            'total_reward': total_reward,
            'max_stakes': MAX_ACTIVE_STAKES
        }

# Global instance
staking_manager = StakingManager()