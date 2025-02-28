// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract SimpleIdenticalNFT is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    string private baseURI;
    uint256 public constant MINT_PRICE = 0.11 ether; // Minting cost (in ETH or MON)
    uint256 public constant MAX_SUPPLY = 10000; // Maximum number of NFTs

    constructor() ERC721("Monad DiceMaster", "MDM") Ownable(msg.sender) {
        baseURI = "ipfs://bafybeic6djv5orrmikoofgfdfs2q4mdxczloaa4lih42aujqce362iyqlq/"; // Your public CID
    }

    // Function to mint an identical NFT
    function mintNFT() external payable {
        require(msg.value == MINT_PRICE, "Incorrect payment amount");
        require(_tokenIdCounter.current() < MAX_SUPPLY, "Max supply reached");

        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        _safeMint(msg.sender, tokenId);
    }

    // Set base URI (only for owner)
    function setBaseURI(string memory newURI) public onlyOwner {
        baseURI = newURI;
    }

    // Get metadata for NFT
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_tokenIdCounter.current() > tokenId && tokenId >= 0, "NFT does not exist");
        return string(abi.encodePacked(baseURI, "1.json")); // All NFTs reference the same JSON
    }

    // Withdraw funds from contract (only for owner)
    function withdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
       payable(msg.sender).transfer(balance);
    }
}
