import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import asyncio
from cogs import Help

class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pause_state = False
        self.queue = []
        self.loop_state = False  # Variable pour suivre l'état de la boucle
        # Utiliser le chemin centralisé depuis main.py
        ffmpeg_path = bot.paths['ffmpeg_exe']
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
            'executable': ffmpeg_path
        }

    @commands.command()
    async def leave(self, ctx):
        await ctx.message.delete()
        await ctx.voice_client.disconnect()
        embed = discord.Embed(title="YouTube - Déconnexion", description="Déconnecté du salon vocal.", color=discord.Color.red())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def play(self, ctx, url):
        await ctx.message.delete()
        
        if not ctx.author.voice:
            embed = discord.Embed(title="YouTube - Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
            return
        
        ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel

        if not voice or not voice.is_connected():
            # Pas connecté, se connecter
            try:
                voice = await channel.connect()
            except discord.errors.ClientException as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return
            except Exception as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return
        else:
            # Déjà connecté, vérifier si c'est le bon canal
            if voice.channel != channel:
                try:
                    # Déplacer vers le nouveau canal
                    await voice.move_to(channel)
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=Help.version1)
                    await ctx.send(embed=embed, delete_after=10)
                    return
                except Exception as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=Help.version1)
                    await ctx.send(embed=embed, delete_after=10)
                    return

        try:
            with YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(url, download=False)
            audio_url = info['url']

            # Vérifier si c'est vraiment YouTube qui joue
            # Si YT est en pause OU si YT joue ET qu'il y a une queue (c'est YT qui gère), ajouter à la file
            # Sinon (Soundboard/TTS joue ou rien ne joue), arrêter et jouer directement
            if voice and voice.is_paused():
                # YT est en pause, ajouter à la file
                self.queue.append({'title': info['title'], 'url': audio_url})
                embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{info["title"]}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
            elif voice and voice.is_playing() and len(self.queue) > 0:
                # YT joue et il y a déjà une queue YT, ajouter à la file
                self.queue.append({'title': info['title'], 'url': audio_url})
                embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{info["title"]}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
            else:
                # Soit rien ne joue, soit Soundboard/TTS joue (queue vide = pas YT)
                # Arrêter toute lecture en cours et jouer YT directement
                if voice and voice.is_playing():
                    voice.stop()
                    # Vider la queue YT si Soundboard/TTS jouait (pour éviter confusion)
                    self.queue.clear()
                    await asyncio.sleep(0.5)  # Attendre que la lecture s'arrête
                
                # Jouer la vidéo directement
                voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.check_queue(ctx))
                voice.is_playing()
                embed = discord.Embed(title="YouTube - Lecture", description=f'Le bot est en train de jouer : **{info["title"]}**', color=discord.Color.green())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
        except Exception as e:
            embed = discord.Embed(title="YouTube - Erreur", description=f"Une erreur s'est produite : {str(e)}", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

    def check_queue(self, ctx):
        async def inner_check_queue():
            if len(self.queue) > 0:
                next_video = self.queue.pop(0)
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                voice.play(discord.FFmpegPCMAudio(next_video['url'], **self.ffmpeg_options), after=lambda e: self.check_queue(ctx))
                voice.is_playing()
                asyncio.create_task(self.check_empty_channel(ctx))
                embed = discord.Embed(title="YouTube - File d'attente", description=f'Vidéo YouTube suivante dans la file d\'attente : **{next_video["title"]}**', color=discord.Color.blue())
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)

        self.bot.loop.create_task(inner_check_queue())

    async def check_empty_channel(self, ctx):
        await asyncio.sleep(120)
        voice_channel = ctx.voice_client.channel
        if len(voice_channel.members) == 1:
            await ctx.voice_client.disconnect()
            embed = discord.Embed(title="YouTube - Déconnexion automatique", description="Aucun utilisateur détecté pendant 2 minutes. Je quitte le canal vocal.", color=discord.Color.orange())
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def skip(self, ctx):
        await ctx.message.delete()
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            next_video = self.queue[0] if self.queue else None
            voice_client.stop()
            if next_video:
                embed = discord.Embed(title="YouTube - Skip", description=f"Vidéo YouTube suivante dans la file d'attente : **{next_video['title']}**", color=discord.Color.green())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
            else:
                embed = discord.Embed(title="YouTube - Skip", description="Aucune vidéo YouTube suivante dans la file d'attente.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en cours de lecture.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def stopm(self, ctx):
        await ctx.message.delete()
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            embed = discord.Embed(title="YouTube - Arrêt", description="Lecture terminée.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en cours de lecture.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def pause(self, ctx):
        await ctx.message.delete()
        voice_client = ctx.voice_client
        if voice_client.is_playing() and not self.pause_state:
            voice_client.pause()
            self.pause_state = True
            embed = discord.Embed(title="YouTube - Pause", description="La vidéo YouTube est en pause.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en cours de lecture ou la vidéo est déjà en pause.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def resume(self, ctx):
        await ctx.message.delete()
        voice_client = ctx.voice_client
        if voice_client.is_paused() and self.pause_state:
            voice_client.resume()
            self.pause_state = False
            embed = discord.Embed(title="YouTube - Reprise", description="La vidéo YouTube a repris.", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
        else:
            embed = discord.Embed(title="YouTube - Erreur", description="Aucune vidéo n'est en pause.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def queue(self, ctx):
        await ctx.message.delete()
        if not self.queue:
            embed = discord.Embed(title="YouTube - File d'attente", description="La file d'attente de vidéos YouTube est vide.", color=discord.Color.orange())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
        else:
            queue_list = "\n".join([f"**{index + 1}.** {video['title']}" for index, video in enumerate(self.queue)])
            embed = discord.Embed(title="YouTube - File d'attente", description=f"File d'attente de vidéos YouTube :\n\n{queue_list}", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=30)

    @commands.command()
    async def clearq(self, ctx):
        await ctx.message.delete()
        self.queue.clear()
        embed = discord.Embed(title="YouTube - File d'attente", description="La file d'attente de vidéos YouTube a été effacée.", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)

    @commands.command()
    async def search(self, ctx, *query):
        await ctx.message.delete()
        query = " ".join(query)
        
        if not ctx.author.voice:
            embed = discord.Embed(title="YouTube - Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Options pour la recherche initiale (flat = juste les métadonnées de base, pas de téléchargement)
        search_options = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Mode plat - ne télécharge pas toutes les infos
            'noplaylist': True
        }
        
        # Options pour l'extraction complète de la vidéo sélectionnée
        play_options = {
            'format': 'bestaudio',
            'quiet': True,
            'no_warnings': True,
            'skip_unavailable_fragments': True,
            'noplaylist': True
        }

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel

        # Vérifier si le bot n'est pas dans un canal vocal
        if not voice or not voice.is_connected():
            try:
                voice = await channel.connect()
            except discord.errors.ClientException as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return
            except Exception as e:
                embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return
        else:
            # Déjà connecté, vérifier si c'est le bon canal
            if voice.channel != channel:
                try:
                    # Déplacer vers le nouveau canal
                    await voice.move_to(channel)
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=Help.version1)
                    await ctx.send(embed=embed, delete_after=10)
                    return
                except Exception as e:
                    embed = discord.Embed(title="YouTube - Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=Help.version1)
                    await ctx.send(embed=embed, delete_after=10)
                    return

        # Afficher un embed "Recherche en cours..."
        loading_embed = discord.Embed(title="YouTube - Recherche en cours", description=f"Recherche de **'{query}'** en cours...", color=discord.Color.yellow())
        loading_embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        loading_embed.set_footer(text=Help.version1)
        loading_msg = await ctx.send(embed=loading_embed)

        try:
            # Recherche initiale en mode flat (rapide, pas de blocage)
            with YoutubeDL(search_options) as ydl:
                info = ydl.extract_info(f'ytsearch10:{query}', download=False)
            
            # Supprimer l'embed "Recherche en cours..."
            await loading_msg.delete()
            
            if not info or 'entries' not in info:
                embed = discord.Embed(title="YouTube - Recherche", description="Aucun résultat trouvé pour cette recherche.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return
            
            videos = [v for v in info.get('entries', []) if v is not None]
            
            if not videos:
                embed = discord.Embed(title="YouTube - Recherche", description="Aucune vidéo valide trouvée pour cette recherche.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return

            # Afficher les résultats au format numéroté
            result_list = []
            valid_videos = []
            for video in videos:
                try:
                    if video and 'title' in video and 'id' in video:
                        result_list.append(f"**{len(valid_videos) + 1}.** {video['title']}")
                        valid_videos.append(video)
                except Exception:
                    continue

            if not valid_videos:
                embed = discord.Embed(title="YouTube - Recherche", description="Aucune vidéo valide trouvée pour cette recherche.", color=discord.Color.orange())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return

            # Afficher les résultats dans l'embed
            result_text = "\n".join(result_list)
            embed = discord.Embed(title="YouTube - Résultats de recherche", description=f"Résultats pour **'{query}'** :\n\n{result_text}", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=60)

            embed2 = discord.Embed(title="YouTube - Choix", description="Veuillez choisir le numéro du résultat à jouer.", color=discord.Color.blue())
            embed2.set_footer(text=Help.version1)
            await ctx.send(embed=embed2, delete_after=15)

            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit() and 1 <= int(message.content) <= len(valid_videos)

            response = await self.bot.wait_for('message', check=check, timeout=30)
            choice = int(response.content) - 1

            selected_video = valid_videos[choice]
            
            # Extraire l'URL audio de la vidéo sélectionnée (maintenant avec toutes les infos)
            loading_embed = discord.Embed(title="YouTube - Téléchargement", description="Téléchargement des informations de la vidéo...", color=discord.Color.yellow())
            loading_embed.set_footer(text=Help.version1)
            loading_msg = await ctx.send(embed=loading_embed)
            
            try:
                video_url = f"https://www.youtube.com/watch?v={selected_video.get('id', '')}"
                with YoutubeDL(play_options) as ydl:
                    video_info = ydl.extract_info(video_url, download=False)
                audio_url = video_info['url']
                video_title = video_info.get('title', selected_video.get('title', 'Titre inconnu'))
            except Exception as e:
                await loading_msg.delete()
                embed = discord.Embed(title="YouTube - Erreur", description=f"Erreur lors de l'extraction de l'URL audio : {str(e)}", color=discord.Color.red())
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
                return

            await loading_msg.delete()

            # Vérifier si c'est vraiment YouTube qui joue
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            
            if voice and voice.is_paused():
                # YT est en pause, ajouter à la file
                self.queue.append({'title': video_title, 'url': audio_url})
                embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{video_title}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
            elif voice and voice.is_playing() and len(self.queue) > 0:
                # YT joue et il y a déjà une queue YT, ajouter à la file
                self.queue.append({'title': video_title, 'url': audio_url})
                embed = discord.Embed(title="YouTube - File d'attente", description=f'La vidéo YouTube **"{video_title}"** a été ajoutée à la file d\'attente.', color=discord.Color.blue())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)
            else:
                # Soit rien ne joue, soit Soundboard/TTS joue (queue vide = pas YT)
                # Arrêter toute lecture en cours et jouer YT directement
                if voice and voice.is_playing():
                    voice.stop()
                    # Vider la queue YT si Soundboard/TTS jouait (pour éviter confusion)
                    self.queue.clear()
                    await asyncio.sleep(0.5)  # Attendre que la lecture s'arrête
                
                voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.check_queue(ctx))
                voice.is_playing()
                embed = discord.Embed(title="YouTube - Lecture", description=f'Le bot est en train de jouer : **"{video_title}"**', color=discord.Color.green())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=Help.version1)
                await ctx.send(embed=embed, delete_after=10)

        except asyncio.TimeoutError:
            try:
                await loading_msg.delete()
            except:
                pass
            embed = discord.Embed(title="YouTube - Expiration", description="La recherche a expiré. Veuillez relancer la commande si vous souhaitez rechercher à nouveau.", color=discord.Color.orange())
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)

        except Exception as e:
            try:
                await loading_msg.delete()
            except:
                pass
            embed = discord.Embed(title="YouTube - Erreur", description=f"Une erreur s'est produite lors de la recherche : {str(e)}", color=discord.Color.red())
            embed.set_footer(text=Help.version1)
            await ctx.send(embed=embed, delete_after=10)
            print(f"Erreur search: {e}")  # Pour debug

    @commands.command()
    async def loop(self, ctx):
        await ctx.message.delete()
        self.loop_state = not self.loop_state  # Inverser l'état de la boucle
        embed = discord.Embed(title="YouTube - Boucle", description=f"Boucle **{'activée' if self.loop_state else 'désactivée'}**.", color=discord.Color.green() if self.loop_state else discord.Color.red())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)

async def setup(bot):
    await bot.add_cog(Youtube(bot))