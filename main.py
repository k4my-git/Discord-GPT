import os
import re
import discord
from discord.ui import Select, View
from discord import app_commands
import openai
import asyncio
import time

openai.api_key = os.environ["OPENAI_API_KEY"]

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

chat_model="gpt-4o-mini"
#audio_model="gpt-4o"

@client.event
async def on_ready():
    print(f'{client.user} loggin!')
    await tree.sync()

class SelectView(View):
     @discord.ui.select(
         cls=Select,
         placeholder="モデルを選択してください",
         options=[
            discord.SelectOption(label="gpt-4o"),
            discord.SelectOption(label="gpt-4o-mini"),
            discord.SelectOption(label="gpt-3.5-turbo-0125"),
            discord.SelectOption(label="gpt-3.5-turbo-0613")
        ]
     )
     async def selectMenu(self, interaction: discord.Interaction, select: Select):
         global chat_model
         chat_model = select.values[0]
         select.disabled = True
         await interaction.response.edit_message(view=self)
         await interaction.followup.send(f"チャットモデルを【{select.values[0]}】に変更しました")

@tree.command(name="model_change",description="Chat-Gptのモデルの変更")
async def chat_model_change(interaction: discord.Interaction):
    view = SelectView()
    await interaction.response.send_message("", view=view)

@tree.command(name="chatgpt",description="Chat-Gptのコマンド")
async def chat_gpt(interaction: discord.Interaction, text:str):
    await interaction.response.defer()
    #start=time.time()
    res = openai.chat.completions.create(
            model=chat_model,
            messages=[{"role": "user", "content": text}]
        )
    res_text = res.choices[0].message.content
    #end = time.time() - start
    if len(res_text) > 2000:
        with open('res.txt','w') as f:
            f.write(res_text)
        await interaction.followup.send(file=discord.File('res.txt'))
    else:
        await interaction.followup.send(f"{res_text}")

@tree.command(name="dalle",description="Dall-e-3のコマンド(画像)")
async def dalle(interaction: discord.Interaction, prompt:str):
    await interaction.response.defer()
    try:
        response = openai.images.generate(
              model="dall-e-3",
              prompt=prompt,
              size="1024x1024",
              quality="standard",
              n=1,
            )
        image_url = response.data[0].url
        #await asyncio.sleep(5)
        embed = discord.Embed()
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
    except:
        await interaction.followup.send("安全システムの結果、リクエストは拒否されました。あなたのプロンプトには、当社の安全システムで許可されていないテキストが含まれている可能性があります。")

@tree.command(name="whisper",description="Whisperのコマンド(音声)")
async def whisper(interaction: discord.Interaction, prompt:str, audio: discord.Attachment):
    await interaction.response.defer()
    try:
        attachment = audio
        file_name = attachment.filename
        await attachment.save(file_name)
        audio_file = open(file_name, "rb")

        prompts = prompt
        transcript = openai.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            prompt = prompts
        )

        def convert_time(times):
            if times%60 < 10:
                sec = str(times % 60)[:1]
                sec = "0"+sec
                ms = str(times % 60)[2:5]
            else:
                sec = str(times % 60)[:2]
                ms = str(times % 60)[3:6]
            
            if len(ms) == 1:
              sec += "00"
            elif len(ms) == 2:
              sec += "0"
            
            return sec, ms

        transcription = ""
        for index, _dict in enumerate(transcript.segments):
            cumsum_time = 0
            index += 1
            start_time = cumsum_time + _dict["start"]
            end_time = cumsum_time + _dict["end"]
            s_h, e_h = int(start_time//(60 * 60)), int(end_time//(60 * 60))
            s_m, e_m = int(start_time//(60)), int(end_time//(60))
            s_s, s_sm = convert_time(start_time)
            e_s, e_sm = convert_time(end_time)
        
            transcription += f'{index}\n{s_h:02}:{s_m:02}:{s_s},{s_sm} --> {e_h:02}:{e_m:02}:{e_s},{e_sm}\n{_dict["text"]}\n\n'

        #print(transcription)
        with open('res.srt','w') as f:
            f.write(transcription)
        await interaction.followup.send(file=discord.File('res.srt'))

        # Remove the audio file from the local filesystem
        os.remove(file_name)

    except Exception as error:
        await interaction.followup.send(error)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$'):
        res = openai.chat.completions.create(
            model="gpt-3.5-turbo-0613",
            messages=[{"role": "user", "content": message.content[1:]}]
        )
        res_text = res.choices[0].message.content
        
        if len(res_text) > 2000:
            with open('res.txt','w') as f:
                f.write(res_text)
            await message.channel.send(file=discord.File('res.txt'))
        else:
            await asyncio.sleep(3)
            await message.channel.send(res_text)

    if message.content.startswith('%'):
        response = openai.images.generate(
            model="dall-e-3",
            prompt=message.content[1:],
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        await asyncio.sleep(5)
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

            prompts = message.content.replace('#whisper','')
            transcript = openai.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
                prompt = prompts
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

            #print(transcription)
            with open('res.srt','w') as f:
                f.write(transcription)
            await message.channel.send(file=discord.File('res.srt'))

            # Remove the audio file from the local filesystem
            os.remove(file_name)

        except IndexError:
            await message.channel.send("No audio file found as attachment.")


client.run(os.environ["DISCORD_TOKEN"])
