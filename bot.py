import os
import discord
from openai import OpenAI
import random

# API keys
discord_key = os.environ['DISCORD_BOT_API_KEY']
ai_key = os.environ['OPENAI_API_KEY']

# Initialise discord bot and AI
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
ai = OpenAI(api_key=ai_key)

# Base system prompt (attach to all prompts)
# TODO remove hardcoding of language levels
base_prompt = "You are a discord bot with username baguettecat, aimed at providing helpful practice and guidance for language learning. The server members are currently beginner Japanese and/or French learners, in the range of early Japanese JLPT N5 or French CEFR A1 proficiency."


# Channels
channels = {
    "語彙": {"language": "japanese", "interaction_type": "flashcards"},
    "翻訳": {"language": "japanese", "interaction_type": "translation"},
    "会話": {"language": "japanese", "interaction_type": "conversation"},
    "vocabulaire": {"language": "french", "interaction_type": "flashcards"},
    "traduction": {"language": "french", "interaction_type": "translation"},
    "conversation": {"language": "french", "interaction_type": "conversation"},
}

# Placeholder for flashcards
# TODO replace with actual database
flashcards = {
    "japanese": {
        "cat": "猫 (ねこ)",
        "dog": "犬 (いぬ)",
        "hello": "こんにちは",
        "thank you": "ありがとう",
        "you're welcome": "どういたしまして",
        "vending machine": "自動販売機 (じどうはんばいき)",
        "train station": "駅 (えき)",
    },
    "french": {
        "cat": "chat",
        "dog": "chien",
        "hello": "bonjour",
        "thank you": "merci",
        "you're welcome": "de rien",
        "vending machine": "distributeur automatique",
        "train station": "gare",
    }
}

# Implement class for flashcard helper per language per user
flashcard_helpers = {
    "japanese": dict(),
    "french": dict(),
}

class FlashcardHelper:
    def __init__(self, target_language, channel, user_id):
        self.target_language = target_language
        self.user_id = user_id
        self.channel = channel
        self.flashcard_top = ""
        self.flashcard_bottom = ""

        # Store list of keys for flashcards
        self.deck_keys = list(flashcards[target_language].keys())
    
    # Generate flashcards
    # TODO no repeating flashcards
    async def generate_flashcard(self):
        reply_message = await self.channel.send('Generating flashcard...')

        self.flashcard_top = random.choice(self.deck_keys)
        self.deck_keys.remove(self.flashcard_top)
        self.flashcard_bottom = flashcards[self.target_language][self.flashcard_top]
        padding = (" "*(20-len(self.flashcard_bottom))) if len(self.flashcard_bottom) < 20 else "" # pad the spoiler to 20 characters

        await reply_message.edit(content=f'{self.flashcard_top}: ||{self.flashcard_bottom}{padding}||')

    async def evaluate_attempt(self, attempt):
        # Check response
        reply_message = await self.channel.send('Evaluating...')
        system_prompt = f"Additionally, you are currently talking in the Discord channel for flashcards practice for {self.target_language}."
        user_prompt = f"My flashcard maps the word \"{self.flashcard_top}\" in English to the word \"{self.flashcard_bottom}\" in {self.target_language}. I have given \"{attempt}\" in response to the flashcard. Print (Correct,comment) or (Wrong,comment) depending on whether the I got flashcard correct, with an optional comment string (in quotes) for my own learning."

        response = ai.responses.create(
            model="gpt-5-mini", 
            store=True,
            input=[
            {"role": "system", "content": base_prompt + " " + system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        result = response.output_text
        result = result[1:] if result[0] == "(" else result # Remove leading bracket
        result = result[:-1] if result[-1] == ")" else result # Remove trailing bracket
        result = result.split(",") # Parse the text
        is_correct: bool = result[0] == "Correct"
        comment: str = result[1].strip()
        await reply_message.edit(content=f'{"✔️ Correct" if is_correct else "❌ Wrong"}\n {comment}')

    def regenerate_deck(self):
        self.deck_keys = list(flashcards[self.target_language].keys())

    def is_deck_empty(self) -> bool:
        return not self.deck_keys

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    sender_id = message.author.id
    channel = message.channel
    target_language = channels[channel.name]["language"]
    interaction_type = channels[channel.name]["interaction_type"]

    if message.author == bot.user:
        return

    if interaction_type == "flashcards":
        if sender_id not in flashcard_helpers[target_language].keys():
            # Flashcard helper not initialised
            flashcard_helper: FlashcardHelper = FlashcardHelper(target_language=target_language, user_id=sender_id, channel=message.channel)
            flashcard_helpers[target_language][sender_id] = flashcard_helper
            await flashcard_helpers[target_language][sender_id].generate_flashcard()
        else:
            # Flashcard helper initialised
            flashcard_helper: FlashcardHelper = flashcard_helpers[target_language][sender_id]
            attempt = message.content

            await flashcard_helper.evaluate_attempt(attempt)

            if flashcard_helper.is_deck_empty():
                await message.channel.send('Deck completed; Regenerating...')
                flashcard_helper.regenerate_deck()

            await flashcard_helper.generate_flashcard()

            # TODO handle reset (along with implementing no repeats)
    elif interaction_type == "translation":
        # Translation practice
        pass # TODO
    elif interaction_type == "conversation":
        # Conversation practice
        pass # TODO
    else:
        # In a non-practice setting
        pass # TODO responds once only when pinged


    # # Send response in max 2000 char parts
    # response_parts = split_message(long_message=output_text, length=2000)
    # await first_message.edit(content=response_parts[0])
    # if len(response_parts) > 1:
    #     for part in response_parts[1:]:
    #         await message.channel.send(f'{part}')


def split_message(long_message, length):
    split_messages = []
    start = 0
    end = 0

    while start < len(long_message):
        end = start + length
        if end > len(long_message):
            end = len(long_message)
        else:
            while long_message[end] != ' ':
                end -= 1
        split_messages.append(long_message[start:end])
        start = end + 1
    
    return split_messages

# Run bot
bot.run(discord_key)