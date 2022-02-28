const request = require('request-promise')
const CoinGecko = require('coingecko-api')
const Web3 = require('web3')
const config = require('../config')
const redisHelper = require('../helpers/redis')
const BigNumber = require("bignumber.js")
const fs = require('fs')
const Multicall = require('@dopex-io/web3-multicall')

const ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'
const CoinGeckoClient = new CoinGecko()

let CONTRACTS = null
if(config.testnet === '1') {
  CONTRACTS = require('../constants/contractsTestnet.js')
} else {
  CONTRACTS = require('../constants/contracts.js')
}

const model = {
  async mergeTokenLists(req, res, next) {
    try {
      let rawdata = fs.readFileSync('token-list.json');
      let tokenList = JSON.parse(rawdata);

      // get ftm tokens from tokenlists
      const tokenLists = config.tokenLists

      const promises = tokenLists.map(url => request(url));
      const listsOfTokens = await Promise.all(promises)

      let tokensLists = listsOfTokens.map((tl) => {
        try {
          const json = JSON.parse(tl)
          return json.tokens
        } catch(ex) {
          console.log(ex)
          return []
        }
      }).flat()

      tokensLists = [...tokenList, ...tokensLists]

      const removedDuplpicates = tokensLists.filter((t) => {
        return t.chainId === 250 && t.decimals !== ''
      }).filter((value, index, self) =>
        index === self.findIndex((t) => (
          t.address === value.address
        ))
      )

      // const RedisClient = await redisHelper.connect()
      // const done = await RedisClient.set('baseAssets', JSON.stringify(removedDuplpicates));

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

  async updateAssets(req, res, next) {
    try {
      if(config.testnet === '1') {
        let rawdata = fs.readFileSync('testnet-token-list.json');
        let tokenList = JSON.parse(rawdata);

        const RC = await redisHelper.connect()
        const d = await RC.set('baseAssets', JSON.stringify(tokenList));

        res.status(205)
        res.body = { 'status': 200, 'success': true, 'data': tokenList }
        return next(null, req, res, next)
      } else {
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

      const removedDuplpicates = tokensLists.filter((t) => {
        return t.chainId === 250 && t.decimals !== ''
      }).filter((value, index, self) =>
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
      const multicall = new Multicall({
        multicallAddress: CONTRACTS.MULTICALL_ADDRESS,
        provider: web3,
      })

      const factoryContract = new web3.eth.Contract(CONTRACTS.FACTORY_ABI, CONTRACTS.FACTORY_ADDRESS)
      const gaugesContract = new web3.eth.Contract(CONTRACTS.GAUGES_ABI, CONTRACTS.GAUGES_ADDRESS)

      const [ allPairsLength, totalWeight ] = await Promise.all([
        factoryContract.methods.allPairsLength().call(),
        gaugesContract.methods.totalWeight().call()
      ])

      const arr = Array.from({length: parseInt(allPairsLength)}, (v, i) => i)

      const ps = await Promise.all(
        arr.map(async (idx) => {
          const pairAddress = await factoryContract.methods.allPairs(idx).call()

          const pairContract = new web3.eth.Contract(CONTRACTS.PAIR_ABI, pairAddress)

          const [ reserves, token0Address, token1Address, totalSupply, symbol, decimals, stable, gaugeAddress, gaugeWeight ] = await multicall.aggregate([
            pairContract.methods.getReserves(),
            pairContract.methods.token0(),
            pairContract.methods.token1(),
            pairContract.methods.totalSupply(),
            pairContract.methods.symbol(),
            pairContract.methods.decimals(),
            pairContract.methods.stable(),
            gaugesContract.methods.gauges(pairAddress),
            gaugesContract.methods.weights(pairAddress),
          ])

          const token0 = await model._getBaseAsset(web3, token0Address)
          const token1 = await model._getBaseAsset(web3, token1Address)

          const thePair = {
            address: pairAddress,
            symbol: symbol,
            decimals: parseInt(decimals),
            isStable: stable,
            token0: token0,
            token1: token1,
            totalSupply: BigNumber(totalSupply).div(10**decimals).toFixed(parseInt(decimals)),
            reserve0: BigNumber(reserves[0]).div(10**decimals).toFixed(parseInt(decimals)),
            reserve1: BigNumber(reserves[1]).div(10**decimals).toFixed(parseInt(decimals)),
          }

          if(gaugeAddress !== ZERO_ADDRESS) {
            const gaugeContract = new web3.eth.Contract(CONTRACTS.GAUGE_ABI, gaugeAddress)

            const [ gaugeTotalSupply, bribeAddress ] = await multicall.aggregate([
              gaugeContract.methods.totalSupply(),
              gaugesContract.methods.bribes(gaugeAddress)
            ])

            const bribeContract = new web3.eth.Contract(CONTRACTS.BRIBE_ABI, bribeAddress)

            const tokensLength = await bribeContract.methods.rewardsListLength().call()
            const arry = Array.from({length: parseInt(tokensLength)}, (v, i) => i)

            let bribes = await Promise.all(
              arry.map(async (idx) => {

                const tokenAddress = await bribeContract.methods.rewards(idx).call()
                const token = await model._getBaseAsset(web3, tokenAddress)
                const rewardRate = await bribeContract.methods.rewardRate(tokenAddress).call()

                return {
                  token: token,
                  rewardRate: BigNumber(rewardRate).div(10**token.decimals).toFixed(token.decimals),
                  rewardAmount: BigNumber(rewardRate).times(604800).div(10**token.decimals).toFixed(token.decimals)
                }
              })
            )

            bribes = bribes.filter((bribe) => {
              return bribe.token.isWhitelisted
            })

            thePair.gauge = {
              address: gaugeAddress,
              bribeAddress: bribeAddress,
              decimals: 18,
              totalSupply: BigNumber(gaugeTotalSupply).div(10**18).toFixed(18),
              reserve0: thePair.totalSupply > 0 ? BigNumber(thePair.reserve0).times(gaugeTotalSupply).div(totalSupply).toFixed(thePair.token0.decimals) : '0',
              reserve1: thePair.totalSupply > 0 ? BigNumber(thePair.reserve1).times(gaugeTotalSupply).div(totalSupply).toFixed(thePair.token1.decimals) : '0',
              weight: BigNumber(gaugeWeight).div(10**18).toFixed(18),
              weightPercent: BigNumber(totalWeight).gt(0) ? BigNumber(gaugeWeight).times(100).div(totalWeight).toFixed(2) : 0,
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

  async _getBaseAsset(web3, address) {
    try {
      const RedisClient = await redisHelper.connect()

      const multicall = new Multicall({
        multicallAddress: CONTRACTS.MULTICALL_ADDRESS,
        provider: web3,
      })

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
        const gaugesContract = new web3.eth.Contract(CONTRACTS.GAUGES_ABI, CONTRACTS.GAUGES_ADDRESS)
        const isWhitelisted = await gaugesContract.methods.isWhitelisted(address).call()

        let returnAsset = theBaseAsset[0]
        returnAsset.isWhitelisted = isWhitelisted
        return returnAsset
      }

      const gaugesContract = new web3.eth.Contract(CONTRACTS.GAUGES_ABI, CONTRACTS.GAUGES_ADDRESS)
      const baseAssetContract = new web3.eth.Contract(CONTRACTS.ERC20_ABI, address)

      const [ symbol, decimals, name, isWhitelisted ] = await multicall.aggregate([
        baseAssetContract.methods.symbol(),
        baseAssetContract.methods.decimals(),
        baseAssetContract.methods.name(),
        gaugesContract.methods.isWhitelisted(address)
      ]);

      const newBaseAsset = {
        address: address,
        symbol: symbol,
        name: name,
        decimals: parseInt(decimals),
        chainId: 250,
        logoURI: null,
        isWhitelisted: isWhitelisted
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
