# Velodrome Finance HTTP API 🚲💨🕸️

Velodrome Finance HTTP API is used by our app to fetch tokens and liquidity
pool pairs.

Please make sure you have [Docker](https://docs.docker.com/install/) first.

To build the image, run:
```
$ docker build ./ -t velodrome/api
```

Next, make a copy of the `env.example` file, and update the relevant variables.

Finally, to start the container, run:
```
$ docker run --rm --env-file=env.example.copy -v $(pwd):/app -p 3001:3001 -w /app -it velodrome/api
```
