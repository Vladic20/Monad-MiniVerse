import requests
import json
from web3 import Web3
from tronpy import Tron
from solana.rpc.api import Client
from typing import Dict, Optional, Tuple
from config import (
    NETWORK_RPC_URLS, 
    USDT_CONTRACTS, 
    INFURA_URL, 
    TRONGRID_API_KEY, 
    SOLANA_RPC_URL
)

class BalanceChecker:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(INFURA_URL))
        self.tron = Tron()
        self.solana_client = Client(SOLANA_RPC_URL)
        
        # USDT ABI for ERC20
        self.usdt_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]

    def get_ethereum_balance(self, address: str) -> Dict[str, float]:
        """Get ETH and USDT balance for Ethereum address"""
        try:
            # Check ETH balance
            eth_balance_wei = self.w3.eth.get_balance(address)
            eth_balance = self.w3.from_wei(eth_balance_wei, 'ether')
            
            # Check USDT balance
            usdt_contract = self.w3.eth.contract(
                address=USDT_CONTRACTS['ETH'], 
                abi=self.usdt_abi
            )
            usdt_balance_wei = usdt_contract.functions.balanceOf(address).call()
            usdt_balance = usdt_balance_wei / 10**6  # USDT has 6 decimals
            
            return {
                'ETH': float(eth_balance),
                'USDT': float(usdt_balance)
            }
        except Exception as e:
            print(f"Error getting Ethereum balance: {e}")
            return {'ETH': 0.0, 'USDT': 0.0}

    def get_tron_balance(self, address: str) -> Dict[str, float]:
        """Get TRX and USDT balance for Tron address"""
        try:
            # Check TRX balance
            trx_balance_sun = self.tron.get_account_balance(address)
            trx_balance = trx_balance_sun / 1_000_000  # Convert from SUN to TRX
            
            # Check USDT balance
            usdt_contract = self.tron.get_contract(USDT_CONTRACTS['TRX'])
            usdt_balance_sun = usdt_contract.functions.balanceOf(address)
            usdt_balance = usdt_balance_sun / 1_000_000  # USDT has 6 decimals
            
            return {
                'TRX': float(trx_balance),
                'USDT': float(usdt_balance)
            }
        except Exception as e:
            print(f"Error getting Tron balance: {e}")
            return {'TRX': 0.0, 'USDT': 0.0}

    def get_solana_balance(self, address: str) -> Dict[str, float]:
        """Get SOL balance for Solana address"""
        try:
            response = self.solana_client.get_balance(address)
            if response['result']['value']:
                sol_balance_lamports = response['result']['value']
                sol_balance = sol_balance_lamports / 1_000_000_000  # Convert from lamports to SOL
                return {'SOL': float(sol_balance)}
            return {'SOL': 0.0}
        except Exception as e:
            print(f"Error getting Solana balance: {e}")
            return {'SOL': 0.0}

    def get_bnb_balance(self, address: str) -> Dict[str, float]:
        """Get BNB balance for BSC address"""
        try:
            w3 = Web3(Web3.HTTPProvider(NETWORK_RPC_URLS['BSC']))
            bnb_balance_wei = w3.eth.get_balance(address)
            bnb_balance = w3.from_wei(bnb_balance_wei, 'ether')
            return {'BNB': float(bnb_balance)}
        except Exception as e:
            print(f"Error getting BNB balance: {e}")
            return {'BNB': 0.0}

    def get_dogecoin_balance(self, address: str) -> Dict[str, float]:
        """Get DOGE balance for Dogecoin address"""
        try:
            url = f"https://sochain.com/api/v2/get_address_balance/DOGE/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    doge_balance = float(data['data']['confirmed_balance'])
                    return {'DOGE': doge_balance}
            return {'DOGE': 0.0}
        except Exception as e:
            print(f"Error getting Dogecoin balance: {e}")
            return {'DOGE': 0.0}

    def get_avalanche_balance(self, address: str) -> Dict[str, float]:
        """Get AVAX balance for Avalanche address"""
        try:
            w3 = Web3(Web3.HTTPProvider(NETWORK_RPC_URLS['AVAX']))
            avax_balance_wei = w3.eth.get_balance(address)
            avax_balance = w3.from_wei(avax_balance_wei, 'ether')
            return {'AVAX': float(avax_balance)}
        except Exception as e:
            print(f"Error getting Avalanche balance: {e}")
            return {'AVAX': 0.0}

    def get_polygon_balance(self, address: str) -> Dict[str, float]:
        """Get POL balance for Polygon address"""
        try:
            w3 = Web3(Web3.HTTPProvider(NETWORK_RPC_URLS['POL']))
            pol_balance_wei = w3.eth.get_balance(address)
            pol_balance = w3.from_wei(pol_balance_wei, 'ether')
            return {'POL': float(pol_balance)}
        except Exception as e:
            print(f"Error getting Polygon balance: {e}")
            return {'POL': 0.0}

    def get_xrp_balance(self, address: str) -> Dict[str, float]:
        """Get XRP balance for XRP address"""
        try:
            url = f"https://api.xrpscan.com/api/v1/account/{address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'account_data' in data:
                    xrp_balance_drops = int(data['account_data']['Balance'])
                    xrp_balance = xrp_balance_drops / 1_000_000  # Convert from drops to XRP
                    return {'XRP': float(xrp_balance)}
            return {'XRP': 0.0}
        except Exception as e:
            print(f"Error getting XRP balance: {e}")
            return {'XRP': 0.0}

    def get_balance(self, address: str, network: str) -> Dict[str, float]:
        """Get balance for address in specified network"""
        checkers = {
            'ETH': self.get_ethereum_balance,
            'TRX': self.get_tron_balance,
            'SOL': self.get_solana_balance,
            'BNB': self.get_bnb_balance,
            'DOGE': self.get_dogecoin_balance,
            'AVAX': self.get_avalanche_balance,
            'POL': self.get_polygon_balance,
            'XRP': self.get_xrp_balance,
        }
        
        if network not in checkers:
            return {}
        
        return checkers[network](address)

    def get_all_balances(self, wallets: list) -> Dict[str, Dict[str, float]]:
        """Get balances for all wallets"""
        balances = {}
        for wallet in wallets:
            network = wallet.network
            address = wallet.address
            balance = self.get_balance(address, network)
            balances[address] = balance
        return balances

# Global instance
balance_checker = BalanceChecker()