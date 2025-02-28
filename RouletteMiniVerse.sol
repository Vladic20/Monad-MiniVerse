// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Roulette is ReentrancyGuard, Ownable {
    uint256 public constant MIN_BET = 0.1 ether; // Minimum bet in MONA (1 MONA = 10^18 wei)
    uint256 public constant MAX_BET = 100 ether;  // Maximum bet
    uint256 public constant BET_STEP = 0.1 ether; // Bet step

    uint256 public treasuryBalance;              // Treasury balance
    uint256 public constant HOUSE_EDGE = 2;      // 2% house edge
    uint256 public constant SPIN_DELAY_BLOCKS = 2; // Delay of 2 blocks to prevent manipulation

    // Structure to store a player's bet
    struct Bet {
        address player;
        uint256 amount;
        uint8 color;     // 1 for red, 2 for black
    }

    // Spin state
    uint8 public winningColor;     // Winning color (1 for red, 2 for black, 0 for no spin)
    bool public isSpinActive;      // Flag for active spin
    mapping(uint256 => Bet[]) public bets; // Bets for each spin (spinId -> array of bets)
    uint256 public spinCount;      // Spin counter
    uint256 public lastSpinBlock;  // Block number of the last spin

    // Bet history
    struct BetHistory {
        uint256 spinId;
        uint8 color;
        uint256 amount;
        bool won;
        uint256 payout;
    }
    mapping(address => BetHistory[]) public playerHistory; // Bet history for each player

    // Leaderboard (top-10 by total winnings)
    struct Leader {
        address player;
        uint256 totalWinnings;
    }
    Leader[] public leaders;
    uint256 constant MAX_LEADERS = 10;

    // Accumulated nonce for randomness
    uint256 public nonce;

    event BetPlaced(address player, uint256 spinId, uint256 amount, uint8 color);
    event SpinResult(uint256 spinId, uint8 winningColor);
    event WinningsClaimed(address player, uint256 amount);
    event TreasuryDeposited(address depositor, uint256 amount);
    event TreasuryWithdrawal(address owner, uint256 amount);
    event LeaderUpdated(address player, uint256 totalWinnings);
    event BetAndSpinResult(address player, uint256 spinId, uint8 betColor, uint8 winningColor, bool won, uint256 payout);

    constructor() Ownable(msg.sender) {
        spinCount = 0;
        nonce = 0;
        winningColor = 0; // No spin initially
    }

    function placeBet(uint256 betAmount, uint8 color) external payable nonReentrant {
        require(!isSpinActive, "Spin is currently active");
        require(betAmount >= MIN_BET && betAmount <= MAX_BET, "Bet must be between 0.1 and 100 MONA");
        require(betAmount % BET_STEP == 0, "Bet must be a multiple of 0.1 MONA");
        require(msg.value == betAmount, "Incorrect MONA amount sent");
        require(color == 1 || color == 2, "Color must be 1 (red) or 2 (black)");

        spinCount++;
        bets[spinCount].push(Bet(msg.sender, betAmount, color));
        emit BetPlaced(msg.sender, spinCount, betAmount, color);
    }

    function spin() external nonReentrant {
        require(!isSpinActive, "Spin is currently active");
        require(bets[spinCount].length > 0, "No bets for spin");
        require(block.number >= lastSpinBlock + SPIN_DELAY_BLOCKS, "Wait for the 2-block delay");

        isSpinActive = true;
        winningColor = _generateRandomColor();
        lastSpinBlock = block.number;

        _distributeWinnings(spinCount);
        isSpinActive = false;
        emit SpinResult(spinCount, winningColor);
    }

    function placeBetAndSpin(uint256 betAmount, uint8 color) external payable nonReentrant returns (bool won, uint256 payout) {
        require(!isSpinActive, "Spin is currently active");
        require(betAmount >= MIN_BET && betAmount <= MAX_BET, "Bet must be between 0.1 and 100 MONA");
        require(betAmount % BET_STEP == 0, "Bet must be a multiple of 0.1 MONA");
        require(msg.value == betAmount, "Incorrect MONA amount sent");
        require(color == 1 || color == 2, "Color must be 1 (red) or 2 (black)");

        spinCount++;
        bets[spinCount].push(Bet(msg.sender, betAmount, color));
        emit BetPlaced(msg.sender, spinCount, betAmount, color);

        // Try to spin immediately, but check delay and active spin
        if (block.number < lastSpinBlock + SPIN_DELAY_BLOCKS) {
            // Refund the bet if spin cannot be executed due to delay
            (bool success, ) = payable(msg.sender).call{value: betAmount}("");
            require(success, "Refund failed");
            delete bets[spinCount];
            spinCount--;
            emit BetAndSpinResult(msg.sender, spinCount + 1, color, 0, false, 0);
            return (false, 0);
        }

        if (bets[spinCount].length > 0) {
            isSpinActive = true;
            winningColor = _generateRandomColor();
            lastSpinBlock = block.number;

            _distributeWinnings(spinCount);
            isSpinActive = false;
            emit SpinResult(spinCount, winningColor);

            // Determine win/loss for this bet
            uint256 houseFee = (betAmount * HOUSE_EDGE) / 100;
            uint256 potentialPayout = betAmount * 2 - houseFee;
            bool betWon = (color == winningColor);
            uint256 finalPayout = betWon ? potentialPayout : 0;

            if (betWon) {
                (bool success, ) = payable(msg.sender).call{value: finalPayout}("");
                require(success, "Payout failed");
                emit WinningsClaimed(msg.sender, finalPayout);
            }

            // Update history and leaderboard
            playerHistory[msg.sender].push(BetHistory(spinCount, color, betAmount, betWon, finalPayout));
            if (betWon) {
                _updateLeaderBoard(msg.sender, finalPayout);
            }

            emit BetAndSpinResult(msg.sender, spinCount, color, winningColor, betWon, finalPayout);
            return (betWon, finalPayout);
        } else {
            // This should not happen due to the bet placement above, but for safety
            (bool success, ) = payable(msg.sender).call{value: betAmount}("");
            require(success, "Refund failed");
            delete bets[spinCount];
            spinCount--;
            emit BetAndSpinResult(msg.sender, spinCount + 1, color, 0, false, 0);
            return (false, 0);
        }
    }

    function _generateRandomColor() internal returns (uint8) {
        nonce++;
        // Improved randomness: combination of multiple sources for color (1 or 2)
        uint256 seed = uint256(
            keccak256(
                abi.encodePacked(
                    block.timestamp,        // Block timestamp
                    block.number,          // Block number
                    block.prevrandao,      // Randomness source (if available, otherwise block.difficulty)
                    tx.origin,             // Transaction origin
                    msg.sender,            // Current sender
                    nonce                  // Accumulated nonce
                )
            )
        );
        return uint8((seed % 2) + 1); // 0 or 1 from % 2, +1 makes it 1 or 2 (red or black)
    }

    function _distributeWinnings(uint256 spinId) internal {
        Bet[] storage currentBets = bets[spinId];
        uint8 localWinningColor = winningColor; // Use global winningColor directly, no shadowing

        for (uint256 i = 0; i < currentBets.length; i++) {
            Bet storage bet = currentBets[i];
            uint256 payout = 0;
            uint256 houseFee = (bet.amount * HOUSE_EDGE) / 100;
            treasuryBalance += houseFee;

            if (bet.color == localWinningColor) { // Winning color (red or black)
                payout = bet.amount * 2 - houseFee; // 1:1 + bet return
            }

            bool won = payout > 0;
            if (won) {
                (bool success, ) = payable(bet.player).call{value: payout}("");
                require(success, "Payout failed");
                emit WinningsClaimed(bet.player, payout);

                // Update bet history
                playerHistory[bet.player].push(BetHistory(spinId, bet.color, bet.amount, won, payout));
                _updateLeaderBoard(bet.player, payout);
            } else {
                playerHistory[bet.player].push(BetHistory(spinId, bet.color, bet.amount, won, 0));
            }
        }

        // Clear bets after spin
        delete bets[spinId];
    }

    function _updateLeaderBoard(address player, uint256 /* winnings */) internal {
        uint256 totalWinnings = 0;
        for (uint256 i = 0; i < playerHistory[player].length; i++) {
            totalWinnings += playerHistory[player][i].payout;
        }

        // Check if player is in the leaderboard
        bool found = false;
        for (uint256 i = 0; i < leaders.length; i++) {
            if (leaders[i].player == player) {
                leaders[i].totalWinnings = totalWinnings;
                found = true;
                break;
            }
        }

        if (!found && leaders.length < MAX_LEADERS) {
            leaders.push(Leader(player, totalWinnings));
        } else if (!found) {
            // Find the player with the lowest winnings and replace if the new player is better
            uint256 minWinnings = type(uint256).max;
            uint256 minIndex = 0;
            for (uint256 i = 0; i < leaders.length; i++) {
                if (leaders[i].totalWinnings < minWinnings) {
                    minWinnings = leaders[i].totalWinnings;
                    minIndex = i;
                }
            }
            if (totalWinnings > minWinnings) {
                leaders[minIndex] = Leader(player, totalWinnings);
            }
        }

        // Sort the leaderboard (simple bubble sort, can be optimized)
        for (uint256 i = 0; i < leaders.length - 1; i++) {
            for (uint256 j = 0; j < leaders.length - 1 - i; j++) {
                if (leaders[j].totalWinnings < leaders[j + 1].totalWinnings) {
                    Leader memory temp = leaders[j];
                    leaders[j] = leaders[j + 1];
                    leaders[j + 1] = temp;
                }
            }
        }
    }

    function getPlayerHistory(address player) external view returns (BetHistory[] memory) {
        return playerHistory[player];
    }

    function getLeaders() external view returns (Leader[] memory) {
        return leaders;
    }

    function depositToTreasury() external payable nonReentrant {
        require(msg.value > 0, "Deposit amount must be greater than 0");
        treasuryBalance += msg.value;
        emit TreasuryDeposited(msg.sender, msg.value);
    }

    function withdrawTreasury(uint256 amount) external onlyOwner {
        require(amount <= treasuryBalance, "Insufficient treasury balance");
        treasuryBalance -= amount;
        (bool success, ) = payable(owner()).call{value: amount}("");
        require(success, "Treasury withdrawal failed");
        emit TreasuryWithdrawal(owner(), amount);
    }
}
