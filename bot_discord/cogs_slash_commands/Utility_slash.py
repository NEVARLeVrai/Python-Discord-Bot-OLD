import discord
from discord import app_commands
from discord.ext import commands
import random
import io
import asyncio
import traceback
from cogs import Help
from cogs.Help import get_current_version
import datetime
from openai import OpenAI
from typing import Union

class Utility_slash(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.reponse_en_cours = False
        gpt_token_path = client.paths['gpt_token_file']
        with open(gpt_token_path, "r") as f:
            GPT_API_KEY = f.read().strip()
        self.openai_client = OpenAI(api_key=GPT_API_KEY)
        self.rate_limit_delay = 1
    
    def is_bot_dm(self, message):
        return message.author == self.client.user and isinstance(message.channel, discord.DMChannel)

    async def send_tts(self, vc, lang, vol, text):
        """Envoie un texte en TTS"""
        max_length = 200
        text_parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        ffmpeg_path = self.client.paths['ffmpeg_exe']

        for part in text_parts:
            vc.play(discord.FFmpegPCMAudio(
                executable=ffmpeg_path,
                source=f"http://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang}&q={part}",
                options=f"-af volume={vol}"
            ))
            while vc.is_playing():
                await asyncio.sleep(1)

    @app_commands.command(name="tts", description="Fait parler le bot")
    @app_commands.describe(lang="Langue du TTS (défaut: fr)", vol="Volume du TTS (défaut: 3.0)", text="Texte à dire")
    async def tts(self, interaction: discord.Interaction, text: str, lang: str = "fr", vol: str = "3.0"):
        """Commande TTS en slash"""
        await interaction.response.defer(ephemeral=False)
        
        vc = None
        try:
            if not interaction.user.voice:
                embed = discord.Embed(title="TTS - Erreur", description="Vous devez être dans un salon vocal pour utiliser cette commande.", color=discord.Color.red())
                embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            channel = interaction.user.voice.channel
            voice = discord.utils.get(self.client.voice_clients, guild=interaction.guild)
            
            if voice and voice.is_connected():
                if voice.is_playing():
                    voice.stop()
                    youtube_cog = self.client.get_cog('Youtube')
                    if youtube_cog and hasattr(youtube_cog, 'queue'):
                        youtube_cog.queue.clear()
                    await asyncio.sleep(0.5)
                
                if voice.channel == channel:
                    vc = voice
                else:
                    try:
                        await voice.move_to(channel)
                        vc = voice
                    except discord.errors.ClientException as e:
                        embed = discord.Embed(title="TTS - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    except Exception as e:
                        embed = discord.Embed(title="TTS - Erreur", description=f"Impossible de se déplacer vers le canal vocal: {str(e)}", color=discord.Color.red())
                        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                        embed.set_footer(text=get_current_version(self.client))
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
            else:
                try:
                    vc = await channel.connect()
                except discord.errors.ClientException as e:
                    embed = discord.Embed(title="TTS - Erreur", description=f"Conflit de connexion vocale. Le bot est peut-être utilisé par une autre fonctionnalité.", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return
                except Exception as e:
                    embed = discord.Embed(title="TTS - Erreur", description=f"Impossible de se connecter au canal vocal: {str(e)}", color=discord.Color.red())
                    embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
                    embed.set_footer(text=get_current_version(self.client))
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

            embed = discord.Embed(title="TTS Play", description=f"Volume: **{vol}**\nLangue: **{lang}**\nDit: **{text}**", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
            await self.send_tts(vc, lang, vol, text)

        except Exception as e:
            traceback_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            embed = discord.Embed(title="TTS - Erreur", description=f"Une erreur s'est produite lors de la lecture TTS:\n\n```\n{str(e)}\n```", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f"Erreur TTS: {traceback_str}")

    @app_commands.command(name="gpt", description="Utilise GPT pour répondre à une question")
    @app_commands.describe(question="Votre question pour GPT")
    async def gpt(self, interaction: discord.Interaction, question: str):
        """Commande GPT en slash"""
        if self.reponse_en_cours:
            await interaction.response.send_message("Une réponse est déjà en cours de génération. Veuillez patienter.", ephemeral=True)
            return

        self.reponse_en_cours = True
        await interaction.response.defer(ephemeral=False)

        try:
            response = self.gpt_reponse(question)
            if not response:
                await interaction.followup.send("Erreur: Aucune réponse générée.", ephemeral=True)
                return
                
            response = self.nettoyer_texte(response)
            response_with_mention = f"{interaction.user.mention}\n{response}"
            
            if len(response_with_mention) > 2000:
                await self.send_long_message_slash(interaction, response_with_mention)
            else:
                await interaction.followup.send(response_with_mention, ephemeral=False)

            # Logger la requête
            try:
                gpt_logs_path = self.client.paths['gpt_logs']
                with open(gpt_logs_path, "a", encoding='utf-8') as f:
                    current_time = datetime.datetime.now()
                    f.write(f"Date: {current_time.strftime('%Y-%m-%d')}\n")
                    f.write(f"Heure: {current_time.strftime('%H:%M:%S')}\n")
                    f.write(f"User: {interaction.user.mention}\n")                
                    f.write(f"Question: {question}\n")
                    f.write(f"Réponse: {response}\n")
                    f.write("-" * 50 + "\n")
            except Exception as e:
                print(f"Erreur lors de l'écriture du log GPT: {e}")

        except Exception as e:
            error_embed = discord.Embed(title="Erreur GPT", description=f"Une erreur s'est produite: {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            print(f"Erreur GPT: {e}")
        finally:
            self.reponse_en_cours = False

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
        texte_nettoye = "\n".join(line for line in texte.splitlines() if line.strip())
        return texte_nettoye

    async def send_long_message_slash(self, interaction, message):
        """Divise un message long en plusieurs messages pour respecter la limite de Discord"""
        max_length = 1900
        parts = []
        
        while len(message) > max_length:
            split_point = message.rfind('\n', 0, max_length)
            if split_point == -1:
                split_point = max_length
            
            parts.append(message[:split_point])
            message = message[split_point:].lstrip()
        
        if message:
            parts.append(message)
        
        for i, part in enumerate(parts):
            if i == 0:
                await interaction.followup.send(part, ephemeral=False)
            else:
                await interaction.followup.send(f"*Suite {i+1}/{len(parts)}:*\n{part}", ephemeral=False)
            await asyncio.sleep(0.5)

    @app_commands.command(name="dalle", description="Génère une image avec DALL-E")
    @app_commands.describe(question="Votre prompt pour DALL-E")
    async def dalle(self, interaction: discord.Interaction, question: str):
        """Commande DALL-E en slash"""
        if self.reponse_en_cours:
            await interaction.response.send_message("Une réponse est déjà en cours de génération. Veuillez patienter.", ephemeral=True)
            return

        self.reponse_en_cours = True
        await interaction.response.defer(ephemeral=False)

        try:
            response = self.dalle_reponse(question)
            if not response:
                await interaction.followup.send("Erreur: Aucune image générée.", ephemeral=True)
                return
                
            response_with_mention = f"{interaction.user.mention}\n{response}"
            await interaction.followup.send(response_with_mention, ephemeral=False)

            # Logger la requête
            try:
                dalle_logs_path = self.client.paths['dalle_logs']
                with open(dalle_logs_path, "a", encoding='utf-8') as f:
                    current_time = datetime.datetime.now()
                    f.write(f"Date: {current_time.strftime('%Y-%m-%d')}\n")
                    f.write(f"Heure: {current_time.strftime('%H:%M:%S')}\n")
                    f.write(f"User: {interaction.user.mention}\n")                
                    f.write(f"Question: {question}\n")
                    f.write(f"Réponse: {response}\n")
                    f.write("-" * 50 + "\n")
            except Exception as e:
                print(f"Erreur lors de l'écriture du log DALL-E: {e}")

        except Exception as e:
            error_embed = discord.Embed(title="Erreur DALL-E", description=f"Une erreur s'est produite: {str(e)}", color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            print(f"Erreur DALL-E: {e}")
        finally:
            self.reponse_en_cours = False

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

    @app_commands.command(name="8ball", description="Pose une question à la boule magique")
    @app_commands.describe(question="Votre question")
    async def magicball(self, interaction: discord.Interaction, question: str):
        """Commande 8ball en slash"""
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
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.add_field(name='Question: ', value=f'{question}')
        embed.add_field(name='Réponse: ', value=f'{response}')
        embed.set_footer(text=get_current_version(self.client))
        with open(self.client.paths['8ball_png'], "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://8ball.png")
        await interaction.response.send_message(embed=embed, file=discord.File(io.BytesIO(image_data), "8ball.png"), ephemeral=False)

    @app_commands.command(name="hilaire", description="Jeu Hilaire")
    async def hilaire(self, interaction: discord.Interaction):
        """Commande Hilaire en slash"""
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
        response = random.choice(responses)
        embed=discord.Embed(title="Wiliam Hilaire à parlé!", color=discord.Color.purple())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.add_field(name='Hilaire à dit: ', value=f'{response}')
        embed.set_footer(text=get_current_version(self.client))
        with open(self.client.paths['hilaire_png'], "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://hilaire.png")
        await interaction.response.send_message(embed=embed, file=discord.File(io.BytesIO(image_data), "hilaire.png"), ephemeral=False)

    @app_commands.command(name="say", description="Envoie un message dans un salon")
    @app_commands.describe(channel="Le salon où envoyer le message", message="Le message à envoyer")
    async def say_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        """Envoie un message dans un salon"""
        await interaction.response.defer(ephemeral=False)
        
        try:
            await channel.send(message)
            embed = discord.Embed(title="Message Envoyé!", description=f"Message envoyé à {channel.mention}", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Impossible d'envoyer le message: {str(e)}", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    @app_commands.command(name="deldms", description="Supprime tous les DMs du bot")
    @app_commands.default_permissions(administrator=True)
    async def delmp(self, interaction: discord.Interaction):
        """Supprime tous les DMs du bot"""
        await interaction.response.defer(ephemeral=False)
        
        try:
            total_deleted = 0
            embed = discord.Embed(title="Suppression des messages privés en cours...", color=discord.Color.yellow())
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)

            tasks = []
            for member in interaction.guild.members:
                if not member.bot:
                    dm_channel = await member.create_dm()
                    messages_to_delete = [msg async for msg in dm_channel.history() if self.is_bot_dm(msg)]
                    deleted_count = len(messages_to_delete)

                    if deleted_count > 0:
                        tasks.append(dm_channel.send(f"Suppression Terminé!", delete_after=10))
                        tasks.append(asyncio.gather(*[msg.delete() for msg in messages_to_delete]))
                        await asyncio.sleep(self.rate_limit_delay)

                    total_deleted += deleted_count

                    if deleted_count > 0:
                        embed = discord.Embed(title=f"Messages privés de **{member.name}#{member.discriminator}** supprimés !", color=discord.Color.green())
                        embed.add_field(name="Nombre de messages supprimés", value=str(deleted_count))
                        embed.set_footer(text=get_current_version(self.client))
                        tasks.append(interaction.channel.send(embed=embed, delete_after=10))
                        await asyncio.sleep(self.rate_limit_delay)

            await asyncio.gather(*tasks)
            
            if total_deleted > 0:
                embed1 = discord.Embed(title=f"Messages privés supprimés au total.", description=f"{total_deleted}", color=discord.Color.purple())
            else:
                embed1 = discord.Embed(title="Aucun message privé à supprimer.", color=discord.Color.red())
            embed1.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed1, ephemeral=False)
            
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Une erreur s'est produite: {str(e)}", color=discord.Color.red())
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            import traceback
            traceback.print_exc()
    
    @app_commands.command(name="correcteur", description="Active ou désactive le correcteur automatique d'orthographe et de grammaire")
    @app_commands.describe(action="Action à effectuer: activer, désactiver ou afficher le statut")
    @app_commands.choices(action=[
        app_commands.Choice(name="Activer", value="activer"),
        app_commands.Choice(name="Désactiver", value="désactiver"),
        app_commands.Choice(name="Statut", value="statut")
    ])
    @app_commands.default_permissions(manage_messages=True)
    async def grammar_corrector_slash(self, interaction: discord.Interaction, action: str = "statut"):
        """
        Commande slash pour activer/désactiver le correcteur automatique.
        
        Le correcteur analyse automatiquement les messages et répond avec les corrections.
        Supporte 40+ langues avec mode auto pour détection automatique.
        
        Actions disponibles:
            - activer: Active le correcteur pour ce serveur
            - désactiver: Désactive le correcteur pour ce serveur
            - statut: Affiche le statut actuel (par défaut)
        
        Permissions requises: Manage Messages
        Configuration: Les paramètres sont sauvegardés par serveur dans grammar_corrector.json
        """
        await interaction.response.defer(ephemeral=False)
        
        # Récupérer le cog GrammarCorrector_auto
        grammar_cog = self.client.get_cog('GrammarCorrector_auto')
        if not grammar_cog:
            embed = discord.Embed(
                title="Erreur",
                description="Le correcteur automatique n'est pas disponible.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Vérifier si settings est chargé
        if grammar_cog.settings is None:
            grammar_cog.settings = {}
        
        guild_id = str(interaction.guild.id)
        
        # Initialiser les paramètres pour ce serveur si nécessaire
        if guild_id not in grammar_cog.settings:
            grammar_cog.settings[guild_id] = {'enabled': False, 'languages': ['fr']}
        # S'assurer que languages existe
        if 'languages' not in grammar_cog.settings[guild_id]:
            grammar_cog.settings[guild_id]['languages'] = ['fr']
        
        current_status = grammar_cog.settings[guild_id].get('enabled', False)
        
        # Traiter l'action
        action_lower = action.lower()
        
        if action_lower == "activer":
            grammar_cog.settings[guild_id]['enabled'] = True
            grammar_cog.save_settings()
            embed = discord.Embed(
                title="✅ Correcteur activé",
                description="Le correcteur automatique d'orthographe et de grammaire est maintenant **activé** pour ce serveur.",
                color=discord.Color.green()
            )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
        
        elif action_lower == "désactiver":
            grammar_cog.settings[guild_id]['enabled'] = False
            grammar_cog.save_settings()
            embed = discord.Embed(
                title="❌ Correcteur désactivé",
                description="Le correcteur automatique d'orthographe et de grammaire est maintenant **désactivé** pour ce serveur.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
        
        else:  # statut ou autre
            status_text = "activé" if current_status else "désactivé"
            status_emoji = "✅" if current_status else "❌"
            embed = discord.Embed(
                title="Correcteur automatique",
                description=f"Le correcteur automatique est actuellement **{status_text}** {status_emoji}",
                color=discord.Color.green() if current_status else discord.Color.red()
            )
            embed.add_field(
                name="Utilisation",
                value="Utilisez `/correcteur activer` pour activer\nUtilisez `/correcteur désactiver` pour désactiver",
                inline=False
            )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
    
    @app_commands.command(name="langue", description="Gère les langues du correcteur automatique")
    @app_commands.describe(action="Action à effectuer: afficher, ajouter ou enlever une langue", lang_code="Code de la langue (ex: fr, en, es, auto). Tapez le code directement pour les langues non listées.")
    @app_commands.choices(action=[
        app_commands.Choice(name="Afficher", value="afficher"),
        app_commands.Choice(name="Ajouter", value="ajouter"),
        app_commands.Choice(name="Enlever", value="enlever")
    ])
    @app_commands.choices(lang_code=[
        app_commands.Choice(name="Détection automatique (auto)", value="auto"),
        app_commands.Choice(name="Français (fr)", value="fr"),
        app_commands.Choice(name="Anglais (en)", value="en"),
        app_commands.Choice(name="Espagnol (es)", value="es"),
        app_commands.Choice(name="Allemand (de)", value="de"),
        app_commands.Choice(name="Italien (it)", value="it"),
        app_commands.Choice(name="Portugais (pt)", value="pt"),
        app_commands.Choice(name="Russe (ru)", value="ru"),
        app_commands.Choice(name="Polonais (pl)", value="pl"),
        app_commands.Choice(name="Néerlandais (nl)", value="nl"),
        app_commands.Choice(name="Catalan (ca)", value="ca"),
        app_commands.Choice(name="Tchèque (cs)", value="cs"),
        app_commands.Choice(name="Danois (da)", value="da"),
        app_commands.Choice(name="Grec (el)", value="el"),
        app_commands.Choice(name="Finnois (fi)", value="fi"),
        app_commands.Choice(name="Japonais (ja)", value="ja"),
        app_commands.Choice(name="Roumain (ro)", value="ro"),
        app_commands.Choice(name="Slovaque (sk)", value="sk"),
        app_commands.Choice(name="Slovène (sl)", value="sl"),
        app_commands.Choice(name="Suédois (sv)", value="sv"),
        app_commands.Choice(name="Ukrainien (uk)", value="uk"),
        app_commands.Choice(name="Chinois (zh)", value="zh"),
        app_commands.Choice(name="Bulgare (bg)", value="bg"),
        app_commands.Choice(name="Croate (hr)", value="hr"),
        app_commands.Choice(name="Norvégien (no)", value="no")
    ])
    @app_commands.default_permissions(manage_messages=True)
    async def langue_slash(self, interaction: discord.Interaction, action: str = "afficher", lang_code: str = None):
        """
        Commande slash pour gérer les langues du correcteur automatique.
        
        Permet d'ajouter/enlever des langues ou d'afficher la liste des langues configurées.
        Supporte 40+ langues (fr, en, es, de, it, pt, ru, pl, nl, etc.) et le mode 'auto'.
        
        Actions disponibles:
            - afficher: Affiche les langues configurées et la liste complète des langues supportées
            - ajouter: Ajoute une langue à la liste (ex: /langue ajouter en)
            - enlever: Retire une langue de la liste (ex: /langue enlever en)
        
        Mode auto:
            Le mode 'auto' détecte automatiquement la langue de chaque message.
            Quand 'auto' est ajouté, toutes les autres langues sont remplacées.
            Le mode auto est recommandé pour les serveurs multilingues.
        
        Langues supportées:
            Plus de 40 langues sont disponibles (français, anglais, espagnol, allemand, italien,
            portugais, russe, polonais, néerlandais, et bien d'autres).
            Utilisez l'action "afficher" pour voir la liste complète.
        
        Permissions requises: Manage Messages
        Configuration: Sauvegardée par serveur dans grammar_corrector.json
        """
        await interaction.response.defer(ephemeral=False)
        
        # Récupérer le cog GrammarCorrector_auto
        grammar_cog = self.client.get_cog('GrammarCorrector_auto')
        if not grammar_cog:
            embed = discord.Embed(
                title="Erreur",
                description="Le correcteur automatique n'est pas disponible.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        action_lower = action.lower()
        
        if action_lower == "afficher":
            languages = grammar_cog.get_languages(interaction.guild.id)
            languages_list = []
            for lang in languages:
                lang_name = grammar_cog.supported_languages.get(lang, lang.upper())
                languages_list.append(f"**{lang}** - {lang_name}")
            
            embed = discord.Embed(
                title="🌍 Langues du correcteur",
                description=f"**Langues configurées pour ce serveur:**\n" + "\n".join(languages_list) if languages_list else "Aucune langue configurée",
                color=discord.Color.blue()
            )
            
            # Ajouter la liste des langues supportées (toutes les langues)
            supported_list = []
            for code, name in grammar_cog.supported_languages.items():
                supported_list.append(f"`{code}` - {name}")
            
            # Diviser en plusieurs fields si nécessaire (limite Discord: 1024 caractères par field)
            # On divise en chunks de ~30 langues pour être sûr de ne pas dépasser
            chunk_size = 30
            for i in range(0, len(supported_list), chunk_size):
                chunk = supported_list[i:i + chunk_size]
                field_name = "Langues supportées:" if i == 0 else f"Langues supportées (suite {i//chunk_size + 1}):"
                embed.add_field(
                    name=field_name,
                    value="\n".join(chunk),
                    inline=False
                )
            
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
        
        elif action_lower == "ajouter":
            if lang_code is None:
                embed = discord.Embed(
                    title="Erreur",
                    description="Veuillez spécifier un code de langue.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            lang_code_lower = lang_code.lower()
            
            # Vérifier si la langue est supportée
            if lang_code_lower not in grammar_cog.supported_languages:
                embed = discord.Embed(
                    title="Erreur",
                    description=f"La langue `{lang_code_lower}` n'est pas supportée.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Vérifier si la langue est déjà ajoutée
            current_languages = grammar_cog.get_languages(interaction.guild.id)
            if lang_code_lower in current_languages:
                embed = discord.Embed(
                    title="Information",
                    description=f"La langue `{lang_code_lower}` ({grammar_cog.supported_languages[lang_code_lower]}) est déjà configurée.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=False)
                return
            
            # Ajouter la langue
            grammar_cog.add_language(interaction.guild.id, lang_code_lower)
            new_languages = grammar_cog.get_languages(interaction.guild.id)
            
            embed = discord.Embed(
                title="✅ Langue ajoutée",
                description=f"La langue `{lang_code_lower}` ({grammar_cog.supported_languages[lang_code_lower]}) a été ajoutée.",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Langues configurées:",
                value=", ".join([f"`{l}`" for l in new_languages]),
                inline=False
            )
            if lang_code_lower == 'auto':
                embed.add_field(
                    name="ℹ️ Note:",
                    value="Le mode **auto** détecte automatiquement la langue de chaque message. Toutes les autres langues ont été remplacées.",
                    inline=False
                )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)
        
        elif action_lower == "enlever":
            if lang_code is None:
                embed = discord.Embed(
                    title="Erreur",
                    description="Veuillez spécifier un code de langue.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            lang_code_lower = lang_code.lower()
            
            # Vérifier si la langue est configurée
            current_languages = grammar_cog.get_languages(interaction.guild.id)
            if lang_code_lower not in current_languages:
                embed = discord.Embed(
                    title="Erreur",
                    description=f"La langue `{lang_code_lower}` n'est pas configurée pour ce serveur.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Vérifier qu'on ne supprime pas la dernière langue (sauf si c'est "auto" qui sera remplacé par "fr")
            if len(current_languages) == 1 and lang_code_lower != 'auto':
                embed = discord.Embed(
                    title="Erreur",
                    description="Vous ne pouvez pas supprimer la dernière langue. Il doit y avoir au moins une langue configurée.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Enlever la langue
            grammar_cog.remove_language(interaction.guild.id, lang_code_lower)
            new_languages = grammar_cog.get_languages(interaction.guild.id)
            
            embed = discord.Embed(
                title="❌ Langue enlevée",
                description=f"La langue `{lang_code_lower}` a été enlevée.",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="Langues configurées restantes:",
                value=", ".join([f"`{l}`" for l in new_languages]),
                inline=False
            )
            embed.set_footer(text=get_current_version(self.client))
            await interaction.followup.send(embed=embed, ephemeral=False)


async def setup(client):
    await client.add_cog(Utility_slash(client))

