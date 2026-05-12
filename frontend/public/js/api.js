/** LexChain Sovereign - API Client */
class LexAPI {
  static baseURL = '/api/v1';
  static token = null;

  static getToken() {
    if (!this.token) {
      this.token = localStorage.getItem('lex_access_token');
    }
    return this.token;
  }

  static setToken(token) {
    this.token = token;
    localStorage.setItem('lex_access_token', token);
  }

  static clearToken() {
    this.token = null;
    localStorage.removeItem('lex_access_token');
    localStorage.removeItem('lex_refresh_token');
  }

  static async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (response.status === 401) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers['Authorization'] = `Bearer ${this.getToken()}`;
          return fetch(url, { ...options, headers });
        }
        this.clearToken();
        window.location.href = '/login';
        return null;
      }

      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  static async refreshToken() {
    const refreshToken = localStorage.getItem('lex_refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        this.setToken(data.access_token);
        localStorage.setItem('lex_refresh_token', data.refresh_token);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  // Auth endpoints
  static async login(email, password, remember = false) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password, remember_me: remember })
    });
    if (response && response.ok) {
      const data = await response.json();
      this.setToken(data.access_token);
      localStorage.setItem('lex_refresh_token', data.refresh_token);
      return data;
    }
    return null;
  }

  static async register(userData) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    return response ? await response.json() : null;
  }

  static async logout() {
    await this.request('/auth/logout', { method: 'POST' });
    this.clearToken();
  }

  static async getCurrentUser() {
    const response = await this.request('/auth/me');
    return response ? await response.json() : null;
  }

  // Asset endpoints
  static async getAssets(params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await this.request(`/assets${query ? `?${query}` : ''}`);
    return response ? await response.json() : null;
  }

  static async getAsset(id) {
    const response = await this.request(`/assets/${id}`);
    return response ? await response.json() : null;
  }

  static async createAsset(data) {
    const response = await this.request('/assets', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response ? await response.json() : null;
  }

  static async updateAsset(id, data) {
    const response = await this.request(`/assets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
    return response ? await response.json() : null;
  }

  static async tokenizeAsset(id, tokenizationData) {
    const response = await this.request(`/assets/${id}/tokenize`, {
      method: 'POST',
      body: JSON.stringify(tokenizationData)
    });
    return response ? await response.json() : null;
  }

  // Document endpoints
  static async getDocuments(params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await this.request(`/documents${query ? `?${query}` : ''}`);
    return response ? await response.json() : null;
  }

  static async createDocument(data) {
    const response = await this.request('/documents', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response ? await response.json() : null;
  }

  static async signDocument(id, signatureData) {
    const response = await this.request(`/documents/${id}/sign`, {
      method: 'POST',
      body: JSON.stringify(signatureData)
    });
    return response ? await response.json() : null;
  }

  static async anchorDocument(id, txHash, chainId = 1) {
    const response = await this.request(`/documents/${id}/anchor`, {
      method: 'POST',
      body: JSON.stringify({ tx_hash: txHash, chain_id: chainId })
    });
    return response ? await response.json() : null;
  }

  // Compliance endpoints
  static async runComplianceCheck(checkType, userId, data = {}) {
    const response = await this.request(`/compliance/${checkType}`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, ...data })
    });
    return response ? await response.json() : null;
  }

  static async getComplianceStatus(userId) {
    const response = await this.request(`/compliance/status/${userId}`);
    return response ? await response.json() : null;
  }

  static async getRiskScore(userId) {
    const response = await this.request(`/compliance/risk-score/${userId}`);
    return response ? await response.json() : null;
  }

  // Legal AI endpoints
  static async analyzeContract(contractText, options = {}) {
    const response = await this.request('/legal-ai/analyze', {
      method: 'POST',
      body: JSON.stringify({ contract_text: contractText, ...options })
    });
    return response ? await response.json() : null;
  }

  static async extractClauses(documentText, clauseTypes = null) {
    const response = await this.request('/legal-ai/clauses', {
      method: 'POST',
      body: JSON.stringify({ document_text: documentText, clause_types: clauseTypes })
    });
    return response ? await response.json() : null;
  }

  static async detectRisks(contractText) {
    const response = await this.request('/legal-ai/risks', {
      method: 'POST',
      body: JSON.stringify({ contract_text: contractText })
    });
    return response ? await response.json() : null;
  }

  // Governance endpoints
  static async getProposals(params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await this.request(`/governance/proposals${query ? `?${query}` : ''}`);
    return response ? await response.json() : null;
  }

  static async createProposal(data) {
    const response = await this.request('/governance/proposals', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response ? await response.json() : null;
  }

  static async castVote(proposalId, choice, weight = 1, reason = null) {
    const response = await this.request(`/governance/proposals/${proposalId}/vote`, {
      method: 'POST',
      body: JSON.stringify({ choice, weight, reason })
    });
    return response ? await response.json() : null;
  }

  // Evidence endpoints
  static async getEvidence(params = {}) {
    const query = new URLSearchParams(params).toString();
    const response = await this.request(`/evidence${query ? `?${query}` : ''}`);
    return response ? await response.json() : null;
  }

  static async storeEvidence(data) {
    const response = await this.request('/evidence', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response ? await response.json() : null;
  }

  static async verifyEvidence(evidenceId, fileHash) {
    const response = await this.request(`/evidence/${evidenceId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ file_content_hash: fileHash })
    });
    return response ? await response.json() : null;
  }

  // DID endpoints
  static async createDID(method = 'ethr', network = 'mainnet') {
    const response = await this.request('/did/create', {
      method: 'POST',
      body: JSON.stringify({ method, network })
    });
    return response ? await response.json() : null;
  }

  static async issueCredential(issuerDID, holderDID, credentialType, claims) {
    const response = await this.request('/did/issue-credential', {
      method: 'POST',
      body: JSON.stringify({ issuer_did: issuerDID, holder_did: holderDID, credential_type: credentialType, claims })
    });
    return response ? await response.json() : null;
  }

  // Analytics endpoints
  static async getDashboardMetrics() {
    const response = await this.request('/analytics/dashboard');
    return response ? await response.json() : null;
  }

  static async getComplianceMetrics() {
    const response = await this.request('/analytics/compliance');
    return response ? await response.json() : null;
  }

  static async getGovernanceActivity() {
    const response = await this.request('/analytics/governance');
    return response ? await response.json() : null;
  }
}

window.LexAPI = LexAPI;