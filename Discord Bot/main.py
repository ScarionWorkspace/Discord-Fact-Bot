import discord
import requests
import os
import asyncio
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv() 
# ------------------------------------------------------------------#
# Create a .env file containing the api keys for the following apis
# DEEPL
# UNSPLASH
# Your Discord Bot Token from Discord.dev
# The facts API Key
# This is very important as the Bot wont work otherwise 
# ------------------------------------------------------------------#

deepl_api_key = os.getenv('DEEPL_API_KEY')
unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
discord_token = os.getenv('DISCORD_TOKEN')
facts_api_key = os.getenv('FACTS_API_KEY')

intents = discord.Intents.default()
intents.message_content = True

# ------------------------------------------------------------------#
# If the Bot doesnt work check that these Links are still up to date
# ------------------------------------------------------------------#

api_url = 'https://api.api-ninjas.com/v1/facts'
unsplash_api_url = 'https://api.unsplash.com/photos/random'

client = discord.Client(intents=intents)


tfidf_vectorizer = TfidfVectorizer()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
    await post_fact()


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$fact'):
        response = requests.get(api_url, headers={'X-Api-Key': facts_api_key})
        if response.status_code == 200:
            fact = response.json()[0]['fact']
            
            # ------------------------------------------------------------------#
            # Translate fact to German using DeepL API
            # You can change the output language here 
            # de is german otherwise please check documentation of deepl api
            # ------------------------------------------------------------------#

            german_fact = translate_with_deepl(fact, 'en', 'de')
            
            most_important_word = extract_most_important_word(fact)
            
            image_url = get_unsplash_image(most_important_word)

            # ------------------------------------------------------------------#
            # here you can edit the way the message gets displayed
            # ------------------------------------------------------------------#

            embed = discord.Embed(title='Fact of the Day!', description=german_fact, color=0x696880)
        
            embed.set_footer(text='Bot by Scarion')
            
            if image_url:
                embed.set_image(url=image_url)
                
            await message.channel.send(embed=embed)
            
            asyncio.create_task(post_fact(message.channel))
        else:
            await message.channel.send('Failed to fetch a fact.')

# ------------------------------------------------------------------#
# We are using a TFID Vectorizer here so please dont expect perfect 
# Picture results as this Vectorizer only has limited words in its
# Matrix. 
# ------------------------------------------------------------------#

def extract_most_important_word(text):
    tfidf_matrix = tfidf_vectorizer.fit_transform([text])
    feature_names = tfidf_vectorizer.get_feature_names_out()

    max_tfidf_index = tfidf_matrix.argmax()
    most_important_word = feature_names[max_tfidf_index]

    print(f"The most important word is: {most_important_word}")  # Added print statement

    return most_important_word

# ------------------------------------------------------------------#
# Please let me know if the Translations dont work as intended
# anymore Discord: Scarion
# ------------------------------------------------------------------#
def translate_with_deepl(text, source_lang, target_lang):
    url = 'https://api-free.deepl.com/v2/translate'
    params = {
        'auth_key': deepl_api_key,
        'text': text,
        'source_lang': source_lang,
        'target_lang': target_lang
    }

    response = requests.post(url, data=params)
    if response.status_code == 200:
        return response.json()['translations'][0]['text']
    else:
        return 'Translation failed'

# ------------------------------------------------------------------#
# This is not the perfect solution im just not interested
# in a Law Suit from Google if i start webcrawling images
# ------------------------------------------------------------------#
def get_unsplash_image(query, min_width=512, min_height=512):
    params = {
        'client_id': unsplash_access_key,
        'query': query
    }

    if min_width is not None:
        params['min_width'] = min_width

    if min_height is not None:
        params['min_height'] = min_height

    response = requests.get(unsplash_api_url, params=params)

    if response.status_code == 200:
        return response.json()['urls']['regular']
    return None

# ------------------------------------------------------------------#
# Here the Facts get posted i will comment where you can decide the 
# Time how often it should Post Facts
# ------------------------------------------------------------------#

async def post_fact():
    await client.wait_until_ready()
    while not client.is_closed():
        response = requests.get(api_url, headers={'X-Api-Key': facts_api_key})
        if response.status_code == 200:
            fact = response.json()[0]['fact']
            
            german_fact = translate_with_deepl(fact, 'en', 'de')
            
            most_important_word = extract_most_important_word(fact)
            
            image_url = get_unsplash_image(most_important_word)
            
            embed = discord.Embed(title='Fact of the Day!', description=german_fact, color=0x696880)
            embed.set_footer(text='Bot by Scarion')
            
            if image_url:
                embed.set_image(url=image_url)
                
            channel = discord.utils.get(client.get_all_channels(), name='discord-fact-bot')
            if channel is not None:
                await channel.send(embed=embed)
        
        # ------------------------------------------------------------------#
        # I have made 2 extra examples for once a message every 24 hours
        # And one for once every Hour (Dont forget your API Use and max 
        # requests)
        # await asyncio.sleep(24 * 60 * 60)
        # await asyncio.sleep(1 * 60 * 60)
        # 6 * 60 * 60 Seconds = 6 Hours 
        await asyncio.sleep(6 * 60 * 60)

client.run(discord_token)
