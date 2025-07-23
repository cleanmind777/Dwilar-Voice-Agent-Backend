from dotenv import load_dotenv
import os
import json
import logging
from typing import Any
from typing_extensions import TypedDict
from livekit.rtc import participant
from openai import OpenAI
from openai.types.beta.realtime import session
from pinecone import Pinecone, ServerlessSpec
import asyncio
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, function_tool, RunContext, get_job_context
from livekit.plugins import deepgram, silero, aws, openai, noise_cancellation, elevenlabs, google
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

class SendItem(TypedDict):
    data: str


def get_embedding(text: str) -> list:
    res = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return res.data[0].embedding


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.current_language = "en"
        self.language_names = {"en": "English", "ja": "Japanese"}
        self.greetings = {
            "en": "Hello! I'm now speaking in English.",
            "ja": "こんにちは！今、日本語で話しています。"
        }


    @function_tool()
    async def get_language(self):
        logging.debug(f"[get_language] Current language is: {self.current_language}")
        return self.current_language

    @function_tool()
    async def search_real_estate(self, location: str, price: str, bedrooms: str, context: RunContext, top_k: int = 3):
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
                "imgs": listing.get("imgs", []),
                "videos": listing.get("videos", ""),
                "floor_plan": listing.get("floor_plain", []),
                "virtual_tutor": listing.get("virtual_tutor", []),
                "property_id": listing.get("property_detail", {}).get("PROPERTY ID", ""),
                "price": listing.get("property_detail", {}).get("PRICE", ""),
                "property_type": listing.get("property_detail", {}).get("PROPERTY TYPE", ""),
                "marketed_by": listing.get("property_detail", {}).get("MARKETED BY", ""),
                "status": listing.get("property_detail", {}).get("STATUS", ""),
                "county": listing.get("property_detail", {}).get("COUNTY", ""),
                "total_sqft": listing.get("property_detail", {}).get("TOTAL SQFT", ""),
                "lot_size_unit": listing.get("property_detail", {}).get("LOT SIZE UNI", ""),
                "lot_size": listing.get("property_detail", {}).get("LOT SIZE", ""),
                "full_bathrooms": listing.get("property_detail", {}).get("FULL BATHROOMS", ""),
                "bedrooms": listing.get("property_detail", {}).get("BEDROOMS", ""),
                "right": listing.get("description_detail", {}).get("Right", ""),
                "address": listing.get("description_detail", {}).get("Address", ""),
                "access": listing.get("description_detail", {}).get("Access", []),
                "structure": listing.get("description_detail", {}).get("Structure", ""),
                "lot_catetory": listing.get("description_detail", {}).get("Lot Category", ""),
                "area_designation": listing.get("description_detail", {}).get("Area designation", ""),
                "area_of_use": listing.get("description_detail", {}).get("Area of use", ""),
                "building_ratio_and_floor_area_ratio": listing.get("description_detail", {}).get("Building ratio and floor area ratio", ""),
                "fire_protection_designation": listing.get("description_detail", {}).get("Fire protection designation", ""),
                "other_restrictions": listing.get("description_detail", {}).get("Other Restrictions", ""),
                "living_area": listing.get("description_detail", {}).get("Living Area", ""),
                "year_built": listing.get("description_detail", {}).get("Year built", ""),
                "current_status": listing.get("description_detail", {}).get("Current Status", ""),
                "delivery_date": listing.get("description_detail", {}).get("Delivery Date", ""),
                "mode_of_transaction": listing.get("description_detail", {}).get("Mode of Transaction", ""),
            })
        print(matches)
        room = get_job_context().room
        dest_identity = next(iter(room.remote_participants))
        payload_str = json.dumps(matches)

        response = await room.local_participant.perform_rpc(
            destination_identity=dest_identity,
            method="initData",
            payload=payload_str,
            response_timeout=10.0,
        )
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
            self._session.tts.update_options(gender="female", voice_name="ja-JP-Chirp3-HD-Algenib")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "あなたは親切なアシスタントです。常に日本語で応答してください。"}
            ])
        if language_code == "en":
            self._session.stt.update_options(model="nova-2", language="en")
            self._session.tts.update_options(gender="male", voice_name="en-US-Chirp-HD-D")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "You are a helpful assistant. Always respond in English."}
            ])
        self.current_language = language_code
        await self._session.say(self.greetings[language_code])

    async def entrypoint(self, ctx: agents.JobContext):
        
        session = AgentSession(
            stt=deepgram.STT(model="nova-2", language="en"),  # Multi-language detection
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.3),
            tts=google.TTS(gender="male", voice_name="en-US-Chirp-HD-D"),
            vad=silero.VAD.load(activation_threshold=0.7),
            # turn_detection=EnglishModel(),  # Disabled due to timeout issues
        )

        await session.start(
            room=ctx.room,
            agent=self,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(), 
            ),
        )

        # Store session reference for language switching
        self._session = session
        await ctx.connect()
        await session.generate_reply(
            instructions="Say first",
            allow_interruptions=False,
        )

        # Set up participant attribute change listener
        @ctx.room.on("participant_attributes_changed")
        def on_participant_attributes_changed(changed_attributes, participant):
            if "language" in changed_attributes:
                language_code = participant.attributes.get("language")
                if language_code in ["en", "ja"]:
                    asyncio.create_task(self._switch_language(language_code))


    def run(self):
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=self.entrypoint))

if __name__ == "__main__":
    Assistant().run()