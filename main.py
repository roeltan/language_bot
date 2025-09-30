# External libraries
import os
import discord
from discord.ui import View, Button

# Internal files
import helpers

# API keys
discord_key = os.environ['DISCORD_BOT_API_KEY']

# Initialise discord bot and AI
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Channels
channels: dict[str, dict[str, str]] = {
    "語彙": {"language": "japanese", "interaction_type": "flashcards"},
    "翻訳": {"language": "japanese", "interaction_type": "translation"},
    "会話": {"language": "japanese", "interaction_type": "conversation"},
    "書き込み": {"language": "japanese", "interaction_type": "conversation"},
    "vocabulaire": {"language": "french", "interaction_type": "flashcards"},
    "traduction": {"language": "french", "interaction_type": "translation"},
    "conversation": {"language": "french", "interaction_type": "conversation"},
    "écriture": {"language": "french", "interaction_type": "composition"}
}

class SimpleButtonView(View):
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Button clicked!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    sender_id = message.author.id
    channel = message.channel
    target_language = channels[channel.name]["language"] if channel.name in channels else None
    interaction_type = channels[channel.name]["interaction_type"] if channel.name in channels else None
    
    if message.author == bot.user:
        return

    # Example: Send a button when user types "!button"
    if message.content == "!button":
        view = SimpleButtonView()
        await message.channel.send("Here is a button:", view=view)
        return

    if interaction_type == "flashcards":
        if sender_id not in helpers.flashcard_helpers[target_language].keys():
            # Flashcard helper not initialised
            flashcard_helper = helpers.FlashcardHelper(target_language=target_language, user_id=sender_id, channel=message.channel)
            helpers.flashcard_helpers[target_language][sender_id] = flashcard_helper
            await helpers.flashcard_helpers[target_language][sender_id].send_flashcard()
        else:
            # Flashcard helper initialised
            flashcard_helper= helpers.flashcard_helpers[target_language][sender_id]
            attempt = message.content

            # Check user's attempt
            await flashcard_helper.send_evaluation(attempt)

            # Regenerate deck if used up
            # TODO replace with Leitner system
            if flashcard_helper.is_deck_empty():
                await message.channel.send('Deck completed; Regenerating...')
                flashcard_helper.regenerate_deck()

            await flashcard_helper.send_flashcard()

    elif interaction_type == "translation":
        # Translation practice
        if sender_id not in helpers.translation_helpers[target_language].keys():
            # Translation helper not initialised
            translation_helper = helpers.TranslationHelper(target_language=target_language,user_id=sender_id, channel=message.channel, difficulty="medium")
            helpers.translation_helpers[target_language][sender_id] = translation_helper
            await translation_helper.start_practice()
        else:
            # Translation helper initialised
            translation_helper = helpers.translation_helpers[target_language][sender_id]
            attempt = message.content
            await translation_helper.send_response(attempt)

    elif interaction_type == "conversation":
        # Conversation practice
        pass # TODO
    elif interaction_type == "composition":
        # Composition practice
        pass # TODO

# Run bot
bot.run(discord_key)