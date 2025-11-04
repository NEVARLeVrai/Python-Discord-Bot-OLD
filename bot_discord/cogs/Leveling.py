import discord
from discord.ext import commands
import json
import asyncio
from cogs import Help
import traceback

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_leveling_enabled = False  # par défaut, le niveau est activé
        
    @commands.Cog.listener()
    async def on_ready(self):
        # Utiliser le chemin centralisé depuis main.py
        levels_path = self.bot.paths['levels_json']
        # Chargement du fichier JSON qui stocke les données de niveau
        with open(levels_path, 'r') as f:
            self.levels = json.load(f)
 
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not self.is_leveling_enabled:
            return  # Ignore les messages des bots et si le niveau est désactivé

        author_id = str(message.author.id)

        # Vérifie si l'utilisateur existe dans le fichier JSON
        if author_id not in self.levels:
            self.levels[author_id] = {
                'level': 0,
                'experience': 0
            }

        # Ajoute de l'expérience à l'utilisateur
        self.levels[author_id]['experience'] += 1

        # Vérifie si l'utilisateur a atteint un nouveau niveau
        experience = self.levels[author_id]['experience']
        level = self.levels[author_id]['level']
        if experience >= (level + 1) ** 2:
            self.levels[author_id]['level'] += 1
            member = message.author
            embed = discord.Embed(title="Nouveau niveau atteint !", description=f"{member.mention} a atteint le niveau {level + 1} !", color=discord.Color.green())
            embed.set_author(name=f"{message.author.name}", icon_url=message.author.avatar)
            embed.set_footer(text=Help.version1)
            await message.channel.send(embed=embed)

        # Utiliser le chemin centralisé depuis main.py
        levels_path = self.bot.paths['levels_json']
        # Enregistre les données de niveau dans le fichier JSON
        with open(levels_path, 'w') as f:
            json.dump(self.levels, f)

    # Commande pour afficher le niveau de l'utilisateur
    @commands.command(aliases=["lvl"])
    async def level(self, ctx, member: discord.Member = None):
        await ctx.message.delete()
        member = member or ctx.author
        author_id = str(member.id)

        # Vérifie si l'utilisateur existe dans le fichier JSON
        if author_id not in self.levels:
            embed = discord.Embed(title=f"L'utilisateur **{member.display_name}** n'a pas encore de niveau", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after= 10)
            return

        level = self.levels[author_id]['level']
        experience = self.levels[author_id]['experience']
        exp_needed = (level + 1) ** 2 - experience

        # Crée un embed pour afficher le niveau de l'utilisateur
        embed = discord.Embed(title=f"Niveau de {member.display_name}", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.add_field(name="Niveau", value=level)
        embed.add_field(name="Expérience", value=f"{experience}/{(level + 1) ** 2}")
        embed.add_field(name="Expérience nécessaire pour le prochain niveau", value=exp_needed)
        embed.set_footer(text=Help.version1)

        await ctx.send(embed=embed)

    @commands.command(aliases=["rsl"])
    async def resetlevel(self, ctx):
        msg = 1
        await ctx.message.delete()  # Supprime la commande de l'utilisateur
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ["oui", "non"]

        embed = discord.Embed(title="Tu veux reset les levels ?", description="C'est définitif! Ecris 'oui' ou 'non' pour confirmer", color=discord.Color.red())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after= 5)

        try:
            confirm = await self.bot.wait_for("message", check=check, timeout=5)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Confirmation a expiré.", description="Commande annulée.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after= 5)
            return

        if confirm.content.lower() == "oui":
           
            await ctx.channel.purge(limit=msg)
            embed = discord.Embed(title="Réinitialisation", description="Tous les niveaux ont été réinitialisés.", color=discord.Color.yellow())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after= 5)
            self.levels = {}
            self.save_levels()
        else:
            await ctx.channel.purge(limit=msg)
            embed = discord.Embed(title="Commande annulé", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after= 5)

    @commands.command(aliases=["lvls"])
    @commands.has_permissions(administrator=True)
    async def levelsettings(self, ctx):
        await ctx.message.delete()
        self.is_leveling_enabled = not self.is_leveling_enabled
        
        if self.is_leveling_enabled:
            embed = discord.Embed(title="Paramètre des levels", description=f"Leveling est maintenant {'activé'}.", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after= 10)
        else:
            embed = discord.Embed(title="Paramètre des levels", description=f"Leveling est maintenant {'désactivé'}.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after= 10)
        
async def setup(bot):
    await bot.add_cog(Leveling(bot))