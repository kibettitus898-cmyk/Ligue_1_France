---
title: EPL Predictor API
emoji: ⚽
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# EPL Predictor API

FastAPI backend for Premier League match prediction and value-bet analysis.

## What it does

- Predicts match outcomes: Home Win, Draw, Away Win.
- Uses an ensemble ML model with engineered football features.
- Supports upcoming fixtures and optional odds-based EV analysis.

## Main endpoints

- `GET /health`
- `POST /api/v1/predict`
- `GET /api/v1/predict/upcoming?limit=20`

## Notes

- This Space runs with Docker.
- The frontend should call this API using the deployed Space URL.
- Make sure your environment variables are configured in the Space settings.