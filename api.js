require('dotenv').config()

const express = require('express')
const compression = require('compression')
const routes  = require('./routes/routes')
const morgan = require('morgan')
const helmet = require('helmet')
const https = require('https')
const basicAuth = require('express-basic-auth')

var app = express()

app.all('/*', function(req, res, next) {
  // CORS headers
  res.set('Content-Type', 'application/json')
  res.header('Access-Control-Allow-Origin', '*')
  res.header('Access-Control-Allow-Methods', 'POST,OPTIONS')
  // Set custom headers for CORS
  res.header('Access-Control-Allow-Headers', 'Content-Type,Accept,Authorization,Username,Password,Signature,X-Access-Token,X-Key')
  if (req.method == 'OPTIONS') {
    res.status(200).end()
  } else {
    next()
  }
})

app.all('/health', function(req, res, next) {
  res.status(200)
  res.json({
    'status': 200,
    'message': 'health ok'
  })
})

app.use(morgan('dev'))

app.use(basicAuth({users: { [process.env.AUTH_USER]: process.env.AUTH_PASS }}))

app.use(helmet())
app.use(compression())

app.use('/', routes)

function handleData(req, res) {
  if (res.statusCode === 205) {
    if (res.body) {
      if (res.body.length === 0) {
        res.status(204)
        res.json({
          'status': 204,
          'message': 'No Content'
        })
      } else {
        res.status(200)
        res.json(res.body)
      }
    } else {
      res.status(204)
      res.json({
        'status': 204,
        'message': 'No Content'
      })
    }
  } else if (res.statusCode === 400) {
    res.status(res.statusCode)
    res.json({
      'status': res.statusCode,
      'message': 'Bad Request'
    })
  } else if (res.statusCode === 401) {
    res.status(res.statusCode)
    res.json({
      'status': res.statusCode,
      'message': 'Unauthorized'
    })
  } else if (res.statusCode) {
    res.status(res.statusCode)
    res.json(res.body)
  } else {
    res.status(200)
    res.json(res.body)
  }
}
app.use(handleData)
app.use(function(err, req, res) {
  if (err) {
    if (res.statusCode == 500) {
      res.status(250)
      res.json({
        'status': 250,
        'message': err
      })
    } else if (res.statusCode == 501) {
      res.status(250)
      res.json({
        'status': 250,
        'message': err
      })
    } else {
      res.status(500)
      res.json({
        'status': 500,
        'message': err.message
      })
    }
  } else {
    res.status(404)
    res.json({
      'status': 404,
      'message': 'Request not found'
    })
  }
})

var options = {}
https.globalAgent.maxSockets = process.env.MAX_SOCKETS || 50
app.set('port', process.env.PORT || 3000)
var server = null
server = require('http').Server(app)
server.listen(app.get('port'), function () {
  console.log('Running on port:', server.address().port)
  module.exports = server
})

Array.prototype.contains = function(obj) {
  var i = this.length
  while (i--) {
    if (this[i] === obj) {
      return true
    }
  }
  return false
}
