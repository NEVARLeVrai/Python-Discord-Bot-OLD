import discord
from discord.ext import commands
import asyncio
import io
from cogs.Help import get_current_version

class Owner(commands.Cog):
    """Commandes réservées au propriétaire du bot"""
    def __init__(self, client):
        self.client = client
    
    # Commande pour re-synchroniser les commandes slash
    @commands.command(name="sync", aliases=["syncslash", "reloadslash"])
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Re-synchronise les commandes slash (owner only)"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        
        try:
            # Message intermédiaire
            embed = discord.Embed(
                title="🔄 Synchronisation en cours...",
                description="Synchronisation des commandes slash...",
                color=discord.Color.orange()
            )
            embed.set_footer(text=get_current_version(self.client))
            status_msg = await ctx.send(embed=embed)
            
            # Synchroniser sur le serveur actuel
            synced_guild = await self.client.tree.sync(guild=ctx.guild)
            # Synchroniser globalement
            synced_global = await self.client.tree.sync()
            
            success_embed = discord.Embed(
                title="✓ Synchronisation réussie",
                description=f"Commandes synchronisées sur '{ctx.guild.name}'",
                color=discord.Color.green()
            )
            
            if synced_guild or synced_global:
                count = len(synced_guild) if synced_guild else len(synced_global) if synced_global else 0
                success_embed.add_field(
                    name="Commandes synchronisées",
                    value=f"{count} commande(s) disponible(s)",
                    inline=False
                )
            
            success_embed.set_footer(text=get_current_version(self.client))
            await status_msg.edit(embed=success_embed)
            
            # Supprimer le message après 10 secondes
            await asyncio.sleep(10)
            try:
                await status_msg.delete()
            except:
                pass
                
        except Exception as e:
            error_embed = discord.Embed(
                title="✗ Erreur de synchronisation",
                description=f"Erreur: {str(e)}",
                color=discord.Color.red()
            )
            error_embed.set_footer(text=get_current_version(self.client))
            try:
                await status_msg.edit(embed=error_embed)
                await asyncio.sleep(10)
                try:
                    await status_msg.delete()
                except:
                    pass
            except:
                await ctx.send(embed=error_embed, delete_after=10)

    # Commande pour diagnostiquer les problèmes de commandes slash
    @commands.command(name="slashinfo", aliases=["slashdebug", "cmdinfo"])
    @commands.is_owner()
    async def slash_info(self, ctx):
        """Affiche des informations de diagnostic sur les commandes slash (owner only)"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        
        embed = discord.Embed(
            title="🔍 Diagnostic des Commandes Slash",
            color=discord.Color.blue()
        )
        
        # Informations du bot
        embed.add_field(
            name="Bot Information",
            value=f"**Nom:** {self.client.user.name}\n**ID:** {self.client.user.id}",
            inline=False
        )
        
        # Commandes locales
        local_commands = []
        try:
            commands_list = self.client.tree.get_commands()
            for cmd in commands_list:
                local_commands.append(cmd.name)
        except:
            pass
        
        embed.add_field(
            name="Commandes Enregistrées",
            value=f"{len(local_commands)} commande(s): {', '.join([f'`/{cmd}`' for cmd in local_commands]) if local_commands else 'Aucune'}", 
            inline=False
        )
        
        # Lien d'invitation
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.client.user.id}&permissions=8&scope=bot%20applications.commands"
        embed.add_field(
            name="🔗 Lien d'Invitation",
            value=f"[Cliquez ici]({invite_url})",
            inline=False
        )
        
        embed.set_footer(text=get_current_version(self.client))
        await ctx.send(embed=embed, delete_after=30)

    # Commande pour effacer toutes les commandes slash
    @commands.command(name="clearslash", aliases=["clearslashcommands", "deleteslash"])
    @commands.is_owner()
    async def clear_slash_commands(self, ctx):
        """Efface toutes les commandes slash de Discord (owner only)"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        
        status_msg = None
        try:
            # Message intermédiaire
            embed = discord.Embed(
                title="🗑️ Suppression des commandes slash",
                description="Suppression en cours...",
                color=discord.Color.orange()
            )
            embed.set_footer(text=get_current_version(self.client))
            status_msg = await ctx.send(embed=embed)
            
            # Obtenir l'application ID pour compter les commandes avant suppression
            app_info = await self.client.application_info()
            application_id = app_info.id
            
            # Compter les commandes avant suppression
            try:
                global_commands_before = await self.client.http.get_global_commands(application_id)
                count_global_before = len(global_commands_before)
            except:
                count_global_before = 0
            
            guild_counts_before = {}
            for guild in self.client.guilds:
                try:
                    guild_commands = await self.client.http.get_guild_commands(application_id, guild.id)
                    guild_counts_before[guild.id] = len(guild_commands)
                except:
                    guild_counts_before[guild.id] = 0
            
            # Méthode recommandée : clear_commands() puis sync()
            # Cette méthode synchronise un arbre vide, ce qui supprime toutes les commandes
            
            # 1. Effacer les commandes globales
            self.client.tree.clear_commands(guild=None)
            await self.client.tree.sync(guild=None)
            
            # 2. Effacer les commandes par serveur
            synced_guilds = 0
            for guild in self.client.guilds:
                try:
                    self.client.tree.clear_commands(guild=guild)
                    await self.client.tree.sync(guild=guild)
                    synced_guilds += 1
                except Exception:
                    continue
            
            # Vérifier que les commandes ont bien été supprimées
            try:
                global_commands_after = await self.client.http.get_global_commands(application_id)
                count_global_after = len(global_commands_after)
            except:
                count_global_after = 0
            
            total_deleted_global = count_global_before - count_global_after
            total_deleted_guild = sum(guild_counts_before.values())
            
            # Créer l'embed de résultat
            success_embed = discord.Embed(
                title="✅ Commandes slash supprimées",
                description="Toutes les commandes slash ont été supprimées.",
                color=discord.Color.green()
            )
            
            if count_global_before > 0:
                success_embed.add_field(
                    name="Commandes globales",
                    value=f"{count_global_before} → {count_global_after} (supprimées: {total_deleted_global})",
                    inline=False
                )
            
            if sum(guild_counts_before.values()) > 0:
                success_embed.add_field(
                    name="Commandes par serveur",
                    value=f"Supprimées de {synced_guilds} serveur(s)",
                    inline=False
                )
            
            success_embed.add_field(
                name="⚠️ Important",
                value="Les commandes ont été supprimées. **Redémarrez Discord** ou attendez quelques minutes pour que les changements soient visibles. Les commandes peuvent rester en cache côté client Discord.",
                inline=False
            )
            
            success_embed.set_footer(text=get_current_version(self.client))
            await status_msg.edit(embed=success_embed)
            
            # Supprimer le message après 10 secondes
            await asyncio.sleep(10)
            try:
                await status_msg.delete()
            except:
                pass
            
        except Exception as e:
            error_embed = discord.Embed(
                title="✗ Erreur de suppression",
                description=f"Erreur: {str(e)}",
                color=discord.Color.red()
            )
            error_embed.set_footer(text=get_current_version(self.client))
            try:
                if status_msg:
                    await status_msg.edit(embed=error_embed)
                    await asyncio.sleep(10)
                    try:
                        await status_msg.delete()
                    except:
                        pass
                else:
                    await ctx.send(embed=error_embed, delete_after=10)
            except:
                await ctx.send(embed=error_embed, delete_after=10)

    # Commande pour arrêter le bot
    @commands.command()
    @commands.is_owner()
    async def stop(self, ctx):
        """Arrête le bot (owner only)"""
        await ctx.message.delete()
        bot_latency = round(self.client.latency * 1000)
        embed = discord.Embed(title="Arrêt", description=f"Le Bot s'arrête Ping {bot_latency} ms.", color=discord.Color.red())
        embed.set_footer(text=get_current_version(self.client))
        with open(self.client.paths['hilaire2_png'], "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://hilaire2.png")
        embed.set_image(url=ctx.guild.icon)
        await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), "hilaire2.png"))
        print("")
        print("Arrêté par l'utilisateur")
        print("")
        await self.client.close()

async def setup(client):
    await client.add_cog(Owner(client))

