# FastAPI backend for AI-Powered Adaptive Learning Mentor
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    answer: Optional[str] = None

class QuizSubmission(BaseModel):
    answers: List[str]

class FeedbackRequest(BaseModel):
    user_input: str

# --- Endpoints ---
@app.get("/quiz", response_model=List[QuizQuestion])
def get_quiz():
    # Placeholder: Generate quiz questions using LangGraph + OpenRouter
    return [
        QuizQuestion(question="What is 2 + 2?", options=["3", "4", "5"]),
        QuizQuestion(question="What is the capital of France?", options=["Berlin", "Paris", "Rome"]),
    ]

@app.post("/quiz/submit")
def submit_quiz(submission: QuizSubmission):
    # Placeholder: Evaluate answers and return score/feedback
    correct = ["4", "Paris"]
    score = sum([a == c for a, c in zip(submission.answers, correct)])
    return {"score": score, "total": len(correct)}

@app.post("/feedback")
def get_feedback(req: FeedbackRequest):
    # Placeholder: Use OpenRouter model for sentiment analysis and motivational feedback
    return {"feedback": "Keep going! You're making great progress."}

@app.get("/content")
def get_content():
    # Placeholder: Return personalized learning content
    return {"title": "Introduction to Math", "body": "Math is the study of numbers, shapes, and patterns."}

# --- Health check ---
@app.get("/")
def health():
    return {"status": "ok"}
