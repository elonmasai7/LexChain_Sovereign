// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract LegalEvidenceStore is AccessControlEnumerable, Pausable {
    struct Evidence {
        bytes32 fileHash;
        uint256 timestamp;
        address uploadedBy;
        uint256 chainId;
        bytes32 ipfsCid;
        bytes32 blockchainAnchor;
        uint256 verificationCount;
        bool verified;
        bytes metadata;
    }

    bytes32 public constant EVIDENCE_MANAGER_ROLE = keccak256("EVIDENCE_MANAGER_ROLE");
    
    mapping(bytes32 => Evidence) public evidenceStore;
    mapping(bytes32 => mapping(address => bool)) public verificationHistory;
    mapping(bytes32 => address[]) public verifierList;
    
    event EvidenceStored(
        bytes32 indexed evidenceId,
        bytes32 indexed fileHash,
        uint256 timestamp,
        address indexed uploader
    );
    event EvidenceAnchored(bytes32 indexed evidenceId, bytes32 anchor, uint256 chainId);
    event EvidenceVerified(bytes32 indexed evidenceId, address indexed verifier, bool isValid);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(EVIDENCE_MANAGER_ROLE, msg.sender);
    }

    modifier onlyEvidenceManager() {
        require(
            hasRole(EVIDENCE_MANAGER_ROLE, msg.sender) || 
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not evidence manager"
        );
        _;
    }

    function storeEvidence(
        bytes32 evidenceId,
        bytes32 fileHash,
        bytes memory metadata
    ) 
        external 
        onlyEvidenceManager 
        whenNotPaused 
    {
        require(evidenceStore[evidenceId].timestamp == 0, "Evidence exists");

        evidenceStore[evidenceId] = Evidence({
            fileHash: fileHash,
            timestamp: block.timestamp,
            uploadedBy: msg.sender,
            chainId: 0,
            ipfsCid: bytes32(0),
            blockchainAnchor: bytes32(0),
            verificationCount: 0,
            verified: false,
            metadata: metadata
        });

        emit EvidenceStored(evidenceId, fileHash, block.timestamp, msg.sender);
    }

    function anchorToChain(
        bytes32 evidenceId,
        bytes32 anchor,
        uint256 chainId
    ) 
        external 
        onlyEvidenceManager 
        whenNotPaused 
    {
        require(evidenceStore[evidenceId].timestamp > 0, "Evidence not stored");

        evidenceStore[evidenceId].blockchainAnchor = anchor;
        evidenceStore[evidenceId].chainId = chainId;

        emit EvidenceAnchored(evidenceId, anchor, chainId);
    }

    function verifyEvidence(
        bytes32 evidenceId,
        bytes32 providedHash
    ) 
        external 
        onlyEvidenceManager 
        returns (bool) 
    {
        require(evidenceStore[evidenceId].timestamp > 0, "Evidence not stored");
        
        bool isValid = keccak256(abi.encodePacked(providedHash)) == 
                       keccak256(abi.encodePacked(evidenceStore[evidenceId].fileHash));

        evidenceStore[evidenceId].verificationCount += 1;
        verificationHistory[evidenceId][msg.sender] = isValid;
        verifierList[evidenceId].push(msg.sender);

        if (isValid) {
            evidenceStore[evidenceId].verified = true;
        }

        emit EvidenceVerified(evidenceId, msg.sender, isValid);
        return isValid;
    }

    function getEvidence(bytes32 evidenceId) 
        external 
        view 
        returns (Evidence memory) 
    {
        return evidenceStore[evidenceId];
    }

    function getVerificationCount(bytes32 evidenceId) 
        external 
        view 
        returns (uint256) 
    {
        return evidenceStore[evidenceId].verificationCount;
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}