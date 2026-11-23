import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import root_agent
from grounding import UNAVAILABLE_MESSAGE

APP_NAME = "hbntory"
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME,
                session_service=session_service)


async def answer_question_async(question):
    session = await session_service.create_session(app_name=APP_NAME,
                                                   user_id="anonymous")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    async for event in runner.run_async(user_id="anonymous",
                                        session_id=session.id,
                                        new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts
                           if p.text and not p.thought)
            if text.strip():
                return text.strip()

    return UNAVAILABLE_MESSAGE


def answer_question(question):
    return asyncio.run(answer_question_async(question))
