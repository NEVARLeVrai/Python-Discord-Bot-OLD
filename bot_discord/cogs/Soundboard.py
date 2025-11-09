import discord
from discord.ext import commands
import asyncio
import traceback
import os
from cogs import Help
from cogs.Help import get_current_version
import mutagen
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.oggopus import OggOpus
from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from mutagen.wave import WAVE
import random



class Soundboard(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.voice_client = None
        # Utiliser le chemin centralisé depuis main.py
        sounds_dir = client.paths['sounds_dir']
        self.sound_files = os.listdir(sounds_dir)
        # Support pour plusieurs formats audio
        audio_extensions = (".mp3", ".mp4", ".m4a", ".ogg", ".opus", ".wav", ".flac", ".aac")
        self.sound_files = [f for f in self.sound_files if f.lower().endswith(audio_extensions)]
        self.random_task = None
        # Utiliser le chemin centralisé depuis main.py
        self.ffmpeg_path = client.paths['ffmpeg_exe']
        self.sounds_dir = sounds_dir
    
    def get_audio_duration(self, file_path):
        """Obtient la durée d'un fichier audio en secondes, supporte plusieurs formats."""
        # Essayer d'abord avec mutagen.File() qui détecte automatiquement le format
        try:
            audio_file = mutagen.File(file_path)
            if audio_file is not None:
                return int(audio_file.info.length)
        except Exception:
            # Si mutagen.File() échoue, continuer avec les méthodes spécifiques
            pass
        
        # Si mutagen.File() retourne None ou échoue, essayer les formats spécifiques
        # Chaque format est essayé indépendamment avec sa propre gestion d'erreur
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in [".mp3"]:
            try:
                audio = MP3(file_path)
                return int(audio.info.length)
            except Exception:
                # Fichier MP3 invalide ou corrompu
                pass
        
        if file_ext in [".mp4", ".m4a"]:
            try:
                audio = MP4(file_path)
                return int(audio.info.length)
            except Exception:
                pass
        
        if file_ext == ".opus":
            try:
                audio = OggOpus(file_path)
                return int(audio.info.length)
            except Exception:
                pass
        
        if file_ext == ".ogg":
            # OGG peut être Vorbis ou Opus, essayer les deux
            try:
                audio = OggVorbis(file_path)
                return int(audio.info.length)
            except Exception:
                try:
                    audio = OggOpus(file_path)
                    return int(audio.info.length)
                except Exception:
                    pass
        
        if file_ext == ".flac":
            try:
                audio = FLAC(file_path)
                return int(audio.info.length)
            except Exception:
                pass
        
        if file_ext == ".wav":
            try:
                audio = WAVE(file_path)
                return int(audio.info.length)
            except Exception:
                pass
        
        # Si tout échoue, retourner None pour indiquer que la durée est inconnue
        return None    
    
        
    @commands.command()
    async def srandom(self, ctx):
        await ctx.message.delete()
        
        # S'assurer que le bot est connecté au canal vocal
        voice_client = await self.ensure_voice_connection(ctx)
        if not voice_client:
            return

        if self.random_task and not self.random_task.done():
            embed91 = discord.Embed(title= "SoundBoard Random Erreur", description=f"La lecture aléatoire est déjà en cours.", color=discord.Color.yellow())
            embed91.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed91.set_footer(text=get_current_version(self.client))
            return await ctx.send(embed = embed91, delete_after=5)

        self.random_task = asyncio.create_task(self.play_random_sound(ctx.channel.id))
        embed20 = discord.Embed(title= "SoundBoard Random", description=f"Lecture aléatoire.", color=discord.Color.green())
        embed20.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed20.set_footer(text=get_current_version(self.client))
        await ctx.send(embed = embed20, delete_after=5)
        
    @commands.command()
    async def srandomskip(self, ctx):
        await ctx.message.delete()
        # Récupérer la connexion vocale depuis le bot
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            embed98 = discord.Embed(title="SoundBoard Random Skip", description="Le son en cours de lecture a été skip.", color=discord.Color.green())
            embed98.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed98.set_footer(text=get_current_version(self.client))
            print("le son de la lecture aléatoire à été skip")
            await ctx.send(embed=embed98, delete_after=5)
        else:
            embed89 = discord.Embed(title="SoundBoard Random Skip Erreur", description="Aucun son n'est en cours de lecture.", color=discord.Color.yellow())
            embed89.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed89.set_footer(text=get_current_version(self.client))
            print("Aucun son n'est en cours dans la lecture aléatoire")
            await ctx.send(embed=embed89, delete_after=5)

    async def play_random_sound(self, channel_id):
        while True:
            # Vérifier la connexion via le bot plutôt que self.voice_client
            voice_client = None
            if self.voice_client and self.voice_client.is_connected():
                voice_client = self.voice_client
            else:
                # Essayer de récupérer la connexion depuis le bot
                channel = self.client.get_channel(channel_id)
                if channel:
                    voice_client = discord.utils.get(self.client.voice_clients, guild=channel.guild)
            
            if voice_client and voice_client.is_connected():
                if not voice_client.is_playing():
                    if self.random_task and not self.random_task.done():
                        wait_time = random.randint(1, 5) * 60  # choisir un temps aléatoire entre 1 et 5 minutes
                        print(f"Attente de {wait_time // 60} minutes")
                        await asyncio.sleep(wait_time)
                        sound_num = random.randint(1, len(self.sound_files))
                        sound_name = self.sound_files[sound_num-1]
                        file_path = f"{self.sounds_dir}/{sound_name}"
                        if os.path.isfile(file_path):
                            source = discord.FFmpegPCMAudio(file_path, executable=self.ffmpeg_path)
                            voice_client.play(source)
                            embed90 = discord.Embed(title= "SoundBoard Random", description=f"Joue {sound_name}", color=discord.Color.green())
                            embed90.set_footer(text=get_current_version(self.client))
                            print(f"Joue {sound_name}")
                            await self.client.get_channel(channel_id).send(embed=embed90, delete_after=15)
                            print("En attente de la fin de l'audio en cours de lecture")
                    else:
                        embed45 = discord.Embed(title= "SoundBoard Random", description=f"Arrêt de la lecture aléatoire.", color=discord.Color.red())
                        embed45.set_footer(text=get_current_version(self.client))
                        print("Arrêt de la lecture aléatoire")
                        await self.client.get_channel(channel_id).send(embed=embed45, delete_after=5)
                        break
            else:
                # Plus connecté, arrêter la tâche
                embed45 = discord.Embed(title= "SoundBoard Random", description=f"Arrêt de la lecture aléatoire (déconnexion).", color=discord.Color.red())
                embed45.set_footer(text=get_current_version(self.client))
                print("Arrêt de la lecture aléatoire - déconnexion")
                try:
                    await self.client.get_channel(channel_id).send(embed=embed45, delete_after=5)
                except:
                    pass
                break
            await asyncio.sleep(1)
            
    @commands.command()
    async def srandomstop(self, ctx):
        await ctx.message.delete()
        if self.random_task and not self.random_task.done():
            self.random_task.cancel()
            embed = discord.Embed(title="SoundBoard Random Stop", description="Arrêt de la lecture aléatoire réussi", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            print("Lecture aléatoire arreté")
            await ctx.send(embed=embed, delete_after=5)
        else:
            embed = discord.Embed(title="SoundBoard Random Stop Erreur", description="La lecture aléatoire n'est pas en cours.", color=discord.Color.yellow())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            print("Lecture aléatoire erreur pas en cours")
            await ctx.send(embed=embed, delete_after=5)    
    
    async def ensure_voice_connection(self, ctx, stop_current=False):
        """Vérifie et établit une connexion au canal vocal de l'utilisateur."""
        if not ctx.author.voice:
            embed = discord.Embed(title= "SoundBoard Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=5)
            return None
        
        channel = ctx.author.voice.channel
        
        # Vérifier si le bot est déjà connecté dans ce serveur
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        
        if voice_client:
            # Si une lecture est en cours et qu'on veut l'arrêter (pour Soundboard)
            if voice_client.is_playing() and stop_current:
                # Arrêter la lecture en cours
                voice_client.stop()
                # Si YouTube jouait, vider sa queue pour éviter confusion
                youtube_cog = ctx.bot.get_cog('Youtube')
                if youtube_cog and hasattr(youtube_cog, 'queue'):
                    youtube_cog.queue.clear()
                await asyncio.sleep(0.5)  # Attendre que la lecture s'arrête
            
            # Si une lecture est en cours et qu'on ne veut pas l'arrêter, vérifier
            elif voice_client.is_playing() and not stop_current:
                # Vérifier si c'est dans le même canal
                if voice_client.channel == channel:
                    # Même canal mais déjà en lecture, on arrête pour laisser la place
                    voice_client.stop()
                    # Vider la queue YT si nécessaire
                    youtube_cog = ctx.bot.get_cog('Youtube')
                    if youtube_cog and hasattr(youtube_cog, 'queue'):
                        youtube_cog.queue.clear()
                else:
                    # Canal différent, arrêter et déplacer
                    voice_client.stop()
                    # Vider la queue YT si nécessaire
                    youtube_cog = ctx.bot.get_cog('Youtube')
                    if youtube_cog and hasattr(youtube_cog, 'queue'):
                        youtube_cog.queue.clear()
            
            # Si déjà connecté au même canal, utiliser cette connexion
            if voice_client.channel == channel:
                self.voice_client = voice_client
                return voice_client
            # Si connecté à un autre canal, déplacer vers le nouveau canal
            else:
                try:
                    await voice_client.move_to(channel)
                    self.voice_client = voice_client
                    return voice_client
                except discord.errors.ClientException as e:
                    # Erreur de connexion Discord (déjà connecté ailleurs, etc.)
                    embed = discord.Embed(title= "SoundBoard Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await ctx.send(embed=embed, delete_after=5)
                    return None
                except Exception as e:
                    embed = discord.Embed(title= "SoundBoard Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await ctx.send(embed=embed, delete_after=5)
                    return None
        else:
            # Pas encore connecté, se connecter
            try:
                self.voice_client = await channel.connect()
                return self.voice_client
            except discord.errors.ClientException as e:
                # Erreur de connexion Discord
                embed = discord.Embed(title= "SoundBoard Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await ctx.send(embed=embed, delete_after=5)
                return None
            except Exception as e:
                embed = discord.Embed(title= "SoundBoard Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await ctx.send(embed=embed, delete_after=5)
                return None
 
    @commands.command()
    async def slist(self, ctx):
        await ctx.message.delete()
        # Support pour plusieurs formats audio
        audio_extensions = (".mp3", ".mp4", ".m4a", ".ogg", ".opus", ".wav", ".flac", ".aac")
        sound_files = [f for f in os.listdir(self.sounds_dir) if f.lower().endswith(audio_extensions)]
        
        if not sound_files:
            embed54 = discord.Embed(title= "SoundBoard List", description="Aucun fichier dans le dossier **Sounds**", color=discord.Color.random())
            embed54.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed54.set_footer(text=get_current_version(self.client))
            await ctx.send(embed = embed54, delete_after=10)
            return

        file_list = ""
        for i, file in enumerate(sound_files):
            file_path = f"{self.sounds_dir}/{file}"
            file_name = os.path.splitext(file)[0]
            
            # Obtenir la durée du fichier audio
            duration = self.get_audio_duration(file_path)
            
            # Formater la durée
            if duration is not None:
                duration_str = ""
                if duration >= 3600:
                    hours = duration // 3600
                    duration_str += f"{hours}h "
                    duration %= 3600
                if duration >= 60:
                    minutes = duration // 60
                    duration_str += f"{minutes}m "
                    duration %= 60
                duration_str += f"{duration}s"
            else:
                duration_str = "N/A"
            
            file_list += f"{i+1}. ({duration_str}) {file_name}\n"
        embed13 = discord.Embed(title= "SoundBoard List", description=f"Liste des fichiers audio disponibles :```\n{file_list}\n```", color=discord.Color.random())
        embed13.add_field(name=" ", value=" ", inline=True)
        embed13.add_field(name="Commande", value="Exemple =splay 4", inline=True)
        embed13.add_field(name=" ", value=" ", inline=True)
        embed13.add_field(name="Le nombre", value="1", inline=True)
        embed13.add_field(name="Le temps", value="hh:mm:ss", inline=True)
        embed13.add_field(name="Le nom", value="Test", inline=True)
        embed13.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed13.set_footer(text=get_current_version(self.client))
        await ctx.send(embed = embed13)
        
    @commands.command()
    async def splay(self, ctx, sound_num: int=None):
        await ctx.message.delete()
        """Commande pour jouer un son enregistré."""
        
        # S'assurer que le bot est connecté au canal vocal (arrêter toute lecture en cours)
        voice_client = await self.ensure_voice_connection(ctx, stop_current=True)
        if not voice_client:
            return

        # Vérifier une dernière fois après la connexion
        if voice_client.is_playing():
            voice_client.stop()
            # Attendre un peu pour que la lecture s'arrête proprement
            await asyncio.sleep(0.5)

        # Obtenir le nom du fichier audio correspondant au numéro donné
        # Support pour plusieurs formats audio
        audio_extensions = (".mp3", ".mp4", ".m4a", ".ogg", ".opus", ".wav", ".flac", ".aac")
        sound_files = [f for f in os.listdir(self.sounds_dir) if f.lower().endswith(audio_extensions)]
        if sound_num is None:
            file_path2 = f"{self.sounds_dir}/blepair.mp3"
            embed16 = discord.Embed(title= "SoundBoard Play", description=f"Pour jouer un son, utilisez la commande avec un numéro de son valide. Exemple : `=splay 1`", color=discord.Color.blue())
            embed16.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed16.set_footer(text=get_current_version(self.client))
            source = discord.FFmpegPCMAudio(file_path2, executable=self.ffmpeg_path)
            voice_client.play(source)
            return await ctx.send(embed = embed16, delete_after=5)

        if sound_num <= 0 or sound_num > len(sound_files):
            embed5 = discord.Embed(title= "SoundBoard Play Erreur", description="Numéro audio invalide.", color=discord.Color.red())
            embed5.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed5.set_footer(text=get_current_version(self.client))
            return await ctx.send(embed = embed5, delete_after=5)

        sound_name = sound_files[sound_num-1 if sound_num > 0 else 0]

        # Vérifiez que le fichier audio existe
        file_path = f"{self.sounds_dir}/{sound_name}"  # chemin vers le fichier audio
        if not os.path.isfile(file_path):
            return await ctx.send(f"Le fichier audio {sound_name} n'existe pas.")

        # Joue le fichier audio
        embed9 = discord.Embed(title= "SoundBoard Play", description=f"Joue {sound_name}", color=discord.Color.green())
        embed9.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed9.set_footer(text=get_current_version(self.client))
        await ctx.send(embed = embed9, delete_after=10)
        source = discord.FFmpegPCMAudio(file_path, executable=self.ffmpeg_path)
        voice_client.play(source)
    
        # Exécuter la suite si le fichier "Outro.mp3" a été joué
        if sound_name == "Outro.mp3":
            print("Outro détecté")
            await asyncio.sleep(58)
            print("58 secondes écoulées")

            # déconnecte les utilisateurs de la vocale
            if voice_client and voice_client.channel:
                for member in voice_client.channel.members:
                    if not member.bot:
                        try:
                            await member.move_to(None)
                        except Exception as e:
                            print(f"Erreur lors de l'expulsion de {member.name}: {e}")
                    
            
            embed6 = discord.Embed(title= "SoundBoard Play Outro", description="Expulsion des utilisateurs du salon vocal.", color=discord.Color.yellow())
            embed6.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed6.set_footer(text=get_current_version(self.client))
            await ctx.channel.send(embed = embed6, delete_after=5)

    @commands.command()
    async def sstop(self, ctx):
        await ctx.message.delete()
        """Commande pour arrêter la lecture en cours."""
        # Récupérer la connexion vocale depuis le bot
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            embed15 = discord.Embed(title= "SoundBoard Stop", description="Arrêt de la lecture réussi", color=discord.Color.red())
            embed15.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed15.set_footer(text=get_current_version(self.client))
            await ctx.send(embed = embed15, delete_after=5)
        else:
            embed8 = discord.Embed(title= "SoundBoard Stop Erreur", description="Je ne suis pas en train de jouer de la musique.", color=discord.Color.yellow())
            embed8.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed8.set_footer(text=get_current_version(self.client))
            await ctx.send(embed = embed8, delete_after=5)
    
    @commands.command()
    async def sleave(self, ctx):
        await ctx.message.delete()
        """Commande pour déconnecter le bot du salon vocal actuel."""
        # Récupérer la connexion vocale depuis le bot
        voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
        if not voice_client or not voice_client.is_connected():
            print("Je ne suis pas connecté")
            embed10 = discord.Embed(title= "SoundBoard Leave Erreur", description="Je ne suis pas connecté à un salon vocal.", color=discord.Color.yellow())
            embed10.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed10.set_footer(text=get_current_version(self.client))
            return await ctx.send(embed = embed10, delete_after=5)
            
        await voice_client.disconnect()
        self.voice_client = None
        embed12 = discord.Embed(title= "SoundBoard Leave", description="Déconnexion du salon vocal réussi", color=discord.Color.green())
        embed12.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed12.set_footer(text=get_current_version(self.client))
        await ctx.send(embed = embed12, delete_after=5)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def vkick(self, ctx, member: discord.Member = None):
        await ctx.message.delete()

        if member is not None:
            if not member.bot and member.voice is not None:
                await member.move_to(None)
                embed42 = discord.Embed(title= "Vocal Kick", description=f"**{member.name}#{member.discriminator}** a été expulsé du salon vocal", color=discord.Color.green())
                embed42.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed42.set_footer(text=get_current_version(self.client))
                await ctx.send(embed = embed42, delete_after=5)
            else:
                await ctx.send("")
                embed46 = discord.Embed(title= "Vocal Kick Erreur", description="L'utilisateur spécifié ne peut pas être expulsé.", color=discord.Color.red())
                embed46.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed46.set_footer(text=get_current_version(self.client))
                await ctx.send(embed = embed46, delete_after=5)
        else:
            # Récupérer la connexion vocale depuis le bot
            voice_client = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            if voice_client and voice_client.channel:
                for member in voice_client.channel.members:
                    if not member.bot:
                        try:
                            await member.move_to(None)
                        except Exception as e:
                            print(f"Erreur lors de l'expulsion de {member.name}: {e}")

            embed47 = discord.Embed(title= "Vocal Kick", description="Tous les utilisateurs ont été expulsés du salon vocal", color=discord.Color.green())
            embed47.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed47.set_footer(text=get_current_version(self.client))
            await ctx.send(embed = embed47, delete_after=5)            




async def setup(client):
    await client.add_cog(Soundboard(client))