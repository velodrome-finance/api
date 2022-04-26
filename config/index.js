require('dotenv').config()

const config = {

  testnet: process.env.TESTNET,

  web3: {
    provider: process.env.PROVIDER
  },

  redis: {
    host: process.env.REDIS_HOST,
    port: process.env.REDIS_PORT,
    // password: PROCESS.ENV.REDIS_PASSWORD
  },

  tokenLists: [],

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
