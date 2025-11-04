import discord
from discord.ext import commands
import youtube_dl

class Test(commands.Cog):
    def __init__(self, client):
        self.client = client

async def setup(client):
    await client.add_cog(Test(client))
