import discord
from discord.ext import commands, tasks
import asyncio
from cogs import Help
import traceback
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import pytz
import requests
import typing
import json
import os


class Mods(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.protected_role_id = 1236660715151167548  # ID du rôle à enlever
        self.blocked_user_id = 440168985615400984  # ID de l'utilisateur bloqué
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Mods.py is ready")
        # Chargement du fichier JSON qui stocke les warns
        if os.path.exists('./Autres/warns.json'):
            with open('./Autres/warns.json', 'r') as f:
                self.warns = json.load(f)
        else:
            self.warns = {}
            with open('./Autres/warns.json', 'w') as f:
                json.dump(self.warns, f)
        
        # Démarrer la tâche pour vérifier les timeouts terminés
        self.check_timeout_end.start()
    
    def save_warns(self):
        """Sauvegarde les warns dans le fichier JSON"""
        with open('./Autres/warns.json', 'w') as f:
            json.dump(self.warns, f)
    
    async def remove_protected_role(self, member, guild):
        """Enlève le rôle protégé et retourne True si le rôle était présent"""
        try:
            role = guild.get_role(self.protected_role_id)
            if role and role in member.roles:
                await member.remove_roles(role, reason="Enlèvement temporaire pour action de modération")
                return True
        except Exception as e:
            print(f"Erreur lors de l'enlèvement du rôle: {e}")
        return False
    
    @tasks.loop(minutes=1)
    async def check_timeout_end(self):
        """Vérifie périodiquement si des timeouts sont terminés et remet les rôles"""
        for guild_id_str, guild_data in self.warns.items():
            try:
                guild = self.client.get_guild(int(guild_id_str))
                if not guild:
                    continue
                
                role = guild.get_role(self.protected_role_id)
                if not role:
                    continue
                
                # Vérifier chaque membre du serveur
                for member in guild.members:
                    # Si le membre n'a plus de timeout et a des warns avec rôle enlevé
                    member_id_str = str(member.id)
                    if member_id_str in guild_data:
                        member_data = guild_data[member_id_str]
                        
                        # Vérifier si le timeout est terminé
                        if member.timed_out_until is None or member.timed_out_until < datetime.now(timezone.utc):
                            # Vérifier si on doit remettre le rôle
                            if member_data.get("role_removed", False):
                                if role not in member.roles:
                                    try:
                                        await member.add_roles(role, reason="Rôle remis après timeout terminé")
                                        member_data["role_removed"] = False
                                        self.save_warns()
                                        print(f"Rôle remis à {member.display_name} ({member_id_str}) après timeout terminé")
                                    except Exception as e:
                                        print(f"Erreur lors de la remise du rôle: {e}")
            except Exception as e:
                print(f"Erreur dans check_timeout_end: {e}")
    
    @check_timeout_end.before_loop
    async def before_check_timeout_end(self):
        await self.client.wait_until_ready()


        
    @commands.command(aliases=["prune"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        max_amount = 70 # limite de suppression de messages
        if amount > max_amount:
            await ctx.send(f"Vous ne pouvez pas supprimer plus de **{max_amount}** messages à la fois.")
            await asyncio.sleep(1) # Attendre une seconde entre chaque envoi de message
            amount = max_amount
        await ctx.channel.purge(limit=amount+1)
        await asyncio.sleep(1) # Attendre une seconde entre chaque envoi de message
        await ctx.send(f"**{amount}** messages ont été supprimés.", delete_after=10)
        
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, modreaseon):
        await ctx.message.delete()
        await ctx.guild.kick(member)
        
        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.yellow())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        conf_embed.add_field(name="Expulsé:", value=f"{member.mention} à été kick par {ctx.author.mention}.", inline=False)
        conf_embed.add_field(name="Raison:", value=modreaseon, inline=False)
        conf_embed.set_footer(text=Help.version1)
        
        await ctx.send(embed=conf_embed)
        
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, args=None):
        await ctx.message.delete()
        
        # Vérifier si l'auteur ou le membre ciblé est bloqué
        if ctx.author.id == self.blocked_user_id or member.id == self.blocked_user_id:
            embed = discord.Embed(title="Erreur", description=f"Cet utilisateur ne peut pas utiliser ou être averti par cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
            return
        
        member_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        # Initialiser la structure si elle n'existe pas
        if guild_id not in self.warns:
            self.warns[guild_id] = {}
        if member_id not in self.warns[guild_id]:
            self.warns[guild_id][member_id] = {"count": 0, "warnings": []}
        
        # Parser les arguments : args peut être None, une raison, ou "raison nombre"
        warn_count_to_add = 1
        reason = "Aucune raison spécifiée"
        
        if args:
            # Séparer les arguments
            parts = args.strip().split()
            if len(parts) > 0:
                # Vérifier si le dernier argument est un nombre
                try:
                    last_part = parts[-1]
                    if last_part.isdigit():
                        # Le dernier élément est un nombre, c'est le nombre de warns
                        warn_count_to_add = int(last_part)
                        # Le reste est la raison
                        if len(parts) > 1:
                            reason = " ".join(parts[:-1])
                        else:
                            reason = "Aucune raison spécifiée"
                    else:
                        # Pas de nombre, tout est la raison
                        reason = args
                except (ValueError, IndexError):
                    # Si erreur, tout est la raison
                    reason = args
        
        # Ajouter les warns
        for _ in range(warn_count_to_add):
            self.warns[guild_id][member_id]["count"] += 1
            self.warns[guild_id][member_id]["warnings"].append({
                "reason": reason,
                "moderator": ctx.author.name,
                "timestamp": datetime.now().isoformat()
            })
        
        total_warn_count = self.warns[guild_id][member_id]["count"]
        self.save_warns()
        
        await ctx.send(f"{member.mention}")
        
        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.orange())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        
        if warn_count_to_add > 1:
            conf_embed.add_field(name="Averti:", value=f"{member.mention} a reçu **{warn_count_to_add}** avertissements de {ctx.author.mention}.", inline=False)
        else:
            conf_embed.add_field(name="Averti:", value=f"{member.mention} a été averti par {ctx.author.mention}.", inline=False)
        
        conf_embed.add_field(name="Raison:", value=reason, inline=False)
        conf_embed.add_field(name="Nombre total de warns:", value=f"{total_warn_count}", inline=False)
        conf_embed.set_footer(text=Help.version1)
        
        await ctx.send(embed=conf_embed)
        
        # Appliquer les actions automatiques selon le nombre de warns
        previous_warn_count = total_warn_count - warn_count_to_add
        
        # Vérifier les seuils atteints (on vérifie dans l'ordre décroissant pour prendre l'action la plus sévère)
        if total_warn_count >= 20 and previous_warn_count < 20:
            # Ban
            # Enlever le rôle protégé avant le ban si nécessaire
            role_was_removed = await self.remove_protected_role(member, ctx.guild)
            
            try:
                await ctx.guild.ban(member, reason=f"20 warns atteints")
                action_desc = f"{member.mention} a été banni(e) pour avoir atteint 20 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé avant le ban."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.red())
                await ctx.send(embed=action_embed)
            except discord.Forbidden:
                error_embed = discord.Embed(title="Erreur", description=f"Impossible de bannir {member.mention}. Le bot n'a pas les permissions nécessaires.", color=discord.Color.red())
                await ctx.send(embed=error_embed, delete_after=10)
            except Exception as e:
                print(f"Erreur ban (20 warns): {e}")
        
        elif total_warn_count >= 15 and previous_warn_count < 15:
            # Kick
            # Enlever le rôle protégé avant le kick si nécessaire
            role_was_removed = await self.remove_protected_role(member, ctx.guild)
            
            try:
                await ctx.guild.kick(member, reason=f"15 warns atteints")
                action_desc = f"{member.mention} a été expulsé(e) pour avoir atteint 15 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé avant le kick."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.red())
                await ctx.send(embed=action_embed)
            except discord.Forbidden:
                error_embed = discord.Embed(title="Erreur", description=f"Impossible d'expulser {member.mention}. Le bot n'a pas les permissions nécessaires.", color=discord.Color.red())
                await ctx.send(embed=error_embed, delete_after=10)
            except Exception as e:
                print(f"Erreur kick (15 warns): {e}")
        
        elif total_warn_count >= 10 and previous_warn_count < 10:
            # Timeout de 10 minutes pour 10 warns
            # Enlever le rôle protégé avant le timeout si nécessaire
            role_was_removed = await self.remove_protected_role(member, ctx.guild)
            
            timeout_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            try:
                await member.edit(timed_out_until=timeout_until, reason=f"10 warns atteints")
                
                # Si le rôle a été enlevé, le sauvegarder pour le remettre après
                if role_was_removed:
                    if guild_id not in self.warns:
                        self.warns[guild_id] = {}
                    if member_id not in self.warns[guild_id]:
                        self.warns[guild_id][member_id] = {"count": 0, "warnings": []}
                    self.warns[guild_id][member_id]["role_removed"] = True
                    self.warns[guild_id][member_id]["timeout_end"] = timeout_until.isoformat()
                    self.save_warns()
                
                action_desc = f"{member.mention} a reçu un timeout de 10 minutes pour avoir atteint 10 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé temporairement et sera remis après le timeout."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.yellow())
                await ctx.send(embed=action_embed)
            except (discord.Forbidden, AttributeError, TypeError) as e:
                # Si la méthode ne fonctionne pas, on ignore l'erreur
                print(f"Erreur timeout (10 warns): {e}")
                action_embed = discord.Embed(title="Action Automatique", description=f"{member.mention} a atteint 10 warns mais le timeout n'a pas pu être appliqué.", color=discord.Color.orange())
                await ctx.send(embed=action_embed)
        
        elif total_warn_count >= 5 and previous_warn_count < 5:
            # Timeout de 10 minutes pour 5 warns
            # Enlever le rôle protégé avant le timeout si nécessaire
            role_was_removed = await self.remove_protected_role(member, ctx.guild)
            
            timeout_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            try:
                await member.edit(timed_out_until=timeout_until, reason=f"5 warns atteints")
                
                # Si le rôle a été enlevé, le sauvegarder pour le remettre après
                if role_was_removed:
                    if guild_id not in self.warns:
                        self.warns[guild_id] = {}
                    if member_id not in self.warns[guild_id]:
                        self.warns[guild_id][member_id] = {"count": 0, "warnings": []}
                    self.warns[guild_id][member_id]["role_removed"] = True
                    self.warns[guild_id][member_id]["timeout_end"] = timeout_until.isoformat()
                    self.save_warns()
                
                action_desc = f"{member.mention} a reçu un timeout de 10 minutes pour avoir atteint 5 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé temporairement et sera remis après le timeout."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.yellow())
                await ctx.send(embed=action_embed)
            except (discord.Forbidden, AttributeError, TypeError) as e:
                # Si la méthode ne fonctionne pas, on ignore l'erreur
                print(f"Erreur timeout (5 warns): {e}")
                action_embed = discord.Embed(title="Action Automatique", description=f"{member.mention} a atteint 5 warns mais le timeout n'a pas pu être appliqué.", color=discord.Color.orange())
                await ctx.send(embed=action_embed)
    
    @commands.command(aliases=["warnreset"])
    @commands.has_permissions(manage_messages=True)
    async def resetwarn(self, ctx, member: discord.Member):
        await ctx.message.delete()
        
        member_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.warns or member_id not in self.warns[guild_id]:
            embed = discord.Embed(title="Erreur", description=f"{member.mention} n'a aucun warn.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
            return
        
        member_data = self.warns[guild_id][member_id]
        
        # Si un timeout est en cours, le retirer
        timeout_removed = False
        if member.timed_out_until and member.timed_out_until > datetime.now(timezone.utc):
            try:
                await member.edit(timed_out_until=None, reason="Timeout retiré après reset des warns")
                timeout_removed = True
            except Exception as e:
                print(f"Erreur lors de la suppression du timeout après reset: {e}")
        
        # Si un timeout est en cours et que le rôle a été enlevé, le remettre
        role_was_restored = False
        if member_data.get("role_removed", False):
            try:
                role = ctx.guild.get_role(self.protected_role_id)
                if role and role not in member.roles:
                    await member.add_roles(role, reason="Rôle remis après reset des warns")
                    role_was_restored = True
            except Exception as e:
                print(f"Erreur lors de la remise du rôle après reset: {e}")
        
        # Réinitialiser les warns
        self.warns[guild_id][member_id] = {"count": 0, "warnings": []}
        self.save_warns()
        
        conf_embed = discord.Embed(title="Réussi!", description="", color=discord.Color.green())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        
        desc_text = f"Les warns de {member.mention} ont été réinitialisés."
        if timeout_removed:
            desc_text += f"\nLe timeout a été retiré."
        if role_was_restored:
            desc_text += f"\nLe rôle protégé a été remis."
        
        conf_embed.add_field(name="Warns réinitialisés:", value=desc_text, inline=False)
        conf_embed.set_footer(text=Help.version1)
        
        await ctx.send(embed=conf_embed)
    
    @commands.command(aliases=["warnleaderboard", "warnlb"])
    async def warnboard(self, ctx):
        await ctx.message.delete()
        
        guild_id = str(ctx.guild.id)
        
        # Vérifier si le serveur a des warns
        if guild_id not in self.warns or not self.warns[guild_id]:
            embed = discord.Embed(title="Leaderboard des Warns", description="Aucun warn enregistré sur ce serveur.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed)
            return
        
        # Récupérer tous les membres avec leurs warns et les trier
        warn_list = []
        for member_id, warn_data in self.warns[guild_id].items():
            warn_count = warn_data.get("count", 0)
            if warn_count > 0:
                try:
                    member = ctx.guild.get_member(int(member_id))
                    if member:
                        warn_list.append((member, warn_count))
                    else:
                        # Si le membre n'est plus sur le serveur, on l'affiche quand même
                        warn_list.append((None, warn_count, member_id))
                except (ValueError, AttributeError):
                    warn_list.append((None, warn_count, member_id))
        
        # Trier par nombre de warns décroissant
        warn_list.sort(key=lambda x: x[1], reverse=True)
        
        # Prendre les top 10
        top_warns = warn_list[:10]
        
        # Créer l'embed
        embed = discord.Embed(title="🏆 Leaderboard des Warns", description="Top 10 des utilisateurs avec le plus de warns", color=discord.Color.orange())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=Help.version1)
        
        # Ajouter les résultats
        if top_warns:
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for idx, entry in enumerate(top_warns):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                
                if len(entry) == 3:  # Membre qui n'est plus sur le serveur
                    member_id = entry[2]
                    warn_count = entry[1]
                    leaderboard_text += f"{medal} **<@{member_id}>** (Parti du serveur) - **{warn_count}** warn(s)\n"
                else:
                    member = entry[0]
                    warn_count = entry[1]
                    if member:
                        leaderboard_text += f"{medal} **{member.display_name}** ({member.mention}) - **{warn_count}** warn(s)\n"
            
            embed.add_field(name="", value=leaderboard_text, inline=False)
        else:
            embed.add_field(name="", value="Aucun warn trouvé.", inline=False)
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, modreaseon):
        await ctx.message.delete()
        await ctx.guild.ban(member)

        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.red())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        conf_embed.add_field(name="Banni:", value=f"{member.mention} a été banni par {ctx.author.mention}.", inline=False)
        conf_embed.add_field(name="Raison:", value=modreaseon, inline=False)
        conf_embed.set_footer(text=Help.version1)
        
        await ctx.send(embed=conf_embed)
        
    @commands.command(name="banid")
    @commands.has_permissions(ban_members=True)
    async def banid(self, ctx, user_id: int, *, modreaseon):
        await ctx.message.delete()
        user_obj = discord.Object(id=user_id)
        await ctx.guild.ban(user_obj)

        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.red())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        conf_embed.add_field(name="Banni:", value=f"<@{user_id}> a été banni par {ctx.author.mention}.", inline=False)
        conf_embed.add_field(name="Raison:", value=modreaseon, inline=False)
        conf_embed.set_footer(text=Help.version1)
        
        await ctx.send(embed=conf_embed)
        
    @commands.command(name="unban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, userId):
        user = discord.Object(id=userId)
        await ctx.message.delete()
        await ctx.guild.unban(user)

        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.green())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        conf_embed.add_field(name="Débanni:", value=f"<@{userId}> à été débanni du serveur par {ctx.author.mention}.", inline=False)
        conf_embed.set_footer(text=Help.version1)
    
        
        await ctx.send(embed=conf_embed)
        
            

    @commands.command(name='spam')
    @commands.has_permissions(administrator=True)
    async def spam(self, ctx, amount: int, destination: typing.Union[discord.TextChannel, str], *, message=None):
        
        if isinstance(destination, str):
            if destination.startswith("<#") and destination.endswith(">"):
                channel_id = int(destination[2:-1])  # Extraction de l'ID à partir de la mention
                destination = self.client.get_channel(channel_id)
                if not isinstance(destination, discord.TextChannel):
                    await ctx.send("Salon invalide spécifié.")
                    return
            else:
                embed1 = discord.Embed(title="Spam Non Envoyé!", description="Format de mention de salon incorrect.", color=discord.Color.red())
                embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed1.set_footer(text=Help.version1)

                await ctx.send(embed=embed1, delete_after=10)
                return
        
        max_amount = 200
        if amount > max_amount:
            await ctx.send(f"Le nombre maximum de messages que vous pouvez envoyer est de **{max_amount}**.")
            amount = max_amount
        
        # Vérifiez si des fichiers sont attachés au message
        if ctx.message.attachments:
            files = [await attachment.to_file() for attachment in ctx.message.attachments]
        else:
            files = []

        embed = discord.Embed(title="Spam Envoyé!", description=f"Spam envoyé de {amount} message(s) dans {destination.mention}" if isinstance(destination, discord.TextChannel) else f"Message envoyé à {destination.name}#{destination.discriminator}", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=Help.version1)
        
        await ctx.send(embed=embed, delete_after=10)


        sent_messages = 0
        while sent_messages < amount:
            if sent_messages >= max_amount:
                break
            await destination.send(message, files=files)
            sent_messages += 1
            await asyncio.sleep(0.5)  # Attendre une seconde entre chaque envoi de message

            


            
    @commands.command(aliases=["clr"])
    @commands.has_permissions(manage_messages=True)
    async def cleanraidsimple(self, ctx, name):
        found = False
        channeldel = None 
        
        for channel in self.client.get_all_channels():
            if channel.name == name:
                found = True
                channeldel = channel
                        
        if found:
            embed4 = discord.Embed(title="Nettoyage Raid par nom", description=f"Suppression des ou d'un Salon(s) **{channel}**", color=discord.Color.yellow())
            embed4.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed4.set_footer(text=Help.version1)
            await ctx.send(embed=embed4, delete_after=5)           
            await channeldel.delete()
            embed3 = discord.Embed(title="Nettoyage Raid par nom", description=f"Salon(s) **{channel}** supprimé avec succès!", color=discord.Color.green())
            embed3.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed3.set_footer(text=Help.version1)
            await ctx.send(embed=embed3, delete_after=5)
            
        else:
            embed5 = discord.Embed(title="Nettoyage Raid par nom", description=f"Aucun Salon(s) avec le nom **{name}** trouvé.", color=discord.Color.red())
            embed5.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed5.set_footer(text=Help.version1)
            await ctx.send(embed=embed5, delete_after=5)

    @commands.command(aliases=["clrs"])
    @commands.has_permissions(manage_messages=True)
    async def cleanraidmultiple(self, ctx, raid_date: str, raid_time: str):
        raid_datetime_str = raid_date + " " + raid_time.replace("h", ":")
        raid_datetime = datetime.strptime(raid_datetime_str, "%Y-%m-%d %H:%M")
        time_difference = datetime.now(pytz.utc).hour - datetime.now().hour
        raid_datetime = raid_datetime.replace(hour=time_difference+raid_datetime.hour, tzinfo=pytz.UTC)
        for channel in self.client.get_all_channels():
            if channel.created_at > raid_datetime:
                await channel.delete()
        embed6 = discord.Embed(title="Nettoyage Raid par temps", description=f"Salon(s) entre **{raid_datetime}** ont été supprimés", color=discord.Color.green())
        embed6.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed6.set_footer(text=Help.version1)
        await ctx.send(embed=embed6, delete_after=5)

    @commands.command(name='giverole')
    @commands.is_owner()
    async def giverole(self, ctx, utilisateur: discord.Member, role: discord.Role):
        await ctx.message.delete()
        try:
            await utilisateur.add_roles(role)
            conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.random())
            conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed.add_field(name=f"Le rôle **@{role.name}**", value=f"a été attribué à {utilisateur.mention}", inline=False)
            conf_embed.set_footer(text=Help.version1)
            await ctx.send(embed=conf_embed, delete_after=10)
            
        except discord.Forbidden:
            conf_embed1 = discord.Embed(title= "Erreur !", description="", color=discord.Color.red())
            conf_embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed1.add_field(name="Je n'ai pas les permissions nécessaires pour attribuer ce rôle", value=" ", inline=False)
            conf_embed1.set_footer(text=Help.version1)
            await ctx.send(embed=conf_embed1, delete_after=10)
            
        except discord.HTTPException as e:
            await ctx.send(f"Une erreur s'est produite : {e}")
                
    @commands.command(name='removerole')
    @commands.is_owner()
    async def removerole(self, ctx, utilisateur: discord.Member, role: discord.Role):
        await ctx.message.delete()
        try:
            await utilisateur.remove_roles(role)
            conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.random())
            conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed.add_field(name=f"Le rôle **@{role.name}**", value=f" a été enlevé à {utilisateur.mention}", inline=False)
            conf_embed.set_footer(text=Help.version1)
            await ctx.send(embed=conf_embed, delete_after=10)
    
        except discord.Forbidden:
            conf_embed1 = discord.Embed(title= "Erreur !", description="", color=discord.Color.red())
            conf_embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed1.add_field(name="Je n'ai pas les permissions nécessaires pour enlever ce rôle", value=" ", inline=False)
            conf_embed1.set_footer(text=Help.version1)
            await ctx.send(embed=conf_embed1, delete_after=10)

        except discord.HTTPException as e:
            await ctx.send(f"Une erreur s'est produite : {e}")


    @cleanraidsimple.error
    async def cleanraidsimple_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to manage messages.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please enter the name of the channel to delete.")
        else:
            await ctx.send("An error occurred while processing the command.")

    
    @cleanraidmultiple.error
    async def cleanraidmultiple_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to manage messages.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a valid raid date and time in the format 'YYYY-MM-DD HH:MM'.")
        else:
            await ctx.send("An error occurred while processing the command.")
                  
async def setup(client):
    await client.add_cog(Mods(client))