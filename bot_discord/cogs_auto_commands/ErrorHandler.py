import discord
from discord.ext import commands
from discord import app_commands
from cogs.Help import get_current_version
import traceback

class ErrorHandler(commands.Cog):
    """Gestionnaire d'erreurs global pour les commandes prefix et slash"""
    def __init__(self, client):
        self.client = client
    
    # Gestionnaire d'erreurs pour les commandes prefix
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Supprimer le message de commande si c'est un channel texte
        if isinstance(ctx.channel, discord.TextChannel):
            try:
                await ctx.message.delete()
            except:
                pass
        
        # Commande inconnue
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="Commande inconnue",
                description="Utilisez **=helps** pour la liste des commandes",
                color=discord.Color.red()
            )
            if ctx.guild:
                embed.set_image(url=ctx.guild.icon)
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Permissions manquantes pour l'utilisateur
        if isinstance(error, commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms_text = ", ".join(missing_perms)
            embed = discord.Embed(
                title="Permissions insuffisantes",
                description=f"Vous n'avez pas les permissions nécessaires pour utiliser cette commande.\n\n**Permissions requises:** {perms_text}",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Permissions manquantes pour le bot
        if isinstance(error, commands.BotMissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms_text = ", ".join(missing_perms)
            embed = discord.Embed(
                title="Permissions du bot insuffisantes",
                description=f"Le bot n'a pas les permissions nécessaires pour exécuter cette commande.\n\n**Permissions requises:** {perms_text}",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Argument requis manquant
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Argument manquant",
                description=f"La commande `{ctx.command.name}` nécessite l'argument `{error.param.name}`.\n\nUtilisez **=helps** pour voir la syntaxe correcte.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Argument invalide
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="Argument invalide",
                description=f"L'argument fourni est invalide.\n\nUtilisez **=helps** pour voir la syntaxe correcte de la commande `{ctx.command.name}`.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Commande en cooldown
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Commande en cooldown",
                description=f"Vous devez attendre **{error.retry_after:.1f}** secondes avant de réutiliser cette commande.",
                color=discord.Color.orange()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=error.retry_after)
            return
        
        # Commande réservée au propriétaire
        if isinstance(error, commands.NotOwner):
            embed = discord.Embed(
                title="Accès refusé",
                description="Cette commande est réservée au propriétaire du bot.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Commande uniquement en guild
        if isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="Commande non disponible",
                description="Cette commande ne peut pas être utilisée en message privé.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Erreur de check (pour les checks personnalisés)
        if isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="Vérification échouée",
                description="Vous ne remplissez pas les conditions requises pour utiliser cette commande.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Erreur d'invocation (erreurs générales dans la commande)
        if isinstance(error, commands.CommandInvokeError):
            original_error = error.original
            # Gérer les erreurs Discord spécifiques
            if isinstance(original_error, discord.Forbidden):
                embed = discord.Embed(
                    title="Erreur de permissions",
                    description="Le bot n'a pas les permissions nécessaires pour effectuer cette action.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                try:
                    await ctx.send(embed=embed, delete_after=10)
                except:
                    pass
                return
            elif isinstance(original_error, discord.NotFound):
                embed = discord.Embed(
                    title="Ressource introuvable",
                    description="La ressource demandée n'a pas été trouvée.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                try:
                    await ctx.send(embed=embed, delete_after=10)
                except:
                    pass
                return
            else:
                # Autres erreurs - afficher un message générique
                embed = discord.Embed(
                    title="Erreur lors de l'exécution",
                    description="Une erreur s'est produite lors de l'exécution de la commande.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                try:
                    await ctx.send(embed=embed, delete_after=10)
                except:
                    pass
                # Logger l'erreur pour le débogage
                command_name = ctx.command.name if ctx.command else 'inconnue'
                print(f"\nErreur dans la commande {command_name}:")
                traceback.print_exception(type(original_error), original_error, original_error.__traceback__)
                return
        
        # Pour toutes les autres erreurs non gérées
        command_name = ctx.command.name if ctx.command else 'inconnue'
        print(f"\nErreur non gérée dans {command_name}:")
        traceback.print_exception(type(error), error, error.__traceback__)
    
    # Méthode pour gérer les erreurs des commandes slash (appelée depuis main.py)
    async def handle_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Gestionnaire d'erreurs global pour les commandes slash"""
        # Fonction helper pour répondre à l'interaction avec fallback
        async def send_error_embed(embed, use_channel_fallback=True):
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(embed=embed, ephemeral=True, wait=False)
                else:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            except (discord.NotFound, discord.HTTPException):
                # Webhook expiré ou erreur HTTP - essayer avec followup si pas déjà fait
                if not interaction.response.is_done():
                    try:
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    except:
                        pass
                
                # Si le fallback est activé et que le channel est disponible, envoyer un message normal
                if use_channel_fallback and interaction.channel:
                    try:
                        await interaction.channel.send(embed=embed, delete_after=10)
                    except:
                        pass
            except Exception:
                # Dernière tentative avec le channel si disponible
                if use_channel_fallback and interaction.channel:
                    try:
                        await interaction.channel.send(embed=embed, delete_after=10)
                    except:
                        pass
        
        command_name = interaction.command.name if interaction.command else 'inconnue'
        
        # Permissions manquantes pour l'utilisateur
        if isinstance(error, app_commands.MissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms_text = ", ".join(missing_perms)
            embed = discord.Embed(
                title="Permissions insuffisantes",
                description=f"Vous n'avez pas les permissions nécessaires pour utiliser cette commande.\n\n**Permissions requises:** {perms_text}",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await send_error_embed(embed)
            return
        
        # Permissions manquantes pour le bot
        if isinstance(error, app_commands.BotMissingPermissions):
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms_text = ", ".join(missing_perms)
            embed = discord.Embed(
                title="Permissions du bot insuffisantes",
                description=f"Le bot n'a pas les permissions nécessaires pour exécuter cette commande.\n\n**Permissions requises:** {perms_text}",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await send_error_embed(embed)
            return
        
        # Commande en cooldown
        if isinstance(error, app_commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Commande en cooldown",
                description=f"Vous devez attendre **{error.retry_after:.1f}** secondes avant de réutiliser cette commande.",
                color=discord.Color.orange()
            )
            embed.set_footer(text=get_current_version(self.client))
            await send_error_embed(embed)
            return
        
        # Erreur de check
        if isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(
                title="Vérification échouée",
                description="Vous ne remplissez pas les conditions requises pour utiliser cette commande.",
                color=discord.Color.red()
            )
            embed.set_footer(text=get_current_version(self.client))
            await send_error_embed(embed)
            return
        
        # Erreur d'invocation
        if isinstance(error, app_commands.CommandInvokeError):
            original_error = error.original
            
            # Gérer les erreurs Discord spécifiques
            if isinstance(original_error, discord.Forbidden):
                embed = discord.Embed(
                    title="Erreur de permissions",
                    description="Le bot n'a pas les permissions nécessaires pour effectuer cette action.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await send_error_embed(embed)
                return
            elif isinstance(original_error, discord.NotFound):
                # Erreur 404 - peut être due à un webhook expiré ou une ressource supprimée
                error_code = getattr(original_error, 'code', None)
                if error_code == 10008:
                    # Webhook expiré - ne pas afficher d'erreur car la commande a probablement réussi
                    print(f"Webhook expiré pour la commande {command_name} (code 10008) - géré par la commande")
                    return
                else:
                    embed = discord.Embed(
                        title="Ressource introuvable",
                        description="La ressource demandée n'a pas été trouvée.",
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=get_current_version(self.client))
                    await send_error_embed(embed, use_channel_fallback=True)
                    return
            elif isinstance(original_error, discord.HTTPException):
                embed = discord.Embed(
                    title="Erreur HTTP",
                    description=f"Une erreur HTTP s'est produite: {str(original_error)}",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await send_error_embed(embed)
                print(f"\nErreur HTTP dans la commande slash {command_name}:")
                traceback.print_exception(type(original_error), original_error, original_error.__traceback__)
                return
            elif isinstance(original_error, (ValueError, TypeError, AttributeError, KeyError, FileNotFoundError)):
                error_type = type(original_error).__name__
                error_messages = {
                    'ValueError': "La valeur fournie est invalide",
                    'TypeError': "Le type fourni est invalide",
                    'AttributeError': "Une erreur s'est produite lors de l'accès à un attribut",
                    'KeyError': "Une clé nécessaire n'a pas été trouvée",
                    'FileNotFoundError': "Un fichier nécessaire n'a pas été trouvé"
                }
                embed = discord.Embed(
                    title=error_type,
                    description=error_messages.get(error_type, f"Une erreur s'est produite: {str(original_error)}"),
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await send_error_embed(embed)
                if error_type in ['AttributeError', 'KeyError', 'FileNotFoundError']:
                    print(f"\nErreur {error_type} dans la commande slash {command_name}:")
                    traceback.print_exception(type(original_error), original_error, original_error.__traceback__)
                return
            else:
                # Autres erreurs
                embed = discord.Embed(
                    title="Erreur lors de l'exécution",
                    description="Une erreur s'est produite lors de l'exécution de la commande.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=get_current_version(self.client))
                await send_error_embed(embed)
                # Logger l'erreur pour le débogage
                print(f"\nErreur dans la commande slash {command_name}:")
                traceback.print_exception(type(original_error), original_error, original_error.__traceback__)
                return
        
        # Pour toutes les autres erreurs non gérées
        embed = discord.Embed(
            title="Erreur",
            description="Une erreur inattendue s'est produite.",
            color=discord.Color.red()
        )
        embed.set_footer(text=get_current_version(self.client))
        await send_error_embed(embed)
        print(f"\nErreur non gérée dans la commande slash {command_name}:")
        traceback.print_exception(type(error), error, error.__traceback__)

async def setup(client):
    await client.add_cog(ErrorHandler(client))

