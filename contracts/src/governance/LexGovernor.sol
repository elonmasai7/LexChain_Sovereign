// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorTimelockControl.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorQuadraticVotes.sol";

contract LexGovernor is 
    Governor, 
    GovernorCountingSimple, 
    GovernorVotes, 
    GovernorVotesQuorumFraction,
    GovernorTimelockControl,
    Pausable 
{
    uint256 public constant VOTE_RATIO = 50;
    mapping(address => uint256) public votingPower;
    mapping(address => mapping(uint256 => bool)) public hasVotedProposals;
    
    event ProposalExecuted(address indexed proposer, uint256 proposalId, bytes executionData);
    event VotingPowerUpdated(address indexed voter, uint256 newPower);

    constructor(
        IVotes _token,
        TimelockController _timelock,
        uint256 _quorumPercentage,
        uint256 _votingDelay,
        uint256 _votingPeriod
    )
        Governor("LexChain DAO Governor")
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(_quorumPercentage)
        GovernorTimelockControl(_timelock)
    {}

    function votingDelay() public view override(IGovernor) returns (uint256) {
        return 1 days;
    }

    function votingPeriod() public view override(IGovernor) returns (uint256) {
        return 7 days;
    }

    function quorum(uint256 blockNumber) 
        public 
        view 
        override(IGovernor, GovernorVotesQuorumFraction) 
        returns (uint256) 
    {
        return super.quorum(blockNumber);
    }

    function proposeWithQuadratic(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description,
        uint256 votingPower
    ) 
        public 
        returns (uint256) 
    {
        require(_msgSender() == tx.origin || tx.origin == address(0), "No contracts");
        require(votingPower >= 1, "Insufficient voting power");
        
        return super.propose(targets, values, calldatas, description);
    }

    function execute(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        bytes32 descriptionHash
    ) 
        public 
        payable 
        override(Governor) 
        returns (uint256) 
    {
        uint256 proposalId = super.execute(targets, values, calldatas, descriptionHash);
        emit ProposalExecuted(_msgSender(), proposalId, keccak256(calldatas[0]));
        return proposalId;
    }

    function updateVotingPower(address voter, uint256 newPower) 
        external 
        onlyRole(DEFAULT_ADMIN_ROLE) 
    {
        votingPower[voter] = newPower;
        emit VotingPowerUpdated(voter, newPower);
    }

    function getVotingPower(address account) public view returns (uint256) {
        uint256 tokenVotes = ERC20Votes(token).getPastVotes(account, block.number - 1);
        return tokenVotes + votingPower[account];
    }

    function _authorizeGovernor(address newTimelock) 
        internal 
        pure 
        override(Governor, GovernorTimelockControl) 
    {}
}