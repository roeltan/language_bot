# External libraries
import os
from openai import OpenAI
import random
import textwrap

# Internal files
import flashcards

# API Keys
ai_key = os.environ['OPENAI_API_KEY']
ai = OpenAI(api_key=ai_key)

languages = ["french", "japanese"]

# Base prompt at the start of every conversation
# TODO remove the hardcoding of proficiency level

base_prompt = """You are a discord bot with username baguettecat, aimed at providing helpful practice and guidance for language learning. 
The server members are at about middle Japanese JLPT N5 or early French CEFR A1 in proficiency."""
class Chatbot:
    def __init__(self, target_language, user_id, channel, memory_length):
        self.target_language: str = target_language
        self.user_id = user_id
        self.channel = channel
        self.memory_length = memory_length
        self.history = []

    async def send_response(self, user_message):
        reply_message = await self.channel.send('Thinking...')

        self.history.append({"role":"user", "content":user_message})

        response = ai.responses.create(
            model="gpt-5-mini", 
            store=False,
            reasoning={ "effort": "low" },
            input=self.history,
        )
        
        result = response.output_text
        
        # Update conversation history
        self.history.append({"role": "assistant", "content": result})
        self.history = [self.history[0]] + self.history[-self.memory_length:] # Keep system prompt and most recent messages

        await reply_message.edit(content=result)

class FlashcardHelper(Chatbot):
    # Constructor
    def __init__(self, target_language, user_id, channel):
        super().__init__(target_language, user_id, channel, 2)
        self.flashcard_top: str = ""
        self.flashcard_bottom: str = ""

        # Store list of keys for flashcards
        self.curr_deck_keys = list(flashcards.decks[target_language].keys())
    
    # Generate flashcards
    async def send_flashcard(self):
        reply_message = await self.channel.send('Generating flashcard...')

        self.flashcard_top = random.choice(self.curr_deck_keys)
        self.curr_deck_keys.remove(self.flashcard_top)
        self.flashcard_bottom = flashcards.decks[self.target_language][self.flashcard_top]
        padding = (" "*(20-len(self.flashcard_bottom))) if len(self.flashcard_bottom) < 20 else "" # pad the spoiler to 20 characters

        await reply_message.edit(content=f'{self.flashcard_top}: ||{self.flashcard_bottom}{padding}||')

    async def send_evaluation(self, attempt):
        # Check response
        reply_message = await self.channel.send('Evaluating...')
        system_prompt = textwrap.dedent(f"""You are currently in the Discord channel for flashcards practice for {self.target_language}.
        The user has been shown a flashcard which shows the word/phrase \"{self.flashcard_top}\" in English, and the user is to reply with a message indicating what they believe it is in \"{self.target_language}\".
        The answer is \"{self.flashcard_bottom}\". Print \"Correct,comment\" or \"Wrong,comment\" without quotes only, depending on whether the user got the flashcard correct. 
        The comment is to aid the user's learning, and is to be very brief and primarily in English.""")
        user_prompt = f"\"{attempt}\""

        response = ai.responses.create(
            model="gpt-5-mini", 
            store=False,
            reasoning={ "effort": "low" },
            text={ "verbosity": "low" },
            input=[
            {"role": "system", "content": base_prompt + " " + system_prompt},
            {"role": "user", "content": user_prompt},
        ])
        
        result = response.output_text
         
        # Parse output
        result = result.split(",", 1)
        is_correct: bool = result[0] == "Correct"
        comment: str = result[1].strip()

        await reply_message.edit(content=f'{"✔️ Correct" if is_correct else "❌ Wrong"}\n {comment}')

    def regenerate_deck(self):
        self.curr_deck_keys = list(flashcards.decks[self.target_language].keys())

    def is_deck_empty(self) -> bool:
        return not self.curr_deck_keys

class TranslationHelper(Chatbot):
    # Constructor
    def __init__(self, target_language, user_id, channel, memory_length, difficulty):
        super().__init__(target_language, user_id, channel, 10)
        self.difficulty = difficulty
        
    async def start_practice(self):
        # TODO integrate flashcard weakpoints into difficulty setting
        # TODO allow user to select difficulty level
        # TODO allow user to choose the kind of practice that they want
        # can be done with a natural language prompt
        difficulty_settings = {
            "easy": {"exercise_count": 6, "prompt": "Each exercise is to be one short and simple sentence, using simple grammatical structures."},
            "medium": {"exercise_count": 4, "prompt": "Each exercise is to be two sentences long, utilising varied grammatical structures."},
            "hard": {"exercise_count": 2, "prompt": "Each exercise is to be a few sentences long. The exercises are diffcult, testing varied and complex grammatical structures. Prompt the user to also add in their own ideas based on exercise context, and provide appropriate feedback after."}
        }
        system_prompt = textwrap.dedent(f"""You are currently in the Discord channel for translation practice. 
        You are to generate a numbered list of exercises for the user to translate from English to {self.target_language}.
        When giving the exercises, limit extra commentary. Following a user's attempt, provide insightful feedback, and generate new exercises when all have been attempted.
        {difficulty_settings[self.difficulty]["prompt"]}""")
        user_prompt = f"Could you create me a list of {difficulty_settings[self.difficulty]["exercise_count"]} exercises?"
        self.history.append({"role":"system", "content":base_prompt + " " + system_prompt})
        await self.send_response(user_prompt)

class ConversationHelper(Chatbot):
    # Constructor
    def __init__(self, target_language, user_id, channel, memory_length, difficulty):
        super().__init__(target_language, user_id, channel, 20)
        self.difficulty = difficulty
        
    # async def start_practice(self):
    #     # TODO integrate flashcard weakpoints into difficulty setting
    #     # TODO allow user to select difficulty level
    #     # TODO allow user to choose the kind of practice that they want - conversation topic
    #     # can be done with a natural language prompt
    #     difficulty_settings = {
    #         "easy": {"exercise_count": 6, "prompt": "Each exercise is to be one short and simple sentence, using simple grammatical structures."},
    #         "medium": {"exercise_count": 4, "prompt": "Each exercise is to be two sentences long, utilising varied grammatical structures."},
    #         "hard": {"exercise_count": 2, "prompt": "Each exercise is to be a few sentences long. The exercises are diffcult, testing varied and complex grammatical structures. Prompt the user to also add in their own ideas based on exercise context, and provide appropriate feedback after."}
    #     }
    #     system_prompt = textwrap.dedent(f"""You are currently in the Discord channel for conversation practice. 
    #     You are to generate a numbered list of exercises for the user to translate from English to {self.target_language}.
    #     When giving the exercises, limit extra commentary. Following a user's attempt, provide insightful feedback, and generate new exercises when all have been attempted.
    #     {difficulty_settings[self.difficulty]["prompt"]}""")
    #     user_prompt = f"Could you create me a list of {difficulty_settings[self.difficulty]["exercise_count"]} exercises?"
    #     self.history.append({"role":"system", "content":base_prompt + " " + system_prompt})
    #     await self.send_response(user_prompt)

class CompositionHelper(Chatbot):
    pass # TODO

# Implement class for flashcard helper per language per user
flashcard_helpers: dict[str, dict[str, FlashcardHelper]] = {language: dict() for language in languages}
translation_helpers: dict[str, dict[str, TranslationHelper]] = {language: dict() for language in languages}
conversation_helpers: dict[str, dict[str, ConversationHelper]] = {language: dict() for language in languages}
composition_helpers: dict[str, dict[str, CompositionHelper]] = {language: dict() for language in languages}