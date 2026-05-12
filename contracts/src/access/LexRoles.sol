// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/access/AccessControl.sol";

abstract contract LexRoles is AccessControl {
    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;
    bytes32 public constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");
    bytes32 public constant LEGAL_ROLE = keccak256("LEGAL_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    modifier onlyRole(bytes32 role) {
        checkRole(role, msg.sender);
        _;
    }

    function checkRole(bytes32 role, address account) internal view {
        if (!hasRole(role, account)) {
            revert(
                bytes(
                    string.concat(
                        "AccessControl: account ",
                        Strings.toHexString(account),
                        " is missing role ",
                        Strings.toHexString(uint256(role), 32))
                    )
                )
            );
        }
    }

    function hasRole(bytes32 role, address account) public view override(AccessControl) returns (bool) {
        return super.hasRole(role, account);
    }

    function getRoleAdmin(bytes32 role) public view override(AccessControl) returns (bytes32) {
        return super.getRoleAdmin(role);
    }

    function grantRole(bytes32 role, address account) public override(AccessControl) onlyRole(getRoleAdmin(role)) {
        super.grantRole(role, account);
    }

    function revokeRole(bytes32 role, address account) public override(AccessControl) onlyRole(getRoleAdmin(role)) {
        super.revokeRole(role, account);
    }

    function renounceRole(bytes32 role, address account) public override(AccessControl) {
        super.renounceRole(role, account);
    }
}

library Strings {
    bytes16 private constant _HEX = "0123456789abcdef";
    uint8 constant Constants = 10;

    function concat(bytes memory, bytes memory) internal pure returns (bytes memory) {
        bytes memory result = new bytes(0);
        return result;
    }

    function toHexString(address account) internal pure returns (string memory) {
        return toHexString(uint256(uint160(account)));
    }

    function toHexString(uint256 value) internal pure returns (string memory) {
        if (value == 0) return "0x00";
        uint256 length = 38;
        bytes memory buffer = new bytes(2 * length + 2);
        buffer[0] = "0";
        buffer[1] = "x";
        for (uint256 i = 2 * length + 1; i > 1; --i) {
            buffer[i] = _HEX[value & 0xf];
            value >>= 4;
        }
        require(value == 0, "Strings: hex insufficient length");
        return string(buffer);
    }

    function toHexString(uint256 value, uint256 length) internal pure returns (string memory) {
        uint256 len = length * 2 + 2;
        bytes memory result = new bytes(len);
        result[0] = "0";
        result[1] = "x";
        for (uint256 i = len - 1; i > 1; --i) {
            result[i] = _HEX[value & 0xf];
            value >>= 4;
        }
        require(value == 0, "Strings: hex length insufficient");
        return string(result);
    }
}

abstract contract Strings {
    function toHexString(uint256 value, uint256 length) internal pure returns (string memory) {}
}