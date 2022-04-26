require('dotenv').config()

const config = {

  testnet: process.env.TESTNET,

  web3: {
    provider: process.env.PROVIDER
  },

  tokenLists: process.env.TOKENLISTS.toString().split('|').filter(Boolean),

  weth: {
    "chainId":10,
    "name":"Wrapped ETH",
    "symbol":"WETH",
    "address":"0x4200000000000000000000000000000000000006",
    "decimals":18,
    "logoURI":"https://weth.io/img/weth_favi.png"
  },
  usdc: {
    "chainId":10,
    "name":"USD Coin",
    "symbol":"USDC",
    "address":"0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
    "decimals":6,
    "logoURI":"https://assets.spookyswap.finance/tokens/USDC.png"
  }

}


module.exports = config
