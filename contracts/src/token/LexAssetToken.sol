// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165.sol";

contract LexAssetToken is AccessControlEnumerable, Pausable, ReentrancyGuard, ERC20, ERC20Burnable {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");
    
    uint256 public totalSupplyCap;
    mapping(address => bool) public transferRestrictions;
    mapping(address => uint256) public lastTransferTime;
    uint256 public complianceCheckInterval;
    
    event AssetMinted(address indexed to, uint256 amount, bytes metadata);
    event ComplianceUpdated(address indexed user, bool restricted);
    event TransferRestricted(address indexed user, bool restricted);

    modifier onlyMinterOrAdmin() {
        require(hasRole(MINTER_ROLE, msg.sender) || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Not authorized");
        _;
    }

    constructor(string memory name, string memory symbol, uint256 cap) ERC20(name, symbol) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(PAUSER_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(COMPLIANCE_ROLE, msg.sender);
        
        totalSupplyCap = cap;
        complianceCheckInterval = 1 days;
    }

    function mint(address to, uint256 amount, bytes memory metadata) 
        external 
        onlyMinterOrAdmin 
        whenNotPaused 
        nonReentrant 
    {
        require(totalSupply() + amount <= totalSupplyCap, "Cap exceeded");
        
        _mint(to, amount);
        emit AssetMinted(to, amount, metadata);
    }

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    function setTransferRestriction(address user, bool restricted) 
        external 
        onlyRole(COMPLIANCE_ROLE) 
    {
        transferRestrictions[user] = restricted;
        emit TransferRestricted(user, restricted);
    }

    function _update(address from, address to, uint256 value) 
        internal 
        override(ERC20) 
        whenNotPaused 
    {
        if (transferRestrictions[from] || transferRestrictions[to]) {
            require(
                block.timestamp >= lastTransferTime[from] + complianceCheckInterval,
                "Compliance check interval not met"
            );
            lastTransferTime[from] = block.timestamp;
        }
        super._update(from, to, value);
    }

    function burn(uint256 amount) public override(ERC20Burnable) {
        super.burn(amount);
    }

    function supportsInterface(bytes4 interfaceId) 
        public 
        view 
        override(AccessControlEnumerable, ERC20) 
        returns (bool) 
    {
        return super.supportsInterface(interfaceId);
    }
}