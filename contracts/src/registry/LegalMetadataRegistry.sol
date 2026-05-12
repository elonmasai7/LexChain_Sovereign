// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract LegalMetadataRegistry is AccessControlEnumerable, Pausable {
    struct LegalMetadata {
        bytes32 documentHash;
        uint256 timestamp;
        address registrar;
        uint256 chainId;
        bytes additionalData;
    }

    bytes32 public constant REGISTRAR_ROLE = keccak256("REGISTRAR_ROLE");
    
    mapping(bytes32 => LegalMetadata) public metadata;
    mapping(address => bool) public authorizedChains;
    bytes32[] public allHashes;
    mapping(bytes32 => uint256) public hashIndex;

    event MetadataAnchored(
        bytes32 indexed hash,
        uint256 timestamp,
        address indexed registrar,
        uint256 chainId
    );
    event ChainAuthorizationUpdated(address indexed chain, bool authorized);
    event MetadataUpdated(bytes32 indexed hash, bytes additionalData);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(REGISTRAR_ROLE, msg.sender);
    }

    modifier onlyRegistrar() {
        require(hasRole(REGISTRAR_ROLE, msg.sender) || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Not registrar");
        _;
    }

    function anchorMetadata(
        bytes32 documentHash,
        uint256 chainId,
        bytes memory additionalData
    ) 
        external 
        onlyRegistrar 
        whenNotPaused 
    {
        require(authorizedChains[msg.sender] || tx.origin == address(0), "Unauthorized chain");
        
        metadata[documentHash] = LegalMetadata({
            documentHash: documentHash,
            timestamp: block.timestamp,
            registrar: msg.sender,
            chainId: chainId,
            additionalData: additionalData
        });
        
        if (hashIndex[documentHash] == 0 && metadata[documentHash].timestamp == block.timestamp) {
            allHashes.push(documentHash);
            hashIndex[documentHash] = allHashes.length;
        }
        
        emit MetadataAnchored(documentHash, block.timestamp, msg.sender, chainId);
    }

    function getMetadata(bytes32 hash) external view returns (LegalMetadata memory) {
        return metadata[hash];
    }

    function verifyAnchoring(bytes32 documentHash, bytes32 providedHash) 
        external 
        view 
        returns (bool) 
    {
        return metadata[documentHash].documentHash == providedHash && 
               metadata[documentHash].timestamp > 0;
    }

    function updateAdditionalData(bytes32 hash, bytes memory newData) 
        external 
        onlyRegistrar 
    {
        require(metadata[hash].timestamp > 0, "Hash not anchored");
        metadata[hash].additionalData = newData;
        emit MetadataUpdated(hash, newData);
    }

    function authorizeChain(address chain, bool authorized) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        authorizedChains[chain] = authorized;
        emit ChainAuthorizationUpdated(chain, authorized);
    }

    function getAnchoredCount() external view returns (uint256) {
        return allHashes.length;
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}