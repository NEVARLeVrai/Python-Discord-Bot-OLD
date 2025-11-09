import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import pytz
import asyncio
import json
import os
from cogs import Help
from cogs.Help import get_current_version

class Mods_slash(commands.Cog):
    def __init__(self, client):
        self.client = client
        # Récupérer le cog Mods original pour réutiliser les données et méthodes
        self.mods_cog = None
        # Initialiser les valeurs par défaut pour éviter les erreurs
        self.warns = {}
        self.banned_words = []
        self.protected_role_id = 1236660715151167548
        self.blocked_user_id = 440168985615400984
        self.mp_conversations = {}
    
    async def cog_load(self):
        # Ne rien faire ici, on attendra on_ready()
        pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Récupérer le cog Mods original après que tous les cogs soient prêts
        # Attendre un peu pour que tous les cogs soient complètement initialisés
        await asyncio.sleep(2)
        self.mods_cog = self.client.get_cog('Mods')
        if self.mods_cog:
            # Synchroniser les données du cog Mods
            if hasattr(self.mods_cog, 'warns'):
                self.warns = self.mods_cog.warns
                print(f"Mods_slash: Système de warns synchronisé depuis le cog Mods. {len(self.warns)} serveur(s) avec des warns.")
            if hasattr(self.mods_cog, 'banned_words'):
                self.banned_words = self.mods_cog.banned_words
                print(f"Mods_slash: Système de mots bannis synchronisé depuis le cog Mods. {len(self.banned_words)} mot(s) banni(s).")
            if hasattr(self.mods_cog, 'protected_role_id'):
                self.protected_role_id = self.mods_cog.protected_role_id
            if hasattr(self.mods_cog, 'blocked_user_id'):
                self.blocked_user_id = self.mods_cog.blocked_user_id
            if hasattr(self.mods_cog, 'mp_conversations'):
                self.mp_conversations = self.mods_cog.mp_conversations
        else:
            print("Mods_slash: ATTENTION - Le cog Mods n'a pas été trouvé! Chargement depuis les fichiers JSON...")
            # Charger depuis les fichiers JSON si le cog n'est pas disponible
            self._load_from_files()
    
    def _load_from_files(self):
        """Charge les données depuis les fichiers JSON si le cog n'est pas disponible"""
        # Charger les warns
        try:
            warns_path = self.client.paths['warns_json']
            if os.path.exists(warns_path):
                with open(warns_path, 'r', encoding='utf-8') as f:
                    self.warns = json.load(f)
                    print(f"Mods_slash: Warns chargés depuis le fichier. {len(self.warns)} serveur(s) avec des warns.")
            else:
                self.warns = {}
                print("Mods_slash: Fichier warns.json introuvable, initialisation d'un dictionnaire vide.")
        except Exception as e:
            print(f"Mods_slash: Erreur lors du chargement des warns depuis le fichier: {e}")
            self.warns = {}
        
        # Charger les mots bannis
        try:
            banned_words_path = self.client.paths['banned_words_json']
            if os.path.exists(banned_words_path):
                with open(banned_words_path, 'r', encoding='utf-8') as f:
                    self.banned_words = json.load(f)
                    print(f"Mods_slash: Mots bannis chargés depuis le fichier. {len(self.banned_words)} mot(s) banni(s).")
            else:
                self.banned_words = []
                print("Mods_slash: Fichier banned_words.json introuvable, initialisation d'une liste vide.")
        except Exception as e:
            print(f"Mods_slash: Erreur lors du chargement des mots bannis depuis le fichier: {e}")
            self.banned_words = []

    def save_warns(self):
        """Sauvegarde les warns"""
        if self.mods_cog:
            self.mods_cog.warns = self.warns
            self.mods_cog.save_warns()
        else:
            # Sauvegarder directement dans le fichier
            try:
                warns_path = self.client.paths['warns_json']
                with open(warns_path, 'w', encoding='utf-8') as f:
                    json.dump(self.warns, f, indent=2)
            except Exception as e:
                print(f"Mods_slash: Erreur lors de la sauvegarde des warns: {e}")

    def save_banned_words(self):
        """Sauvegarde les mots bannis"""
        if self.mods_cog:
            self.mods_cog.banned_words = self.banned_words
            self.mods_cog.save_banned_words()
        else:
            # Sauvegarder directement dans le fichier
            try:
                banned_words_path = self.client.paths['banned_words_json']
                with open(banned_words_path, 'w', encoding='utf-8') as f:
                    json.dump(self.banned_words, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Mods_slash: Erreur lors de la sauvegarde des mots bannis: {e}")
    
    def get_mods_cog(self):
        """Récupère le cog Mods de manière robuste"""
        if not self.mods_cog:
            self.mods_cog = self.client.get_cog('Mods')
            # Si le cog n'est toujours pas disponible, charger depuis les fichiers
            if not self.mods_cog:
                self._load_from_files()
        
        # Toujours s'assurer que le cog Mods a les attributs nécessaires initialisés
        if self.mods_cog:
            self._ensure_mods_cog_initialized()
        
        return self.mods_cog
    
    def _ensure_mods_cog_initialized(self):
        """S'assure que le cog Mods a tous ses attributs initialisés"""
        if not self.mods_cog:
            return
        
        # Vérifier et initialiser warns si nécessaire
        if not hasattr(self.mods_cog, 'warns') or self.mods_cog.warns is None:
            try:
                warns_path = self.client.paths['warns_json']
                if os.path.exists(warns_path):
                    with open(warns_path, 'r', encoding='utf-8') as f:
                        self.mods_cog.warns = json.load(f)
                else:
                    self.mods_cog.warns = {}
            except Exception as e:
                print(f"Erreur lors du chargement des warns dans le cog Mods: {e}")
                self.mods_cog.warns = {}
        
        # Vérifier et initialiser banned_words si nécessaire
        if not hasattr(self.mods_cog, 'banned_words') or self.mods_cog.banned_words is None:
            try:
                banned_words_path = self.client.paths['banned_words_json']
                if os.path.exists(banned_words_path):
                    with open(banned_words_path, 'r', encoding='utf-8') as f:
                        self.mods_cog.banned_words = json.load(f)
                else:
                    self.mods_cog.banned_words = []
            except Exception as e:
                print(f"Erreur lors du chargement des mots bannis dans le cog Mods: {e}")
                self.mods_cog.banned_words = []
    
    def ensure_warns_loaded(self):
        """S'assure que les warns sont chargés"""
        if not self.warns:
            mods_cog = self.get_mods_cog()
            if mods_cog and hasattr(mods_cog, 'warns'):
                self.warns = mods_cog.warns
            elif not self.warns:
                self._load_from_files()
    
    def ensure_banned_words_loaded(self):
        """S'assure que les mots bannis sont chargés"""
        if not self.banned_words:
            mods_cog = self.get_mods_cog()
            if mods_cog and hasattr(mods_cog, 'banned_words'):
                self.banned_words = mods_cog.banned_words
            elif not self.banned_words:
                self._load_from_files()
    
    def create_fake_ctx(self, interaction, use_edit_response=False):
        """Crée un FakeCtx pour utiliser les méthodes du cog original avec les commandes slash"""
        class FakeMessage:
            """Fake message avec méthode delete async qui ne fait rien"""
            async def delete(self):
                pass  # Ne rien faire pour les commandes slash
        
        # Compteur pour savoir si c'est le premier message après defer
        first_message = {'value': True}
        
        async def send_wrapper(*args, **kwargs):
            """Wrapper pour send qui gère delete_after avec les webhooks et edit_original_response"""
            # Si c'est le premier message après defer et qu'on veut utiliser edit_original_response
            if use_edit_response and first_message['value']:
                first_message['value'] = False
                # Pour edit_original_response, on ignore delete_after (on veut que le message reste)
                kwargs.pop('delete_after', None)
                try:
                    # Utiliser edit_original_response pour remplacer le message "réfléchit..."
                    return await interaction.edit_original_response(*args, **kwargs)
                except (discord.NotFound, discord.HTTPException) as e:
                    # Si l'édition échoue, utiliser followup.send
                    print(f"Erreur lors de l'édition de la réponse originale: {e}")
                    return await interaction.followup.send(*args, **kwargs)
            else:
                # Pour les messages suivants ou si use_edit_response=False
                delete_after = kwargs.pop('delete_after', None)
                if delete_after is not None:
                    # Les webhooks ne supportent pas delete_after, donc on utilise channel.send à la place
                    if interaction.channel:
                        return await interaction.channel.send(*args, **kwargs, delete_after=delete_after)
                # Utiliser le followup normal
                return await interaction.followup.send(*args, **kwargs)
        
        class FakeCtx:
            """Fake context pour réutiliser la logique des commandes préfixées"""
            def __init__(self, interaction):
                self.author = interaction.user
                self.guild = interaction.guild
                self.channel = interaction.channel
                self.send = send_wrapper
                self.message = FakeMessage()
        
        return FakeCtx(interaction)

    @app_commands.command(name="clear", description="Supprime des messages")
    @app_commands.describe(amount="Nombre de messages à supprimer (max 70)")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        """Supprime des messages"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Vous n'avez pas la permission de gérer les messages.", ephemeral=True)
            return
        
        # Defer immédiatement pour éviter les problèmes de double réponse
        await interaction.response.defer(ephemeral=False)
        
        max_amount = 70
        if amount > max_amount:
            await interaction.followup.send(f"Vous ne pouvez pas supprimer plus de **{max_amount}** messages à la fois. Le nombre a été limité à {max_amount}.", ephemeral=False)
            amount = max_amount
        
        if amount < 1:
            await interaction.followup.send("Le nombre de messages à supprimer doit être supérieur à 0.", ephemeral=True)
            return
        
        try:
            # purge() supprime les messages, mais pas le message de l'interaction
            # On doit supprimer amount messages (pas amount+1 car il n'y a pas de message de commande)
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: not m.pinned)
            
            # Essayer d'envoyer le message de confirmation rapidement
            # Le webhook expire après 15 minutes, mais on essaie quand même
            try:
                # Utiliser wait=True pour s'assurer que le webhook est disponible
                await interaction.followup.send(f"**{len(deleted)}** messages ont été supprimés.", ephemeral=False, wait=False)
            except (discord.NotFound, discord.HTTPException) as e:
                # Webhook expiré ou erreur HTTP - envoyer un message normal au channel
                try:
                    if interaction.channel:
                        embed = discord.Embed(
                            title="Messages supprimés",
                            description=f"**{len(deleted)}** messages ont été supprimés.",
                            color=discord.Color.green()
                        )
                        embed.set_footer(text=get_current_version(self.client))
                        await interaction.channel.send(embed=embed, delete_after=5)
                except Exception as channel_error:
                    # Si on ne peut pas envoyer de message, juste logger
                    print(f"Impossible d'envoyer le message de confirmation: {channel_error}")
            except Exception as e:
                # Autre erreur - logger mais continuer
                print(f"Erreur lors de l'envoi du message de confirmation: {e}")
                
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="Erreur",
                description="Le bot n'a pas la permission de supprimer des messages dans ce channel.",
                color=discord.Color.red()
            )
            error_embed.set_footer(text=get_current_version(self.client))
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True, wait=False)
            except (discord.NotFound, discord.HTTPException):
                # Webhook expiré - envoyer un message normal
                try:
                    if interaction.channel:
                        await interaction.channel.send(embed=error_embed, delete_after=10)
                except:
                    pass
        except Exception as e:
            error_embed = discord.Embed(
                title="Erreur",
                description=f"Erreur lors de la suppression: {str(e)}",
                color=discord.Color.red()
            )
            error_embed.set_footer(text=get_current_version(self.client))
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True, wait=False)
            except (discord.NotFound, discord.HTTPException):
                # Webhook expiré - envoyer un message normal
                try:
                    if interaction.channel:
                        await interaction.channel.send(embed=error_embed, delete_after=10)
                except:
                    pass
            except Exception as send_error:
                print(f"Erreur lors de l'envoi du message d'erreur: {send_error}")

    @app_commands.command(name="kick", description="Expulse un membre")
    @app_commands.describe(member="Le membre à expulser", reason="La raison de l'expulsion")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Aucune raison spécifiée"):
        """Expulse un membre"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("Vous n'avez pas la permission d'expulser des membres.", ephemeral=True)
            return
        
        # Vérifier qu'on ne peut pas kick soi-même
        if member.id == interaction.user.id:
            await interaction.response.send_message("Vous ne pouvez pas vous expulser vous-même.", ephemeral=True)
            return
        
        # Vérifier la hiérarchie des rôles
        if interaction.user.top_role <= member.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Vous ne pouvez pas expulser ce membre car il a un rôle supérieur ou égal au vôtre.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=False)
        
        try:
            # Envoyer un MP à l'utilisateur
            try:
                kick_dm = discord.Embed(title="Expulsion", description=f"Vous avez été expulsé(e) du serveur **{interaction.guild.name}**", color=discord.Color.yellow())
                kick_dm.add_field(name="Modérateur:", value=f"{interaction.user.name} ({interaction.user.mention})", inline=False)
                kick_dm.add_field(name="Raison:", value=reason, inline=False)
                kick_dm.set_footer(text=get_current_version(self.client))
                await member.send(embed=kick_dm)
            except discord.Forbidden:
                pass
            
            # Expulser le membre
            await interaction.guild.kick(member, reason=reason)
            
            # Confirmation
            conf_embed = discord.Embed(title="Réussi!", description="", color=discord.Color.yellow())
            conf_embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            conf_embed.add_field(name="Expulsé:", value=f"{member.mention} a été expulsé par {interaction.user.mention}.", inline=False)
            conf_embed.add_field(name="Raison:", value=reason, inline=False)
            conf_embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=conf_embed, ephemeral=False)
        except discord.Forbidden:
            error_embed = discord.Embed(title="Erreur", description="Le bot n'a pas la permission d'expulser des membres.", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="Erreur", description=f"Une erreur s'est produite: {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="warn", description="Avertit un membre")
    @app_commands.describe(member="Le membre à avertir", reason="La raison de l'avertissement", count="Nombre de warns à ajouter (défaut: 1)")
    @app_commands.default_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str, count: int = 1):
        """Avertit un membre"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Vous n'avez pas la permission de gérer les messages.", ephemeral=True)
            return
        
        # S'assurer que les warns sont chargés
        self.ensure_warns_loaded()
        
        # Vérifier qu'on a bien un système de warns disponible
        if not hasattr(self, 'warns') or self.warns is None:
            await interaction.response.send_message("Le système de warns n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        # Synchroniser avec le cog si disponible
        mods_cog = self.get_mods_cog()
        if mods_cog and hasattr(mods_cog, 'warns'):
            self.mods_cog = mods_cog
            self.warns = mods_cog.warns
        if mods_cog and hasattr(mods_cog, 'blocked_user_id'):
            self.blocked_user_id = mods_cog.blocked_user_id
        
        # Vérifications
        if interaction.user.id == member.id:
            await interaction.response.send_message("Vous ne pouvez pas vous avertir vous-même.", ephemeral=True)
            return
        
        # Vérifier si on essaie d'avertir un bot
        if member.bot:
            await interaction.response.send_message("Vous ne pouvez pas avertir un bot.", ephemeral=True)
            return
        
        if hasattr(self, 'blocked_user_id') and interaction.user.id == self.blocked_user_id:
            await interaction.response.send_message("Vous n'avez pas accès à cette commande.", ephemeral=True)
            return
        
        if count < 1:
            count = 1
        if count > 10:
            await interaction.response.send_message("Vous ne pouvez pas ajouter plus de 10 warns à la fois.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=False)
        
        # Utiliser la logique du cog original via un wrapper
        guild_id = str(interaction.guild.id)
        member_id = str(member.id)
        
        # Initialiser les structures de données si nécessaire
        if guild_id not in self.warns:
            self.warns[guild_id] = {}
        if member_id not in self.warns[guild_id]:
            self.warns[guild_id][member_id] = {"count": 0, "warnings": []}
        
        # Ajouter les warns
        for _ in range(count):
            self.warns[guild_id][member_id]["count"] += 1
            self.warns[guild_id][member_id]["warnings"].append({
                "reason": reason,
                "moderator": interaction.user.name,
                "timestamp": datetime.now().isoformat()
            })
        
        total_warn_count = self.warns[guild_id][member_id]["count"]
        
        # Sauvegarder les warns
        if self.mods_cog:
            self.mods_cog.warns = self.warns
            self.mods_cog.save_warns()
        else:
            self.save_warns()
        
        # Embed de confirmation
        conf_embed = discord.Embed(title="Réussi!", description="", color=discord.Color.orange())
        conf_embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        
        if count > 1:
            conf_embed.add_field(name="Averti:", value=f"{member.mention} a reçu **{count}** avertissements de {interaction.user.mention}.", inline=False)
        else:
            conf_embed.add_field(name="Averti:", value=f"{member.mention} a été averti par {interaction.user.mention}.", inline=False)
        
        conf_embed.add_field(name="Raison:", value=reason, inline=False)
        conf_embed.add_field(name="Nombre total de warns:", value=f"{total_warn_count}", inline=False)
        conf_embed.set_footer(text=get_current_version(self.client))
        await interaction.followup.send(embed=conf_embed)
        
        # Envoyer un MP à l'utilisateur averti (seulement si ce n'est pas un bot)
        if not member.bot:
            try:
                warn_dm = discord.Embed(title="Avertissement", description=f"Vous avez reçu un avertissement sur **{interaction.guild.name}**", color=discord.Color.orange())
                if count > 1:
                    warn_dm.add_field(name="Avertissements:", value=f"Vous avez reçu **{count}** avertissements de {interaction.user.mention}.", inline=False)
                else:
                    warn_dm.add_field(name="Modérateur:", value=f"{interaction.user.name} ({interaction.user.mention})", inline=False)
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
        
        # Appliquer les actions automatiques (simplifié pour les commandes slash)
        # On délègue au cog original pour la logique complète
        try:
            fake_ctx = self.create_fake_ctx(interaction)
            # Appeler la logique d'actions automatiques du cog original (simplifié)
            # Pour une implémentation complète, il faudrait refactorer cette logique
        except Exception as e:
            print(f"Erreur lors de l'application des actions automatiques: {e}")

    @app_commands.command(name="resetwarn", description="Reset les warns d'un membre")
    @app_commands.describe(member="Le membre dont les warns doivent être reset")
    @app_commands.default_permissions(manage_messages=True)
    async def resetwarn(self, interaction: discord.Interaction, member: discord.Member):
        """Reset les warns d'un membre"""
        # S'assurer que les warns sont chargés
        self.ensure_warns_loaded()
        
        if not hasattr(self, 'warns') or self.warns is None:
            await interaction.response.send_message("Le système de warns n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        mods_cog = self.get_mods_cog()
        if mods_cog:
            await interaction.response.defer(ephemeral=False)
            # Synchroniser avec le cog original
            self.mods_cog = mods_cog
            if hasattr(mods_cog, 'warns'):
                self.warns = mods_cog.warns
            # Utiliser la logique du cog original
            fake_ctx = self.create_fake_ctx(interaction, use_edit_response=True)
            await mods_cog.resetwarn(fake_ctx, member)
        else:
            await interaction.response.send_message("Le système de warns n'est pas disponible. Le cog Mods n'a pas été trouvé.", ephemeral=True)

    @app_commands.command(name="warnboard", description="Affiche le leaderboard des warns")
    async def warnboard(self, interaction: discord.Interaction):
        """Affiche le leaderboard des warns"""
        # S'assurer que les warns sont chargés
        self.ensure_warns_loaded()
        
        if not hasattr(self, 'warns') or self.warns is None:
            await interaction.response.send_message("Le système de warns n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        mods_cog = self.get_mods_cog()
        if mods_cog:
            await interaction.response.defer(ephemeral=False)
            # Synchroniser avec le cog original
            self.mods_cog = mods_cog
            if hasattr(mods_cog, 'warns'):
                self.warns = mods_cog.warns
            fake_ctx = self.create_fake_ctx(interaction, use_edit_response=True)
            await mods_cog.warnboard(fake_ctx)
        else:
            await interaction.response.send_message("Le système de warns n'est pas disponible. Le cog Mods n'a pas été trouvé.", ephemeral=True)

    @app_commands.command(name="ban", description="Bannit un membre")
    @app_commands.describe(user="Le membre ou l'ID à bannir", reason="La raison du bannissement")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: str, reason: str):
        """Bannit un membre"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("Vous n'avez pas la permission de bannir des membres.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=False)
        
        try:
            # Essayer de convertir en int (ID) ou récupérer le membre
            try:
                user_id = int(user)
                target = user_id
            except ValueError:
                # Ce n'est pas un ID, essayer de récupérer le membre depuis la mention
                if user.startswith("<@") and user.endswith(">"):
                    user_id = int(user[2:-1].replace("!", "").replace("&", ""))
                    target = user_id
                else:
                    await interaction.followup.send("Format invalide. Utilisez une mention ou un ID.", ephemeral=True)
                    return
            
            # S'assurer que le cog Mods est disponible
            if not self.mods_cog:
                self.mods_cog = self.client.get_cog('Mods')
            
            if self.mods_cog:
                fake_ctx = self.create_fake_ctx(interaction, use_edit_response=True)
                await self.mods_cog.ban(fake_ctx, target, modreaseon=reason)
            else:
                # Fallback si le cog n'est pas disponible
                try:
                    await interaction.guild.ban(discord.Object(id=target), reason=reason)
                    embed = discord.Embed(
                        title="Réussi!",
                        description=f"Utilisateur {target} a été banni.",
                        color=discord.Color.red()
                    )
                    embed.add_field(name="Raison:", value=reason, inline=False)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed)
                except discord.Forbidden:
                    error_embed = discord.Embed(
                        title="Erreur",
                        description="Le bot n'a pas la permission de bannir des membres.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                except discord.NotFound:
                    error_embed = discord.Embed(
                        title="Erreur",
                        description="Utilisateur introuvable.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(
                title="Erreur",
                description=f"Erreur lors du bannissement: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="unban", description="Débannit un membre")
    @app_commands.describe(user_id="L'ID de l'utilisateur à débannir")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        """Débannit un membre"""
        await interaction.response.defer(ephemeral=False)
        
        try:
            user = discord.Object(id=int(user_id))
            await interaction.guild.unban(user)
            
            conf_embed = discord.Embed(title="Réussi!", description="", color=discord.Color.green())
            conf_embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            conf_embed.add_field(name="Débanni:", value=f"<@{user_id}> à été débanni du serveur par {interaction.user.mention}.", inline=False)
            conf_embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=conf_embed, ephemeral=False)
        except Exception as e:
            await interaction.followup.send(f"Erreur: {str(e)}", ephemeral=True)

    @app_commands.command(name="banword", description="Ajoute un mot à la liste des mots bannis")
    @app_commands.describe(word="Le mot à bannir")
    @app_commands.default_permissions(manage_messages=True)
    async def banword(self, interaction: discord.Interaction, word: str):
        """Ajoute un mot à la liste des mots bannis"""
        # S'assurer que les mots bannis sont chargés
        self.ensure_banned_words_loaded()
        
        if not hasattr(self, 'banned_words') or self.banned_words is None:
            await interaction.response.send_message("Le système de mots bannis n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        mods_cog = self.get_mods_cog()
        if mods_cog:
            await interaction.response.defer(ephemeral=False)
            # Synchroniser avec le cog original
            self.mods_cog = mods_cog
            if hasattr(mods_cog, 'banned_words'):
                self.banned_words = mods_cog.banned_words
            fake_ctx = self.create_fake_ctx(interaction, use_edit_response=True)
            await mods_cog.banword(fake_ctx, word=word)
        else:
            await interaction.response.send_message("Le système de mots bannis n'est pas disponible. Le cog Mods n'a pas été trouvé.", ephemeral=True)

    @app_commands.command(name="unbanword", description="Retire un mot de la liste des mots bannis")
    @app_commands.describe(word="Le mot à retirer")
    @app_commands.default_permissions(manage_messages=True)
    async def unbanword(self, interaction: discord.Interaction, word: str):
        """Retire un mot de la liste des mots bannis"""
        # S'assurer que les mots bannis sont chargés
        self.ensure_banned_words_loaded()
        
        if not hasattr(self, 'banned_words') or self.banned_words is None:
            await interaction.response.send_message("Le système de mots bannis n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        mods_cog = self.get_mods_cog()
        if mods_cog:
            await interaction.response.defer(ephemeral=False)
            # Synchroniser avec le cog original
            self.mods_cog = mods_cog
            if hasattr(mods_cog, 'banned_words'):
                self.banned_words = mods_cog.banned_words
            fake_ctx = self.create_fake_ctx(interaction, use_edit_response=True)
            await mods_cog.unbanword(fake_ctx, word=word)
        else:
            await interaction.response.send_message("Le système de mots bannis n'est pas disponible. Le cog Mods n'a pas été trouvé.", ephemeral=True)

    @app_commands.command(name="listbannedwords", description="Affiche la liste des mots bannis")
    @app_commands.default_permissions(manage_messages=True)
    async def listbannedwords(self, interaction: discord.Interaction):
        """Affiche la liste des mots bannis"""
        # S'assurer que les mots bannis sont chargés
        self.ensure_banned_words_loaded()
        
        if not hasattr(self, 'banned_words') or self.banned_words is None:
            await interaction.response.send_message("Le système de mots bannis n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        mods_cog = self.get_mods_cog()
        if mods_cog:
            await interaction.response.defer(ephemeral=False)
            # Synchroniser avec le cog original
            self.mods_cog = mods_cog
            if hasattr(mods_cog, 'banned_words'):
                self.banned_words = mods_cog.banned_words
            fake_ctx = self.create_fake_ctx(interaction, use_edit_response=True)
            await mods_cog.listbannedwords(fake_ctx)
        else:
            await interaction.response.send_message("Le système de mots bannis n'est pas disponible. Le cog Mods n'a pas été trouvé.", ephemeral=True)

    @app_commands.command(name="spam", description="Spam des messages")
    @app_commands.describe(amount="Nombre de messages", channel="Le salon où envoyer les messages", message="Le message à spammer")
    @app_commands.default_permissions(administrator=True)
    async def spam(self, interaction: discord.Interaction, amount: int, channel: discord.TextChannel, message: str):
        """Spam des messages"""
        await interaction.response.defer(ephemeral=False)
        
        max_amount = 200
        if amount > max_amount:
            await interaction.followup.send(f"Le nombre maximum de messages que vous pouvez envoyer est de **{max_amount}**.", ephemeral=False)
            amount = max_amount

        embed = discord.Embed(title="Spam Envoyé!", description=f"Spam envoyé de {amount} message(s) dans {channel.mention}", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await interaction.followup.send(embed=embed, ephemeral=False)

        sent_messages = 0
        while sent_messages < amount:
            if sent_messages >= max_amount:
                break
            await channel.send(message)
            sent_messages += 1
            await asyncio.sleep(0.5)

    @app_commands.command(name="cleanraidsimple", description="Supprime un salon par nom")
    @app_commands.describe(name="Le nom du salon à supprimer")
    @app_commands.default_permissions(manage_messages=True)
    async def cleanraidsimple(self, interaction: discord.Interaction, name: str):
        """Supprime un salon par nom"""
        await interaction.response.defer(ephemeral=False)
        
        found = False
        channeldel = None 
        
        for channel in self.client.get_all_channels():
            if channel.name == name:
                found = True
                channeldel = channel
                        
        if found:
            embed4 = discord.Embed(title="Nettoyage Raid par nom", description=f"Suppression des ou d'un Salon(s) **{channeldel.name}**", color=discord.Color.yellow())
            embed4.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed4.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed4, ephemeral=False)           
            await channeldel.delete()
            embed3 = discord.Embed(title="Nettoyage Raid par nom", description=f"Salon(s) **{channeldel.name}** supprimé avec succès!", color=discord.Color.green())
            embed3.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed3.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed3, ephemeral=False)
            
        else:
            embed5 = discord.Embed(title="Nettoyage Raid par nom", description=f"Aucun Salon(s) avec le nom **{name}** trouvé.", color=discord.Color.red())
            embed5.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed5.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed5, ephemeral=False)

    @app_commands.command(name="cleanraidmultiple", description="Supprime des salons par date")
    @app_commands.describe(raid_date="Date du raid (format: YYYY-MM-DD)", raid_time="Heure du raid (format: HH:MM ou HHhMM)")
    @app_commands.default_permissions(manage_messages=True)
    async def cleanraidmultiple(self, interaction: discord.Interaction, raid_date: str, raid_time: str):
        """Supprime des salons par date"""
        await interaction.response.defer(ephemeral=False)
        
        try:
            raid_datetime_str = raid_date + " " + raid_time.replace("h", ":")
            raid_datetime = datetime.strptime(raid_datetime_str, "%Y-%m-%d %H:%M")
            time_difference = datetime.now(pytz.utc).hour - datetime.now().hour
            raid_datetime = raid_datetime.replace(hour=time_difference+raid_datetime.hour, tzinfo=pytz.UTC)
            
            deleted_count = 0
            for channel in self.client.get_all_channels():
                if channel.created_at > raid_datetime:
                    try:
                        await channel.delete()
                        deleted_count += 1
                    except:
                        pass
            
            embed6 = discord.Embed(title="Nettoyage Raid par temps", description=f"Salon(s) créés après **{raid_datetime}** ont été supprimés ({deleted_count} salon(s))", color=discord.Color.green())
            embed6.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed6.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed6, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Format de date/heure invalide. Utilisez le format: YYYY-MM-DD pour la date et HH:MM pour l'heure. Erreur: {str(e)}", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def is_owner_check(self, interaction: discord.Interaction) -> bool:
        """Vérifie si l'utilisateur est le propriétaire du bot"""
        try:
            app_info = await self.client.application_info()
            return interaction.user.id == app_info.owner.id
        except:
            return False

    @app_commands.command(name="giverole", description="Donne un rôle à un utilisateur")
    @app_commands.describe(member="L'utilisateur", role="Le rôle à donner")
    async def giverole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Donne un rôle"""
        # Vérifier si l'utilisateur est le propriétaire
        if not await self.is_owner_check(interaction):
            await interaction.response.send_message("Cette commande est réservée au propriétaire du bot.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=False)
        
        try:
            await member.add_roles(role, reason=f"Commande exécutée par {interaction.user}")
            conf_embed = discord.Embed(title="Réussi!", description="", color=discord.Color.random())
            conf_embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            conf_embed.add_field(name=f"Le rôle **@{role.name}**", value=f"a été attribué à {member.mention}", inline=False)
            conf_embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=conf_embed, ephemeral=False)
            
        except discord.Forbidden:
            conf_embed1 = discord.Embed(title="Erreur !", description="", color=discord.Color.red())
            conf_embed1.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            conf_embed1.add_field(name="Erreur", value="Je n'ai pas les permissions nécessaires pour attribuer ce rôle.", inline=False)
            conf_embed1.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=conf_embed1, ephemeral=False)
            
        except discord.HTTPException as e:
            error_embed = discord.Embed(title="Erreur", description=f"Une erreur s'est produite : {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="Erreur", description=f"Une erreur inattendue s'est produite : {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="removerole", description="Enlève un rôle à un utilisateur")
    @app_commands.describe(member="L'utilisateur", role="Le rôle à enlever")
    async def removerole(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Enlève un rôle"""
        # Vérifier si l'utilisateur est le propriétaire
        if not await self.is_owner_check(interaction):
            await interaction.response.send_message("Cette commande est réservée au propriétaire du bot.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=False)
        
        try:
            await member.remove_roles(role, reason=f"Commande exécutée par {interaction.user}")
            conf_embed = discord.Embed(title="Réussi!", description="", color=discord.Color.random())
            conf_embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            conf_embed.add_field(name=f"Le rôle **@{role.name}**", value=f"a été enlevé à {member.mention}", inline=False)
            conf_embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=conf_embed, ephemeral=False)

        except discord.Forbidden:
            conf_embed1 = discord.Embed(title="Erreur !", description="", color=discord.Color.red())
            conf_embed1.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            conf_embed1.add_field(name="Erreur", value="Je n'ai pas les permissions nécessaires pour enlever ce rôle.", inline=False)
            conf_embed1.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=conf_embed1, ephemeral=False)

        except discord.HTTPException as e:
            error_embed = discord.Embed(title="Erreur", description=f"Une erreur s'est produite : {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        except Exception as e:
            error_embed = discord.Embed(title="Erreur", description=f"Une erreur inattendue s'est produite : {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)

    @app_commands.command(name="mp", description="Envoie un message privé à un utilisateur")
    @app_commands.describe(user="L'utilisateur", message="Le message à envoyer")
    async def mp(self, interaction: discord.Interaction, user: discord.User, message: str):
        """Envoie un message privé"""
        await interaction.response.defer(ephemeral=False)
        
        try:
            target_user = user
            
            # S'assurer que le cog Mods est disponible
            if not self.mods_cog:
                self.mods_cog = self.client.get_cog('Mods')
            
            # Envoyer le message en MP
            await target_user.send(f"**Message de {interaction.user.name} ({interaction.user.mention}):**\n\n{message}")
            
            # Sauvegarder la conversation pour que les réponses soient forwardées
            if self.mods_cog and hasattr(self.mods_cog, 'mp_conversations'):
                self.mods_cog.mp_conversations[target_user.id] = interaction.user.id
                if hasattr(self, 'mp_conversations'):
                    self.mp_conversations[target_user.id] = interaction.user.id
            
            # Confirmation
            embed = discord.Embed(title="Message envoyé", description=f"Message envoyé en MP à {target_user.mention}", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.add_field(name="Message:", value=message[:500] + ("..." if len(message) > 500 else ""), inline=False)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
            
        except discord.Forbidden:
            embed = discord.Embed(title="Erreur", description=f"Impossible d'envoyer un message à cet utilisateur. Les messages privés sont peut-être désactivés.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Une erreur s'est produite: {str(e)}", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(client):
    await client.add_cog(Mods_slash(client))

