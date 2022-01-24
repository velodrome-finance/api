const config = require('../config')
const redis = require('redis');

const connect = async () => {
  try {
    const RedisClient = redis.createClient({
      url: `redis://${config.redis.host}:${config.redis.port}`
    })

    const connected = false
    try {
      const pong = await RedisClient.ping()
      console.log(pong)
      if(pong == 'pong') {
        connected = true
      }
    } catch(ex) {

    }

    if(!connected) {
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
