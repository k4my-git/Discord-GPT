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
    print(f'We have logged in as {client.user}')

# メッセージを受信した時に呼ばれる
@client.event
async def on_message(message):
    # 自分のメッセージを無効
    if message.author == client.user:
        return

    # メッセージが"$hello"で始まっていたら"Hello!"と応答
    if message.content.startswith('$'):
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.content}]
        )

        res_text = res["choices"][0]["message"]["content"]
        await message.channel.send('res_text')

client.run(os.environ["DISCORD_TOKEN"])
