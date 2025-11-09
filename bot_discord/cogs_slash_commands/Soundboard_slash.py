import discord
from discord import app_commands
from discord.ext import commands
import asyncio
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

class Soundboard_slash(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.voice_client = None
        sounds_dir = client.paths['sounds_dir']
        self.sound_files = os.listdir(sounds_dir)
        audio_extensions = (".mp3", ".mp4", ".m4a", ".ogg", ".opus", ".wav", ".flac", ".aac")
        self.sound_files = [f for f in self.sound_files if f.lower().endswith(audio_extensions)]
        self.random_task = None
        self.ffmpeg_path = client.paths['ffmpeg_exe']
        self.sounds_dir = sounds_dir
        # Récupérer le cog Soundboard original pour réutiliser ses méthodes
        self.soundboard_cog = None
    
    async def cog_load(self):
        # Récupérer le cog Soundboard original
        self.soundboard_cog = self.client.get_cog('Soundboard')
    
    def get_audio_duration(self, file_path):
        """Obtient la durée d'un fichier audio en secondes, supporte plusieurs formats."""
        try:
            audio_file = mutagen.File(file_path)
            if audio_file is not None:
                return int(audio_file.info.length)
        except Exception:
            pass
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in [".mp3"]:
            try:
                audio = MP3(file_path)
                return int(audio.info.length)
            except Exception:
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
        
        return None

    async def ensure_voice_connection(self, interaction, stop_current=False, already_deferred=False):
        """Vérifie et établit une connexion au canal vocal de l'utilisateur."""
        if not interaction.user.voice:
            embed = discord.Embed(title="SoundBoard Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            # Si déjà deferred, utiliser followup, sinon response
            if already_deferred:
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
        
        channel = interaction.user.voice.channel
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        
        if voice_client:
            if voice_client.is_playing() and stop_current:
                voice_client.stop()
                youtube_cog = self.client.get_cog('Youtube')
                if youtube_cog and hasattr(youtube_cog, 'queue'):
                    youtube_cog.queue.clear()
                await asyncio.sleep(0.5)
            elif voice_client.is_playing() and not stop_current:
                if voice_client.channel == channel:
                    voice_client.stop()
                    youtube_cog = self.client.get_cog('Youtube')
                    if youtube_cog and hasattr(youtube_cog, 'queue'):
                        youtube_cog.queue.clear()
                else:
                    voice_client.stop()
                    youtube_cog = self.client.get_cog('Youtube')
                    if youtube_cog and hasattr(youtube_cog, 'queue'):
                        youtube_cog.queue.clear()
            
            if voice_client.channel == channel:
                self.voice_client = voice_client
                return voice_client
            else:
                try:
                    await voice_client.move_to(channel)
                    self.voice_client = voice_client
                    return voice_client
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="SoundBoard Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    if already_deferred:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    return None
                except Exception as e:
                    embed = discord.Embed(title="SoundBoard Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    if already_deferred:
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    return None
        else:
            try:
                self.voice_client = await channel.connect()
                return self.voice_client
            except discord.errors.ClientException as e:
                embed = discord.Embed(title="SoundBoard Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                if already_deferred:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return None
            except Exception as e:
                embed = discord.Embed(title="SoundBoard Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                if already_deferred:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return None

    @app_commands.command(name="slist", description="Liste tous les sons disponibles avec leur durée")
    async def slist(self, interaction: discord.Interaction):
        """Liste tous les sons disponibles"""
        await interaction.response.defer(ephemeral=False)
        
        audio_extensions = (".mp3", ".mp4", ".m4a", ".ogg", ".opus", ".wav", ".flac", ".aac")
        sound_files = [f for f in os.listdir(self.sounds_dir) if f.lower().endswith(audio_extensions)]
        
        if not sound_files:
            embed54 = discord.Embed(title="SoundBoard List", description="Aucun fichier dans le dossier **Sounds**", color=discord.Color.random())
            embed54.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed54.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed54, ephemeral=False)
            return

        file_list = ""
        for i, file in enumerate(sound_files):
            file_path = f"{self.sounds_dir}/{file}"
            file_name = os.path.splitext(file)[0]
            duration = self.get_audio_duration(file_path)
            
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
        
        embed13 = discord.Embed(title="SoundBoard List", description=f"Liste des fichiers audio disponibles :```\n{file_list}\n```", color=discord.Color.random())
        embed13.add_field(name=" ", value=" ", inline=True)
        embed13.add_field(name="Commande", value="Exemple /splay sound_num:4", inline=True)
        embed13.add_field(name=" ", value=" ", inline=True)
        embed13.add_field(name="Le nombre", value="1", inline=True)
        embed13.add_field(name="Le temps", value="hh:mm:ss", inline=True)
        embed13.add_field(name="Le nom", value="Test", inline=True)
        embed13.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed13.set_footer(text=get_current_version(self.client))
        await interaction.followup.send(embed=embed13, ephemeral=False)

    @app_commands.command(name="splay", description="Joue un son du soundboard")
    @app_commands.describe(sound_num="Numéro du son à jouer (voir /slist)")
    async def splay(self, interaction: discord.Interaction, sound_num: int):
        """Joue un son du soundboard"""
        await interaction.response.defer(ephemeral=False)
        
        voice_client = await self.ensure_voice_connection(interaction, stop_current=True, already_deferred=True)
        if not voice_client:
            return

        if voice_client.is_playing():
            voice_client.stop()
            await asyncio.sleep(0.5)

        audio_extensions = (".mp3", ".mp4", ".m4a", ".ogg", ".opus", ".wav", ".flac", ".aac")
        sound_files = [f for f in os.listdir(self.sounds_dir) if f.lower().endswith(audio_extensions)]

        if sound_num <= 0 or sound_num > len(sound_files):
            embed5 = discord.Embed(title="SoundBoard Play Erreur", description="Numéro audio invalide.", color=discord.Color.red())
            embed5.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed5.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed5, ephemeral=True)
            return

        sound_name = sound_files[sound_num-1]
        file_path = f"{self.sounds_dir}/{sound_name}"
        
        if not os.path.isfile(file_path):
            await interaction.followup.send(f"Le fichier audio {sound_name} n'existe pas.", ephemeral=True)
            return

        embed9 = discord.Embed(title="SoundBoard Play", description=f"Joue {sound_name}", color=discord.Color.green())
        embed9.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed9.set_footer(text=get_current_version(self.client))
        await interaction.followup.send(embed=embed9, ephemeral=False)
        source = discord.FFmpegPCMAudio(file_path, executable=self.ffmpeg_path)
        voice_client.play(source)
        
        if sound_name == "Outro.mp3":
            print("Outro détecté")
            await asyncio.sleep(58)
            print("58 secondes écoulées")
            
            if voice_client and voice_client.channel:
                for member in voice_client.channel.members:
                    if not member.bot:
                        try:
                            await member.move_to(None)
                        except Exception as e:
                            print(f"Erreur lors de l'expulsion de {member.name}: {e}")
            
            embed6 = discord.Embed(title="SoundBoard Play Outro", description="Expulsion des utilisateurs du salon vocal.", color=discord.Color.yellow())
            embed6.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed6.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed6, ephemeral=False)

    @app_commands.command(name="sstop", description="Arrête le son en cours")
    async def sstop(self, interaction: discord.Interaction):
        """Arrête le son en cours"""
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            embed15 = discord.Embed(title="SoundBoard Stop", description="Arrêt de la lecture réussi", color=discord.Color.red())
            embed15.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed15.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed15, ephemeral=False)
        else:
            embed8 = discord.Embed(title="SoundBoard Stop Erreur", description="Je ne suis pas en train de jouer de la musique.", color=discord.Color.yellow())
            embed8.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed8.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed8, ephemeral=True)

    @app_commands.command(name="sleave", description="Fait quitter le bot du salon vocal")
    async def sleave(self, interaction: discord.Interaction):
        """Déconnecte le bot du salon vocal"""
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if not voice_client or not voice_client.is_connected():
            embed10 = discord.Embed(title="SoundBoard Leave Erreur", description="Je ne suis pas connecté à un salon vocal.", color=discord.Color.yellow())
            embed10.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed10.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed10, ephemeral=True)
            return
        
        await voice_client.disconnect()
        self.voice_client = None
        embed12 = discord.Embed(title="SoundBoard Leave", description="Déconnexion du salon vocal réussi", color=discord.Color.green())
        embed12.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed12.set_footer(text=get_current_version(self.client))
        await interaction.response.send_message(embed=embed12, ephemeral=False)

    @app_commands.command(name="srandom", description="Joue des sons aléatoires toutes les 1-5 minutes")
    async def srandom(self, interaction: discord.Interaction):
        """Démarre la lecture aléatoire"""
        await interaction.response.defer(ephemeral=False)
        
        voice_client = await self.ensure_voice_connection(interaction, already_deferred=True)
        if not voice_client:
            return

        # Utiliser le cog Soundboard original pour réutiliser la logique
        soundboard_cog = self.client.get_cog('Soundboard')
        if soundboard_cog:
            if soundboard_cog.random_task and not soundboard_cog.random_task.done():
                embed91 = discord.Embed(title="SoundBoard Random Erreur", description=f"La lecture aléatoire est déjà en cours.", color=discord.Color.yellow())
                embed91.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed91.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed91, ephemeral=True)
                return

            # Utiliser directement play_random_sound avec le channel_id
            soundboard_cog.random_task = asyncio.create_task(soundboard_cog.play_random_sound(interaction.channel.id))
            embed20 = discord.Embed(title="SoundBoard Random", description=f"Lecture aléatoire.", color=discord.Color.green())
            embed20.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed20.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed20, ephemeral=False)

    @app_commands.command(name="srandomstop", description="Arrête la lecture aléatoire")
    async def srandomstop(self, interaction: discord.Interaction):
        """Arrête la lecture aléatoire"""
        soundboard_cog = self.client.get_cog('Soundboard')
        if soundboard_cog and soundboard_cog.random_task and not soundboard_cog.random_task.done():
            soundboard_cog.random_task.cancel()
            embed = discord.Embed(title="SoundBoard Random Stop", description="Arrêt de la lecture aléatoire réussi", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="SoundBoard Random Stop Erreur", description="La lecture aléatoire n'est pas en cours.", color=discord.Color.yellow())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="srandomskip", description="Skip le son aléatoire en cours")
    async def srandomskip(self, interaction: discord.Interaction):
        """Skip le son aléatoire en cours"""
        voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            embed98 = discord.Embed(title="SoundBoard Random Skip", description="Le son en cours de lecture a été skip.", color=discord.Color.green())
            embed98.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed98.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed98, ephemeral=False)
        else:
            embed89 = discord.Embed(title="SoundBoard Random Skip Erreur", description="Aucun son n'est en cours de lecture.", color=discord.Color.yellow())
            embed89.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed89.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed89, ephemeral=True)

    @app_commands.command(name="vkick", description="Expulse un utilisateur du vocal")
    @app_commands.describe(member="L'utilisateur à expulser (optionnel, sinon tous)")
    @app_commands.default_permissions(administrator=True)
    async def vkick(self, interaction: discord.Interaction, member: discord.Member = None):
        """Expulse un utilisateur du vocal"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Cette commande nécessite les permissions administrateur.", ephemeral=True)
            return
        
        if member is not None:
            if not member.bot and member.voice is not None:
                await member.move_to(None)
                embed42 = discord.Embed(title="Vocal Kick", description=f"**{member.name}#{member.discriminator}** a été expulsé du salon vocal", color=discord.Color.green())
                embed42.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed42.set_footer(text=get_current_version(self.client))
                await interaction.response.send_message(embed=embed42, ephemeral=False)
            else:
                embed46 = discord.Embed(title="Vocal Kick Erreur", description="L'utilisateur spécifié ne peut pas être expulsé.", color=discord.Color.red())
                embed46.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed46.set_footer(text=get_current_version(self.client))
                await interaction.response.send_message(embed=embed46, ephemeral=True)
        else:
            voice_client = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            if voice_client and voice_client.channel:
                for member in voice_client.channel.members:
                    if not member.bot:
                        try:
                            await member.move_to(None)
                        except Exception as e:
                            print(f"Erreur lors de l'expulsion de {member.name}: {e}")

            embed47 = discord.Embed(title="Vocal Kick", description="Tous les utilisateurs ont été expulsés du salon vocal", color=discord.Color.green())
            embed47.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed47.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed47, ephemeral=False)


async def setup(client):
    await client.add_cog(Soundboard_slash(client))

