#!/usr/bin/python3
"""Main entry point to initialize the AI application."""

from ai_app import create_ai_app
from answer import answer_question

app = create_ai_app(answer_question)
