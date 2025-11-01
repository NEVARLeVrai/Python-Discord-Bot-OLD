import discord
from discord.ext import commands
import io
import requests
from cogs import Help
import traceback
from datetime import datetime

version1="Bot V.2910-25"
version2 ="`optimization, fixed bugs and added new commands`"


class Help(commands.Cog):   
    def __init__(self, client):
        self.target_user_id = 745923070736465940  # Replace with your Discord user ID
        self.client = client
        self.webhook_url = "https://discord.com/api/webhooks/1433124903397359673/FTyJEbBq0cxVGx_kwaws1D5WRhPVq5MnQgko4ZqbZMqOa6DJoYbZOwpOVkXiV8oFYIQl" # Remplacez WEBHOOK
 
 
     
    @commands.Cog.listener()
    async def on_ready(self):
        print("Help.py is ready")
        


    @commands.command(name="report")
    async def report(self, ctx, *, message: str):
        """Signaler un bug"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
            
        ticket_number = datetime.now().strftime("%d%m%Y")  # Créez un numéro de ticket basé sur la date et l'heure
        data = {
            "content": f"**Bug signalé !**\n\nTicket: **#{ticket_number}{ctx.author.name}**\nPar: **{ctx.author.name}**\nID: **{ctx.author.id}**\nMention: {ctx.author.mention}\n\nContenu: {message}\n\n**{version1}**"
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.webhook_url, json=data, headers=headers)
        
        if response.status_code == 204:
            # Envoyer un message à l'utilisateur avec le numéro de ticket
            user = ctx.author
            embedc2 = discord.Embed(title="Signalement", description="Votre rapport de bug a été enregistré avec succès.", color=discord.Color.green())
            embedc2.add_field(name="",value=f"Ticket : **#{ticket_number}{ctx.author.name}**", inline=False)
            embedc2.add_field(name="",value="Nous allons le corriger dès que possible!", inline=False)
            embedc2.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc2.set_footer(text=version1)
            await user.send(embed=embedc2)
            
            # Envoyer un message de confirmation dans le canal actuel
            embedc = discord.Embed(title="Signalement", description="Merci d'avoir signalé ce bug.", color=discord.Color.green())
            embedc.add_field(name="",value=f"Ticket : **#{ticket_number}{ctx.author.name}**", inline=False)
            embedc.add_field(name="",value="Nous allons le corriger dès que possible.", inline=False)
            embedc.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc.set_footer(text=version1)
            await ctx.send(embed=embedc, delete_after=5)
        else:
            embedc1 = discord.Embed(title="Erreur de signalement.", description="Erreur lors de l'envoi du message.", color=discord.Color.red())
            embedc1.add_field(name="",value="Veuillez réessayer plus tard.", inline=False)
            embedc1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc1.set_footer(text=version1)
            await ctx.send(embed=embedc1, delete_after=5)


        
    @commands.command()
    async def helps(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()

        embed_message = discord.Embed(
            title="Helps",
            description="Toutes les commandes",
            color=discord.Color.random()
        )

        embed_message.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )

        embed_message.add_field(name="helps", value="help show this message =help")
        embed_message.add_field(name="ping", value="ping the bot =ping")
        embed_message.add_field(name="version, v", value="Bot version =version",)
        embed_message.add_field(name="stop", value="stop the bot =stop (only owner)")
        embed_message.add_field(name="report", value="report only for report a bug or make a feedback =report [something to send]")
        embed_message.set_footer(text=version1)

        embed_message2 = discord.Embed(
            title="Helps Soundboard",
            description="Toutes les commandes de Soundboard",
            color=discord.Color.random()
        )

        embed_message2.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
        embed_message2.add_field(name="slist", value="slist list all soundboard =slist 4")
        embed_message2.add_field(name="splay", value="splay make play soundboard =splay [number]")
        embed_message2.add_field(name="sjoin", value="sjoin make join bot =sjoin [need to be in a vc]")
        embed_message2.add_field(name="sleave", value="sleave make leave bot =sleave")
        embed_message2.add_field(name="sstop", value="stop bot making soundboard =sstop")
        embed_message2.add_field(name="srandom", value="srandom play a random soundboard between 1 and 5 minutes =srandom")
        embed_message2.add_field(name="srandomskip", value="skip skip random soundboard =srandomskip [only when a sound is playing]")
        embed_message2.add_field(name="srandomstop", value="stops stop random soundboard =srandomstop")
        embed_message2.add_field(name="vkick", value="vkick kick user in a vc =vkick [@ID] (admin perms only)")
        embed_message2.add_field(name="tts", value="tts make bot say something with googletts voice in vc =tts [langue] [texte]")
        
        
        embed_message3 = discord.Embed(
        title="Helps Leveling",
        description="Toutes les commandes de Leveling",
        color=discord.Color.random()
        )

        embed_message3.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        

        embed_message3.add_field(name="level, lvl", value="level see your ranking =level [@ user]")
        embed_message3.add_field(name="resetlevel, rsl", value="resetlevel reset member level =resetlevel [@ user] (messages perms only)")
        embed_message3.add_field(name="levelsettings, lvls", value="levelsettings enable or disable leveling system (admins perms only)")
        
        embed_message4 = discord.Embed(
        title="Helps Mods",
        description="Toutes les commandes Mods",
        color=discord.Color.random()
        )

        embed_message4.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
      
        embed_message4.add_field(name="clear, prune", value="clear messages =clear [number] (messages perms only) max 70 messages")
        embed_message4.add_field(name="cleanraidsimple, clr", value="clear raid with channel name =cleanraidsimple [channel name] (messages perms only)")
        embed_message4.add_field(name="cleanraidmultiple, clrs", value="clear raid with datetime =cleanraidmultiple [Y-m-d-H:M] (messages perms only)")
        embed_message4.add_field(name="warn", value="warn members =warn [@ user] [reason] [count] (messages perms only) - Ex: =warn @user Spam 3")
        embed_message4.add_field(name="resetwarn, warnreset", value="reset warns =resetwarn [@ user] (messages perms only)")
        embed_message4.add_field(name="warnboard, warnleaderboard, warnlb", value="leaderboard des warns =warnboard")
        embed_message4.add_field(name="kick", value="kick members =kick [@ user or ID] (kick perms only)")
        embed_message4.add_field(name="ban", value="ban members =ban [@ user] (ban perms only)")
        embed_message4.add_field(name="banid", value="ban members =banid [ID] (ban perms only)")
        embed_message4.add_field(name="unban", value="unban members =unban [@ user or ID] (ban perms only)")
        embed_message4.add_field(name="giverole", value="give a role to a members =giverole [@ user or ID] [@ role or ID]  (admins perms only)")
        embed_message4.add_field(name="removerole", value="removerole a role to a members =removerole [@ user or ID] [@ role or ID] (admins perms only)")
        
        embed_message5 = discord.Embed(
        title="Helps Utility",
        description="Toutes les commandes d'Utility",
        color=discord.Color.random()
        )

        embed_message5.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
      
        embed_message5.add_field(name="gpt", value="use gpt in discord =gpt [Something to ask]")
        embed_message5.add_field(name="dalle", value="use dalle in discord =dalle [Something to ask]")
        embed_message5.add_field(name="spam", value="spam in chat =spam [Number of Times] [Something to say] (admin perms only)")
        embed_message5.add_field(name="repeat, say", value="Repeat messages =repeat [Something to repeat]")
        embed_message5.add_field(name="8ball, magicball", value="8ball game =8ball [Something to answer]")
        embed_message5.add_field(name="hilaire", value="hilaire game =hilaire")
        embed_message5.add_field(name="deldms, delmp", value="deldms clear dms with bot =deldms (admin perms only)")
        
        embed_message6 = discord.Embed(
            title="Helps MP",
            description="Commandes disponible en MP",
            color=discord.Color.random()
        )

        embed_message6.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )

        embed_message6.add_field(name="helps", value="help show this message =help")
        embed_message6.add_field(name="ping", value="ping the bot =ping")
        embed_message6.add_field(name="version, v", value="Bot version =version",)
        embed_message6.add_field(name="stop", value="stop the bot =stop (only owner)")
        embed_message6.add_field(name="report", value="report only for report a bug or make a feedback =report [something to send]")
        embed_message6.add_field(name="gpt", value="use gpt in discord =gpt [Something to ask]")
        embed_message6.add_field(name="dalle", value="use dalle in discord =dalle [Something to ask]")
       
              
        with open("./Autres/info.png", "rb") as f:
            image_data = f.read()
        embed_message6.set_thumbnail(url="attachment://info.png")

        await ctx.send(embed=embed_message)
        await ctx.send(embed=embed_message4)
        await ctx.send(embed=embed_message5)
        await ctx.send(embed=embed_message2)
        await ctx.send(embed=embed_message3)
        await ctx.send(embed=embed_message6, file=discord.File(io.BytesIO(image_data), "info.png"))
    
    
    @commands.command(aliases=["v"])
    async def version(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        embed = discord.Embed(title="Versions du Bot", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.add_field(name="", value="")
        embed.add_field(name="Last Version", value=version1)
        embed.add_field(name="Update Logs", value=version2)
        embed.add_field(name="", value="")
        embed.add_field(name="Date format", value="`DD/MM/YYYY`")
        with open("./Autres/version.jpg", "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://version.jpg")
        await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), "version.jpg"))
        
    @commands.command()
    async def ping(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
            
        bot_latency = round(self.client.latency * 1000)
        
        embed = discord.Embed(title=f"Pong! {bot_latency} ms.", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=version1)
        await ctx.send(embed=embed)



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return  # Ignore les messages envoyés par le bot lui-même
        
        if isinstance(message.channel, discord.DMChannel):
            user = message.author
            content = message.content
            
            # Vérifie si le message est une commande ou une mention
            if content.startswith("=") or message.mention_everyone or self.client.user in message.mentions:
                return  # Ignore les messages de commande ou les mentions
            
            target_user = self.client.get_user(self.target_user_id)
            
            if target_user:
                await target_user.send(f"Message privé de **{user}**: \n\n{content}")


async def setup(client):
    await client.add_cog(Help(client))