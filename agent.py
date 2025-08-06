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
        self.contact_info = {"email": "", "phone": ""}
        self.collecting_contact = False


    @function_tool()
    async def get_language(self):
        logging.debug(f"[get_language] Current language is: {self.current_language}")
        return self.current_language

    @function_tool()
    async def initial_greeting(self):
        """Provide initial greeting and introduction"""
        greeting = f"Hello! I'm your real estate agent from Dwilar Company. I'm here to help you find your perfect property. Before we begin, I'd like to ask for your consent to collect some information to better assist you with your property search. Is that okay with you?"
        return greeting

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

    @function_tool()
    async def show_contact_form(self, context: RunContext):
        """Show contact form to collect user's email and phone number"""
        room = get_job_context().room
        dest_identity = next(iter(room.remote_participants))
        
        # Send UI state to show contact form
        contact_form_state = {
            "showContactForm": True,
            "message": "Please provide your contact information below:"
        }
        payload_str = json.dumps(contact_form_state)

        response = await room.local_participant.perform_rpc(
            destination_identity=dest_identity,
            method="showContactForm",
            payload=payload_str,
            response_timeout=10.0,
        )
        return "Contact form displayed"

    @function_tool()
    async def submit_contact_info(self, email: str, phone: str, context: RunContext):
        """Submit collected contact information"""
        room = get_job_context().room
        dest_identity = next(iter(room.remote_participants))
        
        # Use the provided email and phone, or fall back to collected info
        final_email = email if email else self.contact_info.get("email", "")
        final_phone = phone if phone else self.contact_info.get("phone", "")
        
        # Send contact info to frontend and hide form
        contact_info = {
            "showContactForm": False,
            "contactSubmitted": True,
            "email": final_email,
            "phone": final_phone,
            "message": f"Thank you! We have received your contact information. Email: {final_email}, Phone: {final_phone}"
        }
        payload_str = json.dumps(contact_info)

        response = await room.local_participant.perform_rpc(
            destination_identity=dest_identity,
            method="submitContactInfo",
            payload=payload_str,
            response_timeout=10.0,
        )
        return f"Contact information submitted: Email: {final_email}, Phone: {final_phone}"

    @function_tool()
    async def handle_contact_form_submission(self, context: RunContext):
        """Handle when user submits contact form via frontend"""
        if self.collecting_contact:
            # Get the contact info from frontend first
            await self.get_contact_info_from_frontend(None)
            
            # The frontend has already processed the contact form submission
            # and the contact information is stored in the frontend state
            email = self.contact_info.get("email", "")
            phone = self.contact_info.get("phone", "")
            
            if email and phone:
                await self._session.say(f"Thank you for submitting your contact information through the form. I have received your email {email} and phone number {phone}. I'll be in touch with you soon about the property you're interested in.")
            else:
                await self._session.say("Thank you for submitting your contact information through the form. I have received your details and will be in touch with you soon about the property you're interested in.")
            
            self.collecting_contact = False
            self.contact_info = {"email": "", "phone": ""}
            return "Contact form submitted successfully"
        else:
            await self._session.say("I notice you submitted the contact form. Please make sure to provide both your email address and phone number.")
            return "Contact form incomplete"

    @function_tool()
    async def get_contact_info_from_frontend(self, context: RunContext):
        """Get contact information that was submitted through the frontend form"""
        room = get_job_context().room
        dest_identity = next(iter(room.remote_participants))
        
        # Request contact info from frontend
        response = await room.local_participant.perform_rpc(
            destination_identity=dest_identity,
            method="getContactInfo",
            payload="",
            response_timeout=10.0,
        )
        
        if response and response != "No contact info available":
            try:
                contact_data = json.loads(response)
                self.contact_info["email"] = contact_data.get("email", "")
                self.contact_info["phone"] = contact_data.get("phone", "")
                return f"Retrieved contact info: Email: {self.contact_info['email']}, Phone: {self.contact_info['phone']}"
            except:
                return "Error parsing contact info from frontend"
        else:
            return "No contact info available from frontend"

    @function_tool()
    async def auto_acknowledge_contact_submission(self, context: RunContext):
        """Automatically acknowledge contact form submission without waiting for user speech"""
        if self.collecting_contact:
            # Get contact info from frontend
            await self.get_contact_info_from_frontend(None)
            
            # Acknowledge the submission
            email = self.contact_info.get("email", "")
            phone = self.contact_info.get("phone", "")
            
            if email and phone:
                await self._session.say(f"Thank you for submitting your contact information. I have received your email {email} and phone number {phone}. I'll be in touch with you soon about the property you're interested in.")
            else:
                await self._session.say("Thank you for submitting your contact information. I have received your details and will be in touch with you soon about the property you're interested in.")
            
            self.collecting_contact = False
            self.contact_info = {"email": "", "phone": ""}
            return "Contact submission automatically acknowledged"
        else:
            return "No contact collection in progress"

    async def collect_contact_info(self, user_input: str):
        """Helper method to collect contact information from user input"""
        if not self.collecting_contact:
            return None
            
        # Check if user provided email
        if "@" in user_input and "." in user_input and not self.contact_info["email"]:
            # Extract email from user input
            import re
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', user_input)
            if email_match:
                self.contact_info["email"] = email_match.group()
                await self._session.say(f"Thank you for providing your email. I heard: {self.contact_info['email']}")
                return "email_collected"
        
        # Check if user provided phone number
        if not self.contact_info["phone"]:
            import re
            # Remove all non-digit characters and check if it looks like a phone number
            digits_only = re.sub(r'\D', '', user_input)
            if len(digits_only) >= 7 and len(digits_only) <= 15:  # Reasonable phone number length
                self.contact_info["phone"] = digits_only
                await self._session.say(f"Thank you for providing your phone number. I heard: {self.contact_info['phone']}")
                return "phone_collected"
        
        # If both email and phone are collected, submit the information
        if self.contact_info["email"] and self.contact_info["phone"]:
            await self.submit_contact_info(self.contact_info["email"], self.contact_info["phone"], None)
            self.collecting_contact = False
            self.contact_info = {"email": "", "phone": ""}
            return "contact_completed"
        
        return None

    async def chat(self, message: str, ctx: ChatContext) -> str:
        """Override chat method to handle contact information collection"""
        # Check if we're collecting contact information
        contact_result = await self.collect_contact_info(message)
        if contact_result:
            if contact_result == "contact_completed":
                return "Thank you for providing your contact information. I'll be in touch with you soon about the property you're interested in."
            elif contact_result == "email_collected":
                return "Great! Now could you please provide your phone number?"
            elif contact_result == "phone_collected":
                return "Perfect! I have both your email and phone number. Let me submit this information."
        
        # Check if user wants to provide contact information
        if any(word in message.lower() for word in ["yes", "sure", "okay", "contact", "email", "phone", "call", "reach"]) and not self.collecting_contact:
            self.collecting_contact = True
            await self.show_contact_form(None)
            return "I'll help you provide your contact information. Please tell me your email address first."
        
        # Check if user submitted the contact form (they might say "submitted" or "done")
        if any(word in message.lower() for word in ["submitted", "done", "finished", "complete", "sent", "contact information", "form"]) and self.collecting_contact:
            # Automatically acknowledge the contact form submission
            await self.auto_acknowledge_contact_submission(None)
            return "Contact form submission acknowledged"
        
        # Default chat behavior
        return await super().chat(message, ctx)


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
            self._session.tts.update_options(gender="female", voice_name="ja-JP-Chirp3-HD-Achernar")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "あなたは親切なアシスタントです。常に日本語で応答してください。"}
            ])
        if language_code == "en":
            self._session.stt.update_options(model="nova-2", language="en")
            self._session.tts.update_options(gender="male", voice_name="en-US-Chirp-HD-F")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "You are a helpful assistant. Always respond in English."}
            ])
        self.current_language = language_code
        await self._session.say(self.greetings[language_code])

    async def entrypoint(self, ctx: agents.JobContext):
        
        session = AgentSession(
            stt=deepgram.STT(model="nova-2", language="en"),  # Multi-language detection
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.3),
            tts=google.TTS(gender="male", voice_name="en-US-Chirp-HD-F"),
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
        
        # Check initial language from participant attributes
        initial_language = "en"  # default
        logging.info(f"Checking participant attributes for language...")
        for participant in ctx.room.remote_participants.values():
            logging.info(f"Participant {participant.identity} attributes: {participant.attributes}")
            if participant.attributes and "language" in participant.attributes:
                initial_language = participant.attributes.get("language", "en")
                logging.info(f"Found language attribute: {initial_language}")
                break
        logging.info(f"Using initial language: {initial_language}")
        
        # Set initial language
        if initial_language == "ja":
            self.current_language = "ja"
            self._session.stt.update_options(model="nova-2", language="ja")
            self._session.tts.update_options(gender="female", voice_name="ja-JP-Chirp3-HD-Achernar")
            self._session.chat_ctx = ChatContext([
                {"role": "system", "text": "あなたは親切なアシスタントです。常に日本語で応答してください。"}
            ])
            await self._session.say("こんにちは!私はDwilar Companyの不動産エージェントです。あなたの理想的な物件を見つけるお手伝いをします。まず、物件検索をより良くサポートするために、いくつかの情報を収集する許可をいただけますか？")
        else:
            self.current_language = "en"
            await self._session.say("Hello! I'm your real estate agent from Dwilar Company. I'm here to help you find your perfect property. Before we begin, I'd like to ask for your consent to collect some information to better assist you with your property search. Is that okay with you?")
        
        # Register RPC method to receive contact info from frontend
        @ctx.room.local_participant.on("rpc_request")
        async def handle_rpc_request(request):
            if request.method == "receiveContactInfo":
                try:
                    contact_data = json.loads(request.payload)
                    self.contact_info["email"] = contact_data.get("email", "")
                    self.contact_info["phone"] = contact_data.get("phone", "")
                    logging.info(f"Received contact info from frontend: {self.contact_info}")
                    return "Contact info received successfully"
                except Exception as e:
                    logging.error(f"Error processing contact info: {e}")
                    return "Error processing contact info"
            return None
        
        await ctx.connect()
        
        # Make the agent speak first with a proper greeting
        await session.generate_reply(
            instructions="Start the conversation immediately by greeting the user and introducing yourself as a real estate agent from Dwilar Company. Ask for their consent to collect data and then begin asking about their property search needs. Be proactive and initiate the conversation.",
            allow_interruptions=False,
        )

        # Set up participant attribute change listener
        @ctx.room.on("participant_attributes_changed")
        def on_participant_attributes_changed(changed_attributes, participant):
            logging.info(f"Participant attributes changed: {changed_attributes} for {participant.identity}")
            if "language" in changed_attributes:
                language_code = participant.attributes.get("language")
                logging.info(f"Language changed to: {language_code}")
                if language_code in ["en", "ja"]:
                    asyncio.create_task(self._switch_language(language_code))


    def run(self):
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=self.entrypoint))

if __name__ == "__main__":
    Assistant().run()