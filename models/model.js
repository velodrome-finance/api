const request = require('request-promise')
const CoinGecko = require('coingecko-api')
const Web3 = require('web3')
const config = require('../config')
const redisHelper = require('../helpers/redis')
const BigNumber = require("bignumber.js")
const fs = require('fs')

const ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
const CoinGeckoClient = new CoinGecko()

let CONTRACTS = null
if(config.testnet === '1') {
  CONTRACTS = require('../constants/contractsTestnet.js')
} else {
  CONTRACTS = require('../constants/contracts.js')
}

const model = {
  async updateAssets(req, res, next) {
    try {
      if(config.testnet === '1') {
        let rawdata = fs.readFileSync('token-list.json');
        let tokenList = JSON.parse(rawdata);

        const RC = await redisHelper.connect()
        const d = await RC.set('baseAssets', JSON.stringify(tokenList));

        res.status(205)
        res.body = { 'status': 200, 'success': true, 'data': tokenList }
        return next(null, req, res, next)
      }

      // get ftm tokens from tokenlists
      const tokenLists = config.tokenLists

      const promises = tokenLists.map(url => request(url));
      const listsOfTokens = await Promise.all(promises)
      const tokensJSON = JSON.parse(listsOfTokens[0])

      const tokensLists = listsOfTokens.map((tl) => {
        const json = JSON.parse(tl)
        return json.tokens
      }).flat()

      const removedDuplpicates = tokensLists.filter((value, index, self) =>
        index === self.findIndex((t) => (
          t.address === value.address
        ))
      )

      const RedisClient = await redisHelper.connect()
      const done = await RedisClient.set('baseAssets', JSON.stringify(removedDuplpicates));

      res.status(205)
      res.body = { 'status': 200, 'success': true, 'data': removedDuplpicates }
      return next(null, req, res, next)

    } catch(ex) {
      console.error(ex)
      res.status(500)
      res.body = { 'status': 500, 'success': false, 'data': ex }
      return next(null, req, res, next)
    }
  },

  async getBaseAssets(req, res, next) {
    try {
      const RedisClient = await redisHelper.connect()

      const reply = await RedisClient.get('baseAssets');
      const baseAssets = JSON.parse(reply)

      res.status(205)
      res.body = { 'status': 200, 'success': true, 'data': baseAssets }
      return next(null, req, res, next)
    } catch(ex) {
      console.error(ex)
      res.status(500)
      res.body = { 'status': 500, 'success': false, 'data': ex }
      return next(null, req, res, next)
    }
  },

  getRouteAssets(req, res, next) {
    try {
      const routeAssets = [
        config.wftm
      ]
      res.status(205)
      res.body = { 'status': 200, 'success': true, 'data': routeAssets }
      return next(null, req, res, next)
    } catch(ex) {
      console.error(ex)
      res.status(500)
      res.body = { 'status': 500, 'success': false, 'data': ex }
      return next(null, req, res, next)
    }
  },

  async updatePairs(req, res, next) {
    try {
      const RedisClient = await redisHelper.connect()

      const web3 =  new Web3(config.web3.provider);

      const factoryContract = new web3.eth.Contract(CONTRACTS.FACTORY_ABI, CONTRACTS.FACTORY_ADDRESS)
      const gaugesContract = new web3.eth.Contract(CONTRACTS.GAUGES_ABI, CONTRACTS.GAUGES_ADDRESS)

      const [ allPairsLength, totalWeight ] = await Promise.all([
        factoryContract.methods.allPairsLength().call(),
        gaugesContract.methods.totalWeight().call()
      ])

      const arr = Array.from({length: parseInt(allPairsLength)}, (v, i) => i)

      const ps = await Promise.all(
        arr.map(async (idx) => {
          const [ pairAddress ] = await Promise.all([
            factoryContract.methods.allPairs(idx).call()
          ])

          const pairContract = new web3.eth.Contract(CONTRACTS.PAIR_ABI, pairAddress)

          const [ token0Address, token1Address, totalSupply, symbol, decimals, stable, gaugeAddress, gaugeWeight ] = await Promise.all([
            pairContract.methods.token0().call(),
            pairContract.methods.token1().call(),
            pairContract.methods.totalSupply().call(),
            pairContract.methods.symbol().call(),
            pairContract.methods.decimals().call(),
            pairContract.methods.stable().call(),
            gaugesContract.methods.gauges(pairAddress).call(),
            gaugesContract.methods.weights(pairAddress).call()
          ])

          const token0 = await model._getBaseAsset(token0Address)
          const token1 = await model._getBaseAsset(token1Address)

          const thePair = {
            address: pairAddress,
            symbol: symbol,
            decimals: parseInt(decimals),
            isStable: stable,
            token0: token0,
            token1: token1,
            totalSupply: BigNumber(totalSupply).div(10**decimals).toFixed(parseInt(decimals)),
          }

          if(gaugeAddress !== ZERO_ADDRESS) {
            const gaugeContract = new web3.eth.Contract(CONTRACTS.GAUGE_ABI, gaugeAddress)

            const [ totalSupply, bribeAddress ] = await Promise.all([
              gaugeContract.methods.totalSupply().call(),
              gaugesContract.methods.bribes(gaugeAddress).call()
            ])

            const bribeContract = new web3.eth.Contract(CONTRACTS.BRIBE_ABI, bribeAddress)

            const tokensLength = await bribeContract.methods.rewardsListLength().call()
            const arry = Array.from({length: parseInt(tokensLength)}, (v, i) => i)

            const bribes = await Promise.all(
              arry.map(async (idx) => {

                const tokenAddress = await bribeContract.methods.rewards(idx).call()
                const token = await model._getBaseAsset(tokenAddress)

                const [ rewardRate ] = await Promise.all([
                  bribeContract.methods.rewardRate(tokenAddress).call(),
                ])

                return {
                  token: token,
                  rewardRate: BigNumber(rewardRate).div(10**token.decimals).toFixed(token.decimals),
                  rewardAmount: BigNumber(rewardRate).times(604800).div(10**token.decimals).toFixed(token.decimals)
                }
              })
            )

            thePair.gauge = {
              address: gaugeAddress,
              bribeAddress: bribeAddress,
              decimals: 18,
              totalSupply: BigNumber(totalSupply).div(10**18).toFixed(18),
              weight: BigNumber(gaugeWeight).div(10**18).toFixed(18),
              weightPercent: BigNumber(gaugeWeight).times(100).div(totalWeight).toFixed(2),
              bribes: bribes,
            }
          }

          return thePair;
        })
      )

      const done = await RedisClient.set('pairs', JSON.stringify(ps))

      res.status(205)
      res.body = { 'status': 200, 'success': true, 'data': ps }
      return next(null, req, res, next)

    } catch(ex) {
      console.error(ex)
      res.status(500)
      res.body = { 'status': 500, 'success': false, 'data': ex }
      return next(null, req, res, next)
    }
  },

  async _getBaseAsset(address) {
    try {
      const RedisClient = await redisHelper.connect()

      const ba = await RedisClient.get('baseAssets');
      const baseAssets = JSON.parse(ba)

      let xa = await RedisClient.get('extraAssets');
      if(!xa || xa.length === 0) {
        xa = '[]'
      }
      const extraAssets = JSON.parse(xa)

      const allAssets = [...baseAssets, ...extraAssets]

      const theBaseAsset = allAssets.filter((as) => {
        return as.address.toLowerCase() === address.toLowerCase()
      })
      if(theBaseAsset.length > 0) {
        return theBaseAsset[0]
      }

      const web3 =  new Web3(config.web3.provider);

      const baseAssetContract = new web3.eth.Contract(CONTRACTS.ERC20_ABI, address)

      const [ symbol, decimals, name ] = await Promise.all([
        baseAssetContract.methods.symbol().call(),
        baseAssetContract.methods.decimals().call(),
        baseAssetContract.methods.name().call(),
      ]);

      const newBaseAsset = {
        address: address,
        symbol: symbol,
        name: name,
        decimals: parseInt(decimals),
        chainId: 250,
        logoURI: null
      }

      extraAssets.push(newBaseAsset)

      const done = await RedisClient.set('extraAssets', JSON.stringify(extraAssets))

      return newBaseAsset
    } catch(ex) {
      console.error(ex)
      return null
    }
  },

  async getPairs(req, res, next) {
    try {
      const RedisClient = await redisHelper.connect()

      const reply = await RedisClient.get('pairs');
      const pairs = JSON.parse(reply)

      res.status(205)
      res.body = { 'status': 200, 'success': true, 'data': pairs }
      return next(null, req, res, next)
    } catch(ex) {
      console.error(ex)
      res.status(500)
      res.body = { 'status': 500, 'success': false, 'data': ex }
      return next(null, req, res, next)
    }
  },


}

module.exports = model
