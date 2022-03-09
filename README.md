# stac-fastapi-nodb

In-memory backend for stac-fastapi. 

## Development Environment Setup

Install [pre-commit](https://pre-commit.com/#install).

Prior to commit, run:

```
pre-commit run --all-files`
```

## Building

```
docker-compose build
```

## Running API on localhost:8083

```
docker-compose up
```

## Testing

```
make test
```

## Ingest sample data

```
make ingest
```
