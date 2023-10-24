import discord
import requests
import os
import asyncio
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv()  # Load environment variables from .env file

deepl_api_key = os.getenv('DEEPL_API_KEY')
unsplash_access_key = os.getenv('UNSPLASH_ACCESS_KEY')
discord_token = os.getenv('DISCORD_TOKEN')
facts_api_key = os.getenv('FACTS_API_KEY')

intents = discord.Intents.default()
intents.message_content = True

api_url = 'https://api.api-ninjas.com/v1/facts'
unsplash_api_url = 'https://api.unsplash.com/photos/random'

client = discord.Client(intents=intents)

# Define the TF-IDF vectorizer
tfidf_vectorizer = TfidfVectorizer()

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
    # Start the background fact posting
    await post_fact()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$fact'):
        response = requests.get(api_url, headers={'X-Api-Key': facts_api_key})
        if response.status_code == 200:
            fact = response.json()[0]['fact']  # Assuming the response is in JSON format
            
            # Translate fact to German using DeepL API
            german_fact = translate_with_deepl(fact, 'en', 'de')
            
            # Extract the most important word from the English fact
            most_important_word = extract_most_important_word(fact)
            
            # Get an image related to the most important word from Unsplash
            image_url = get_unsplash_image(most_important_word)
            
            # Create an embedded message
            embed = discord.Embed(title='Fact of the Day!', description=german_fact, color=0x696880)
            embed.set_footer(text='Bot by Scarion')
            
            if image_url:
                embed.set_image(url=image_url)
                
            await message.channel.send(embed=embed)
            
            # Start the background fact posting
            asyncio.create_task(post_fact(message.channel))
        else:
            await message.channel.send('Failed to fetch a fact.')

def extract_most_important_word(text):
    tfidf_matrix = tfidf_vectorizer.fit_transform([text])
    feature_names = tfidf_vectorizer.get_feature_names_out()

    # Get the word with the highest TF-IDF score
    max_tfidf_index = tfidf_matrix.argmax()
    most_important_word = feature_names[max_tfidf_index]

    print(f"The most important word is: {most_important_word}")  # Added print statement

    return most_important_word

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

async def post_fact():
    await client.wait_until_ready()
    while not client.is_closed():
        response = requests.get(api_url, headers={'X-Api-Key': facts_api_key})
        if response.status_code == 200:
            fact = response.json()[0]['fact']  # Assuming the response is in JSON format
            
            # Translate fact to German using DeepL API
            german_fact = translate_with_deepl(fact, 'en', 'de')
            
            # Extract the most important word from the English fact
            most_important_word = extract_most_important_word(fact)
            
            # Get an image related to the most important word from Unsplash
            image_url = get_unsplash_image(most_important_word)
            
            # Create an embedded message
            embed = discord.Embed(title='Fact of the Day!', description=german_fact, color=0x696880)
            embed.set_footer(text='Bot by Scarion')
            
            if image_url:
                embed.set_image(url=image_url)
                
            channel = discord.utils.get(client.get_all_channels(), name='discord-fact-bot')
            if channel is not None:
                await channel.send(embed=embed)
        
        # Wait for 6 hours before fetching the next fact
        await asyncio.sleep(6 * 60 * 60)

# Run the bot
client.run(discord_token)
