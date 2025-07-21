from dotenv import load_dotenv
import os
import json
import logging
from openai import OpenAI
from openai.types.beta.realtime import session
from pinecone import Pinecone, ServerlessSpec
import asyncio
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, function_tool
from livekit.plugins import deepgram, silero, aws, openai, noise_cancellation, elevenlabs
# from livekit.plugins.turn_detector.english import EnglishModel  # Disabled due to timeout issues
from prompt import SYSTEM_PROMPT

load_dotenv()
# import env
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

openai_client = OpenAI(api_key=OPENAI_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding(text: str) -> list:
    res = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return res.data[0].embedding


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.current_language = "en"  # Default to Japanese
        self.language_names = {"en": "English", "ja": "Japanese"}
        self.greetings = {
            "en": "Hello! I'm now speaking in English. How can I help you today?",
            "ja": "こんにちは！今、日本語で話しています。今日はどのようにお手伝いできますか？"
        }

    @function_tool()
    async def search_real_estate(self, location: str, price: str, bedrooms: str, top_k: int = 3):
        # Build your query vector from the input (use your embedding logic)
        query = f"{bedrooms} bedroom property in {location} priced around {price}"
        # Use the same embedding model as during upsert
        embedding = await asyncio.to_thread(get_embedding, query)
        results = await asyncio.to_thread(index.query, vector=embedding, top_k=top_k, include_metadata=True)
        matches = []
        for match in results['matches']:
            listing = json.loads(match['metadata']['full'])
            matches.append({
                "title": listing.get("title", "Untitled"),
                "address": listing.get("description_detail", {}).get("Address", ""),
                "price": listing.get("property_detail", {}).get("PRICE", ""),
                "bedrooms": listing.get("property_detail", {}).get("BEDROOMS", ""),
            })
        print(matches)
        return matches


    @function_tool
    async def end_call(self):
        # Use the session property from the Agent class
        if hasattr(self, '_activity') and self._activity:
            await self._activity.session.say("Thank you for calling. Goodbye!")
            await self._activity.session.aclose()


    async def _switch_language(self, language_code: str):
        if language_code == self.current_language:
            await self._session.say(f"I'm already speaking in {self.language_names[language_code]}.")
            return
        # Update chat context for language-specific instructions
        if language_code == "ja":
            self._session.stt.update_options(model="nova-2", language="ja")
            # self._session.tts = aws.TTS(language="ja-JP", voice="Mizuki", speech_engine="standard", region="us-east-1")
            self._session.tts = aws.TTS(language="ja-JP", voice="Mizuki", speech_engine="standard", region="us-east-1")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "あなたは親切なアシスタントです。常に日本語で応答してください。"}
            ])
        if language_code == "en":
            self._session.stt.update_options(model="nova-2", language="en")
            self._session.tts.update_options(model="aura-asteria-en")
            # self._session.tts = aws.TTS(language="en-US", voice="Joanna", speech_engine="neural", region="us-east-1")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "You are a helpful assistant. Always respond in English."}
            ])
        self.current_language = language_code
        await self._session.say(self.greetings[language_code])

    async def entrypoint(self, ctx: agents.JobContext):
        
        session = AgentSession(
            stt=deepgram.STT(model="nova-2", language="en"),  # Multi-language detection
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.3),
            tts=deepgram.TTS(model="aura-asteria-en"),
            vad=silero.VAD.load(activation_threshold=0.7),
            # turn_detection=EnglishModel(),  # Disabled due to timeout issues
        )

        await session.start(
            room=ctx.room,
            agent=Assistant(),
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(), 
            ),
        )

        # Store session reference for language switching
        self._session = session

        # Set up participant attribute change listener
        @ctx.room.on("participant_attributes_changed")
        def on_participant_attributes_changed(changed_attributes, participant):
            if "language" in changed_attributes:
                language_code = participant.attributes.get("language")
                if language_code in ["en", "ja"]:
                    asyncio.create_task(self._switch_language(language_code))

        await ctx.connect()

        await session.generate_reply(
            instructions="Say first",
            allow_interruptions=False,
        )

    async def on_tool_result(self, session, tool_name, result):
        try:
            if tool_name == "search_real_estate":
                # Ensure result is serializable (list of dicts)
                payload = json.dumps({
                    "type": "matches",
                    "data": result
                }).encode("utf-8")
                await session.room.local_participant.publish_data(
                    payload=payload,
                    topic="real_estate_matches",
                    reliable=True  # Reliable delivery, max 15KB
                )
        except Exception as e:
            import logging  
            logging.exception("Failed to send matches to frontend")



    def run(self):
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=self.entrypoint))


if __name__ == "__main__":
    Assistant().run()