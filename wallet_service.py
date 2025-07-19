import asyncio
import aiohttp
import json
import base58
from typing import Dict, Optional, Tuple, List
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip39MnemonicGenerator
from web3 import Web3
from tronpy import Tron
from solana.rpc.api import Client
import config
from database import Database

class WalletService:
    def __init__(self, database: Database):
        self.db = database
        self.web3_eth = None
        self.tron_client = None
        self.solana_client = None
        
        # Initialize clients
        self._init_clients()
    
    def _init_clients(self):
        """Initialize blockchain clients"""
        try:
            # Ethereum
            if config.SUPPORTED_NETWORKS['ETH']['rpc_url']:
                self.web3_eth = Web3(Web3.HTTPProvider(config.SUPPORTED_NETWORKS['ETH']['rpc_url']))
            
            # Tron
            if config.SUPPORTED_NETWORKS['TRX']['rpc_url']:
                self.tron_client = Tron(network='mainnet')
            
            # Solana
            if config.SUPPORTED_NETWORKS['SOL']['rpc_url']:
                self.solana_client = Client(config.SUPPORTED_NETWORKS['SOL']['rpc_url'])
                
        except Exception as e:
            print(f"Error initializing clients: {e}")
    
    def generate_wallet(self, network: str, count: int = 1) -> List[Dict]:
        """Generate wallets for specified network"""
        wallets = []
        
        try:
            for i in range(count):
                # Generate mnemonic
                mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12)
                seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
                
                # Generate wallet based on network
                if network == 'ETH':
                    wallet = self._generate_eth_wallet(seed_bytes, i)
                elif network == 'TRX':
                    wallet = self._generate_trx_wallet(seed_bytes, i)
                elif network == 'SOL':
                    wallet = self._generate_sol_wallet(seed_bytes, i)
                elif network == 'BNB':
                    wallet = self._generate_bnb_wallet(seed_bytes, i)
                elif network == 'DOGE':
                    wallet = self._generate_doge_wallet(seed_bytes, i)
                elif network == 'AVAX':
                    wallet = self._generate_avax_wallet(seed_bytes, i)
                elif network == 'POL':
                    wallet = self._generate_pol_wallet(seed_bytes, i)
                elif network == 'XRP':
                    wallet = self._generate_xrp_wallet(seed_bytes, i)
                else:
                    raise ValueError(f"Unsupported network: {network}")
                
                wallets.append(wallet)
                
        except Exception as e:
            print(f"Error generating wallet: {e}")
            raise
        
        return wallets
    
    def _generate_eth_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate Ethereum wallet"""
        bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM).DeriveDefaultPath()
        private_key = bip44_ctx.PrivateKey().Raw().ToHex()
        address = bip44_ctx.PublicKey().ToAddress()
        
        return {
            'network': 'ETH',
            'address': address,
            'private_key': private_key,
            'seed_phrase': ' '.join(bip44_ctx.Mnemonic().ToWords())
        }
    
    def _generate_trx_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate Tron wallet"""
        bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON).DeriveDefaultPath()
        private_key = bip44_ctx.PrivateKey().Raw().ToHex()
        address = bip44_ctx.PublicKey().ToAddress()
        
        return {
            'network': 'TRX',
            'address': address,
            'private_key': private_key,
            'seed_phrase': ' '.join(bip44_ctx.Mnemonic().ToWords())
        }
    
    def _generate_sol_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate Solana wallet"""
        bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA).DeriveDefaultPath()
        private_key = base58.b58encode(bip44_ctx.PrivateKey().Raw().ToBytes()).decode()
        address = bip44_ctx.PublicKey().ToAddress()
        
        return {
            'network': 'SOL',
            'address': address,
            'private_key': private_key,
            'seed_phrase': ' '.join(bip44_ctx.Mnemonic().ToWords())
        }
    
    def _generate_bnb_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate BNB wallet (same as ETH)"""
        return self._generate_eth_wallet(seed_bytes, index)
    
    def _generate_doge_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate Dogecoin wallet"""
        bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.DOGECOIN).DeriveDefaultPath()
        private_key = bip44_ctx.PrivateKey().Raw().ToHex()
        address = bip44_ctx.PublicKey().ToAddress()
        
        return {
            'network': 'DOGE',
            'address': address,
            'private_key': private_key,
            'seed_phrase': ' '.join(bip44_ctx.Mnemonic().ToWords())
        }
    
    def _generate_avax_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate Avalanche wallet (same as ETH)"""
        return self._generate_eth_wallet(seed_bytes, index)
    
    def _generate_pol_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate Polygon wallet (same as ETH)"""
        return self._generate_eth_wallet(seed_bytes, index)
    
    def _generate_xrp_wallet(self, seed_bytes: bytes, index: int) -> Dict:
        """Generate XRP wallet"""
        bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.RIPPLE).DeriveDefaultPath()
        private_key = bip44_ctx.PrivateKey().Raw().ToHex()
        address = bip44_ctx.PublicKey().ToAddress()
        
        return {
            'network': 'XRP',
            'address': address,
            'private_key': private_key,
            'seed_phrase': ' '.join(bip44_ctx.Mnemonic().ToWords())
        }
    
    async def get_balance(self, address: str, network: str, token_type: str = None) -> float:
        """Get balance for address and network"""
        try:
            if network == 'ETH':
                return await self._get_eth_balance(address, token_type)
            elif network == 'TRX':
                return await self._get_trx_balance(address, token_type)
            elif network == 'SOL':
                return await self._get_sol_balance(address)
            elif network == 'BNB':
                return await self._get_bnb_balance(address)
            elif network == 'DOGE':
                return await self._get_doge_balance(address)
            elif network == 'AVAX':
                return await self._get_avax_balance(address)
            elif network == 'POL':
                return await self._get_pol_balance(address)
            elif network == 'XRP':
                return await self._get_xrp_balance(address)
            else:
                return 0.0
        except Exception as e:
            print(f"Error getting balance for {address} on {network}: {e}")
            return 0.0
    
    async def _get_eth_balance(self, address: str, token_type: str = None) -> float:
        """Get Ethereum balance"""
        if not self.web3_eth:
            return 0.0
        
        try:
            if token_type == 'USDT':
                # Get USDT balance
                contract_address = config.SUPPORTED_NETWORKS['ETH']['usdt_contract']
                contract_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'
                contract = self.web3_eth.eth.contract(address=contract_address, abi=contract_abi)
                balance = contract.functions.balanceOf(address).call()
                return balance / (10 ** 6)  # USDT has 6 decimals
            else:
                # Get ETH balance
                balance = self.web3_eth.eth.get_balance(address)
                return balance / (10 ** 18)  # ETH has 18 decimals
        except Exception as e:
            print(f"Error getting ETH balance: {e}")
            return 0.0
    
    async def _get_trx_balance(self, address: str, token_type: str = None) -> float:
        """Get Tron balance"""
        if not self.tron_client:
            return 0.0
        
        try:
            if token_type == 'USDT':
                # Get USDT balance
                contract_address = config.SUPPORTED_NETWORKS['TRX']['usdt_contract']
                contract = self.tron_client.get_contract(contract_address)
                balance = contract.functions.balanceOf(address)
                return balance / (10 ** 6)  # USDT has 6 decimals
            else:
                # Get TRX balance
                account = self.tron_client.get_account(address)
                return account.balance / (10 ** 6)  # TRX has 6 decimals
        except Exception as e:
            print(f"Error getting TRX balance: {e}")
            return 0.0
    
    async def _get_sol_balance(self, address: str) -> float:
        """Get Solana balance"""
        if not self.solana_client:
            return 0.0
        
        try:
            response = self.solana_client.get_balance(address)
            if response.value:
                return response.value / (10 ** 9)  # SOL has 9 decimals
            return 0.0
        except Exception as e:
            print(f"Error getting SOL balance: {e}")
            return 0.0
    
    async def _get_bnb_balance(self, address: str) -> float:
        """Get BNB balance"""
        try:
            async with aiohttp.ClientSession() as session:
                url = config.SUPPORTED_NETWORKS['BNB']['rpc_url']
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                async with session.post(url, json=payload) as response:
                    data = await response.json()
                    if 'result' in data:
                        balance = int(data['result'], 16)
                        return balance / (10 ** 18)
            return 0.0
        except Exception as e:
            print(f"Error getting BNB balance: {e}")
            return 0.0
    
    async def _get_doge_balance(self, address: str) -> float:
        """Get Dogecoin balance"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config.SUPPORTED_NETWORKS['DOGE']['rpc_url']}/get_address_balance/DOGE/{address}"
                async with session.get(url) as response:
                    data = await response.json()
                    if data['status'] == 'success':
                        return float(data['data']['confirmed_balance'])
            return 0.0
        except Exception as e:
            print(f"Error getting DOGE balance: {e}")
            return 0.0
    
    async def _get_avax_balance(self, address: str) -> float:
        """Get Avalanche balance"""
        try:
            async with aiohttp.ClientSession() as session:
                url = config.SUPPORTED_NETWORKS['AVAX']['rpc_url']
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                async with session.post(url, json=payload) as response:
                    data = await response.json()
                    if 'result' in data:
                        balance = int(data['result'], 16)
                        return balance / (10 ** 18)
            return 0.0
        except Exception as e:
            print(f"Error getting AVAX balance: {e}")
            return 0.0
    
    async def _get_pol_balance(self, address: str) -> float:
        """Get Polygon balance"""
        try:
            async with aiohttp.ClientSession() as session:
                url = config.SUPPORTED_NETWORKS['POL']['rpc_url']
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                async with session.post(url, json=payload) as response:
                    data = await response.json()
                    if 'result' in data:
                        balance = int(data['result'], 16)
                        return balance / (10 ** 18)
            return 0.0
        except Exception as e:
            print(f"Error getting POL balance: {e}")
            return 0.0
    
    async def _get_xrp_balance(self, address: str) -> float:
        """Get XRP balance"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config.SUPPORTED_NETWORKS['XRP']['rpc_url']}/account/{address}"
                async with session.get(url) as response:
                    data = await response.json()
                    if 'account_data' in data:
                        balance = int(data['account_data']['Balance'])
                        return balance / (10 ** 6)  # XRP has 6 decimals
            return 0.0
        except Exception as e:
            print(f"Error getting XRP balance: {e}")
            return 0.0
    
    async def get_all_balances(self, user_id: int) -> Dict[str, Dict]:
        """Get all balances for user's wallets"""
        wallets = self.db.get_user_wallets(user_id)
        balances = {}
        
        for wallet in wallets:
            network = wallet['network']
            address = wallet['address']
            
            if network not in balances:
                balances[network] = {}
            
            # Get native token balance
            native_balance = await self.get_balance(address, network)
            balances[network][address] = {
                'native': native_balance,
                'symbol': config.SUPPORTED_NETWORKS[network]['symbol']
            }
            
            # Get USDT balance if supported
            if config.SUPPORTED_NETWORKS[network]['supports_usdt']:
                usdt_balance = await self.get_balance(address, network, 'USDT')
                balances[network][address]['USDT'] = usdt_balance
        
        return balances
    
    def validate_address(self, address: str, network: str) -> bool:
        """Validate address format for network"""
        try:
            if network == 'ETH':
                return Web3.is_address(address)
            elif network == 'TRX':
                return address.startswith('T') and len(address) == 34
            elif network == 'SOL':
                return len(address) == 44 and address.isalnum()
            elif network == 'BNB':
                return Web3.is_address(address)
            elif network == 'DOGE':
                return address.startswith('D') and len(address) >= 26
            elif network == 'AVAX':
                return Web3.is_address(address)
            elif network == 'POL':
                return Web3.is_address(address)
            elif network == 'XRP':
                return address.startswith('r') and len(address) >= 25
            else:
                return False
        except:
            return False