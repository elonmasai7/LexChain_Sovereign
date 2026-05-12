"""Web3 blockchain helper utilities."""
from typing import Optional, Dict, Any
from web3 import Web3
from eth_account import Account
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class Web3Helper:
    """Web3 blockchain interaction helper."""

    def __init__(self):
        self.web3 = None
        if settings.WEB3_PROVIDER_URL:
            self.web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))

    @property
    def is_connected(self) -> bool:
        """Check if connected to blockchain."""
        if not self.web3:
            return False
        return self.web3.is_connected()

    def get_chain_id(self) -> int:
        """Get current chain ID."""
        if self.web3:
            return self.web3.eth.chain_id
        return 1

    def get_chain_name(self, chain_id: int) -> str:
        """Get chain name from ID."""
        chains = {
            1: "ethereum",
            11155111: "sepolia",
            137: "polygon",
            8453: "base",
            42161: "arbitrum"
        }
        return chains.get(chain_id, "unknown")

    def is_valid_address(self, address: str) -> bool:
        """Check if address is valid."""
        if not self.web3:
            return False
        return self.web3.is_address(address)

    def to_checksum_address(self, address: str) -> str:
        """Convert address to checksum format."""
        if not self.web3:
            return address
        return self.web3.to_checksum_address(address)

    def sign_message(self, message: str, private_key: str) -> str:
        """Sign a message with a private key."""
        account = Account.from_key(private_key)
        signed = account.sign_message(message)
        return signed.signature.hex()

    def verify_signature(self, message: str, signature: str, address: str) -> bool:
        """Verify a signature."""
        try:
            recovered = Account.recover_message(message, signature)
            return recovered == address
        except Exception:
            return False

    async def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction details."""
        if not self.web3:
            return None
        try:
            return self.web3.eth.get_transaction(tx_hash)
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
            return None

    async def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction receipt."""
        if not self.web3:
            return None
        try:
            return self.web3.eth.get_transaction_receipt(tx_hash)
        except Exception as e:
            logger.error(f"Failed to get receipt: {e}")
            return None

    async def send_transaction(
        self,
        from_address: str,
        to_address: str,
        value: int = 0,
        data: bytes = None,
        gas: int = None,
        private_key: str = None
    ) -> Optional[str]:
        """Send a transaction."""
        if not self.web3:
            return None

        try:
            tx = {
                "from": from_address,
                "to": to_address,
                "value": value,
                "data": data or b"",
                "chainId": self.get_chain_id()
            }

            if gas:
                tx["gas"] = gas
            else:
                tx["gas"] = self.web3.eth.estimate_gas(tx)

            if not private_key:
                return None

            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            return None

    async def estimate_gas(self, from_address: str, to_address: str, value: int = 0, data: bytes = None) -> int:
        """Estimate gas for a transaction."""
        if not self.web3:
            return 21000

        try:
            tx = {
                "from": from_address,
                "to": to_address,
                "value": value,
                "data": data or b""
            }
            return self.web3.eth.estimate_gas(tx)
        except Exception:
            return 21000

    def call_contract_function(
        self,
        contract_address: str,
        abi: list,
        function_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Call a contract function."""
        if not self.web3:
            return None

        try:
            contract = self.web3.eth.contract(address=contract_address, abi=abi)
            function = getattr(contract.functions, function_name)
            return function(*args).call(**kwargs)
        except Exception as e:
            logger.error(f"Contract call failed: {e}")
            return None


web3_helper = Web3Helper()