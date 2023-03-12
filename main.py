import os
import discord
import openai
import asyncio

openai.api_key = os.environ["OPENAI_API_KEY"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} loggin!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$'):
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.content}]
        )

        res_text = res["choices"][0]["message"]["content"]
        if len(res_text) > 2000:
            with open('res.txt','w') as f:
                f.write(res_text)
            await message.channel.send(file=discord.File('res.txt'))
        else:
            await message.channel.send(res_text)

    if message.content.startswith('%'):
        response = openai.Image.create(
            prompt=message.content[1:],
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        embed = discord.Embed()
        embed.set_image(url=image_url)

        await message.channel.send(embed=embed)

    if message.content.startswith('#whisper'):
        try:
            attachment = message.attachments[0]
            file_name = attachment.filename

            # Download the file
            await attachment.save(file_name)

            files = open(file_name, "rb")
            transcription = openai.Audio.transcribe("whisper-1", files, "ja")
            restrans = transcription["text"].replace(" ","\n")
            if len(restrans) > 2000:
                with open('res.txt','w') as f:
                    f.write(restrans)
                await message.channel.send(file=discord.File('res.txt'))
            else:
                await message.channel.send(restrans)

            # Remove the audio file from the local filesystem
            os.remove(file_name)

        except IndexError:
            await message.channel.send("No audio file found as attachment.")


client.run(os.environ["DISCORD_TOKEN"])
