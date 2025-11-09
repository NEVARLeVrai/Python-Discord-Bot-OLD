import discord
from discord.ext import commands
import json
from cogs.Help import get_current_version

class Leveling_auto(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    def get_leveling_cog(self):
        """Récupère le cog Leveling pour accéder aux données partagées"""
        return self.client.get_cog('Leveling')
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Récupérer le cog Leveling pour accéder aux données
        leveling_cog = self.get_leveling_cog()
        if not leveling_cog:
            return
        
        # Vérifier si le leveling est activé
        if not hasattr(leveling_cog, 'is_leveling_enabled') or not leveling_cog.is_leveling_enabled:
            return
        
        if message.author.bot:
            return  # Ignore les messages des bots

        author_id = str(message.author.id)

        # Vérifier si levels est chargé (un dict vide {} est valide)
        if not hasattr(leveling_cog, 'levels'):
            return
        
        # Initialiser levels si c'est None
        if leveling_cog.levels is None:
            leveling_cog.levels = {}

        # Vérifie si l'utilisateur existe dans le fichier JSON
        if author_id not in leveling_cog.levels:
            leveling_cog.levels[author_id] = {
                'level': 0,
                'experience': 0
            }

        # Ajoute de l'expérience à l'utilisateur
        leveling_cog.levels[author_id]['experience'] += 1

        # Vérifie si l'utilisateur a atteint un nouveau niveau
        experience = leveling_cog.levels[author_id]['experience']
        level = leveling_cog.levels[author_id]['level']
        if experience >= (level + 1) ** 2:
            leveling_cog.levels[author_id]['level'] += 1
            member = message.author
            embed = discord.Embed(title="Nouveau niveau atteint !", description=f"{member.mention} a atteint le niveau {level + 1} !", color=discord.Color.green())
            embed.set_author(name=f"{message.author.name}", icon_url=message.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await message.channel.send(embed=embed)

        # Utiliser le chemin centralisé depuis main.py pour sauvegarder
        levels_path = self.client.paths['levels_json']
        # Enregistre les données de niveau dans le fichier JSON
        with open(levels_path, 'w') as f:
            json.dump(leveling_cog.levels, f)

async def setup(client):
    await client.add_cog(Leveling_auto(client))

