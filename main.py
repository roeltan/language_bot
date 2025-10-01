# External libraries
import os
import discord
from discord import app_commands
from discord.ext import commands

# Internal files
import helpers

# API keys
discord_key = os.environ['DISCORD_BOT_API_KEY']

# Initialise discord bot and AI
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents, command_prefix="!")

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

@bot.tree.command(name="start", description="Start practice session")
@app_commands.describe(
    difficulty="Choose a difficulty",
    custom_instruction="Add custom instructions"
)
@app_commands.choices(difficulty=[
    app_commands.Choice(name="Easy", value="easy"),
    app_commands.Choice(name="Medium", value="medium"),
    app_commands.Choice(name="Hard", value="hard"),
])
async def start(
    interaction: discord.Interaction,
    difficulty: app_commands.Choice[str],
    custom_instruction: str = None
):
    """Starts the practice session with difficulty and custom instructions configured.\n
    Restarts practice session if already started."""
    sender_id = interaction.user.id
    channel = interaction.channel
    target_language = channels[channel.name]["language"]
    interaction_type = channels[channel.name]["interaction_type"]
    
    if interaction_type == "flashcards":
        if sender_id in helpers.flashcard_helpers[target_language].keys():
            # Delete current helper (if exists)
            del helpers.flashcard_helpers[target_language][sender_id]
        
        # Initialise helper
        flashcard_helper = helpers.FlashcardHelper(target_language=target_language, user_id=sender_id, channel=channel, memory_length=2, 
                                                   difficulty=difficulty.value,
                                                   custom_instruction=custom_instruction)
        helpers.flashcard_helpers[target_language][sender_id] = flashcard_helper
        await interaction.response.send_message("New practice session successfully started!", ephemeral=True)
        await helpers.flashcard_helpers[target_language][sender_id].send_flashcard()
        
    elif interaction_type == "translation":
        if sender_id in helpers.translation_helpers[target_language].keys():
            # Delete current helper (if exists)
            del helpers.translation_helpers[target_language][sender_id]
        
        # Initialise helper
        translation_helper = helpers.TranslationHelper(target_language=target_language, user_id=sender_id, channel=channel, memory_length=10, 
                                                       difficulty=difficulty.value,
                                                       custom_instruction=custom_instruction)
        helpers.translation_helpers[target_language][sender_id] = translation_helper
        await interaction.response.send_message("New practice session successfully started!", ephemeral=True)
        await translation_helper.start_practice()

    # TODO for other interaction types

@bot.tree.command(name="end", description="End exercise")
async def end(interaction: discord.Interaction):
    """Ends the current practice."""
    sender_id = interaction.user.id
    channel = interaction.channel
    target_language = channels[channel.name]["language"]
    interaction_type = channels[channel.name]["interaction_type"]

    if sender_id in helpers.translation_helpers[target_language].keys():
        del helpers.translation_helpers[target_language][sender_id]
        await interaction.response.send_message('Current practice session successfully ended.', ephemeral=True)
    else:
        await interaction.response.send_message('You do not have an active practice session.', ephemeral=True)

    # TODO for other interaction types

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')    
    await bot.tree.sync()  # Sync slash commands
    print('Commands synced!')

@bot.event
async def on_message(message):
    sender_id = message.author.id
    channel = message.channel
    target_language = channels[channel.name]["language"] if channel.name in channels else None
    interaction_type = channels[channel.name]["interaction_type"] if channel.name in channels else None
    
    if message.author == bot.user:
        return

    if interaction_type == "flashcards":
        if sender_id in helpers.flashcard_helpers[target_language].keys():
            # Flashcard helper initialised
            flashcard_helper = helpers.flashcard_helpers[target_language][sender_id]
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
        if sender_id in helpers.translation_helpers[target_language].keys():
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