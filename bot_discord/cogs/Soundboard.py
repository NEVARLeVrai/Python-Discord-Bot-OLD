import discord
from discord.ext import commands
import asyncio
import traceback
import os
from cogs import Help
import mutagen
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
import random



class Soundboard(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.voice_client = None
        # Utiliser le chemin centralisé depuis main.py
        sounds_dir = client.paths['sounds_dir']
        self.sound_files = os.listdir(sounds_dir)
        self.sound_files = [f for f in self.sound_files if f.endswith(".mp3")]
        self.random_task = None
        # Utiliser le chemin centralisé depuis main.py
        self.ffmpeg_path = client.paths['ffmpeg_exe']
        self.sounds_dir = sounds_dir    
    
        
    @commands.command()
    async def srandom(self, ctx):
        await ctx.message.delete()
        if not ctx.author.voice:
            embed16 = discord.Embed(title= "SoundBoard Random Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed16.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed16.set_footer(text=Help.version1)
            return await ctx.send(embed = embed16, delete_after=5)

        if not self.voice_client or not self.voice_client.is_connected():
            embed42 = discord.Embed(title= "SoundBoard Random Erreur", description="Je ne suis pas connecté à un salon vocal.", color=discord.Color.yellow())
            embed42.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed42.set_footer(text=Help.version1)
            return await ctx.send(embed = embed42, delete_after=5)

        if self.random_task and not self.random_task.done():
            embed91 = discord.Embed(title= "SoundBoard Random Erreur", description=f"La lecture aléatoire est déjà en cours.", color=discord.Color.yellow())
            embed91.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed91.set_footer(text=Help.version1)
            return await ctx.send(embed = embed91, delete_after=5)

        self.random_task = asyncio.create_task(self.play_random_sound(ctx.channel.id))
        embed20 = discord.Embed(title= "SoundBoard Random", description=f"Lecture aléatoire.", color=discord.Color.green())
        embed20.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed20.set_footer(text=Help.version1)
        await ctx.send(embed = embed20, delete_after=5)
        
    @commands.command()
    async def srandomskip(self, ctx):
        await ctx.message.delete()
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            embed98 = discord.Embed(title="SoundBoard Random Skip", description="Le son en cours de lecture a été skip.", color=discord.Color.green())
            embed98.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed98.set_footer(text=Help.version1)
            print("le son de la lecture aléatoire à été skip")
            await ctx.send(embed=embed98, delete_after=5)
        else:
            embed89 = discord.Embed(title="SoundBoard Random Skip Erreur", description="Aucun son n'est en cours de lecture.", color=discord.Color.yellow())
            embed89.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed89.set_footer(text=Help.version1)
            print("Aucun son n'est en cours dans la lecture aléatoire")
            await ctx.send(embed=embed89, delete_after=5)

    async def play_random_sound(self, channel_id):
        while True:
            if self.voice_client and self.voice_client.is_connected():
                if not self.voice_client.is_playing():
                    if self.random_task and not self.random_task.done():
                        wait_time = random.randint(1, 5) * 60  # choisir un temps aléatoire entre 1 et 5 minutes
                        print(f"Attente de {wait_time // 60} minutes")
                        await asyncio.sleep(wait_time)
                        sound_num = random.randint(1, len(self.sound_files))
                        sound_name = self.sound_files[sound_num-1]
                        file_path = f"{self.sounds_dir}/{sound_name}"
                        if os.path.isfile(file_path):
                            source = discord.FFmpegPCMAudio(file_path, executable=self.ffmpeg_path)
                            self.voice_client.play(source)
                            embed90 = discord.Embed(title= "SoundBoard Random", description=f"Joue {sound_name}", color=discord.Color.green())
                            embed90.set_footer(text=Help.version1)
                            print(f"Joue {sound_name}")
                            await self.client.get_channel(channel_id).send(embed=embed90, delete_after=15)
                            print("En attente de la fin de l'audio en cours de lecture")
                    else:
                        embed45 = discord.Embed(title= "SoundBoard Random", description=f"Arrêt de la lecture aléatoire.", color=discord.Color.red())
                        embed45.set_footer(text=Help.version1)
                        print("Arrêt de la lecture aléatoire")
                        await self.client.get_channel(channel_id).send(embed=embed45, delete_after=5)          
            await asyncio.sleep(1)
            
    @commands.command()
    async def srandomstop(self, ctx):
        await ctx.message.delete()
        if self.random_task and not self.random_task.done():
            self.random_task.cancel()
            embed = discord.Embed(title="SoundBoard Random Stop", description="Arrêt de la lecture aléatoire réussi", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            print("Lecture aléatoire arreté")
            await ctx.send(embed=embed, delete_after=5)
        else:
            embed = discord.Embed(title="SoundBoard Random Stop Erreur", description="La lecture aléatoire n'est pas en cours.", color=discord.Color.yellow())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=Help.version1)
            print("Lecture aléatoire erreur pas en cours")
            await ctx.send(embed=embed, delete_after=5)    
    
    @commands.command()
    async def sjoin(self, ctx):
        await ctx.message.delete()
        if not ctx.author.voice:
            embed1 = discord.Embed(title= "SoundBoard Join Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.yellow())
            embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed1.set_footer(text=Help.version1)
            return await ctx.send(embed = embed1, delete_after=5)
        
        channel = ctx.author.voice.channel
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.move_to(channel)
            embed2 = discord.Embed(title= "SoundBoard Join Erreur", description="Je suis déjà connecté à un salon vocal.", color=discord.Color.yellow())
            embed2.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed2.set_footer(text=Help.version1)
            await ctx.send(embed = embed2, delete_after=5)
        
        else:
            embed3 = discord.Embed(title= "SoundBoard Join", description="Je suis connecté à un salon vocal.", color=discord.Color.green())
            embed3.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed3.set_footer(text=Help.version1)
            await ctx.send(embed = embed3, delete_after=5)
            self.voice_client = await channel.connect()
 
    @commands.command()
    async def slist(self, ctx):
        await ctx.message.delete()
        sound_files = [f for f in os.listdir(self.sounds_dir) if f.endswith(".mp3")]
        
        
        if not sound_files:
            embed54 = discord.Embed(title= "SoundBoard List", description="Aucun fichier dans le dossier **Sounds**", color=discord.Color.random())
            embed54.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed54.set_footer(text=Help.version1)
            await ctx.send(embed = embed54, delete_after=10)
            return

        file_list = ""
        for i, file in enumerate(sound_files):
            file_path = f"{self.sounds_dir}/{file}"
            file_name = os.path.splitext(file)[0]
            if file.endswith(".mp3"):
                audio = MP3(file_path)
                duration = int(audio.info.length)
            else:
                duration = 0
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
            file_list += f"{i+1}. ({duration_str}) {file_name}\n"
        embed13 = discord.Embed(title= "SoundBoard List", description=f"Liste des fichiers audio disponibles :```\n{file_list}\n```", color=discord.Color.random())
        embed13.add_field(name=" ", value=" ", inline=True)
        embed13.add_field(name="Commande", value="Exemple =splay 4", inline=True)
        embed13.add_field(name=" ", value=" ", inline=True)
        embed13.add_field(name="Le nombre", value="1", inline=True)
        embed13.add_field(name="Le temps", value="hh:mm:ss", inline=True)
        embed13.add_field(name="Le nom", value="Test", inline=True)
        embed13.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed13.set_footer(text=Help.version1)
        await ctx.send(embed = embed13)
        
    @commands.command()
    async def splay(self, ctx, sound_num: int=None):
        await ctx.message.delete()
        """Commande pour jouer un son enregistré."""
        if not ctx.author.voice:
            embed1 = discord.Embed(title= "SoundBoard Play Erreur", description="Vous devez être connecté à un salon vocal pour utiliser cette commande.", color=discord.Color.red())
            embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed1.set_footer(text=Help.version1)
            return await ctx.send(embed = embed1, delete_after=5)

        if not self.voice_client or not self.voice_client.is_connected():
            embed4 = discord.Embed(title= "SoundBoard Play Erreur", description="Je ne suis pas connecté à un salon vocal.", color=discord.Color.yellow())
            embed4.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed4.set_footer(text=Help.version1)
            return await ctx.send(embed = embed4, delete_after=5)

        if self.voice_client.is_playing():
            embed9 = discord.Embed(title= "SoundBoard Play Erreur", description=f"Une musique est déjà en cours de lecture.", color=discord.Color.yellow())
            embed9.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed9.set_footer(text=Help.version1)
            return await ctx.send(embed = embed9, delete_after=5)

        # Obtenir le nom du fichier audio correspondant au numéro donné
        sound_files = os.listdir(self.sounds_dir)
        sound_files = [f for f in os.listdir(self.sounds_dir) if f.endswith(".mp3")]
        if sound_num is None:
            file_path2 = f"{self.sounds_dir}/blepair.mp3"
            embed16 = discord.Embed(title= "SoundBoard Play", description=f"Pour jouer un son, utilisez la commande avec un numéro de son valide. Exemple : `=splay 1`", color=discord.Color.blue())
            embed16.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed16.set_footer(text=Help.version1)
            source = discord.FFmpegPCMAudio(file_path2, executable=self.ffmpeg_path)
            self.voice_client.play(source)
            return await ctx.send(embed = embed16, delete_after=5)

        if sound_num <= 0 or sound_num > len(sound_files):
            embed5 = discord.Embed(title= "SoundBoard Play Erreur", description="Numéro audio invalide.", color=discord.Color.red())
            embed5.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed5.set_footer(text=Help.version1)
            return await ctx.send(embed = embed5, delete_after=5)

        sound_name = sound_files[sound_num-1 if sound_num > 0 else 0]

        # Vérifiez que le fichier audio existe
        file_path = f"{self.sounds_dir}/{sound_name}"  # chemin vers le fichier audio
        if not os.path.isfile(file_path):
            return await ctx.send(f"Le fichier audio {sound_name} n'existe pas.")

        # Joue le fichier audio
        embed9 = discord.Embed(title= "SoundBoard Play", description=f"Joue {sound_name}", color=discord.Color.green())
        embed9.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed9.set_footer(text=Help.version1)
        await ctx.send(embed = embed9, delete_after=10)
        source = discord.FFmpegPCMAudio(file_path, executable=self.ffmpeg_path)
        self.voice_client.play(source)
    
        # Exécuter la suite si le fichier "Outro.mp3" a été joué
        if sound_name == "Outro.mp3":
            print("Outro détecté")
            await asyncio.sleep(58)
            print("58 secondes écoulées")

            # déconnecte les utilisateurs de la vocale
            for member in self.voice_client.channel.members:
                if not member.bot:
                    await member.move_to(None)
                    
            
            embed6 = discord.Embed(title= "SoundBoard Play Outro", description="Expulsion des utilisateurs du salon vocal.", color=discord.Color.yellow())
            embed6.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed6.set_footer(text=Help.version1)
            await ctx.channel.send(embed = embed6, delete_after=5)

    @commands.command()
    async def sstop(self, ctx):
        await ctx.message.delete()
        """Commande pour arrêter la lecture en cours."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            embed15 = discord.Embed(title= "SoundBoard Stop", description="Arrêt de la lecture réussi", color=discord.Color.red())
            embed15.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed15.set_footer(text=Help.version1)
            await ctx.send(embed = embed15, delete_after=5)
        else:
            embed8 = discord.Embed(title= "SoundBoard Stop Erreur", description="Je ne suis pas en train de jouer de la musique.", color=discord.Color.yellow())
            embed8.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed8.set_footer(text=Help.version1)
            await ctx.send(embed = embed8, delete_after=5)
    
    @commands.command()
    async def sleave(self, ctx):
        await ctx.message.delete()
        """Commande pour déconnecter le bot du salon vocal actuel."""
        if not self.voice_client or not self.voice_client.is_connected():
            print("Je ne suis pas connecté")
            embed10 = discord.Embed(title= "SoundBoard Leave Erreur", description="Je ne suis pas connecté à un salon vocal.", color=discord.Color.yellow())
            embed10.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed10.set_footer(text=Help.version1)
            return await ctx.send(embed = embed10, delete_after=5)
            
        await self.voice_client.disconnect()
        self.voice_client = None
        embed12 = discord.Embed(title= "SoundBoard Leave", description="Déconnexion du salon vocal réussi", color=discord.Color.green())
        embed12.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed12.set_footer(text=Help.version1)
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
                embed42.set_footer(text=Help.version1)
                await ctx.send(embed = embed42, delete_after=5)
            else:
                await ctx.send("")
                embed46 = discord.Embed(title= "Vocal Kick Erreur", description="L'utilisateur spécifié ne peut pas être expulsé.", color=discord.Color.red())
                embed46.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed46.set_footer(text=Help.version1)
                await ctx.send(embed = embed46, delete_after=5)
        else:
            for member in self.voice_client.channel.members:
                if not member.bot:
                    await member.move_to(None)

            embed47 = discord.Embed(title= "Vocal Kick", description="Tous les utilisateurs ont été expulsés du salon vocal", color=discord.Color.green())
            embed47.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed47.set_footer(text=Help.version1)
            await ctx.send(embed = embed47, delete_after=5)            



    @vkick.error
    async def vkick_error(self, ctx, error):
        await ctx.message.delete()
        if isinstance(error, commands.MissingPermissions):
            embed8 = discord.Embed(title= "Erreur Vocal Kick", description="Tu na pas les permissions **Adminiristrateur**", color=discord.Color.red())
            embed8.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed8.set_footer(text=Help.version1)
            await ctx.send(embed = embed8, delete_after=10)
        elif isinstance(error, commands.BadArgument):
            embed9 = discord.Embed(title= "Erreur Vocal Kick", description="Mets un argument vailde", color=discord.Color.red())
            embed9.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed9.set_footer(text=Help.version1)
            await ctx.send(embed = embed9, delete_after=10)
        else:
            embed10 = discord.Embed(title= "Erreur Vocal Kick", description="Il y a eu un problème, lors de l'éxécution de la commande `=report` si vous voulez signaler un bug", color=discord.Color.red())
            embed10.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed10.set_footer(text=Help.version1)
            await ctx.send(embed = embed10, delete_after=10)


async def setup(client):
    await client.add_cog(Soundboard(client))