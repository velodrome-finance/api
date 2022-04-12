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

  tokenLists: [,
    'https://raw.githubusercontent.com/SpookySwap/spooky-info/master/src/constants/token/spookyswap.json',
    'https://raw.githubusercontent.com/DimensionDev/Mask-Token-List/gh-pages/latest/250/tokens.json',
    'https://unpkg.com/@crocoswap/default-token-list@3.2.1/build/sushiswap-default.tokenlist.json',
    'https://raw.githubusercontent.com/BoggedFinance/Bogged-Token-List/main/ftm/tokenlist.json'
  ],

  wftm: {
    "chainId":250,
    "name":"Wrapped FTM",
    "symbol":"WFTM",
    "address":"0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83",
    "decimals":18,
    "logoURI":"https://assets.spookyswap.finance/tokens/wFTM.png"
  },
  solidSEX: {
    "chainId":250,
    "name":"SOLIDsex: Tokenized veSOLID",
    "symbol":"SOLIDSEX",
    "address":"0x41adac6c1ff52c5e27568f27998d747f7b69795b",
    "decimals":18,
    "logoURI":"https://assets.coingecko.com/coins/images/23992/large/solidSEX.png"
  },
  usdc: {
    "chainId":250,
    "name":"USD Coin",
    "symbol":"USDC",
    "address":"0x04068DA6C83AFCFA0e13ba15A6696662335D5B75",
    "decimals":6,
    "logoURI":"https://assets.spookyswap.finance/tokens/USDC.png"
  }

}


module.exports = config
