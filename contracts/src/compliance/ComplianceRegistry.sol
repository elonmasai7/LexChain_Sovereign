// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract ComplianceRegistry is AccessControlEnumerable, Pausable {
    enum ComplianceLevel { None, Basic, Enhanced, Full }
    
    struct ComplianceRecord {
        uint256 kycLevel;
        uint256 amlScore;
        bool sanctionsHit;
        uint256 riskLevel;
        uint256 lastUpdate;
        address verifier;
        bytes additionalData;
    }

    bytes32 public constant COMPLIANCE_OFFICER_ROLE = keccak256("COMPLIANCE_OFFICER_ROLE");
    
    mapping(address => ComplianceRecord) public complianceRecords;
    mapping(address => bool) public sanctionedAddresses;
    mapping(address => bool) public verifiedIssuers;
    
    event ComplianceUpdated(
        address indexed user,
        uint256 kycLevel,
        uint256 amlScore,
        uint256 indexed riskLevel
    );
    event SanctionHit(address indexed user, bool hit);
    event IssuerVerified(address indexed issuer, bool verified);
    event RiskAlert(address indexed user, uint256 indexed riskLevel);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(COMPLIANCE_OFFICER_ROLE, msg.sender);
    }

    modifier onlyComplianceOfficer() {
        require(
            hasRole(COMPLIANCE_OFFICER_ROLE, msg.sender) || 
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not compliance officer"
        );
        _;
    }

    function updateCompliance(
        address user,
        uint256 kycLevel,
        uint256 amlScore,
        bool sanctionsHit,
        uint256 riskLevel,
        bytes memory additionalData
    ) 
        external 
        onlyComplianceOfficer 
        whenNotPaused 
    {
        complianceRecords[user] = ComplianceRecord({
            kycLevel: kycLevel,
            amlScore: amlScore,
            sanctionsHit: sanctionsHit,
            riskLevel: riskLevel,
            lastUpdate: block.timestamp,
            verifier: msg.sender,
            additionalData: additionalData
        });

        if (riskLevel >= 75) {
            emit RiskAlert(user, riskLevel);
        }

        emit ComplianceUpdated(user, kycLevel, amlScore, riskLevel);
    }

    function checkInvestorEligibility(address user) external view returns (bool) {
        ComplianceRecord memory record = complianceRecords[user];
        
        if (record.kycLevel < 2) return false;
        if (record.sanctionsHit) return false;
        if (record.riskLevel >= 75) return false;
        
        return true;
    }

    function setSanctionHit(address user, bool hit) 
        external 
        onlyComplianceOfficer 
    {
        sanctionedAddresses[user] = hit;
        complianceRecords[user].sanctionsHit = hit;
        emit SanctionHit(user, hit);
    }

    function verifyIssuer(address issuer, bool verified) 
        external 
        onlyComplianceOfficer 
    {
        verifiedIssuers[issuer] = verified;
        emit IssuerVerified(issuer, verified);
    }

    function getComplianceRecord(address user) 
        external 
        view 
        returns (ComplianceRecord memory) 
    {
        return complianceRecords[user];
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}