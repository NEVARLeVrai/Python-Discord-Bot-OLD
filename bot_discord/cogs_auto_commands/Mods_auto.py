import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from cogs.Help import get_current_version
import asyncio

class Mods_auto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.protected_role_id = 1236660715151167548
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Démarrer la tâche pour vérifier les timeouts terminés après un délai
        await asyncio.sleep(5)  # Attendre que les cogs soient complètement initialisés
        if not self.check_timeout_end.is_running():
            self.check_timeout_end.start()
    
    @tasks.loop(minutes=1)
    async def check_timeout_end(self):
        """Vérifie périodiquement si des timeouts sont terminés et remet les rôles"""
        mods_cog = self.get_mods_cog()
        if not mods_cog or not hasattr(mods_cog, 'warns') or not mods_cog.warns:
            return
        
        for guild_id_str, guild_data in mods_cog.warns.items():
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
                                        mods_cog.save_warns()
                                        print(f"Rôle remis à {member.display_name} ({member_id_str}) après timeout terminé")
                                    except Exception as e:
                                        print(f"Erreur lors de la remise du rôle: {e}")
            except Exception as e:
                print(f"Erreur dans check_timeout_end: {e}")
    
    @check_timeout_end.before_loop
    async def before_check_timeout_end(self):
        await self.client.wait_until_ready()
    
    def get_mods_cog(self):
        """Récupère le cog Mods pour accéder aux données partagées"""
        return self.client.get_cog('Mods')
    
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
    
    async def auto_warn_for_banned_word(self, member: discord.Member, guild: discord.Guild, channel: discord.TextChannel, banned_word: str):
        """Warn automatiquement un membre pour avoir utilisé un mot banni"""
        # Ne pas warn les bots
        if member.bot:
            return
        
        # Récupérer le cog Mods pour accéder aux données
        mods_cog = self.get_mods_cog()
        if not mods_cog:
            return
        
        # Vérifier si les warns sont chargés (un dict vide {} est valide, on peut ajouter des warns)
        if not hasattr(mods_cog, 'warns'):
            return
        
        # Initialiser warns si c'est None
        if mods_cog.warns is None:
            mods_cog.warns = {}
        
        member_id = str(member.id)
        guild_id = str(guild.id)
        
        # Initialiser la structure si elle n'existe pas
        if guild_id not in mods_cog.warns:
            mods_cog.warns[guild_id] = {}
        if member_id not in mods_cog.warns[guild_id]:
            mods_cog.warns[guild_id][member_id] = {"count": 0, "warnings": []}
        
        # Raison du warn
        reason = f"mot banni utilisé : {banned_word}"
        warn_count_to_add = 1
        
        # Ajouter le warn
        mods_cog.warns[guild_id][member_id]["count"] += 1
        mods_cog.warns[guild_id][member_id]["warnings"].append({
            "reason": reason,
            "moderator": "Bot (détection automatique)",
            "timestamp": datetime.now().isoformat()
        })
        
        total_warn_count = mods_cog.warns[guild_id][member_id]["count"]
        mods_cog.save_warns()
        
        # Envoyer un MP à l'utilisateur avec l'embed de warn
        if not member.bot:
            try:
                warn_dm = discord.Embed(title="Avertissement", description=f"Vous avez reçu un avertissement sur **{guild.name}**", color=discord.Color.orange())
                warn_dm.add_field(name="Modérateur:", value="Bot (détection automatique)", inline=False)
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
            except Exception:
                # Erreur inattendue, on continue quand même
                pass
        
        # Appliquer les actions automatiques selon le nombre de warns
        previous_warn_count = total_warn_count - warn_count_to_add
        
        # Vérifier les seuils atteints (on vérifie dans l'ordre décroissant pour prendre l'action la plus sévère)
        if total_warn_count >= 20 and previous_warn_count < 20:
            # Ban
            role_was_removed = await self.remove_protected_role(member, guild)
            
            try:
                await guild.ban(member, reason=f"20 warns atteints")
                action_desc = f"{member.mention} a été banni(e) pour avoir atteint 20 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé avant le ban."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.red())
                try:
                    await channel.send(embed=action_embed)
                except:
                    pass
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Erreur ban (20 warns): {e}")
        
        elif total_warn_count >= 15 and previous_warn_count < 15:
            # Kick
            role_was_removed = await self.remove_protected_role(member, guild)
            
            try:
                await guild.kick(member, reason=f"15 warns atteints")
                action_desc = f"{member.mention} a été expulsé(e) pour avoir atteint 15 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé avant le kick."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.red())
                try:
                    await channel.send(embed=action_embed)
                except:
                    pass
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Erreur kick (15 warns): {e}")
        
        elif total_warn_count >= 10 and previous_warn_count < 10:
            # Timeout de 10 minutes pour 10 warns
            role_was_removed = await self.remove_protected_role(member, guild)
            
            timeout_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            try:
                await member.edit(timed_out_until=timeout_until, reason=f"10 warns atteints")
                
                # Si le rôle a été enlevé, le sauvegarder pour le remettre après
                if role_was_removed:
                    if guild_id not in mods_cog.warns:
                        mods_cog.warns[guild_id] = {}
                    if member_id not in mods_cog.warns[guild_id]:
                        mods_cog.warns[guild_id][member_id] = {"count": 0, "warnings": []}
                    mods_cog.warns[guild_id][member_id]["role_removed"] = True
                    mods_cog.warns[guild_id][member_id]["timeout_end"] = timeout_until.isoformat()
                    mods_cog.save_warns()
                
                action_desc = f"{member.mention} a reçu un timeout de 10 minutes pour avoir atteint 10 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé temporairement et sera remis après le timeout."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.yellow())
                try:
                    await channel.send(embed=action_embed)
                except:
                    pass
            except (discord.Forbidden, AttributeError, TypeError) as e:
                print(f"Erreur timeout (10 warns): {e}")
        
        elif total_warn_count >= 5 and previous_warn_count < 5:
            # Timeout de 10 minutes pour 5 warns
            role_was_removed = await self.remove_protected_role(member, guild)
            
            timeout_until = datetime.now(timezone.utc) + timedelta(minutes=10)
            try:
                await member.edit(timed_out_until=timeout_until, reason=f"5 warns atteints")
                
                # Si le rôle a été enlevé, le sauvegarder pour le remettre après
                if role_was_removed:
                    if guild_id not in mods_cog.warns:
                        mods_cog.warns[guild_id] = {}
                    if member_id not in mods_cog.warns[guild_id]:
                        mods_cog.warns[guild_id][member_id] = {"count": 0, "warnings": []}
                    mods_cog.warns[guild_id][member_id]["role_removed"] = True
                    mods_cog.warns[guild_id][member_id]["timeout_end"] = timeout_until.isoformat()
                    mods_cog.save_warns()
                
                action_desc = f"{member.mention} a reçu un timeout de 10 minutes pour avoir atteint 5 warns."
                if role_was_removed:
                    action_desc += f"\nLe rôle protégé a été enlevé temporairement et sera remis après le timeout."
                action_embed = discord.Embed(title="Action Automatique", description=action_desc, color=discord.Color.yellow())
                try:
                    await channel.send(embed=action_embed)
                except:
                    pass
            except (discord.Forbidden, AttributeError, TypeError) as e:
                print(f"Erreur timeout (5 warns): {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Détecte et supprime les messages contenant des mots bannis, puis warn automatiquement"""
        # Ignorer les messages du bot
        if message.author == self.client.user:
            return
        
        # Ignorer les messages dans les DMs
        if not isinstance(message.channel, discord.TextChannel):
            return
        
        # Ignorer les commandes (messages qui commencent par le préfixe "=")
        if message.content and message.content.startswith("="):
            return
        
        # Ignorer les messages vides
        if not message.content:
            return
        
        # Ignorer les bots
        if message.author.bot:
            return
        
        # Récupérer le cog Mods pour accéder aux banned_words
        mods_cog = self.get_mods_cog()
        if not mods_cog:
            return
        
        # Vérifier si banned_words est défini
        if not hasattr(mods_cog, 'banned_words'):
            return
        
        # Initialiser banned_words si c'est None
        if mods_cog.banned_words is None:
            mods_cog.banned_words = []
        
        # Si la liste est vide, pas de mots bannis à vérifier
        if not mods_cog.banned_words:
            return
        
        # Vérifier si le message contient un mot banni
        message_content_lower = message.content.lower()
        for banned_word in mods_cog.banned_words:
            if banned_word.lower() in message_content_lower:
                try:
                    # Supprimer le message
                    await message.delete()
                    
                    # Warn automatiquement l'utilisateur
                    await self.auto_warn_for_banned_word(
                        member=message.author,
                        guild=message.guild,
                        channel=message.channel,
                        banned_word=banned_word
                    )
                    
                    break  # Traiter seulement le premier mot banni trouvé
                except discord.Forbidden:
                    # Le bot n'a pas les permissions pour supprimer le message
                    pass
                except discord.NotFound:
                    # Le message a déjà été supprimé, essayer quand même de warn
                    try:
                        await self.auto_warn_for_banned_word(
                            member=message.author,
                            guild=message.guild,
                            channel=message.channel,
                            banned_word=banned_word
                        )
                    except Exception:
                        pass
                except Exception:
                    # Erreur lors de la détection du mot banni
                    pass

async def setup(client):
    await client.add_cog(Mods_auto(client))

