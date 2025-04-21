# Trade Analysis API

This is a FastAPI backend that powers the trading coach and analysis features of the ReflectIQ trading application. It uses Hugging Face's distilGPT2 model to analyze trades and provide insights.

## Features

- Trade analysis based on data from Supabase
- AI-powered trading coach responses
- Win rate and performance metrics calculation

## Deployment

This project is designed to be deployed to Vercel:

1. Connect this repository to Vercel
2. Set up the following environment variables:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY`: Your Supabase service role key

## Local Development

To run this project locally:

1. Install dependencies: `pip install -r requirements.txt`
2. Run with uvicorn: `uvicorn app:app --reload`

Make sure to set the environment variables either in your shell or in a `.env` file.
