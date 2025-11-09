import discord
from discord import app_commands
from discord.ext import commands
from yt_dlp import YoutubeDL
import asyncio
from cogs import Help
from cogs.Help import get_current_version

class Youtube_slash(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.loop_state = False
        self.pause_state = False
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        self.ffmpeg_path = client.paths['ffmpeg_exe']
    
    async def cog_load(self):
        # Récupérer le cog Youtube original pour réutiliser ses méthodes
        # Note: cog_load est appelé après que tous les cogs soient chargés
        pass
    
    def sync_with_original(self):
        """Synchronise les données avec le cog Youtube original"""
        self.youtube_cog = self.client.get_cog('Youtube')
        if self.youtube_cog:
            # Synchroniser la queue avec le cog original
            self.queue = self.youtube_cog.queue
            self.loop_state = self.youtube_cog.loop_state
            self.pause_state = self.youtube_cog.pause_state
            # Synchroniser les options ffmpeg
            self.ffmpeg_options = self.youtube_cog.ffmpeg_options

    def check_queue(self, interaction):
        async def inner_check_queue():
            if len(self.queue) > 0:
                next_video = self.queue.pop(0)
                voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
                if voice:
                    voice.play(discord.FFmpegPCMAudio(next_video['url'], **self.ffmpeg_options), after=lambda e: self.check_queue(interaction))
                    voice.is_playing()
                    asyncio.create_task(self.check_empty_channel(interaction))
                    embed = discord.Embed(title="YouTube - File d'attente", description=f'Vidéo YouTube suivante dans la file d\'attente : **{next_video["title"]}**', color=discord.Color.blue())
                    embed.set_footer(text=get_current_version(self.client))
                    channel = self.client.get_channel(interaction.channel.id)
                    if channel:
                        await channel.send(embed=embed, delete_after=10)
                else:
                    # Si la boucle est activée, remettre la vidéo dans la queue
                    if self.loop_state:
                        self.queue.append(next_video)

        self.client.loop.create_task(inner_check_queue())

    async def check_empty_channel(self, interaction):
        await asyncio.sleep(120)
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice and voice.channel:
            if len(voice.channel.members) == 1:
                await voice.disconnect()
                embed = discord.Embed(title="YouTube - Déconnexion automatique", description="Aucun utilisateur détecté pendant 2 minutes. Je quitte le canal vocal.", color=discord.Color.orange())
                embed.set_footer(text=get_current_version(self.client))
                channel = self.client.get_channel(interaction.channel.id)
                if channel:
                    await channel.send(embed=embed, delete_after=10)

    @app_commands.command(name="play", description="Joue une vidéo YouTube")
    @app_commands.describe(url="L'URL de la vidéo YouTube")
    async def play(self, interaction: discord.Interaction, url: str):
        """Joue une vidéo YouTube"""
        self.sync_with_original()
        await interaction.response.defer(ephemeral=False)
        
        if not interaction.user.voice:
            embed = discord.Embed(title="YouTube - Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        channel = interaction.user.voice.channel

        if not voice or not voice.is_connected():
            try:
                voice = await channel.connect()
            except discord.errors.ClientException as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            except Exception as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        else:
            if voice.channel != channel:
                try:
                    await voice.move_to(channel)
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                except Exception as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

        try:
            with YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(url, download=False)
            audio_url = info['url']

            if voice and voice.is_paused():
                self.queue.append({'title': info['title'], 'url': audio_url})
                if self.youtube_cog:
                    self.youtube_cog.queue = self.queue.copy()
                embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{info["title"]}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=False)
            elif voice and voice.is_playing() and len(self.queue) > 0:
                self.queue.append({'title': info['title'], 'url': audio_url})
                if self.youtube_cog:
                    self.youtube_cog.queue = self.queue.copy()
                embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{info["title"]}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=False)
            else:
                if voice and voice.is_playing():
                    voice.stop()
                    self.queue.clear()
                    if self.youtube_cog:
                        self.youtube_cog.queue.clear()
                    await asyncio.sleep(0.5)
                
                # Utiliser la méthode check_queue du cog original si disponible
                if self.youtube_cog:
                    # Réutiliser la méthode check_queue du cog original
                    class FakeCtx:
                        def __init__(self, interaction):
                            self.guild = interaction.guild
                            self.channel = interaction.channel
                            self.send = interaction.followup.send
                    fake_ctx = FakeCtx(interaction)
                    voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.youtube_cog.check_queue(fake_ctx))
                else:
                    voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.check_queue(interaction))
                voice.is_playing()
                # Synchroniser avec le cog original
                if self.youtube_cog:
                    self.youtube_cog.queue = self.queue.copy()
                embed = discord.Embed(title="YouTube - Lecture", description=f'Le bot est en train de jouer : **{info["title"]}**', color=discord.Color.green())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(title="YouTube - Erreur", description=f"Une erreur s'est produite : {str(e)}", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="search", description="Recherche une vidéo YouTube")
    @app_commands.describe(query="La recherche à effectuer", choice="Le numéro de la vidéo à jouer (1-10)")
    async def search(self, interaction: discord.Interaction, query: str, choice: int = None):
        """Recherche une vidéo YouTube"""
        self.sync_with_original()
        await interaction.response.defer(ephemeral=False)
        
        if not interaction.user.voice:
            embed = discord.Embed(title="YouTube - Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        search_options = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'noplaylist': True
        }
        
        play_options = {
            'format': 'bestaudio',
            'quiet': True,
            'no_warnings': True,
            'skip_unavailable_fragments': True,
            'noplaylist': True
        }

        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        channel = interaction.user.voice.channel

        if not voice or not voice.is_connected():
            try:
                voice = await channel.connect()
            except discord.errors.ClientException as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            except Exception as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        else:
            if voice.channel != channel:
                try:
                    await voice.move_to(channel)
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                except Exception as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

        try:
            with YoutubeDL(search_options) as ydl:
                info = ydl.extract_info(f'ytsearch10:{query}', download=False)
            
            if not info or 'entries' not in info:
                embed = discord.Embed(title="YouTube - Recherche", description="Aucun résultat trouvé pour cette recherche.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            videos = [v for v in info.get('entries', []) if v is not None]
            
            if not videos:
                embed = discord.Embed(title="YouTube - Recherche", description="Aucune vidéo valide trouvée pour cette recherche.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            valid_videos = []
            result_list = []
            for video in videos:
                try:
                    if video and 'title' in video and 'id' in video:
                        result_list.append(f"**{len(valid_videos) + 1}.** {video['title']}")
                        valid_videos.append(video)
                except Exception:
                    continue

            if not valid_videos:
                embed = discord.Embed(title="YouTube - Recherche", description="Aucune vidéo valide trouvée pour cette recherche.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            result_text = "\n".join(result_list)
            embed = discord.Embed(title="YouTube - Résultats de recherche", description=f"Résultats pour **'{query}'** :\n\n{result_text}", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)

            # Si choice est fourni, jouer directement
            if choice is not None:
                if 1 <= choice <= len(valid_videos):
                    selected_video = valid_videos[choice - 1]
                    video_url = f"https://www.youtube.com/watch?v={selected_video.get('id', '')}"
                    with YoutubeDL(play_options) as ydl:
                        video_info = ydl.extract_info(video_url, download=False)
                    audio_url = video_info['url']
                    video_title = video_info.get('title', selected_video.get('title', 'Titre inconnu'))

                    if voice and voice.is_paused():
                        self.queue.append({'title': video_title, 'url': audio_url})
                        if self.youtube_cog:
                            self.youtube_cog.queue = self.queue.copy()
                        embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{video_title}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await interaction.followup.send(embed=embed, ephemeral=False)
                    elif voice and voice.is_playing() and len(self.queue) > 0:
                        self.queue.append({'title': video_title, 'url': audio_url})
                        if self.youtube_cog:
                            self.youtube_cog.queue = self.queue.copy()
                        embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{video_title}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await interaction.followup.send(embed=embed, ephemeral=False)
                    else:
                        if voice and voice.is_playing():
                            voice.stop()
                            self.queue.clear()
                            if self.youtube_cog:
                                self.youtube_cog.queue.clear()
                            await asyncio.sleep(0.5)
                        
                        # Utiliser la méthode check_queue du cog original si disponible
                        if self.youtube_cog:
                            class FakeCtx:
                                def __init__(self, interaction):
                                    self.guild = interaction.guild
                                    self.channel = interaction.channel
                                    self.send = interaction.followup.send
                            fake_ctx = FakeCtx(interaction)
                            voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.youtube_cog.check_queue(fake_ctx))
                        else:
                            voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.check_queue(interaction))
                        voice.is_playing()
                        # Synchroniser avec le cog original
                        if self.youtube_cog:
                            self.youtube_cog.queue = self.queue.copy()
                        embed = discord.Embed(title="YouTube - Lecture", description=f'Le bot est en train de jouer : **"{video_title}"**', color=discord.Color.green())
                        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await interaction.followup.send(embed=embed, ephemeral=False)
                else:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Numéro invalide. Veuillez choisir un nombre entre 1 et {len(valid_videos)}.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed2 = discord.Embed(title="YouTube - Choix", description=f"Utilisez `/search query:\"{query}\" choice:[numéro]` pour jouer une vidéo.", color=discord.Color.blue())
                embed2.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed2, ephemeral=False)

        except Exception as e:
            embed = discord.Embed(title="YouTube - Erreur", description=f"Une erreur s'est produite lors de la recherche : {str(e)}", color=discord.Color.red())
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"Erreur search: {e}")

    @app_commands.command(name="skip", description="Skip la vidéo en cours")
    async def skip(self, interaction: discord.Interaction):
        """Skip la vidéo en cours"""
        self.sync_with_original()
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            voice.stop()
            # Vérifier si la queue existe et n'est pas vide avant d'accéder au premier élément
            if self.queue and len(self.queue) > 0:
                next_video = self.queue[0]
                embed = discord.Embed(title="YouTube - Skip", description=f"Vidéo YouTube suivante dans la file d'attente : **{next_video['title']}**", color=discord.Color.green())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.response.send_message(embed=embed, ephemeral=False)
            else:
                embed = discord.Embed(title="YouTube - Skip", description="Aucune vidéo YouTube suivante dans la file d'attente.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en cours de lecture.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="stopm", description="Arrête la lecture")
    async def stopm(self, interaction: discord.Interaction):
        """Arrête la lecture"""
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            voice.stop()
            embed = discord.Embed(title="YouTube - Arrêt", description="Lecture terminée.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en cours de lecture.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="pause", description="Met en pause la vidéo")
    async def pause(self, interaction: discord.Interaction):
        """Met en pause la vidéo"""
        self.sync_with_original()
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing() and not self.pause_state:
            voice.pause()
            self.pause_state = True
            if self.youtube_cog:
                self.youtube_cog.pause_state = True
            embed = discord.Embed(title="YouTube - Pause", description="La vidéo YouTube est en pause.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en cours de lecture ou la vidéo est déjà en pause.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="resume", description="Reprend la vidéo")
    async def resume(self, interaction: discord.Interaction):
        """Reprend la vidéo"""
        self.sync_with_original()
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice and voice.is_paused() and self.pause_state:
            voice.resume()
            self.pause_state = False
            if self.youtube_cog:
                self.youtube_cog.pause_state = False
            embed = discord.Embed(title="YouTube - Reprise", description="La vidéo YouTube a repris.", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en pause.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="queue", description="Affiche la file d'attente")
    async def queue(self, interaction: discord.Interaction):
        """Affiche la file d'attente"""
        self.sync_with_original()
        if not self.queue:
            embed = discord.Embed(title="YouTube - File d'attente", description="La file d'attente de vidéos YouTube est vide.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            queue_list = "\n".join([f"**{index + 1}.** {video['title']}" for index, video in enumerate(self.queue)])
            embed = discord.Embed(title="YouTube - File d'attente", description=f"File d'attente de vidéos YouTube :\n\n{queue_list}", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="clearq", description="Vide la file d'attente")
    async def clearq(self, interaction: discord.Interaction):
        """Vide la file d'attente"""
        self.sync_with_original()
        self.queue.clear()
        if self.youtube_cog:
            self.youtube_cog.queue.clear()
            self.queue = self.youtube_cog.queue
        embed = discord.Embed(title="YouTube - File d'attente", description="La file d'attente de vidéos YouTube a été effacée.", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="leave", description="Déconnecte le bot du vocal")
    async def leave(self, interaction: discord.Interaction):
        """Déconnecte le bot du vocal"""
        voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice:
            await voice.disconnect()
            embed = discord.Embed(title="YouTube - Déconnexion", description="Déconnecté du salon vocal.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Le bot n'est pas connecté à un salon vocal.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="loop", description="Active/désactive la boucle")
    async def loop(self, interaction: discord.Interaction):
        """Active/désactive la boucle"""
        self.sync_with_original()
        self.loop_state = not self.loop_state
        if self.youtube_cog:
            self.youtube_cog.loop_state = self.loop_state
        embed = discord.Embed(title="YouTube - Boucle", description=f"Boucle **{'activée' if self.loop_state else 'désactivée'}**.", color=discord.Color.green() if self.loop_state else discord.Color.red())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await interaction.response.send_message(embed=embed, ephemeral=False)


async def setup(client):
    await client.add_cog(Youtube_slash(client))

