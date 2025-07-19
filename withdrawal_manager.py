from web3 import Web3
from tronpy import Tron
from typing import Dict, Optional, Tuple
from config import (
    NETWORK_RPC_URLS, 
    USDT_CONTRACTS, 
    INFURA_URL, 
    TRONGRID_API_KEY,
    MIN_WITHDRAWAL,
    NETWORK_FEES
)

class WithdrawalManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(INFURA_URL))
        self.tron = Tron()
        
        # USDT ABI for ERC20
        self.usdt_abi = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]

    def validate_withdrawal(
        self, 
        address: str, 
        amount: float, 
        asset: str, 
        network: str,
        private_key: str
    ) -> Tuple[bool, str]:
        """Validate withdrawal request"""
        # Check minimum amount
        if asset in MIN_WITHDRAWAL:
            min_amount = MIN_WITHDRAWAL[asset]
            if amount < min_amount:
                return False, f"Минимальная сумма для вывода {asset}: {min_amount}"
        
        # Check balance
        balance = self.get_balance(address, asset, network)
        if balance < amount:
            return False, f"Недостаточно {asset}. Доступно: {balance}"
        
        # Check if private key is valid
        if not self.validate_private_key(private_key, network):
            return False, "Неверный приватный ключ"
        
        return True, "Valid"

    def get_balance(self, address: str, asset: str, network: str) -> float:
        """Get balance for specific asset"""
        if network == 'ETH':
            if asset == 'ETH':
                balance_wei = self.w3.eth.get_balance(address)
                return self.w3.from_wei(balance_wei, 'ether')
            elif asset == 'USDT':
                contract = self.w3.eth.contract(
                    address=USDT_CONTRACTS['ETH'], 
                    abi=self.usdt_abi
                )
                balance_wei = contract.functions.balanceOf(address).call()
                return balance_wei / 10**6
        elif network == 'TRX':
            if asset == 'TRX':
                balance_sun = self.tron.get_account_balance(address)
                return balance_sun / 1_000_000
            elif asset == 'USDT':
                contract = self.tron.get_contract(USDT_CONTRACTS['TRX'])
                balance_sun = contract.functions.balanceOf(address)
                return balance_sun / 1_000_000
        
        return 0.0

    def validate_private_key(self, private_key: str, network: str) -> bool:
        """Validate private key format"""
        try:
            if network in ['ETH', 'BNB', 'AVAX', 'POL']:
                # EVM networks
                account = self.w3.eth.account.from_key(private_key)
                return True
            elif network == 'TRX':
                # Tron network
                account = self.tron.get_account(private_key)
                return True
            else:
                # Other networks - basic validation
                return len(private_key) > 0
        except Exception:
            return False

    def perform_ethereum_withdrawal(
        self, 
        from_address: str, 
        to_address: str, 
        amount: float, 
        asset: str, 
        private_key: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Perform Ethereum withdrawal"""
        try:
            if asset == 'ETH':
                # Native ETH transfer
                nonce = self.w3.eth.get_transaction_count(from_address)
                gas_price = self.w3.eth.gas_price
                
                # Estimate gas
                gas_estimate = 21000  # Standard ETH transfer
                
                # Calculate total cost
                total_cost = amount + (gas_estimate * gas_price / 10**18)
                balance = self.get_balance(from_address, 'ETH', 'ETH')
                
                if balance < total_cost:
                    return False, "Недостаточно ETH для комиссии", None
                
                # Build transaction
                transaction = {
                    'nonce': nonce,
                    'to': to_address,
                    'value': self.w3.to_wei(amount, 'ether'),
                    'gas': gas_estimate,
                    'gasPrice': gas_price,
                    'chainId': 1  # Mainnet
                }
                
                # Sign and send
                signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                return True, "Транзакция отправлена", tx_hash.hex()
                
            elif asset == 'USDT':
                # USDT transfer
                contract = self.w3.eth.contract(
                    address=USDT_CONTRACTS['ETH'], 
                    abi=self.usdt_abi
                )
                
                nonce = self.w3.eth.get_transaction_count(from_address)
                gas_price = self.w3.eth.gas_price
                
                # Build transaction
                transaction = contract.functions.transfer(
                    to_address, 
                    int(amount * 10**6)  # USDT has 6 decimals
                ).build_transaction({
                    'nonce': nonce,
                    'gasPrice': gas_price,
                    'chainId': 1
                })
                
                # Sign and send
                signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                return True, "Транзакция отправлена", tx_hash.hex()
        
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None

    def perform_tron_withdrawal(
        self, 
        from_address: str, 
        to_address: str, 
        amount: float, 
        asset: str, 
        private_key: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Perform Tron withdrawal"""
        try:
            if asset == 'TRX':
                # Native TRX transfer
                txn = self.tron.trx.transfer(
                    from_address, 
                    to_address, 
                    int(amount * 1_000_000)  # Convert to SUN
                )
                signed_txn = txn.sign(private_key)
                result = signed_txn.broadcast()
                
                if result.get('result'):
                    return True, "Транзакция отправлена", result['txid']
                else:
                    return False, "Ошибка отправки транзакции", None
                    
            elif asset == 'USDT':
                # USDT transfer
                contract = self.tron.get_contract(USDT_CONTRACTS['TRX'])
                txn = contract.functions.transfer(
                    to_address, 
                    int(amount * 1_000_000)  # USDT has 6 decimals
                )
                signed_txn = txn.sign(private_key)
                result = signed_txn.broadcast()
                
                if result.get('result'):
                    return True, "Транзакция отправлена", result['txid']
                else:
                    return False, "Ошибка отправки транзакции", None
        
        except Exception as e:
            return False, f"Ошибка: {str(e)}", None

    def perform_withdrawal(
        self, 
        from_address: str, 
        to_address: str, 
        amount: float, 
        asset: str, 
        network: str, 
        private_key: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Perform withdrawal for any supported network"""
        # Validate withdrawal
        is_valid, message = self.validate_withdrawal(
            from_address, amount, asset, network, private_key
        )
        
        if not is_valid:
            return False, message, None
        
        # Perform withdrawal based on network
        if network == 'ETH':
            return self.perform_ethereum_withdrawal(
                from_address, to_address, amount, asset, private_key
            )
        elif network == 'TRX':
            return self.perform_tron_withdrawal(
                from_address, to_address, amount, asset, private_key
            )
        else:
            # For other networks, return pending status
            return True, "Запрос отправлен на ручную обработку", None

    def get_network_fee(self, network: str) -> float:
        """Get network fee for withdrawal"""
        return NETWORK_FEES.get(network, 0.0)

    def estimate_gas_fee(self, network: str, asset: str) -> float:
        """Estimate gas fee for transaction"""
        if network == 'ETH':
            if asset == 'ETH':
                return 0.001  # Approximate gas fee for ETH transfer
            elif asset == 'USDT':
                return 0.005  # Approximate gas fee for USDT transfer
        elif network == 'TRX':
            return 0.1  # TRX fee
        
        return 0.0

# Global instance
withdrawal_manager = WithdrawalManager()