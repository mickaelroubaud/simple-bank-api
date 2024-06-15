# A really simple bank API

## Introduction
This is an example of a basic bank API, using FastApi and Pydantic.
It does not use any DB.

## How to run
The API is containerized, so just run the docker container :

``docker run -d --name bankapi -p 8000:8000 bankapi``

The fastAPI swagger page will be accessible on http://localhost:8000/docs.