var express = require('express')
var router = express.Router()
var model = require('../models/model.js')
var bodyParser = require('body-parser')

router.get('/', function (req, res, next) {
  res.status(400)
  next(null, req, res, next)
})

router.get('/api/v1/pairs', bodyParser.json(), model.getPairs)
router.get('/api/v1/baseAssets', bodyParser.json(), model.getBaseAssets)
router.get('/api/v1/routeAssets', bodyParser.json(), model.getRouteAssets)

router.get('/api/v1/updateAssets', bodyParser.json(), model.updateAssets)
router.get('/api/v1/updatePairs', bodyParser.json(), model.updatePairs)
// router.get('/api/v1/mergeTokenLists', bodyParser.json(), model.mergeTokenLists)


module.exports = router
