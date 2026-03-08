from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import os

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# =====================
# LOAD ENV
# =====================
load_dotenv(".env.local")

JOB_POSITION = "Python Developer"


# =====================
# MONGODB
# =====================
def load_questions_from_mongodb(user_id):

    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["OptiCodeDB"]
    collection = db["interviewquestions"]

    try:
        doc = collection.find_one({"user": ObjectId(user_id)})
    except:
        return []

    if not doc or "questions" not in doc:
        return []

    return doc["questions"]


# =====================
# INTERVIEW AGENT
# =====================
class Assistant(Agent):

    def __init__(self, questions):

        self.questions = questions
        self.index = 0
        self.total = len(questions)

        super().__init__(
            instructions="""
You are an AI interviewer.

Rules:
- Ask questions
- Evaluate answers
- Be professional
"""
        )

    async def on_user_message(self, message: str):

        current = self.questions[self.index]

        prompt = f"""
You are a senior Python interviewer.

Question:
{current['question']}

Correct Answer:
{current['answer']}

Candidate Answer:
{message}

Start with exactly one:

✅ Correct
⚠️ Partially Correct
❌ Incorrect

Then give short explanation (1-3 sentences).
"""

        feedback = await self.llm.generate(prompt)

        await self.say(feedback)

        self.index += 1

        if self.index < self.total:

            await self.say(self.questions[self.index]["question"])

        else:

            await self.say(
                "That concludes the interview. Thank you for participating."
            )


# =====================
# SERVER
# =====================
server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):

    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="google/gemini-2.5-flash",
        tts="cartesia/sonic-3",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # Temporary agent to connect room
    temp_agent = Agent(
        instructions="You are a system agent waiting for interview initialization."
    )

    await session.start(
        room=ctx.room,
        agent=temp_agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params:
                noise_cancellation.BVCTelephony()
                if params.participant.kind
                == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                else noise_cancellation.BVC(),
            ),
        ),
    )

    # Wait for user
    participant = await ctx.wait_for_participant()

    user_id = participant.identity

    print("Interview started for user:", user_id)

    # Load questions
    questions = load_questions_from_mongodb(user_id)

    if len(questions) == 0:
        await session.say("No interview questions found for your account.")
        return

    # Replace agent with interview assistant
    assistant = Assistant(questions)
    session.agent = assistant

    # Start interview
    await session.say(
        f"""
Hello 👋

Welcome to your {JOB_POSITION} interview.

Let's begin.

{questions[0]['question']}
"""
    )


# =====================
# RUN
# =====================
if __name__ == "__main__":
    agents.cli.run_app(server)