import os
import re
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
            messages=[{"role": "user", "content": message.content[1:]}]
        )

        res_text = res["choices"][0]["message"]["content"]
        if len(res_text) > 2000:
            with open('res.txt','w') as f:
                f.write(res_text)
            await message.channel.send(file=discord.File('res.txt'))
        else:
            await asyncio.sleep(3)
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

            audio_file = open(file_name, "rb")
            transcript = openai.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

            transcription = ""
            for index, _dict in enumerate(transcript.segments):
                cumsum_time = 0
                index += 1
                start_time = cumsum_time + _dict["start"]
                end_time = cumsum_time + _dict["end"]
                s_h, e_h = int(start_time//(60 * 60)), int(end_time//(60 * 60))
                s_m, e_m = int(start_time//(60)), int(end_time//(60))
                if start_time%60 < 10:
                  s_s = str(start_time % 60)[:1]
                  s_s = "0"+s_s
                  s_sm = str(start_time % 60)[2:5]
                else:
                  s_s = str(start_time % 60)[:2]
                  s_sm = str(start_time % 60)[3:6]
            
                if end_time%60 < 10:
                  e_s = str(end_time % 60)[:1]
                  e_s = "0"+e_s
                  e_sm = str(end_time % 60)[2:5]
                else:
                  e_s = str(end_time % 60)[:2]
                  e_sm = str(end_time % 60)[3:6]
            
                if len(s_sm) == 1:
                  s_sm += "00"
                elif len(s_sm) == 2:
                  s_sm += "0"
            
                if len(e_sm) == 1:
                  e_sm += "00"
                elif len(e_sm) == 2:
                  e_sm += "0"
            
                transcription += f'{index}\n{s_h:02}:{s_m:02}:{s_s},{s_sm} --> {e_h:02}:{e_m:02}:{e_s},{e_sm}\n{_dict["text"]}\n\n'

            print(transcription)
            with open('res.srt','w') as f:
                f.write(transcription)
            await message.channel.send(file=discord.File('res.srt'))

            # Remove the audio file from the local filesystem
            os.remove(file_name)

        except IndexError:
            await message.channel.send("No audio file found as attachment.")


client.run(os.environ["DISCORD_TOKEN"])
