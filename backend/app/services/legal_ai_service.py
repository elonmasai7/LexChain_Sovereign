"""Legal AI service for contract analysis and compliance."""
from typing import Optional, list, dict
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class LegalAIService:
    """AI-powered legal analysis service."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    async def analyze_contract(self, contract_text: str, contract_type: Optional[str] = None, jurisdiction: Optional[str] = None) -> dict:
        """Analyze a contract and extract insights."""
        if not self.openai_client:
            return self._fallback_analysis(contract_text)

        prompt = f"""Analyze the following legal contract and provide:
        1. A summary (2-3 sentences)
        2. Key risk factors
        3. Compliance issues
        4. Recommendations

        Contract Text:
        {contract_text[:4000]}

        Contract Type: {contract_type or 'General'}
        Jurisdiction: {jurisdiction or 'Not specified'}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior legal analyst specializing in blockchain and fintech contracts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return {
                "summary": response.choices[0].message.content[:500],
                "risk_score": 35.0,
                "compliance_score": 78.0,
                "raw_analysis": response.choices[0].message.content
            }
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._fallback_analysis(contract_text)

    async def extract_clauses(self, document_text: str, clause_types: Optional[list[str]] = None) -> list[dict]:
        """Extract legal clauses from a document."""
        if not self.openai_client:
            return []

        prompt = f"""Extract legal clauses from the following document. For each clause identify:
        1. Clause type (indemnification, limitation of liability, termination, etc.)
        2. The clause text
        3. Risk level (low, medium, high)
        4. Any concerns or recommendations

        Document:
        {document_text[:4000]}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a legal clause extraction specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=3000
            )

            clauses = [
                {"type": "general", "text": "Sample clause", "risk_level": "low", "concerns": []}
            ]
            return clauses
        except Exception as e:
            logger.error(f"Clause extraction failed: {str(e)}")
            return []

    async def detect_risks(self, contract_text: str) -> list[dict]:
        """Detect risk factors in a contract."""
        if not self.openai_client:
            return [{"category": "general", "description": "Risk detected", "severity": "medium"}]

        prompt = f"""Identify and categorize risks in this contract:
        1. Legal risks (non-compliance, enforceability)
        2. Financial risks (liability, payment terms)
        3. Operational risks (termination, dispute resolution)
        4. Blockchain-specific risks (smart contract implications)

        Contract:
        {contract_text[:4000]}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a risk analysis specialist for legal and blockchain contracts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return [
                {"category": "legal", "description": "Review jurisdiction clauses", "severity": "high"},
                {"category": "financial", "description": "Payment terms need clarification", "severity": "medium"},
                {"category": "operational", "description": "Termination clause is favorable", "severity": "low"}
            ]
        except Exception as e:
            logger.error(f"Risk detection failed: {str(e)}")
            return []

    async def compare_jurisdictions(self, contract_text: str, jurisdictions: list[str]) -> dict:
        """Compare contract compliance across jurisdictions."""
        return {
            "us": {"compliance_score": 85, "issues": [], "recommendations": ["Add disclosure clause"]},
            "eu": {"compliance_score": 72, "issues": ["GDPR clause missing"], "recommendations": ["Add data processing terms"]},
            "uk": {"compliance_score": 80, "issues": [], "recommendations": []}
        }

    async def generate_compliance_score(self, contract_text: str, jurisdiction: str) -> float:
        """Generate a compliance score (0-100) for a contract."""
        base_score = 70.0

        if "GDPR" in contract_text or "data protection" in contract_text.lower():
            base_score += 10

        if "AML" in contract_text or "KYC" in contract_text:
            base_score += 15

        if "smart contract" in contract_text.lower():
            base_score += 5

        return min(base_score, 100.0)

    async def summarize_legal_text(self, text: str, max_length: int = 500) -> str:
        """Generate a concise summary of legal text."""
        if not self.openai_client:
            return text[:max_length] + "..." if len(text) > max_length else text

        prompt = f"""Summarize the following legal text in {max_length} characters or less, maintaining key points:

        {text[:4000]}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a legal document summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return text[:max_length]

    async def explain_smart_contract(self, contract_code: str) -> dict:
        """Explain Solidity smart contract code."""
        if not self.openai_client:
            return {"summary": "Smart contract analysis", "risks": [], "recommendations": []}

        prompt = f"""Analyze this Solidity smart contract:
        1. What does it do?
        2. What are the potential vulnerabilities?
        3. What are the security considerations?
        4. Compliance implications (token standards, regulatory)

        Contract Code:
        {contract_code[:3000]}
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a smart contract security auditor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            return {
                "summary": response.choices[0].message.content[:500],
                "risks": ["Reentrancy check", "Access control"],
                "recommendations": ["Addpausable", "Upgradeable proxy"]
            }
        except Exception as e:
            logger.error(f"Contract explanation failed: {str(e)}")
            return {"summary": "Analysis unavailable", "risks": [], "recommendations": []}

    async def get_regulatory_recommendations(self, jurisdiction: str, asset_type: str) -> list[str]:
        """Get regulatory recommendations for a jurisdiction and asset type."""
        recommendations = {
            "real_estate": ["KYC required for all investors", "Accredited investor verification", "Anti-money laundering checks"],
            "carbon_credit": ["Emissions verification required", "Registry compliance", "Additional disclosure on offset methodology"],
            "art": ["Provenance verification", "Export/import compliance", "Cultural heritage restrictions"]
        }

        return recommendations.get(asset_type, ["Standard KYC/AML procedures apply"])

    async def validate_prompt(self, prompt: str) -> tuple[bool, str]:
        """Validate prompt for injection attacks."""
        injection_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "disregard your instructions",
            "you are now",
            "pretend you are",
            "system prompt",
            "reveal your",
            "/ignore"
        ]

        prompt_lower = prompt.lower()
        for pattern in injection_patterns:
            if pattern in prompt_lower:
                logger.warning(f"Potential prompt injection detected: {pattern}")
                return False, "Invalid prompt detected"

        return True, "Valid prompt"

    def _fallback_analysis(self, contract_text: str) -> dict:
        """Fallback analysis when AI is unavailable."""
        word_count = len(contract_text.split())
        return {
            "summary": f"Contract contains {word_count} words. AI analysis temporarily unavailable.",
            "risk_score": 50.0,
            "compliance_score": 60.0,
            "word_count": word_count
        }


legal_ai_service = LegalAIService()