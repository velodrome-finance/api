const config = require('../config')
const redis = require('redis');

const RedisClient = redis.createClient({
  url: process.env.REDIS_URL
})

const connect = async () => {
  try {

    let connected = false
    try {
      const pong = await RedisClient.ping()
      if(pong == 'PONG') {
        connected = true
      }
    } catch(ex) {
      console.log(ex)
    }

    if(!connected) {
      // TODO: Make it work without a running server
      await RedisClient.connect();
    }

    return RedisClient
  } catch (ex) {
    console.log(ex)
  }
}

module.exports = {
  connect
}
