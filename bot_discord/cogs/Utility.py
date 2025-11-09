import discord
from discord.ext import commands
import random
import io
import asyncio
from cogs import Help
from cogs.Help import get_current_version
import traceback
import openai
import datetime
import typing
import asyncio
import re
from openai import OpenAI
import aiohttp
from urllib.parse import urlparse, urljoin

class utility(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.reponse_en_cours = False  # Variable de verrouillage initialement à False
        # Utiliser les chemins centralisés depuis main.py
        gpt_token_path = client.paths['gpt_token_file']
        with open(gpt_token_path, "r") as f:
            GPT_API_KEY = f.read().strip()
        self.openai_client = OpenAI(api_key=GPT_API_KEY)
        self.rate_limit_delay = 1  # Délai en secondes entre chaque requête (1 seconde dans cet exemple)

        
    def is_bot_dm(message):
        return message.author.bot and isinstance(message.channel, discord.DMChannel)
    
    def is_bot_dm(self, message):
        return message.author == self.client.user and isinstance(message.channel, discord.DMChannel)

    async def send_tts(self, vc, lang, vol, text):
        # Découpe le texte en parties de longueur maximale max_length
        max_length = 200
        text_parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]

        # Utiliser le chemin centralisé depuis main.py
        ffmpeg_path = self.client.paths['ffmpeg_exe']

        # Joue chaque partie du texte
        for part in text_parts:
            vc.play(discord.FFmpegPCMAudio(
                executable=ffmpeg_path,
                source=f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang}&q={part}",
                options=f"-af volume={vol}"
            ))
            while vc.is_playing():
                await asyncio.sleep(1)


    @commands.command()
    async def tts(self, ctx, lang="fr", vol="3.0", *, text):
        await ctx.message.delete()
        vc = None
        try:
            if not ctx.author.voice:
                embed = discord.Embed(title="TTS - Erreur", description="Vous devez être dans un salon vocal pour utiliser cette commande.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await ctx.send(embed=embed, delete_after=5)
                return

            channel = ctx.author.voice.channel
            # Vérifier si le bot est déjà connecté dans ce serveur
            voice = discord.utils.get(self.client.voice_clients, guild=ctx.guild)
            
            if voice and voice.is_connected():
                # Si une lecture est en cours, l'arrêter pour TTS
                if voice.is_playing():
                    voice.stop()
                    # Si YouTube jouait, vider sa queue pour éviter confusion
                    youtube_cog = self.client.get_cog('Youtube')
                    if youtube_cog and hasattr(youtube_cog, 'queue'):
                        youtube_cog.queue.clear()
                    await asyncio.sleep(0.5)  # Attendre que la lecture s'arrête
                
                # Déjà connecté, vérifier si c'est le bon canal
                if voice.channel == channel:
                    vc = voice
                else:
                    # Déplacer vers le nouveau canal
                    try:
                        await voice.move_to(channel)
                        vc = voice
                    except discord.errors.ClientException as e:
                        embed = discord.Embed(title="TTS - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await ctx.send(embed=embed, delete_after=5)
                        return
                    except Exception as e:
                        embed = discord.Embed(title="TTS - Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await ctx.send(embed=embed, delete_after=5)
                        return
            else:
                # Pas encore connecté, se connecter
                try:
                    vc = await channel.connect()
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="TTS - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await ctx.send(embed=embed, delete_after=5)
                    return
                except Exception as e:
                    embed = discord.Embed(title="TTS - Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await ctx.send(embed=embed, delete_after=5)
                    return

            embed = discord.Embed(title="TTS Play", description=f"Volume: **{vol}**\nLangue: **{lang}**\nDit: **{text}**", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=25)
            await self.send_tts(vc, lang, vol, text)

        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            embed = discord.Embed(title="TTS - Erreur", description=f"Une erreur s'est produite lors de la lecture TTS:\n\n```\n{str(e)}\n```", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            print(f"Erreur TTS: {traceback_str}")
        finally:
            # Ne pas déconnecter automatiquement, laisser le bot connecté pour les autres fonctionnalités
            # Si vous voulez déconnecter après TTS, décommentez les lignes suivantes:
            # if vc:
            #     await vc.disconnect()
            pass

    @commands.command(aliases=["repeat"])
    async def say(self, ctx, destination: typing.Union[discord.TextChannel, discord.Member, str], *, message=None):
        await ctx.message.delete()

        if isinstance(destination, str):
            if destination.startswith("<#") and destination.endswith(">"):
                channel_id = int(destination[2:-1])  # Extraction de l'ID à partir de la mention
                destination = self.client.get_channel(channel_id)
                if not isinstance(destination, discord.TextChannel):
                    await ctx.send("Salon invalide spécifié.")
                    return
            else:
                embed1 = discord.Embed(title="Message Non Envoyé!", description="Format de mention de salon incorrect.", color=discord.Color.red())
                embed1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                embed1.set_footer(text=get_current_version(self.client))

                await ctx.send(embed=embed1, delete_after=10)
                return

        # Vérifiez si des fichiers sont attachés au message
        if ctx.message.attachments:
            files = [await attachment.to_file() for attachment in ctx.message.attachments]
        else:
            files = []

        await destination.send(message, files=files)

        # Ajouter un message d'information
        embed = discord.Embed(title="Message Envoyé!", description=f"Message envoyé à {destination.mention}", color=discord.Color.green())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await ctx.send(embed=embed, delete_after=10)





        

    @commands.has_permissions(administrator=True)
    @commands.command(aliases=["deldms"])
    async def delmp(self, ctx):
        await ctx.message.delete()
        try:
            total_deleted = 0

            # Envoie d'un message global indiquant que la suppression des DMs est en cours
            embed = discord.Embed(title="Suppression des messages privés en cours...", color=discord.Color.yellow())
            embed.set_footer(text=get_current_version(self.client))
            status_msg = await ctx.send(embed=embed, delete_after=10)

            tasks = []
            for member in ctx.guild.members:
                if not member.bot:
                    dm_channel = await member.create_dm()
                    messages_to_delete = [msg async for msg in dm_channel.history() if self.is_bot_dm(msg)]
                    deleted_count = len(messages_to_delete)

                    if deleted_count > 0:
                        tasks.append(dm_channel.send(f"Suppression Terminé!", delete_after=10))
                        tasks.append(asyncio.gather(*[msg.delete() for msg in messages_to_delete]))
                        await asyncio.sleep(self.rate_limit_delay)  # Limite de taux

                    total_deleted += deleted_count

                    # Envoyer un message individuel pour chaque utilisateur dont les DMs ont été supprimés
                    if deleted_count > 0:
                        embed = discord.Embed(title=f"Messages privés de **{member.name}#{member.discriminator}** supprimés !", color=discord.Color.green())
                        embed.add_field(name="Nombre de messages supprimés", value=str(deleted_count))
                        embed.set_footer(text=get_current_version(self.client))
                        tasks.append(ctx.send(embed=embed, delete_after=10))
                        await asyncio.sleep(self.rate_limit_delay)  # Limite de taux
                    


            # Attendre que toutes les tâches soient terminées
            await asyncio.gather(*tasks)
            
            if total_deleted > 0:
                embed1 = discord.Embed(title=f"Messages privés supprimés au total.", description=f"{total_deleted}", color=discord.Color.purple())
            else:
                embed1 = discord.Embed(title="Aucun message privé à supprimer.", color=discord.Color.red())
            embed1.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed1, delete_after=10)
            
        except Exception as e:
            traceback.print_exc()


    @commands.command(aliases=["8ball"])
    async def magicball(self, ctx, * ,question):
        await ctx.message.delete()
        responses=['Comme je le vois oui.',
                  'Oui.',
                  'Positif',
                  'De mon point de vue, oui',
                  'Convaincu.',
                  'Le plus probable.',
                  'De grandes chances',
                  'Non.',
                  'Négatif.',
                  'Pas convaincu.',
                  'Peut-être.',
                  'Pas certain',
                  'Peut-être',
                  'Je ne peux pas prédire maintenant.',
                  'Je suis trop paresseux pour prédire.',
                  'Je suis fatigué. *continue à dormir*']
        response = random.choice(responses)
        embed=discord.Embed(title="La Boule Magique 8 à parlé!", color=discord.Color.purple())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.add_field(name='Question: ', value=f'{question}')
        embed.add_field(name='Réponse: ', value=f'{response}')
        embed.set_footer(text=get_current_version(self.client))
        # Utiliser le chemin centralisé depuis main.py
        with open(self.client.paths['8ball_png'], "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://8ball.png")
        await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), "8ball.png"))
        
    @commands.command()
    async def hilaire(self, ctx):
        await ctx.message.delete()
        responses = ["le protocole RS232",
                "FTTH",
                "Bit de Start",
                "Bit de parité",
                "Sinusoïdale",
                "RJ45",
                "Trop dbruiiiit!!!!",
                "Raphaël les écouteurs",
                "Can le téléphone",
                "JoOoAnnY",
                "Le théorème de demorgan"]
        responses = random.choice(responses)
        embed=discord.Embed(title="Wiliam Hilaire à parlé!", color=discord.Color.purple())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.add_field(name='Hilaire à dit: ', value=f'{responses}')
        embed.set_footer(text=get_current_version(self.client))
        # Utiliser le chemin centralisé depuis main.py
        with open(self.client.paths['hilaire_png'], "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://hilaire.png")
        await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), "hilaire.png"))
        

    @commands.command()
    async def gpt(self, ctx, *, question):
        if self.reponse_en_cours:
            await ctx.send("\nUne réponse est déjà en cours de génération. Veuillez patienter.", delete_after=5)
            if isinstance(ctx.channel, discord.TextChannel):
                await ctx.message.delete()
            return

        self.reponse_en_cours = True  # Définir le verrouillage sur True

        try:
            async with ctx.typing():
                response = self.gpt_reponse(question)
                response = self.nettoyer_texte(response)
                response_with_mention = f"{ctx.author.mention}\n{response}"  # Ajouter la mention à la réponse
                
                # Gérer les messages trop longs pour Discord (limite de 2000 caractères)
                if len(response_with_mention) > 2000:
                    # Diviser le message en plusieurs parties
                    await self.send_long_message(ctx, response_with_mention)
                else:
                    await ctx.send(response_with_mention)

            # Utiliser le chemin centralisé depuis main.py
            gpt_logs_path = self.client.paths['gpt_logs']
            with open(gpt_logs_path, "a") as f:
                current_time = datetime.datetime.now()
                f.write(f"Date: {current_time.strftime('%Y-%m-%d')}\n")
                f.write(f"Heure: {current_time.strftime('%H:%M:%S')}\n")
                f.write(f"User: {ctx.author.mention}\n")                
                f.write(f"Question: {question}\n")
                f.write(f"Réponse: {response}\n")
                f.write("-" * 50 + "\n")

        finally:
            self.reponse_en_cours = False  # Réinitialiser le verrouillage à False

    def gpt_reponse(self, question):
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "Tu es un assistant IA utile et amical. Réponds en français de manière détaillée et complète. N'hésite pas à développer tes réponses."},
                    {"role": "user", "content": question}
                ],
                max_completion_tokens=4000,
                temperature=1
            )
            bot_response = response.choices[0].message.content.strip()
            print("\n\nChat GPT:")
            print(f"Question: {question}")
            print(f"Réponse: {bot_response}")
            return bot_response
        except Exception as e:
            print(f"Erreur GPT: {e}")
            return f"Désolé, une erreur s'est produite lors de la génération de la réponse: {str(e)}"
        

    def nettoyer_texte(self, texte):
        # Supprimer les sauts de ligne redondants
        texte_nettoye = "\n".join(line for line in texte.splitlines() if line.strip())
        return texte_nettoye

    async def send_long_message(self, ctx, message):
        """Divise un message long en plusieurs messages pour respecter la limite de Discord"""
        max_length = 1900  # Laisser une marge pour la mention
        parts = []
        
        # Diviser le message en parties
        while len(message) > max_length:
            # Trouver le dernier saut de ligne avant la limite
            split_point = message.rfind('\n', 0, max_length)
            if split_point == -1:
                # Si pas de saut de ligne, diviser au milieu d'un mot
                split_point = max_length
            
            parts.append(message[:split_point])
            message = message[split_point:].lstrip()
        
        if message:  # Ajouter le reste du message
            parts.append(message)
        
        # Envoyer chaque partie
        for i, part in enumerate(parts):
            if i == 0:
                await ctx.send(part)
            else:
                await ctx.send(f"*Suite {i+1}/{len(parts)}:*\n{part}")
            await asyncio.sleep(0.5)  # Petite pause entre les messages



    @commands.command()
    async def dalle(self, ctx, *, question):
        if self.reponse_en_cours:
            await ctx.send("\nUne réponse est déjà en cours de génération. Veuillez patienter.", delete_after=5)
            if isinstance(ctx.channel, discord.TextChannel):
                await ctx.message.delete()
            return

        self.reponse_en_cours = True  # Définir le verrouillage sur True

        try:
            async with ctx.typing():
                response = self.dalle_reponse(question)
                response_with_mention = f"{ctx.author.mention}\n{response}"  # Ajouter la mention à la réponse
            await ctx.send(response_with_mention)

            # Utiliser le chemin centralisé depuis main.py
            dalle_logs_path = self.client.paths['dalle_logs']
            with open(dalle_logs_path, "a") as f:
                current_time = datetime.datetime.now()
                f.write(f"Date: {current_time.strftime('%Y-%m-%d')}\n")
                f.write(f"Heure: {current_time.strftime('%H:%M:%S')}\n")
                f.write(f"User: {ctx.author.mention}\n")                
                f.write(f"Question: {question}\n")
                f.write(f"Réponse: {response}\n")
                f.write("-" * 50 + "\n")

        finally:
            self.reponse_en_cours = False  # Réinitialiser le verrouillage à False

    def dalle_reponse(self, question):
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=question,
                n=1,
                size="1024x1024",
                quality="standard"
            )
            bot_response = response.data[0].url
            print("\n\nDall-E:")
            print(f"Question: {question}")
            print(f"Réponse: {bot_response}")
            return bot_response
        except Exception as e:
            print(f"Erreur DALL-E: {e}")
            return f"Désolé, une erreur s'est produite lors de la génération de l'image: {str(e)}"
        

    @commands.Cog.listener()
    async def on_message(self, message):
        if 'tiktok.com' in message.content:
            await self.process_tiktok_message(message)
        elif 'instagram.com' in message.content:
            await self.process_instagram_message(message)
        elif 'twitter.com' in message.content:
            await self.process_twitter_message(message)
        elif 'x.com' in message.content:
            await self.process_x_message(message)
        elif 'reddit.com' in message.content or 'redd.it' in message.content:
            await self.process_reddit_message(message)

    async def get_tiktok_final_url(self, url):
        """Suit les redirections TikTok pour récupérer le lien PC final"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Essayer d'abord avec HEAD (plus rapide)
                try:
                    async with session.head(url, allow_redirects=True) as response:
                        final_url = str(response.url)
                        return final_url
                except:
                    # Si HEAD échoue, essayer avec GET
                    async with session.get(url, allow_redirects=True) as response:
                        final_url = str(response.url)
                        return final_url
        except Exception as e:
            print(f"Erreur lors de la résolution de l'URL TikTok: {e}")
            return None

    async def process_tiktok_message(self, message):
        tiktok_link = re.search(r'(https?://(?:\S+\.)?tiktok\.com/\S+)', message.content)
        if tiktok_link:
            original_link = tiktok_link.group(0)
            # Supprimer les paramètres de requête (tout ce qui vient après ?)
            original_link = original_link.split('?')[0]
            
            # Si c'est un lien court (vm.tiktok.com), suivre la redirection pour récupérer le lien PC
            if 'vm.tiktok.com' in original_link:
                final_url = await self.get_tiktok_final_url(original_link)
                if final_url:
                    original_link = final_url
                    # Supprimer les paramètres de requête du lien final aussi
                    original_link = original_link.split('?')[0]
            
            # Initialiser modified_link
            modified_link = original_link
            # Supprimer le préfixe "www." si présent
            modified_link = modified_link.replace('www.tiktok.com', 'tiktok.com')
            # Remplacer tiktok.com par tiktokez.com
            modified_link = modified_link.replace('tiktok.com', 'tiktokez.com')
            await self.send_modified_message(message, modified_link, "TikTok")



    async def process_instagram_message(self, message):
        instagram_link = re.search(r'(https?://(?:www\.)?instagram\.com/\S+)', message.content)
        if instagram_link:
            original_link = instagram_link.group(0)
            # Ne pas traiter les liens /reels/audio/
            if '/reels/audio/' in original_link:
                return
            # Supprimer tout ce qui vient après le dernier /
            modified_link = original_link.rsplit('/', 1)[0] + '/'
            modified_link = modified_link.replace('instagram.com', 'eeinstagram.com')
            await self.send_modified_message(message, modified_link, "Instagram")

    async def process_twitter_message(self, message):
        twitter_link = re.search(r'(https?://(?:www\.)?twitter\.com/\S+)', message.content)
        if twitter_link:
            original_link = twitter_link.group(0)
            modified_link = original_link.replace('twitter.com', 'fxtwitter.com')
            await self.send_modified_message(message, modified_link, "X (Twitter)")

    async def process_x_message(self, message):
        x_link = re.search(r'(https?://(?:www\.)?x\.com/\S+)', message.content)
        if x_link:
            original_link = x_link.group(0)
            modified_link = original_link.replace('x.com', 'fxtwitter.com')
            await self.send_modified_message(message, modified_link, "X (Twitter)")

    async def get_reddit_final_url(self, url):
        """Suit les redirections Reddit pour récupérer le lien PC final"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                # Essayer d'abord avec HEAD (plus rapide)
                try:
                    async with session.head(url, allow_redirects=True) as response:
                        final_url = str(response.url)
                        return final_url
                except:
                    # Si HEAD échoue, essayer avec GET
                    async with session.get(url, allow_redirects=True) as response:
                        final_url = str(response.url)
                        return final_url
        except Exception as e:
            print(f"Erreur lors de la résolution de l'URL Reddit: {e}")
            return None

    async def process_reddit_message(self, message):
        # Capturer les liens reddit.com et redd.it (liens courts)
        # Regex améliorée pour mieux capturer les liens Reddit
        reddit_link = re.search(r'(https?://(?:www\.)?(?:reddit\.com|redd\.it)/[^\s\)\]\>]+)', message.content)
        if reddit_link:
            original_link = reddit_link.group(0)
            # Nettoyer le lien (enlever les caractères de fin comme ), ], >, etc.)
            original_link = original_link.rstrip('.,;!?)>]')
            # Supprimer les paramètres de requête (tout ce qui vient après ?)
            original_link = original_link.split('?')[0]
            
            # Suivre la redirection pour récupérer le lien PC final (comme pour TikTok)
            final_url = await self.get_reddit_final_url(original_link)
            if final_url:
                original_link = final_url
                # Supprimer les paramètres de requête du lien final aussi
                original_link = original_link.split('?')[0]
            
            # Initialiser modified_link
            modified_link = original_link
            # Remplacer reddit.com par vxreddit.com (garde www. si présent)
            modified_link = modified_link.replace('reddit.com', 'vxreddit.com')
            await self.send_modified_message(message, modified_link, "Reddit")

    async def send_modified_message(self, message, modified_link, platform):
        try:
            await message.delete()
        except:
            # Si on ne peut pas supprimer le message (embeds, permissions, etc.), on continue
            pass
        
        async with message.channel.typing():
            await asyncio.sleep(1)
            await message.channel.send(f"[{message.author.display_name} - {platform}]({modified_link})")
                    
async def setup(client):
    await client.add_cog(utility(client))