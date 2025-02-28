// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DiceGame {
    address public admin;
    uint256 public gameCount;
    uint256 public treasuryBalance;
    uint256 public constant MIN_BET = 0.1 ether;
    uint256 public constant MAX_BET = 100 ether;
    uint256 public constant BET_STEP = 0.1 ether;

    struct Game {
        address player1;
        address player2;
        uint256 betAmount;
        uint256 player1Score;
        uint256 player2Score;
        bool finished;
        uint256[2] player1Rolls;
        uint256[2] player2Rolls;
    }

    // Новая структура для возврата информации об открытых играх
    struct OpenGameInfo {
        uint256 gameId;
        address player1;
        uint256 betAmount;
    }

    mapping(uint256 => Game) public games;
    uint256 private nonce;

    event GameCreated(uint256 gameId, address player1, uint256 betAmount);
    event PlayerJoined(uint256 gameId, address player2);
    event DiceRolled(uint256 gameId, address player, uint256 score, uint256[2] rolls);
    event GameFinished(uint256 gameId, address winner, uint256 winnings);

    constructor() {
        admin = msg.sender;
        gameCount = 0;
        treasuryBalance = 0;
    }

    function createGame() external payable {
        require(msg.value >= MIN_BET && msg.value <= MAX_BET, "Bet must be between 0.1 and 100 Monad");
        require(msg.value % BET_STEP == 0, "Bet must be in steps of 0.1 Monad");

        gameCount++;
        Game storage newGame = games[gameCount];
        newGame.player1 = msg.sender;
        newGame.betAmount = msg.value;
        newGame.finished = false;

        rollDice(gameCount, msg.sender);
        emit GameCreated(gameCount, msg.sender, msg.value);
    }

    function joinGame(uint256 gameId) external payable {
        Game storage game = games[gameId];
        require(game.player1 != address(0), "Game does not exist");
        require(game.player2 == address(0), "Game already has two players");
        require(msg.sender != game.player1, "Cannot join your own game");
        require(msg.value == game.betAmount, "Bet must match Player 1's bet");
        require(!game.finished, "Game already finished");

        game.player2 = msg.sender;
        rollDice(gameId, msg.sender);
        finishGame(gameId);
        emit PlayerJoined(gameId, msg.sender);
    }

    function rollDice(uint256 gameId, address player) internal {
        Game storage game = games[gameId];
        nonce++;
        uint256 dice1 = (uint256(keccak256(abi.encodePacked(block.timestamp, block.number, player, nonce))) % 6) + 1;
        uint256 dice2 = (uint256(keccak256(abi.encodePacked(block.timestamp, block.number, player, dice1, nonce))) % 6) + 1;
        uint256 totalScore = dice1 + dice2;

        if (player == game.player1) {
            game.player1Score = totalScore;
            game.player1Rolls = [dice1, dice2];
        } else {
            game.player2Score = totalScore;
            game.player2Rolls = [dice1, dice2];
        }
        emit DiceRolled(gameId, player, totalScore, [dice1, dice2]);
    }

    function finishGame(uint256 gameId) internal {
        Game storage game = games[gameId];
        require(game.player2Score > 0 && game.player1Score > 0, "Both players must roll");
        require(!game.finished, "Game already finished");
        require(address(this).balance >= game.betAmount * 2, "Insufficient contract balance");

        game.finished = true;
        uint256 totalPot = game.betAmount * 2;
        uint256 treasuryShare = totalPot / 10;
        uint256 winnerShare = totalPot - treasuryShare;

        treasuryBalance += treasuryShare; // 10% остаются на контракте

        if (game.player1Score > game.player2Score) {
            (bool success, ) = payable(game.player1).call{value: winnerShare}("");
            require(success, "Transfer to player1 failed");
            emit GameFinished(gameId, game.player1, winnerShare);
        } else if (game.player2Score > game.player1Score) {
            (bool success, ) = payable(game.player2).call{value: winnerShare}("");
            require(success, "Transfer to player2 failed");
            emit GameFinished(gameId, game.player2, winnerShare);
        } else {
            (bool success1, ) = payable(game.player1).call{value: game.betAmount}("");
            (bool success2, ) = payable(game.player2).call{value: game.betAmount}("");
            require(success1 && success2, "Refund failed");
            emit GameFinished(gameId, address(0), 0);
        }
    }

    function withdrawTreasury(uint256 amount) external {
        require(msg.sender == admin, "Only admin");
        require(amount <= treasuryBalance, "Insufficient treasury balance");
        treasuryBalance -= amount;
        (bool success, ) = payable(admin).call{value: amount}("");
        require(success, "Treasury withdrawal failed");
    }

    function getGame(uint256 gameId) external view returns (Game memory) {
        return games[gameId];
    }

    function getTreasuryBalance() external view returns (uint256) {
        return treasuryBalance;
    }

    function getOpenGames() external view returns (OpenGameInfo[] memory) {
        // Подсчитываем количество открытых игр
        uint256 openCount = 0;
        for (uint256 i = 1; i <= gameCount; i++) {
            if (games[i].player1 != address(0) && 
                games[i].player2 == address(0) && 
                !games[i].finished) {
                openCount++;
            }
        }

        // Создаем массив нужного размера
        OpenGameInfo[] memory openGames = new OpenGameInfo[](openCount);
        uint256 currentIndex = 0;

        // Заполняем массив данными об открытых играх
        for (uint256 i = 1; i <= gameCount; i++) {
            if (games[i].player1 != address(0) && 
                games[i].player2 == address(0) && 
                !games[i].finished) {
                openGames[currentIndex] = OpenGameInfo({
                    gameId: i,
                    player1: games[i].player1,
                    betAmount: games[i].betAmount
                });
                currentIndex++;
            }
        }

        return openGames;
    }
}
