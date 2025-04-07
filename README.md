# Video Generator API

Backend service for generating videos from text input.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
PORT=5001
```

## Running Locally

```bash
python server.py
```

The server will start on http://localhost:5001

## API Endpoints

- `POST /generate`: Generate a new video
- `GET /status/<job_id>`: Check video generation status
- `GET /download/<job_id>`: Download generated video

## Deployment

This service is configured for deployment on Render. The `render.yaml` file contains the necessary configuration.

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `PORT`: Port to run the server on (default: 5001) 