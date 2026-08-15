# Ideal Local Business Engine

Lead discovery, website analysis, AI-assisted demo generation, and outreach preparation for Ideal SEO Agency.

## MVP
- Lead search workspace
- Website/SEO audit input
- Lead scoring
- Gemini content generation
- Pexels image search integration
- Demo website generation foundation
- Outreach draft generation

## Run
1. Copy `.env.example` to `.env`
2. Add your Gemini API key and optional Pexels API key
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload`
5. Open `http://127.0.0.1:8000`

Never commit API keys. Use environment variables.
