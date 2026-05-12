"""Legal AI analysis API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services.legal_ai_service import legal_ai_service
from app.schemas.document import (
    ContractAnalysisRequest, ContractAnalysisResponse,
    ClauseExtractionRequest, ClauseExtractionResponse,
    JurisdictionComparisonRequest
)
from app.models.user import User


router = APIRouter()


@router.post("/analyze", response_model=ContractAnalysisResponse)
async def analyze_contract(
    analysis_request: ContractAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze a legal contract and extract insights."""
    is_valid, message = await legal_ai_service.validate_prompt(analysis_request.contract_text)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    result = await legal_ai_service.analyze_contract(
        analysis_request.contract_text,
        analysis_request.contract_type,
        analysis_request.jurisdiction
    )

    risk_score = result.get("risk_score", 50.0)
    compliance_score = result.get("compliance_score", 60.0)

    return ContractAnalysisResponse(
        summary=result.get("summary", "Analysis complete"),
        risk_score=risk_score,
        risk_factors=[
            {"category": "general", "description": "Review required", "severity": "medium"}
        ],
        clauses=[],
        compliance_score=compliance_score,
        recommendations=["Ensure all parties have signed", "Add dispute resolution clause"],
        jurisdiction_comparison=None
    )


@router.post("/clauses", response_model=ClauseExtractionResponse)
async def extract_clauses(
    extraction_request: ClauseExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Extract legal clauses from a document."""
    clauses = await legal_ai_service.extract_clauses(
        extraction_request.document_text,
        extraction_request.clause_types
    )

    return ClauseExtractionResponse(
        clauses=clauses,
        total_count=len(clauses),
        categories={}
    )


@router.post("/risks")
async def detect_risks(
    contract_text: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Detect risk factors in a contract."""
    risks = await legal_ai_service.detect_risks(contract_text)
    return {"risks": risks, "total_count": len(risks)}


@router.post("/compare-jurisdictions")
async def compare_jurisdictions(
    comparison_request: JurisdictionComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Compare contract compliance across jurisdictions."""
    result = await legal_ai_service.compare_jurisdictions(
        comparison_request.contract_text,
        comparison_request.jurisdictions
    )
    return result


@router.post("/compliance-score")
async def get_compliance_score(
    contract_text: str,
    jurisdiction: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a compliance score for a contract."""
    score = await legal_ai_service.generate_compliance_score(contract_text, jurisdiction)
    return {"score": score, "jurisdiction": jurisdiction}


@router.post("/summarize")
async def summarize_legal_text(
    text: str,
    max_length: int = 500,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a concise summary of legal text."""
    summary = await legal_ai_service.summarize_legal_text(text, max_length)
    return {"summary": summary}


@router.post("/explain-contract")
async def explain_smart_contract(
    contract_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Explain Solidity smart contract code."""
    result = await legal_ai_service.explain_smart_contract(contract_code)
    return result


@router.get("/recommendations/{jurisdiction}/{asset_type}")
async def get_regulatory_recommendations(
    jurisdiction: str,
    asset_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get regulatory recommendations for a jurisdiction and asset type."""
    recommendations = await legal_ai_service.get_regulatory_recommendations(jurisdiction, asset_type)
    return {"recommendations": recommendations, "jurisdiction": jurisdiction, "asset_type": asset_type}