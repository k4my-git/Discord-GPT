# This example requires the 'message_content' privileged intents

import os
import discord
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

# インテントの生成
intents = discord.Intents.default()
intents.message_content = True

# クライアントの生成
client = discord.Client(intents=intents)

# discordと接続した時に呼ばれる
@client.event
async def on_ready():
    print(f'{client.user} loggin!')

# メッセージを受信した時に呼ばれる
@client.event
async def on_message(message):
    # 自分のメッセージを無効
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
        

client.run(os.environ["DISCORD_TOKEN"])
