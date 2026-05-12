/** LexChain Sovereign - Web3 Integration */
class LexWeb3 {
  static provider = null;
  static account = null;
  static chainId = null;

  static async connect() {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        this.account = accounts[0];
        this.chainId = await window.ethereum.request({ method: 'eth_chainId' });
        this.provider = window.ethereum;

        window.ethereum.on('accountsChanged', (accounts) => {
          this.account = accounts[0] || null;
          this.emit('accountChanged', this.account);
        });

        window.ethereum.on('chainChanged', (chainId) => {
          this.chainId = chainId;
          this.emit('chainChanged', chainId);
        });

        return { account: this.account, chainId: this.chainId };
      } catch (error) {
        console.error('MetaMask connection failed:', error);
        throw error;
      }
    }
    throw new Error('MetaMask not installed');
  }

  static async disconnect() {
    this.account = null;
    this.provider = null;
    this.chainId = null;
    this.emit('disconnected');
  }

  static isConnected() {
    return this.account !== null;
  }

  static async switchNetwork(chainId) {
    const networks = {
      '1': { chainId: '0x1', chainName: 'Ethereum Mainnet', rpcUrls: ['https://mainnet.infura.io/v3/'] },
      '11155111': { chainId: '0xaa36a7', chainName: 'Sepolia Testnet', rpcUrls: ['https://sepolia.infura.io/v3/'] },
      '137': { chainId: '0x89', chainName: 'Polygon Mainnet', rpcUrls: ['https://polygon-rpc.com/'] },
      '8453': { chainId: '0x2105', chainName: 'Base', rpcUrls: ['https://mainnet.base.org/'] },
      '42161': { chainId: '0xa4b1', chainName: 'Arbitrum One', rpcUrls: ['https://arb1.arbitrum.io/rpc/'] }
    };

    const network = networks[chainId];
    if (!network) throw new Error('Unsupported network');

    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: network.chainId }]
      });
    } catch (error) {
      if (error.code === 4902) {
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [network]
        });
      }
      throw error;
    }
  }

  static async signMessage(message) {
    if (!this.account) throw new Error('Not connected');

    const msg = typeof message === 'string' ? message : JSON.stringify(message);
    const signature = await window.ethereum.request({
      method: 'personal_sign',
      params: [msg, this.account]
    });

    return signature;
  }

  static async verifySignature(message, signature, address = this.account) {
    const msg = typeof message === 'string' ? message : JSON.stringify(message);
    const recovered = await window.ethereum.request({
      method: 'personal_ecRecover',
      params: [msg, signature]
    });
    return recovered.toLowerCase() === address.toLowerCase();
  }

  static async sendTransaction(to, value = 0, data = '0x') {
    if (!this.account) throw new Error('Not connected');

    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [{
        from: this.account,
        to,
        value: '0x' + (BigInt(value).toString(16)),
        data
      }]
    });

    return txHash;
  }

  static async getTransactionReceipt(txHash) {
    const receipt = await window.ethereum.request({
      method: 'eth_getTransactionReceipt',
      params: [txHash]
    });
    return receipt;
  }

  static async waitForTransaction(txHash, timeout = 30000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      const receipt = await this.getTransactionReceipt(txHash);
      if (receipt) return receipt;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    throw new Error('Transaction timeout');
  }

  static getChainName(chainId = this.chainId) {
    const chains = {
      '0x1': 'Ethereum',
      '0xaa36a7': 'Sepolia',
      '0x89': 'Polygon',
      '0x2105': 'Base',
      '0xa4b1': 'Arbitrum'
    };
    return chains[chainId] || 'Unknown';
  }

  static formatAddress(address) {
    if (!address) return '';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  }

  static listeners = {};

  static on(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  static emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

window.LexWeb3 = LexWeb3;