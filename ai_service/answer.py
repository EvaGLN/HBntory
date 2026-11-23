import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from grouding import UNAVAILABLE_MESSAGE

APP_NAME = "hbntory"
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name=APP_NAME,
                session_service=session_service)


async def answer_question_async(question):
    session = await session_service.create_session(app_name=APP_NAME,
                                                   user_id="anonnymous")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    async for event in runner.run_async(user_id="anonymous",
                                        session_id=session.id,
                                        new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            return event.content.parts[0].text

    return UNAVAILABLE_MESSAGE


def answer_question(question):
    return asyncio.run(answer_question_async(question))
