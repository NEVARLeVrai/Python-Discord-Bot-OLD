import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import asyncio

class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pause_state = False
        self.queue = []
        self.loop_state = False  # Variable pour suivre l'état de la boucle
        self.ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
            'executable': r'C:/Users/Danie/Mon Drive/Bot Python Discord/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe'
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print("Youtube.py is ready")
        
    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send('Déconnecté du salon vocale')

    @commands.command()
    async def play(self, ctx, url):
        print("Début de la commande !play")  # DEBUG
        ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        print(f"voice avant connexion: {voice}")  # DEBUG

        if not voice or not voice.is_connected():
            channel = ctx.author.voice.channel
            print(f"Connexion au salon vocal: {channel}")  # DEBUG
            await channel.connect()

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        print(f"voice après connexion: {voice}")  # DEBUG

        with YoutubeDL(ydl_options) as ydl:
            print(f"Extraction info pour l'URL: {url}")  # DEBUG
            info = ydl.extract_info(url, download=False)
        audio_url = info['url']
        print(f"audio_url: {audio_url}")  # DEBUG

        if voice and (voice.is_playing() or voice.is_paused()):
            print("Ajout à la file d'attente")  # DEBUG
            self.queue.append({'title': info['title'], 'url': audio_url})
            await ctx.send(f'La vidéo YouTube "{info["title"]}" a été ajoutée à la file d\'attente.')
        else:
            print("Lecture de la vidéo")  # DEBUG
            voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.check_queue(ctx))
            voice.is_playing()
            await ctx.send(f'Le bot est en train de jouer : {info["title"]}')

    def check_queue(self, ctx):
        async def inner_check_queue():
            if len(self.queue) > 0:
                next_video = self.queue.pop(0)
                voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                voice.play(discord.FFmpegPCMAudio(next_video['url'], **self.ffmpeg_options), after=lambda e: self.check_queue(ctx))
                voice.is_playing()
                asyncio.create_task(self.check_empty_channel(ctx))
                await ctx.send(f'Vidéo YouTube suivante dans la file d\'attente : {next_video["title"]}')

        self.bot.loop.create_task(inner_check_queue())

    async def check_empty_channel(self, ctx):
        await asyncio.sleep(120)
        voice_channel = ctx.voice_client.channel
        if len(voice_channel.members) == 1:
            await ctx.voice_client.disconnect()
            await ctx.send("Aucun utilisateur détecté pendant 2 minutes. Je quitte le canal vocal.")

    @commands.command()
    async def skip(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            next_video = self.queue[0] if self.queue else None
            voice_client.stop()
            if next_video:
                await ctx.send(f"Vidéo YouTube suivante dans la file d'attente : {next_video['title']}")
            else:
                await ctx.send("Aucune vidéo YouTube suivante dans la file d'attente.")

    @commands.command()
    async def stopm(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.send('Lecture terminé')

    @commands.command()
    async def pause(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_playing() and not self.pause_state:
            voice_client.pause()
            self.pause_state = True
            await ctx.send("La vidéo YouTube est en pause.")

    @commands.command()
    async def resume(self, ctx):
        voice_client = ctx.voice_client
        if voice_client.is_paused() and self.pause_state:
            voice_client.resume()
            self.pause_state = False
            await ctx.send("La vidéo YouTube a repris.")

    @commands.command()
    async def queue(self, ctx):
        if not self.queue:
            await ctx.send("La file d'attente de vidéos YouTube est vide.")
        else:
            queue_list = "\n".join([f"{index + 1}. {video['title']}" for index, video in enumerate(self.queue)])
            await ctx.send(f"File d'attente de vidéos YouTube :\n{queue_list}")

    @commands.command()
    async def clearq(self, ctx):
        self.queue.clear()
        await ctx.send("La file d'attente de vidéos YouTube a été effacée.")

    @commands.command()
    async def search(self, ctx, *query):
        query = " ".join(query)
        ydl_options = {'format': 'bestaudio'}

        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

        # Vérifier si le bot n'est pas dans un canal vocal
        if not voice or not voice.is_connected():
            channel = ctx.author.voice.channel
            await channel.connect()

        with YoutubeDL(ydl_options) as ydl:
            try:
                # Effectuer la recherche YouTube
                info = ydl.extract_info(f'ytsearch10:{query}', download=False)
                videos = info['entries']

                # Afficher les résultats au format numéroté
                result_list = []
                for index, video in enumerate(videos):
                    if 'playlist' in info and index == 0:
                        # Si le premier résultat est une playlist, afficher le titre de la playlist avec le nombre de vidéos
                        playlist_title = video['title']
                        result_list.append(f"``{index + 1}. {playlist_title} (playlist de {len(videos)} vidéos)``")
                    else:
                        # Si ce n'est pas une playlist, afficher le titre de la vidéo
                        result_list.append(f"``{index + 1}. {video['title']} ({video.get('duration', 'durée inconnue')})``")

                # Afficher les résultats dans le message
                result_message = await ctx.send(f"Résultats de la recherche pour '{query}':\n" + "\n".join(result_list))

                if 'playlist' in info:
                    playlist_titles = "\n".join([f"``{index + 1}. {video['title']} ({video.get('duration', 'durée inconnue')})``" for index, video in enumerate(videos)])
                    await ctx.send(f"Sous-résultats de la playlist '{playlist_title}':\n{playlist_titles}")

                    def check_playlist(message):
                        return message.author == ctx.author and message.content.lower() in ['all', '1']

                    await ctx.send("Voulez-vous jouer toute la playlist ou choisir une vidéo spécifique? Répondez avec 'all' ou '1'.")
                    response_playlist = await self.bot.wait_for('message', check=check_playlist, timeout=30)

                    if response_playlist.content.lower() == 'all':
                        for video in videos:
                            audio_url = video['url']
                            self.queue.append({'title': video['title'], 'url': audio_url})
                        await ctx.send(f'Toute la playlist "{playlist_title}" a été ajoutée à la file d\'attente.')

                else:
                    await ctx.send("Veuillez choisir le numéro du résultat à jouer.")

                def check(message):
                    return message.author == ctx.author and message.content.isdigit() and 1 <= int(message.content) <= len(videos)

                response = await self.bot.wait_for('message', check=check, timeout=30)
                choice = int(response.content) - 1

                audio_url = videos[choice]['url']

                # Vérifier si le bot n'est pas en train de jouer ou en pause
                if voice and (voice.is_playing() or voice.is_paused()):
                    self.queue.append({'title': videos[choice]['title'], 'url': audio_url})
                    await ctx.send(f'La vidéo YouTube "{videos[choice]["title"]}" a été ajoutée à la file d\'attente.')
                else:
                    voice.play(discord.FFmpegPCMAudio(audio_url, **self.ffmpeg_options), after=lambda e: self.check_queue(ctx))
                    voice.is_playing()
                    await ctx.send(f'Le bot est en train de jouer : "{videos[choice]["title"]}"')

            except asyncio.TimeoutError:
                await ctx.send("La recherche a expiré. Veuillez relancer la commande si vous souhaitez rechercher à nouveau.")

            except Exception as e:
                await ctx.send(f"Une erreur s'est produite lors de la recherche : {e}")

    @commands.command()
    async def loop(self, ctx):
        self.loop_state = not self.loop_state  # Inverser l'état de la boucle
        await ctx.send(f"Boucle {'activée' if self.loop_state else 'désactivée'}.")

async def setup(bot):
    await bot.add_cog(Youtube(bot))