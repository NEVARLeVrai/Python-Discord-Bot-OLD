import discord
from discord.ext import commands
import asyncio
from cogs import Help
from cogs.Help import get_current_version
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
        self.mp_conversations = {}  # {user_id_receveur: user_id_expediteur} pour tracker les conversations MP
        # Initialiser warns et banned_words à None - seront chargés dans on_ready
        self.warns = None
        self.banned_words = None
    
    @commands.Cog.listener()
    async def on_ready(self):
            # Utiliser le chemin centralisé depuis main.py
        warns_path = self.client.paths['warns_json']
        # Chargement du fichier JSON qui stocke les warns (organisés par serveur)
        if os.path.exists(warns_path):
            with open(warns_path, 'r') as f:
                data = json.load(f)
                # Vérifier que c'est bien un dictionnaire (format par serveur)
                if isinstance(data, dict):
                    self.warns = data
                else:
                    # Si c'est un autre format (liste ou autre), initialiser un dictionnaire vide
                    # L'ancien format n'était pas organisé par serveur, on le supprime
                    self.warns = {}
                    self.save_warns()
        else:
            self.warns = {}
            with open(warns_path, 'w') as f:
                json.dump(self.warns, f)
        
        # Chargement des mots bannis (organisés par serveur)
        banned_words_path = self.client.paths['banned_words_json']
        if os.path.exists(banned_words_path):
            with open(banned_words_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Migration : si c'est une liste (ancien format), convertir en dictionnaire vide
                if isinstance(data, list):
                    # L'ancien format était une liste globale, on la supprime
                    self.banned_words = {}
                    self.save_banned_words()
                elif isinstance(data, dict):
                    # Nouveau format : dictionnaire par guild_id
                    self.banned_words = data
                else:
                    # Format inattendu, initialiser un dictionnaire vide
                    self.banned_words = {}
                    self.save_banned_words()
        else:
            self.banned_words = {}
            with open(banned_words_path, 'w', encoding='utf-8') as f:
                json.dump(self.banned_words, f, ensure_ascii=False, indent=2)
        # Note: La tâche check_timeout_end est maintenant dans cogs_auto_commands/Mods_auto.py
    
    def save_warns(self):
        """Sauvegarde les warns dans le fichier JSON"""
        # Utiliser le chemin centralisé depuis main.py
        warns_path = self.client.paths['warns_json']
        with open(warns_path, 'w') as f:
            json.dump(self.warns, f)
    
    def save_banned_words(self):
        """Sauvegarde les mots bannis dans le fichier JSON"""
        banned_words_path = self.client.paths['banned_words_json']
        with open(banned_words_path, 'w', encoding='utf-8') as f:
            json.dump(self.banned_words, f, ensure_ascii=False, indent=2)
    
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
        
        # Envoyer un MP avant le kick
        try:
            kick_dm = discord.Embed(title="Expulsion", description=f"Vous avez été expulsé(e) du serveur **{ctx.guild.name}**", color=discord.Color.yellow())
            kick_dm.add_field(name="Modérateur:", value=f"{ctx.author.name} ({ctx.author.mention})", inline=False)
            kick_dm.add_field(name="Raison:", value=modreaseon, inline=False)
            kick_dm.set_footer(text=get_current_version(self.client))
            await member.send(embed=kick_dm)
        except discord.Forbidden:
            # L'utilisateur a les DMs désactivés, on continue quand même
            pass
        
        await ctx.guild.kick(member)
        
        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.yellow())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        conf_embed.add_field(name="Expulsé:", value=f"{member.mention} à été kick par {ctx.author.mention}.", inline=False)
        conf_embed.add_field(name="Raison:", value=modreaseon, inline=False)
        conf_embed.set_footer(text=get_current_version(self.client))
        
        await ctx.send(embed=conf_embed)
        
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, args=None):
        """Avertit un membre (par serveur)"""
        await ctx.message.delete()
        
        # Vérifier si on est dans un serveur (pas en MP)
        if not isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(title="Erreur", description="Cette commande ne peut pas être utilisée en MP.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Initialiser warns si c'est None
        if self.warns is None:
            self.warns = {}
        
        # S'assurer que warns est un dictionnaire (format par serveur)
        if not isinstance(self.warns, dict):
            self.warns = {}
        
        # Vérifier si l'auteur essaie de se warn lui-même
        if ctx.author.id == member.id:
            embed = discord.Embed(title="Erreur", description=f"Vous ne pouvez pas vous avertir vous-même.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Vérifier si on essaie d'avertir un bot
        if member.bot:
            embed = discord.Embed(title="Erreur", description=f"Vous ne pouvez pas avertir un bot.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Vérifier si l'auteur est bloqué (ne peut pas utiliser la commande)
        if ctx.author.id == self.blocked_user_id:
            embed = discord.Embed(title="Erreur", description=f"Vous n'avez pas accès à cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
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
        
        conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.orange())
        conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        
        if warn_count_to_add > 1:
            conf_embed.add_field(name="Averti:", value=f"{member.mention} a reçu **{warn_count_to_add}** avertissements de {ctx.author.mention}.", inline=False)
        else:
            conf_embed.add_field(name="Averti:", value=f"{member.mention} a été averti par {ctx.author.mention}.", inline=False)
        
        conf_embed.add_field(name="Raison:", value=reason, inline=False)
        conf_embed.add_field(name="Nombre total de warns:", value=f"{total_warn_count}", inline=False)
        conf_embed.set_footer(text=get_current_version(self.client))
        
        await ctx.send(embed=conf_embed)
        
        # Envoyer un MP à l'utilisateur averti (seulement si ce n'est pas un bot)
        if not member.bot:
            try:
                warn_dm = discord.Embed(title="Avertissement", description=f"Vous avez reçu un avertissement sur **{ctx.guild.name}**", color=discord.Color.orange())
                if warn_count_to_add > 1:
                    warn_dm.add_field(name="Avertissements:", value=f"Vous avez reçu **{warn_count_to_add}** avertissements de {ctx.author.mention}.", inline=False)
                else:
                    warn_dm.add_field(name="Modérateur:", value=f"{ctx.author.name} ({ctx.author.mention})", inline=False)
                warn_dm.add_field(name="Raison:", value=reason, inline=False)
                warn_dm.add_field(name="Nombre total de warns:", value=f"{total_warn_count}", inline=False)
                warn_dm.set_footer(text=get_current_version(self.client))
                await member.send(embed=warn_dm)
            except discord.Forbidden:
                # L'utilisateur a les DMs désactivés, on continue quand même
                pass
            except AttributeError:
                # Erreur si c'est un bot (ne devrait pas arriver avec la vérification, mais on le gère quand même)
                pass
        
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
        """Réinitialise les warns d'un membre (par serveur)"""
        await ctx.message.delete()
        
        # Ignorer si c'est un DM
        if not isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(title="Erreur", description="Cette commande ne peut pas être utilisée en MP.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Initialiser warns si c'est None
        if self.warns is None:
            self.warns = {}
        
        # S'assurer que warns est un dictionnaire (format par serveur)
        if not isinstance(self.warns, dict):
            self.warns = {}
        
        member_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        if guild_id not in self.warns or member_id not in self.warns[guild_id]:
            embed = discord.Embed(title="Erreur", description=f"{member.mention} n'a aucun warn.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
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
        conf_embed.set_footer(text=get_current_version(self.client))
        
        await ctx.send(embed=conf_embed)
    
    @commands.command(aliases=["warnleaderboard", "warnlb"])
    async def warnboard(self, ctx):
        """Affiche le leaderboard des warns (par serveur)"""
        await ctx.message.delete()
        
        # Ignorer si c'est un DM
        if not isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(title="Erreur", description="Cette commande ne peut pas être utilisée en MP.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Initialiser warns si c'est None
        if self.warns is None:
            self.warns = {}
        
        # S'assurer que warns est un dictionnaire (format par serveur)
        if not isinstance(self.warns, dict):
            self.warns = {}
        
        guild_id = str(ctx.guild.id)
        
        # Vérifier si le serveur a des warns
        if guild_id not in self.warns or not self.warns[guild_id]:
            embed = discord.Embed(title="Leaderboard des Warns", description=f"Aucun warn enregistré sur **{ctx.guild.name}**.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
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
        embed = discord.Embed(title="🏆 Leaderboard des Warns", description=f"Top 10 des utilisateurs avec le plus de warns sur **{ctx.guild.name}**", color=discord.Color.orange())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.client))
        
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
    async def ban(self, ctx, target: typing.Union[discord.Member, int], *, modreaseon):
        await ctx.message.delete()
        
        # Vérifier si c'est un ID (int) ou un Member
        if isinstance(target, int):
            # Cas banid : bannir par ID
            user_id = target
            user_obj = discord.Object(id=user_id)
            await ctx.guild.ban(user_obj)
            
            conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.red())
            conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed.add_field(name="Banni:", value=f"<@{user_id}> a été banni par {ctx.author.mention}.", inline=False)
            conf_embed.add_field(name="Raison:", value=modreaseon, inline=False)
            conf_embed.set_footer(text=get_current_version(self.client))
            
            await ctx.send(embed=conf_embed)
        else:
            # Cas ban normal : bannir un Member (avec DM possible)
            member = target
            
            # Envoyer un MP avant le ban
            try:
                ban_dm = discord.Embed(title="Bannissement", description=f"Vous avez été banni(e) du serveur **{ctx.guild.name}**", color=discord.Color.red())
                ban_dm.add_field(name="Modérateur:", value=f"{ctx.author.name} ({ctx.author.mention})", inline=False)
                ban_dm.add_field(name="Raison:", value=modreaseon, inline=False)
                ban_dm.set_footer(text=get_current_version(self.client))
                await member.send(embed=ban_dm)
            except discord.Forbidden:
                # L'utilisateur a les DMs désactivés, on continue quand même
                pass
            
            await ctx.guild.ban(member)

            conf_embed = discord.Embed(title= "Réussi!", description="", color=discord.Color.red())
            conf_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed.add_field(name="Banni:", value=f"{member.mention} a été banni par {ctx.author.mention}.", inline=False)
            conf_embed.add_field(name="Raison:", value=modreaseon, inline=False)
            conf_embed.set_footer(text=get_current_version(self.client))
            
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
        conf_embed.set_footer(text=get_current_version(self.client))
    
        
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
                embed1.set_footer(text=get_current_version(self.client))

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
        embed.set_footer(text=get_current_version(self.client))
        
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
            embed4.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed4, delete_after=5)           
            await channeldel.delete()
            embed3 = discord.Embed(title="Nettoyage Raid par nom", description=f"Salon(s) **{channel}** supprimé avec succès!", color=discord.Color.green())
            embed3.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed3.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed3, delete_after=5)
            
        else:
            embed5 = discord.Embed(title="Nettoyage Raid par nom", description=f"Aucun Salon(s) avec le nom **{name}** trouvé.", color=discord.Color.red())
            embed5.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed5.set_footer(text=get_current_version(self.client))
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
        embed6.set_footer(text=get_current_version(self.client))
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
            conf_embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=conf_embed, delete_after=10)
            
        except discord.Forbidden:
            conf_embed1 = discord.Embed(title= "Erreur !", description="", color=discord.Color.red())
            conf_embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed1.add_field(name="Je n'ai pas les permissions nécessaires pour attribuer ce rôle", value=" ", inline=False)
            conf_embed1.set_footer(text=get_current_version(self.client))
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
            conf_embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=conf_embed, delete_after=10)
    
        except discord.Forbidden:
            conf_embed1 = discord.Embed(title= "Erreur !", description="", color=discord.Color.red())
            conf_embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            conf_embed1.add_field(name="Je n'ai pas les permissions nécessaires pour enlever ce rôle", value=" ", inline=False)
            conf_embed1.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=conf_embed1, delete_after=10)

        except discord.HTTPException as e:
            await ctx.send(f"Une erreur s'est produite : {e}")

    @commands.command()
    async def mp(self, ctx, target: typing.Union[discord.Member, int], *, message: str):
        await ctx.message.delete()
        
        # Si target est un int, c'est un ID, sinon c'est un Member
        if isinstance(target, int):
            try:
                target_user = await self.client.fetch_user(target)
            except discord.NotFound:
                embed = discord.Embed(title="Erreur", description="Utilisateur introuvable.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await ctx.send(embed=embed, delete_after=10)
                return
        else:
            target_user = target
        
        try:
            # Envoyer le message en MP
            await target_user.send(f"**Message de {ctx.author.name} ({ctx.author.mention}):**\n\n{message}")
            
            # Sauvegarder la conversation pour que les réponses soient forwardées
            self.mp_conversations[target_user.id] = ctx.author.id
            
            # Confirmation
            embed = discord.Embed(title="Message envoyé", description=f"Message envoyé en MP à {target_user.mention}", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.add_field(name="Message:", value=message[:500] + ("..." if len(message) > 500 else ""), inline=False)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            
        except discord.Forbidden:
            embed = discord.Embed(title="Erreur", description=f"Impossible d'envoyer un message à {target_user.mention}. Les messages privés sont peut-être désactivés.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Une erreur s'est produite: {str(e)}", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)

    @commands.command(aliases=["addbannedword"])
    @commands.has_permissions(manage_messages=True)
    async def banword(self, ctx, *, word: str):
        """Ajoute un mot à la liste des mots bannis (par serveur)"""
        await ctx.message.delete()
        
        # Ignorer si c'est un DM
        if not isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(title="Erreur", description="Cette commande ne peut pas être utilisée en MP.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Normaliser le mot (minuscules)
        word_lower = word.lower().strip()
        
        if not word_lower:
            embed = discord.Embed(title="Erreur", description="Veuillez spécifier un mot à bannir.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Initialiser banned_words si c'est None
        if self.banned_words is None:
            self.banned_words = {}
        
        # S'assurer que banned_words est un dictionnaire (format par serveur)
        if not isinstance(self.banned_words, dict):
            self.banned_words = {}
        
        # Récupérer le guild_id
        guild_id = str(ctx.guild.id)
        
        # Initialiser la liste pour ce serveur si elle n'existe pas
        if guild_id not in self.banned_words:
            self.banned_words[guild_id] = []
        
        # Vérifier si le mot est déjà banni sur ce serveur
        if word_lower in self.banned_words[guild_id]:
            embed = discord.Embed(title="Mot déjà banni", description=f"Le mot `{word}` est déjà dans la liste des mots bannis de ce serveur.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Ajouter le mot à la liste du serveur
        self.banned_words[guild_id].append(word_lower)
        self.save_banned_words()
        
        embed = discord.Embed(title="Mot banni", description=f"Le mot `{word}` a été ajouté à la liste des mots bannis de ce serveur.", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await ctx.send(embed=embed, delete_after=10)

    @commands.command(aliases=["removebannedword"])
    @commands.has_permissions(manage_messages=True)
    async def unbanword(self, ctx, *, word: str):
        """Retire un mot de la liste des mots bannis (par serveur)"""
        await ctx.message.delete()
        
        # Ignorer si c'est un DM
        if not isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(title="Erreur", description="Cette commande ne peut pas être utilisée en MP.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Normaliser le mot (minuscules)
        word_lower = word.lower().strip()
        
        if not word_lower:
            embed = discord.Embed(title="Erreur", description="Veuillez spécifier un mot à retirer.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Initialiser banned_words si c'est None
        if self.banned_words is None:
            self.banned_words = {}
        
        # S'assurer que banned_words est un dictionnaire (format par serveur)
        if not isinstance(self.banned_words, dict):
            self.banned_words = {}
        
        # Récupérer le guild_id
        guild_id = str(ctx.guild.id)
        
        # Vérifier si le serveur a des mots bannis
        if guild_id not in self.banned_words or word_lower not in self.banned_words[guild_id]:
            embed = discord.Embed(title="Mot non trouvé", description=f"Le mot `{word}` n'est pas dans la liste des mots bannis de ce serveur.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Retirer le mot de la liste du serveur
        self.banned_words[guild_id].remove(word_lower)
        self.save_banned_words()
        
        embed = discord.Embed(title="Mot retiré", description=f"Le mot `{word}` a été retiré de la liste des mots bannis de ce serveur.", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await ctx.send(embed=embed, delete_after=10)

    @commands.command(aliases=["bannedwords", "bwlist"])
    @commands.has_permissions(manage_messages=True)
    async def listbannedwords(self, ctx):
        """Affiche la liste des mots bannis (par serveur)"""
        await ctx.message.delete()
        
        # Ignorer si c'est un DM
        if not isinstance(ctx.channel, discord.TextChannel):
            embed = discord.Embed(title="Erreur", description="Cette commande ne peut pas être utilisée en MP.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Initialiser banned_words si c'est None
        if self.banned_words is None:
            self.banned_words = {}
        
        # S'assurer que banned_words est un dictionnaire (format par serveur)
        if not isinstance(self.banned_words, dict):
            self.banned_words = {}
        
        # Récupérer le guild_id
        guild_id = str(ctx.guild.id)
        
        # Récupérer la liste des mots bannis pour ce serveur
        if guild_id not in self.banned_words or not self.banned_words[guild_id]:
            embed = discord.Embed(title="Liste des mots bannis", description="Aucun mot banni pour le moment sur ce serveur.", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=15)
            return
        
        # Diviser la liste en chunks de 20 mots pour éviter les messages trop longs
        words_list = self.banned_words[guild_id]
        total_words = len(words_list)
        
        # Créer un embed avec la liste
        embed = discord.Embed(title=f"Liste des mots bannis ({total_words})", description=f"Mots bannis sur **{ctx.guild.name}**", color=discord.Color.blue())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.client))
        
        # Afficher les mots (max 1024 caractères par field)
        words_text = ", ".join([f"`{word}`" for word in words_list[:50]])  # Limite à 50 mots pour éviter les messages trop longs
        if len(words_list) > 50:
            words_text += f"\n\n... et {len(words_list) - 50} autre(s) mot(s)"
        
        embed.add_field(name="Mots bannis:", value=words_text if words_text else "Aucun", inline=False)
        await ctx.send(embed=embed, delete_after=30)


                  
async def setup(client):
    await client.add_cog(Mods(client))