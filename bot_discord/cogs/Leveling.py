import discord
from discord.ext import commands
import json
import asyncio
import os
from cogs import Help
from cogs.Help import get_current_version
import traceback

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_leveling_enabled = False  # par défaut, le niveau est activé
        # Initialiser levels à None - sera chargé dans on_ready
        self.levels = None
        
    @commands.Cog.listener()
    async def on_ready(self):
        # Utiliser le chemin centralisé depuis main.py
        levels_path = self.bot.paths['levels_json']
        # Chargement du fichier JSON qui stocke les données de niveau
        if os.path.exists(levels_path):
            with open(levels_path, 'r') as f:
                self.levels = json.load(f)
        else:
            self.levels = {}
            with open(levels_path, 'w') as f:
                json.dump(self.levels, f)
 

    # Commande pour afficher le niveau de l'utilisateur
    @commands.command(aliases=["lvl"])
    async def level(self, ctx, member: discord.Member = None):
        await ctx.message.delete()
        member = member or ctx.author
        author_id = str(member.id)

        # Vérifier si levels est chargé
        if self.levels is None:
            self.levels = {}
        
        # Vérifie si l'utilisateur existe dans le fichier JSON
        if author_id not in self.levels:
            embed = discord.Embed(title=f"L'utilisateur **{member.display_name}** n'a pas encore de niveau", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
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
        embed.set_footer(text=get_current_version(self.bot))

        await ctx.send(embed=embed)

    @commands.command(aliases=["rsl"])
    async def resetlevel(self, ctx):
        msg = 1
        await ctx.message.delete()  # Supprime la commande de l'utilisateur
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in ["oui", "non"]

        embed = discord.Embed(title="Tu veux reset les levels ?", description="C'est définitif! Ecris 'oui' ou 'non' pour confirmer", color=discord.Color.red())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.bot))
        await ctx.send(embed=embed, delete_after= 5)

        try:
            confirm = await self.bot.wait_for("message", check=check, timeout=5)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Confirmation a expiré.", description="Commande annulée.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
            await ctx.send(embed=embed, delete_after= 5)
            return

        if confirm.content.lower() == "oui":
           
            await ctx.channel.purge(limit=msg)
            embed = discord.Embed(title="Réinitialisation", description="Tous les niveaux ont été réinitialisés.", color=discord.Color.yellow())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
            await ctx.send(embed=embed, delete_after= 5)
            self.levels = {}
            # Utiliser le chemin centralisé depuis main.py
            levels_path = self.bot.paths['levels_json']
            with open(levels_path, 'w') as f:
                json.dump(self.levels, f)
        else:
            await ctx.channel.purge(limit=msg)
            embed = discord.Embed(title="Commande annulé", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
            await ctx.send(embed=embed, delete_after= 5)

    @commands.command(aliases=["lvls"])
    @commands.has_permissions(administrator=True)
    async def levelsettings(self, ctx):
        await ctx.message.delete()
        self.is_leveling_enabled = not self.is_leveling_enabled
        
        if self.is_leveling_enabled:
            embed = discord.Embed(title="Paramètre des levels", description=f"Leveling est maintenant {'activé'}.", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
            await ctx.send(embed=embed, delete_after= 10)
        else:
            embed = discord.Embed(title="Paramètre des levels", description=f"Leveling est maintenant {'désactivé'}.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
            await ctx.send(embed=embed, delete_after= 10)
    
    @commands.command(aliases=["levelleaderboard", "levellb", "lvlboard"])
    async def levelboard(self, ctx):
        await ctx.message.delete()
        
        # Vérifier si le système a des levels
        if not self.levels or len(self.levels) == 0:
            embed = discord.Embed(title="Leaderboard des Levels", description="Aucun niveau enregistré.", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.bot))
            await ctx.send(embed=embed)
            return
        
        # Récupérer tous les utilisateurs avec leurs levels et les trier
        level_list = []
        for user_id, level_data in self.levels.items():
            level = level_data.get("level", 0)
            experience = level_data.get("experience", 0)
            if level > 0 or experience > 0:
                try:
                    member = ctx.guild.get_member(int(user_id))
                    if member:
                        level_list.append((member, level, experience))
                    else:
                        # Si l'utilisateur n'est plus sur le serveur, on l'affiche quand même
                        level_list.append((None, level, experience, user_id))
                except (ValueError, AttributeError):
                    level_list.append((None, level, experience, user_id))
        
        # Trier par niveau décroissant, puis par expérience décroissante
        level_list.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Prendre les top 10
        top_levels = level_list[:10]
        
        # Créer l'embed
        embed = discord.Embed(title="🏆 Leaderboard des Levels", description="Top 10 des utilisateurs avec le plus haut niveau", color=discord.Color.blue())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.bot))
        
        # Ajouter les résultats
        if top_levels:
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for idx, entry in enumerate(top_levels):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                
                if len(entry) == 4:  # Utilisateur qui n'est plus sur le serveur
                    user_id = entry[3]
                    level = entry[1]
                    experience = entry[2]
                    leaderboard_text += f"{medal} **Utilisateur inconnu** (ID: {user_id}) - Niveau {level} ({experience} XP)\n"
                else:
                    member = entry[0]
                    level = entry[1]
                    experience = entry[2]
                    leaderboard_text += f"{medal} {member.mention} - Niveau {level} ({experience} XP)\n"
            
            embed.add_field(name="Classement", value=leaderboard_text, inline=False)
        else:
            embed.add_field(name="Classement", value="Aucun utilisateur avec des niveaux.", inline=False)
        
        await ctx.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(Leveling(bot))