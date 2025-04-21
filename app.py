from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import supabase
import random
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="Trade Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
def get_supabase_client():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Missing Supabase credentials")
    
    return supabase.create_client(supabase_url, supabase_key)

# Data models
class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    user_id: str

class TradeAnalysisResult(BaseModel):
    win_rate: float
    avg_profit_loss: float
    strategies: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]

# Helper function to extract user ID from Authorization header
async def get_user_id(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # In a real implementation, validate the token with Supabase
    # For now, we'll just extract the user ID from the request body
    return None  # Will be overridden by the request body

# Helper function to analyze trades
def analyze_trades(trades) -> TradeAnalysisResult:
    if not trades:
        return TradeAnalysisResult(
            win_rate=0.0,
            avg_profit_loss=0.0,
            strategies=[],
            strengths=[],
            weaknesses=[],
            suggestions=["Start recording your trades to get personalized analysis."]
        )
    
    # Calculate win rate
    profitable_trades = [trade for trade in trades if trade.get('pnl', 0) > 0]
    win_rate = len(profitable_trades) / len(trades) if trades else 0
    
    # Calculate average profit/loss
    total_pnl = sum(trade.get('pnl', 0) for trade in trades)
    avg_pnl = total_pnl / len(trades) if trades else 0
    
    # Extract unique strategies
    strategies = list(set(trade.get('trade_type', '').strip() for trade in trades if trade.get('trade_type')))
    
    # Generate strengths, weaknesses and suggestions based on the data
    strengths = []
    weaknesses = []
    suggestions = []
    
    # Basic analysis rules
    if win_rate > 0.5:
        strengths.append("Above 50% win rate")
    else:
        weaknesses.append("Below 50% win rate")
        suggestions.append("Focus on improving your win rate by reviewing losing trades")
    
    if avg_pnl > 0:
        strengths.append("Positive average P&L")
    else:
        weaknesses.append("Negative average P&L")
        suggestions.append("Work on improving your average profit per trade")
    
    if len(strategies) > 2:
        strengths.append(f"Diverse trading approaches ({len(strategies)} different strategies)")
    else:
        suggestions.append("Consider exploring more trading strategies to diversify your approach")
    
    # Look for patterns in notes
    all_notes = " ".join([trade.get('notes', '') for trade in trades if trade.get('notes')])
    if all_notes:
        if "emotion" in all_notes.lower() or "fear" in all_notes.lower() or "greed" in all_notes.lower():
            weaknesses.append("Emotional trading noted in multiple trades")
            suggestions.append("Work on emotional discipline during trading")
        
        if "plan" in all_notes.lower():
            strengths.append("Evidence of trade planning in notes")
            
    return TradeAnalysisResult(
        win_rate=win_rate,
        avg_profit_loss=avg_pnl,
        strategies=strategies,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions
    )

# Generate trading coach response using rules instead of ML
def generate_coach_response(user_message: str, trade_analysis: TradeAnalysisResult) -> str:
    # Dictionary of pre-crafted responses for different topics
    responses = {
        "win_rate": [
            f"Your win rate is {trade_analysis.win_rate:.1%}. " + 
            ("This is above the 50% mark, which is great! " if trade_analysis.win_rate > 0.5 else 
             "This is below 50%, but remember that with a good risk-reward ratio, you can still be profitable. ") +
            "Focus on the quality of your setups rather than quantity.",
            
            f"Based on your trading history, you're winning {trade_analysis.win_rate:.1%} of the time. " +
            "Remember that even the best traders don't win every trade. " +
            "The key is to ensure your winners are bigger than your losers."
        ],
        
        "improvement": [
            f"To improve your trading results, I recommend focusing on these key areas: {', '.join(trade_analysis.suggestions[:2])}. " +
            "Keep a detailed trading journal and review it weekly to identify patterns.",
            
            "The path to improvement starts with consistency and discipline. " +
            f"Based on your trades, I suggest working on: {', '.join(trade_analysis.suggestions[:2])}. " +
            "Consider setting specific, measurable goals for each trading session."
        ],
        
        "strengths": [
            f"Your strengths as a trader include: {', '.join(trade_analysis.strengths)}. " +
            "Continue to build on these while addressing your areas for improvement.",
            
            f"You're doing well with {', '.join(trade_analysis.strengths)}. " +
            "These are solid foundations to build upon. Consider focusing next on your risk management approach."
        ],
        
        "default": [
            f"Looking at your trading data with a win rate of {trade_analysis.win_rate:.1%} and average P&L of ${trade_analysis.avg_profit_loss:.2f}, " +
            f"I recommend focusing on: {', '.join(trade_analysis.suggestions[:2])}. " +
            "Would you like more specific advice on a particular aspect of your trading?",
            
            "Based on your trading history, I see both strengths and areas for improvement. " +
            f"Your win rate is {trade_analysis.win_rate:.1%}, and I'd suggest focusing on {trade_analysis.suggestions[0] if trade_analysis.suggestions else 'maintaining a trading journal'}. " +
            "What specific aspect of your trading would you like to discuss?"
        ]
    }
    
    # Determine which category the message falls into
    category = "default"
    if any(term in user_message.lower() for term in ["win rate", "winning", "success rate"]):
        category = "win_rate"
    elif any(term in user_message.lower() for term in ["improve", "better", "enhance", "increase", "boost"]):
        category = "improvement"
    elif any(term in user_message.lower() for term in ["strength", "good at", "excel", "positive"]):
        category = "strengths"
    
    # Return a random response from the appropriate category
    return random.choice(responses[category])

# Endpoint to get trade statistics
@app.get("/api/trade-analysis", response_model=TradeAnalysisResult)
async def get_trade_analysis(user_id: str, supabase = Depends(get_supabase_client)):
    try:
        # Query trades for the user
        response = supabase.table("trades").select("*").eq("user_id", user_id).execute()
        trades = response.data
        
        # Analyze the trades
        analysis = analyze_trades(trades)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing trades: {str(e)}")

# Chat endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest, supabase = Depends(get_supabase_client)):
    try:
        # Get the last user message
        last_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                last_message = msg.content
                break
        
        if not last_message:
            return {"response": "I didn't receive a message to respond to."}
        
        # Get trades for analysis
        response = supabase.table("trades").select("*").eq("user_id", request.user_id).execute()
        trades = response.data
        
        # Analyze trades
        analysis = analyze_trades(trades)
        
        # Generate response
        coach_response = generate_coach_response(last_message, analysis)
        
        return {
            "response": coach_response,
            "analysis": analysis.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 