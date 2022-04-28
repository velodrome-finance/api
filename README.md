# Velodrome HTTP API 🕸️

The API takes care of the token lists, pairs pricing (caching and updating it).

## Configuration

Make a copy of the `env.example` to `.env` file and update the defaults or deploy
the updated variables from there.

## Development

Build the Docker image:

```
$ docker build ./ -t velodrome/api
```

Start the container using:

```
$ docker run --env-file .env -p 3000:3000 --rm -it velodrome/api
```

## Pairs Update

To trigger an assets update, send a request to the `updateAssets` endpoint:
```
$ curl -u <AUTH_USER:AUTH_PASS> https://api.endpoint/api/v1/updateAssets
```
