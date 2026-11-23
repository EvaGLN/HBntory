#!/usr/bin/python3
"""Expose an HTTP endpoint to send user questions to the AI Agent."""

import logging

from flask import Flask, jsonify, request

MAX_QUESTION = 500

log = logging.getLogger("hbntory.ai")


def create_ai_app(answer_fn):
    """Create and configure the Flask app with the /ask endpoint."""
    app = Flask(__name__, static_folder="../client_web", static_url_path="")

    @app.get("/")
    def index():
        """Return the client web page."""
        return app.send_static_file("index.html")

    @app.post("/ask")
    def ask():
        """Validate the incoming request, pass it to answer_fn and return the answer."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            data = {}
        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify(error="question must be a non-empty string"), 400
        if len(question) > MAX_QUESTION:
            return jsonify(error="question " +
                           f"is too long (max {MAX_QUESTION} characters)"), 400
        try:
            answer = answer_fn(question.strip())
        except TimeoutError:
            return jsonify(error="the assistant took too long"), 504
        except Exception:
            log.exception("agent failure")
            return jsonify(error="the assistant is unavailable"), 502
        return jsonify(answer=answer)
    return app
