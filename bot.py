import os
import discord
from openai import OpenAI

# API keys
discord_key = os.environ['DISCORD_BOT_API_KEY']
ai_key = os.environ['OPENAI_API_KEY']

# Initialise discord bot and AI
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
ai = OpenAI(api_key=ai_key)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    first_message = await message.channel.send('Thinking...')
    response = ai.responses.create(
        model="gpt-4.1", 
        store=True, 
        tools=[{"type": "web_search_preview"}],
        input=[
        {"role": "system", "content": 'You are a discord bot with username baguettecat.'},
        {"role": "user", "content": message.content},
    ])
    output_text = response.output_text
    
    # Send response in max 2000 char parts
    response_parts = split_message(long_message=output_text, length=2000)
    await first_message.edit(content=response_parts[0])
    if len(response_parts) > 1:
        for part in response_parts[1:]:
            await message.channel.send(f'{part}')

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