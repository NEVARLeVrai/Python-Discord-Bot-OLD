import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import io
import requests
from cogs import Help
from datetime import datetime
import os
import json

def get_version_info(client):
    """Lit les informations de version depuis le fichier update_logs.json"""
    try:
        update_logs_path = client.paths['update_logs_json']
        if os.path.exists(update_logs_path):
            with open(update_logs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            # Valeurs par défaut si le fichier n'existe pas
            print(f"Fichier update_logs.json introuvable à: {update_logs_path}")
            return {
                "current_version": "Bot V.NULL",
                "history": []
            }
    except Exception as e:
        print(f"Erreur lors de la lecture de update_logs.json: {e}")
        import traceback
        traceback.print_exc()
        return {
            "current_version": "Bot V.NULL",
            "history": []
        }

def get_current_version(client):
    """Retourne la version actuelle"""
    data = get_version_info(client)
    return data.get("current_version", "Bot V.NULL")

def get_latest_logs(client):
    """Retourne les logs de la dernière version"""
    data = get_version_info(client)
    history = data.get("history", [])
    if history:
        return history[0].get("logs", "Aucun log disponible.")
    return "Aucun log de mise à jour disponible."

def get_all_history(client):
    """Retourne tout l'historique des versions"""
    data = get_version_info(client)
    return data.get("history", [])


class HelpPaginatorView(View):
    """Vue de pagination pour le menu d'aide"""
    def __init__(self, embeds, files=None, client=None, timeout=300):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.files = files if files else [None] * len(embeds)
        self.current_page = 0
        self.owner = None
        self.client = client
    
    async def update_message(self, interaction: discord.Interaction):
        """Met à jour le message avec l'embed actuel"""
        embed = self.embeds[self.current_page]
        
        # Mettre à jour le footer avec le numéro de page (on modifie directement l'embed)
        if self.client:
            current_version = get_current_version(self.client)
        else:
            current_version = "Bot V.NULL"
        embed.set_footer(text=f"{current_version} | Page {self.current_page + 1}/{len(self.embeds)}")
        
        # Mettre à jour les boutons (désactiver si nécessaire)
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.embeds) - 1
        
        try:
            await interaction.response.edit_message(embed=embed, view=self)
        except discord.NotFound:
            # Le message a été supprimé
            pass
        except Exception as e:
            print(f"Erreur lors de la mise à jour du message: {e}")
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except:
                pass
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: Button):
        """Bouton précédent"""
        if interaction.user != self.owner:
            await interaction.response.send_message("Vous n'êtes pas l'auteur de cette commande.", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        """Bouton suivant"""
        if interaction.user != self.owner:
            await interaction.response.send_message("Vous n'êtes pas l'auteur de cette commande.", ephemeral=True)
            return
        
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()
    
    async def on_timeout(self):
        """Désactive les boutons après le timeout"""
        for item in self.children:
            item.disabled = True
        try:
            # Essayer de mettre à jour le message pour désactiver les boutons
            # Note: on ne peut pas toujours récupérer le message, donc on ignore les erreurs
            pass
        except:
            pass


class Help_slash(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.target_user_id = client.config['target_user_id']
        self.webhook_url = client.config['webhook_url']
    
    def get_version_footer(self):
        """Helper pour obtenir la version pour les footers"""
        return get_current_version(self.client)

    @app_commands.command(name="ping", description="Affiche le ping du bot")
    async def ping(self, interaction: discord.Interaction):
        """Commande slash pour afficher le ping"""
        bot_latency = round(self.client.latency * 1000)
        embed = discord.Embed(title=f"Pong! {bot_latency} ms.", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=self.get_version_footer())
        await interaction.response.send_message(embed=embed, ephemeral=False)

    def create_help_embeds(self, user: discord.User):
        """Crée tous les embeds d'aide"""
        embeds = []
        files = []
        
        # Page 1: Helps principal
        embed1 = discord.Embed(
            title="Helps",
            description="Toutes les commandes",
            color=discord.Color.random()
        )
        embed1.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed1.add_field(name="helps", value="Affiche ce message /helps")
        embed1.add_field(name="ping", value="Affiche le ping du bot /ping")
        embed1.add_field(name="version", value="Affiche la version du bot /version")
        embed1.add_field(name="report", value="Signale un bug ou feedback /report [message]")
        embeds.append(embed1)
        files.append(None)

        # Page 2: Mods
        embed2 = discord.Embed(
            title="Helps Mods",
            description="Toutes les commandes Mods",
            color=discord.Color.random()
        )
        embed2.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed2.add_field(name="clear", value="Supprime des messages /clear [nombre] (messages perms only) max 70 messages")
        embed2.add_field(name="cleanraidsimple", value="Supprime un salon par nom /cleanraidsimple [nom] (messages perms only)")
        embed2.add_field(name="cleanraidmultiple", value="Supprime des salons par date /cleanraidmultiple [date] [heure] (messages perms only)")
        embed2.add_field(name="warn", value="Avertir un membre /warn [@user] [raison] [nombre] (messages perms only) - Les warns sont par serveur")
        embed2.add_field(name="resetwarn", value="Reset les warns d'un membre /resetwarn [@user] (messages perms only) - Les warns sont par serveur")
        embed2.add_field(name="warnboard", value="Affiche le leaderboard des warns /warnboard - Affiche les warns du serveur actuel")
        embed2.add_field(name="kick", value="Expulse un membre /kick [@user] [raison] (kick perms only)")
        embed2.add_field(name="ban", value="Bannit un membre /ban [@user ou ID] [raison] (ban perms only)")
        embed2.add_field(name="unban", value="Débannit un membre /unban [ID] (ban perms only)")
        embed2.add_field(name="giverole", value="Donne un rôle /giverole [@user] [@role] (owner only)")
        embed2.add_field(name="removerole", value="Enlève un rôle /removerole [@user] [@role] (owner only)")
        embed2.add_field(name="mp", value="Envoie un message privé /mp [@user] [message]")
        embed2.add_field(name="spam", value="Spam des messages /spam [nombre] [salon] [message] (admin perms only)")
        embed2.add_field(name="banword", value="Ajoute un mot à la liste des mots bannis /banword [mot] (messages perms only) - Les mots bannis sont par serveur")
        embed2.add_field(name="unbanword", value="Retire un mot de la liste des mots bannis /unbanword [mot] (messages perms only) - Les mots bannis sont par serveur")
        embed2.add_field(name="listbannedwords", value="Affiche la liste des mots bannis /listbannedwords (messages perms only) - Affiche les mots bannis du serveur actuel")
        embed2.add_field(name="📌 Système par serveur", value="Les warns et les mots bannis sont **indépendants par serveur**. Chaque serveur a sa propre liste de mots bannis et ses propres warns.", inline=False)
        embed2.add_field(name="⚠️ Détection automatique", value="Les mots bannis sont automatiquement détectés et supprimés. L'utilisateur reçoit un warn automatique par MP avec la raison \"mot banni utilisé : [mot]\".", inline=False)
        embed2.add_field(name="Sanctions automatiques", value="5 warns → timeout 10 min\n10 warns → timeout 10 min\n15 warns → kick automatique\n20 warns → ban automatique\n\nLes sanctions sont appliquées **par serveur** (les warns ne sont pas partagés entre serveurs).", inline=False)
        embeds.append(embed2)
        files.append(None)

        # Page 3: Utility
        embed3 = discord.Embed(
            title="Helps Utility",
            description="Toutes les commandes d'Utility",
            color=discord.Color.random()
        )
        embed3.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed3.add_field(name="gpt", value="Utilise GPT /gpt [votre question]")
        embed3.add_field(name="dalle", value="Génère une image avec DALL-E /dalle [votre prompt]")
        embed3.add_field(name="say", value="Envoie un message /say [salon] [message]")
        embed3.add_field(name="8ball", value="Pose une question à la boule magique /8ball [votre question]")
        embed3.add_field(name="hilaire", value="Jeu Hilaire /hilaire")
        embed3.add_field(name="deldms", value="Supprime tous les DMs du bot /deldms (admin perms only)")
        embed3.add_field(name="correcteur", value="Active/désactive le correcteur automatique /correcteur [action] (messages perms only)")
        embed3.add_field(name="langue", value="Gère les langues du correcteur /langue [action] [langue] (messages perms only)")
        embed3.add_field(name="🔗 Conversion automatique", value="Le bot convertit automatiquement les liens sociaux pour des embeds optimisés:\n• TikTok → tiktokez.com (résout les liens courts vm.tiktok.com)\n• Instagram → eeinstagram.com\n• Twitter/X → fxtwitter.com\n• Reddit → vxreddit.com (résout les liens courts redd.it)\n\nLes messages originaux sont supprimés et remplacés par le lien optimisé.", inline=False)
        embed3.add_field(name="🔍 Correcteur automatique", value="Le bot corrige automatiquement l'orthographe et la grammaire des messages:\n• Supporte 40+ langues (fr, en, es, de, it, pt, etc.)\n• Mode auto pour détection automatique de langue\n• Répond au message avec la phrase corrigée et les fautes en gras\n• Configuration par serveur (activé/désactivé + langues)\n• Analyse contextuelle (grammaire, conjugaison, liaisons)", inline=False)
        embeds.append(embed3)
        files.append(None)

        # Page 4: YouTube
        embed4 = discord.Embed(
            title="Helps YouTube",
            description="Toutes les commandes YouTube",
            color=discord.Color.random()
        )
        embed4.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed4.add_field(name="leave", value="Déconnecte le bot du vocal /leave")
        embed4.add_field(name="play", value="Joue une vidéo YouTube /play [URL] - se connecte automatiquement au vocal")
        embed4.add_field(name="search", value="Recherche une vidéo YouTube /search [recherche] - se connecte automatiquement au vocal")
        embed4.add_field(name="skip", value="Skip la vidéo en cours /skip")
        embed4.add_field(name="stopm", value="Arrête la lecture /stopm")
        embed4.add_field(name="pause", value="Met en pause la vidéo /pause")
        embed4.add_field(name="resume", value="Reprend la vidéo /resume")
        embed4.add_field(name="queue", value="Affiche la file d'attente /queue")
        embed4.add_field(name="clearq", value="Vide la file d'attente /clearq")
        embed4.add_field(name="loop", value="Active/désactive la boucle /loop")
        embed4.add_field(name="File d'attente", value="La file d'attente fonctionne uniquement entre vidéos YouTube. Si Soundboard ou TTS joue, YouTube interrompt et joue directement.", inline=False)
        embeds.append(embed4)
        files.append(None)

        # Page 5: Soundboard
        embed5 = discord.Embed(
            title="Helps Soundboard",
            description="Toutes les commandes de Soundboard",
            color=discord.Color.random()
        )
        embed5.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed5.add_field(name="slist", value="Liste tous les sons disponibles avec leur durée /slist")
        embed5.add_field(name="splay", value="Joue un son /splay [numéro] (ex: /splay 1) - se connecte automatiquement au vocal")
        embed5.add_field(name="sleave", value="Fait quitter le bot du salon vocal /sleave")
        embed5.add_field(name="sstop", value="Arrête le son en cours /sstop")
        embed5.add_field(name="srandom", value="Joue des sons aléatoires toutes les 1-5 minutes /srandom - se connecte automatiquement au vocal")
        embed5.add_field(name="srandomskip", value="Skip le son aléatoire en cours /srandomskip")
        embed5.add_field(name="srandomstop", value="Arrête la lecture aléatoire /srandomstop")
        embed5.add_field(name="vkick", value="Expulse un utilisateur du vocal /vkick [@user] (admin perms only)")
        embed5.add_field(name="tts", value="Fait parler le bot /tts [texte] [langue] [volume] - se connecte automatiquement au vocal")
        embed5.add_field(name="Formats audio", value="Formats supportés : MP3, MP4, M4A, OGG, OPUS, WAV, FLAC, AAC", inline=False)
        embed5.add_field(name="Gestion des conflits", value="Soundboard, YouTube et TTS partagent la connexion vocale. Si un module joue, les autres l'interrompent et jouent directement.", inline=False)
        embeds.append(embed5)
        files.append(None)

        # Page 6: Leveling
        embed6 = discord.Embed(
            title="Helps Leveling",
            description="Toutes les commandes de Leveling",
            color=discord.Color.random()
        )
        embed6.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed6.add_field(name="level, lvl", value="Voir votre niveau /level [@user] (optionnel)")
        embed6.add_field(name="resetlevel, rsl", value="Reset tous les niveaux /resetlevel (messages perms only)")
        embed6.add_field(name="levelsettings, lvls", value="Active/désactive le système de leveling /levelsettings (admins perms only)")
        embed6.add_field(name="levelboard", value="Affiche le leaderboard des levels /levelboard")
        embed6.add_field(name="⚡ Système automatique", value="Le leveling fonctionne automatiquement : chaque message = +1 XP. Un niveau est atteint quand XP ≥ (niveau+1)². Un message de félicitations est envoyé automatiquement.", inline=False)
        embeds.append(embed6)
        files.append(None)

        # Page 7: MP (avec image)
        embed7 = discord.Embed(
            title="Helps MP",
            description="Commandes disponible en MP",
            color=discord.Color.random()
        )
        embed7.set_author(
            name=f"Demandé par {user.name}",
            icon_url=user.avatar
        )
        embed7.add_field(name="helps", value="Affiche ce message /helps")
        embed7.add_field(name="ping", value="Affiche le ping du bot /ping")
        embed7.add_field(name="version", value="Affiche la version du bot /version")
        embed7.add_field(name="report", value="Signale un bug ou feedback /report [message]")
        embed7.add_field(name="gpt", value="Utilise GPT /gpt [votre question]")
        embed7.add_field(name="dalle", value="Génère une image avec DALL-E /dalle [votre prompt]")
        
        try:
            with open(self.client.paths['info_png'], "rb") as f:
                image_data = f.read()
            file = discord.File(io.BytesIO(image_data), "info.png")
            embed7.set_thumbnail(url="attachment://info.png")
            embeds.append(embed7)
            files.append(file)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image info.png: {e}")
            embeds.append(embed7)
            files.append(None)
        
        return embeds, files

    @app_commands.command(name="helps", description="Affiche toutes les commandes disponibles")
    async def helps(self, interaction: discord.Interaction):
        """Affiche toutes les commandes disponibles avec pagination"""
        await interaction.response.defer(ephemeral=False)
        
        # Créer tous les embeds
        embeds, files = self.create_help_embeds(interaction.user)
        
        # Mettre à jour tous les embeds avec le footer pour la pagination
        current_version = get_current_version(self.client)
        for i, embed in enumerate(embeds):
            # Ajouter le footer à chaque embed
            embeds[i].set_footer(text=f"{current_version} | Page {i + 1}/{len(embeds)}")
        
        # Créer la vue de pagination
        view = HelpPaginatorView(embeds, files, client=self.client)
        view.owner = interaction.user
        
        # Envoyer le premier embed avec les boutons
        await interaction.followup.send(embed=embeds[0], view=view)

    @app_commands.command(name="version", description="Affiche la version du bot")
    @app_commands.describe(history="Affiche l'historique complet si mis à 'true'")
    async def version(self, interaction: discord.Interaction, history: bool = False):
        """Affiche la version du bot"""
        try:
            version_info = get_version_info(self.client)
            current_version = get_current_version(self.client)
            latest_logs = get_latest_logs(self.client)
            
            # Si l'utilisateur demande l'historique complet
            if history:
                all_history = get_all_history(self.client)
                if not all_history:
                    embed = discord.Embed(
                        title="Historique des Versions",
                        description="Aucun historique disponible.",
                        color=discord.Color.orange()
                    )
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    await interaction.response.send_message(embed=embed, ephemeral=False)
                    return
                
                await interaction.response.defer(ephemeral=False)
                
                # Créer un embed avec l'historique complet
                embed = discord.Embed(
                    title="📜 Historique des Versions",
                    description=f"**Version actuelle:** {current_version}\n\n",
                    color=discord.Color.blue()
                )
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                
                # Ajouter chaque version de l'historique (limité à 10 pour éviter les embeds trop longs)
                for idx, entry in enumerate(all_history[:10], 1):
                    version = entry.get("version", "Inconnue")
                    date = entry.get("date", "Date inconnue")
                    logs = entry.get("logs", "Aucun log")
                    # Limiter la longueur des logs pour éviter les embeds trop longs
                    if len(logs) > 200:
                        logs = logs[:197] + "..."
                    embed.add_field(
                        name=f"{idx}. {version} - {date}",
                        value=f"`{logs}`",
                        inline=False
                    )
                
                if len(all_history) > 10:
                    embed.set_footer(text=f"Affichage des 10 dernières versions sur {len(all_history)} totales")
                else:
                    embed.set_footer(text=f"{len(all_history)} version(s) dans l'historique")
                
                await interaction.followup.send(embed=embed)
                return
            
            # Affichage normal de la version actuelle
            embed = discord.Embed(title="Versions du Bot", color=discord.Color.random())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.add_field(name="", value="")
            embed.add_field(name="Version Actuelle", value=current_version)
            
            # Ajouter la date de la dernière version si disponible
            all_history = get_all_history(self.client)
            if all_history and len(all_history) > 0:
                latest_date = all_history[0].get("date", "")
                if latest_date:
                    embed.add_field(name="Date de la dernière mise à jour", value=latest_date)
            
            embed.add_field(name="Derniers Logs", value=f"`{latest_logs}`", inline=False)
            embed.add_field(name="", value="")
            embed.add_field(name="📜 Historique", value="Utilisez `/version history:true` pour voir l'historique complet", inline=False)
            embed.add_field(name="Date format", value="`DD/MM/YYYY`")
            
            try:
                with open(self.client.paths['version_jpg'], "rb") as f:
                    image_data = f.read()
                embed.set_thumbnail(url="attachment://version.jpg")
                await interaction.response.send_message(embed=embed, file=discord.File(io.BytesIO(image_data), "version.jpg"), ephemeral=False)
            except Exception as e:
                # Si l'image ne peut pas être chargée, envoyer sans image
                print(f"Erreur lors du chargement de l'image version.jpg: {e}")
                await interaction.response.send_message(embed=embed, ephemeral=False)
        except Exception as e:
            # Gestion d'erreur globale
            print(f"Erreur dans la commande /version: {e}")
            import traceback
            traceback.print_exc()
            try:
                error_embed = discord.Embed(
                    title="Erreur",
                    description="Une erreur s'est produite lors de l'affichage de la version.",
                    color=discord.Color.red()
                )
                if interaction.response.is_done():
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=error_embed, ephemeral=True)
            except:
                pass

    @app_commands.command(name="report", description="Signale un bug ou donne un feedback")
    @app_commands.describe(message="Le message de signalement")
    async def report(self, interaction: discord.Interaction, message: str):
        """Signaler un bug"""
        await interaction.response.defer(ephemeral=True)
        
        ticket_number = datetime.now().strftime("%d%m%Y")
        data = {
            "content": f"**Bug signalé !**\n\nTicket: **#{ticket_number}{interaction.user.name}**\nPar: **{interaction.user.name}**\nID: **{interaction.user.id}**\nMention: {interaction.user.mention}\n\nContenu: {message}\n\n**{self.get_version_footer()}**"
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.client.config['webhook_url'], json=data, headers=headers)
        
        if response.status_code == 204:
            user = interaction.user
            embedc2 = discord.Embed(title="Signalement", description="Votre rapport de bug a été enregistré avec succès.", color=discord.Color.green())
            embedc2.add_field(name="", value=f"Ticket : **#{ticket_number}{interaction.user.name}**", inline=False)
            embedc2.add_field(name="", value="Nous allons le corriger dès que possible!", inline=False)
            embedc2.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embedc2.set_footer(text=self.get_version_footer())
            try:
                await user.send(embed=embedc2)
            except:
                pass
            
            embedc = discord.Embed(title="Signalement", description="Merci d'avoir signalé ce bug.", color=discord.Color.green())
            embedc.add_field(name="", value=f"Ticket : **#{ticket_number}{interaction.user.name}**", inline=False)
            embedc.add_field(name="", value="Nous allons le corriger dès que possible.", inline=False)
            embedc.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embedc.set_footer(text=self.get_version_footer())
            await interaction.followup.send(embed=embedc, ephemeral=True)
        else:
            embedc1 = discord.Embed(title="Erreur de signalement.", description="Erreur lors de l'envoi du message.", color=discord.Color.red())
            embedc1.add_field(name="", value="Veuillez réessayer plus tard.", inline=False)
            embedc1.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embedc1.set_footer(text=self.get_version_footer())
            await interaction.followup.send(embed=embedc1, ephemeral=True)


async def setup(client):
    await client.add_cog(Help_slash(client))

