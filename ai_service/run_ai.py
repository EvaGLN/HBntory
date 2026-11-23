#!/usr/bin/python3
"""Main entry point to initialize the AI application."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "backoffice"))

from ai_app import create_ai_app
from answer import answer_question
from models import make_engine
from stock_tools import configure

configure(make_engine(os.environ.get("DATABASE_URL", "sqlite:///hbntory.db")))
app = create_ai_app(answer_question)
