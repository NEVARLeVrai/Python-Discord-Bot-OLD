import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
from cogs import Help
from cogs.Help import get_current_version

class Leveling_slash(commands.Cog):
    def __init__(self, client):
        self.client = client
        # Récupérer le cog Leveling original pour partager les données
        self.leveling_cog = None
        self.is_leveling_enabled = False
        # Initialiser levels dès le début pour éviter les erreurs
        self.levels = {}
    
    async def cog_load(self):
        # Ne rien faire ici, on attendra on_ready()
        pass
    
    @commands.Cog.listener()
    async def on_ready(self):
        # Récupérer le cog Leveling original après que tous les cogs soient prêts
        # Attendre un peu pour que tous les cogs soient complètement initialisés
        await asyncio.sleep(2)
        self.leveling_cog = self.client.get_cog('Leveling')
        if self.leveling_cog:
            # Synchroniser les données du cog Leveling
            if hasattr(self.leveling_cog, 'is_leveling_enabled'):
                self.is_leveling_enabled = self.leveling_cog.is_leveling_enabled
            # Synchroniser les levels avec le cog original
            if hasattr(self.leveling_cog, 'levels'):
                self.levels = self.leveling_cog.levels
                print(f"Leveling_slash: Système de levels synchronisé depuis le cog Leveling. {len(self.levels)} utilisateur(s) avec des levels.")
        else:
            print("Leveling_slash: ATTENTION - Le cog Leveling n'a pas été trouvé! Chargement depuis le fichier JSON...")
            # Charger depuis le fichier JSON si le cog n'est pas disponible
            self._load_from_files()
    
    def _load_from_files(self):
        """Charge les données depuis le fichier JSON si le cog n'est pas disponible"""
        try:
            levels_path = self.client.paths['levels_json']
            if os.path.exists(levels_path):
                with open(levels_path, 'r', encoding='utf-8') as f:
                    self.levels = json.load(f)
                    print(f"Leveling_slash: Levels chargés depuis le fichier. {len(self.levels)} utilisateur(s) avec des levels.")
            else:
                self.levels = {}
                print("Leveling_slash: Fichier levels.json introuvable, initialisation d'un dictionnaire vide.")
        except Exception as e:
            print(f"Leveling_slash: Erreur lors du chargement des levels depuis le fichier: {e}")
            self.levels = {}
    
    def get_leveling_cog(self):
        """Récupère le cog Leveling de manière robuste"""
        if not self.leveling_cog:
            self.leveling_cog = self.client.get_cog('Leveling')
            # Si le cog n'est toujours pas disponible, charger depuis les fichiers
            if not self.leveling_cog:
                self._load_from_files()
        
        # Toujours s'assurer que le cog Leveling a les attributs nécessaires initialisés
        if self.leveling_cog:
            self._ensure_leveling_cog_initialized()
        
        return self.leveling_cog
    
    def _ensure_leveling_cog_initialized(self):
        """S'assure que le cog Leveling a tous ses attributs initialisés"""
        if not self.leveling_cog:
            return
        
        # Vérifier et initialiser levels si nécessaire
        if not hasattr(self.leveling_cog, 'levels') or self.leveling_cog.levels is None:
            try:
                levels_path = self.client.paths['levels_json']
                if os.path.exists(levels_path):
                    with open(levels_path, 'r', encoding='utf-8') as f:
                        self.leveling_cog.levels = json.load(f)
                else:
                    self.leveling_cog.levels = {}
            except Exception as e:
                print(f"Erreur lors du chargement des levels dans le cog Leveling: {e}")
                self.leveling_cog.levels = {}
    
    def ensure_levels_loaded(self):
        """S'assure que les levels sont chargés"""
        if not self.levels:
            leveling_cog = self.get_leveling_cog()
            if leveling_cog and hasattr(leveling_cog, 'levels'):
                self.levels = leveling_cog.levels
            elif not self.levels:
                self._load_from_files()

    def save_levels(self):
        """Sauvegarde les niveaux dans le fichier JSON"""
        if self.leveling_cog:
            self.leveling_cog.levels = self.levels
            # Le cog Leveling sauvegarde automatiquement dans on_message
        else:
            # Sauvegarder directement dans le fichier
            try:
                levels_path = self.client.paths['levels_json']
                with open(levels_path, 'w', encoding='utf-8') as f:
                    json.dump(self.levels, f, indent=2)
            except Exception as e:
                print(f"Leveling_slash: Erreur lors de la sauvegarde des levels: {e}")

    @app_commands.command(name="level", description="Affiche le niveau d'un utilisateur")
    @app_commands.describe(member="L'utilisateur dont vous voulez voir le niveau (optionnel)")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        """Affiche le niveau d'un utilisateur"""
        # S'assurer que les levels sont chargés
        self.ensure_levels_loaded()
        
        if not hasattr(self, 'levels') or self.levels is None:
            await interaction.response.send_message("Le système de levels n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        member = member or interaction.user
        author_id = str(member.id)

        if author_id not in self.levels:
            embed = discord.Embed(title=f"L'utilisateur **{member.display_name}** n'a pas encore de niveau", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        level = self.levels[author_id]['level']
        experience = self.levels[author_id]['experience']
        exp_needed = (level + 1) ** 2 - experience

        embed = discord.Embed(title=f"Niveau de {member.display_name}", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.add_field(name="Niveau", value=level)
        embed.add_field(name="Expérience", value=f"{experience}/{(level + 1) ** 2}")
        embed.add_field(name="Expérience nécessaire pour le prochain niveau", value=exp_needed)
        embed.set_footer(text=get_current_version(self.client))

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="resetlevel", description="Reset tous les niveaux")
    @app_commands.describe(confirm="Tapez 'oui' pour confirmer (requis)")
    @app_commands.default_permissions(manage_messages=True)
    async def resetlevel(self, interaction: discord.Interaction, confirm: str):
        """Reset tous les niveaux"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("Vous n'avez pas la permission de gérer les messages.", ephemeral=True)
            return
        
        if confirm.lower() != "oui":
            embed = discord.Embed(title="Commande annulée", description="Vous devez écrire 'oui' pour confirmer.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # S'assurer que les levels sont chargés
        self.ensure_levels_loaded()
        
        if not hasattr(self, 'levels') or self.levels is None:
            await interaction.response.send_message("Le système de levels n'est pas disponible. Veuillez réessayer dans quelques secondes.", ephemeral=True)
            return
        
        # Synchroniser avec le cog si disponible
        leveling_cog = self.get_leveling_cog()
        if leveling_cog and hasattr(leveling_cog, 'levels'):
            self.leveling_cog = leveling_cog
        
        self.levels = {}
        self.save_levels()
        
        # Synchroniser avec le cog si disponible
        if self.leveling_cog:
            self.leveling_cog.levels = self.levels
        
        embed = discord.Embed(title="Réinitialisation", description="Tous les niveaux ont été réinitialisés.", color=discord.Color.yellow())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=get_current_version(self.client))
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="levelsettings", description="Active/désactive le système de leveling")
    @app_commands.default_permissions(administrator=True)
    async def levelsettings(self, interaction: discord.Interaction):
        """Active/désactive le système de leveling"""
        # Vérifier les permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Cette commande nécessite les permissions administrateur.", ephemeral=True)
            return
        
        # S'assurer que le cog est chargé
        leveling_cog = self.get_leveling_cog()
        
        if leveling_cog and hasattr(leveling_cog, 'is_leveling_enabled'):
            self.leveling_cog = leveling_cog
            self.leveling_cog.is_leveling_enabled = not self.leveling_cog.is_leveling_enabled
            self.is_leveling_enabled = self.leveling_cog.is_leveling_enabled
        else:
            self.is_leveling_enabled = not self.is_leveling_enabled
        
        if self.is_leveling_enabled:
            embed = discord.Embed(title="Paramètre des levels", description=f"Leveling est maintenant activé.", color=discord.Color.green())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="Paramètre des levels", description=f"Leveling est maintenant désactivé.", color=discord.Color.red())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="levelboard", description="Affiche le leaderboard des levels")
    async def levelboard(self, interaction: discord.Interaction):
        """Affiche le leaderboard des levels"""
        # S'assurer que les levels sont chargés
        self.ensure_levels_loaded()
        
        if not hasattr(self, 'levels') or self.levels is None or len(self.levels) == 0:
            embed = discord.Embed(title="Leaderboard des Levels", description="Aucun niveau enregistré.", color=discord.Color.blue())
            embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
            embed.set_footer(text=get_current_version(self.client))
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return
        
        await interaction.response.defer(ephemeral=False)
        
        # Synchroniser avec le cog si disponible
        leveling_cog = self.get_leveling_cog()
        if leveling_cog and hasattr(leveling_cog, 'levels'):
            self.leveling_cog = leveling_cog
            self.levels = leveling_cog.levels
        
        # Récupérer tous les utilisateurs avec leurs levels et les trier
        level_list = []
        for user_id, level_data in self.levels.items():
            level = level_data.get("level", 0)
            experience = level_data.get("experience", 0)
            if level > 0 or experience > 0:
                try:
                    member = interaction.guild.get_member(int(user_id))
                    if member:
                        level_list.append((member, level, experience))
                    else:
                        # Si l'utilisateur n'est plus sur le serveur, on l'affiche quand même
                        level_list.append((None, level, experience, user_id))
                except (ValueError, AttributeError):
                    level_list.append((None, level, experience, user_id))
        
        # Trier par niveau décroissant, puis par expérience décroissante
        level_list.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Prendre les top 10
        top_levels = level_list[:10]
        
        # Créer l'embed
        embed = discord.Embed(title="🏆 Leaderboard des Levels", description="Top 10 des utilisateurs avec le plus haut niveau", color=discord.Color.blue())
        embed.set_author(name=f"Demandé par {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_footer(text=get_current_version(self.client))
        
        # Ajouter les résultats
        if top_levels:
            leaderboard_text = ""
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for idx, entry in enumerate(top_levels):
                medal = medals[idx] if idx < len(medals) else f"{idx+1}."
                
                if len(entry) == 4:  # Utilisateur qui n'est plus sur le serveur
                    user_id = entry[3]
                    level = entry[1]
                    experience = entry[2]
                    leaderboard_text += f"{medal} **Utilisateur inconnu** (ID: {user_id}) - Niveau {level} ({experience} XP)\n"
                else:
                    member = entry[0]
                    level = entry[1]
                    experience = entry[2]
                    leaderboard_text += f"{medal} {member.mention} - Niveau {level} ({experience} XP)\n"
            
            embed.add_field(name="Classement", value=leaderboard_text, inline=False)
        else:
            embed.add_field(name="Classement", value="Aucun utilisateur avec des niveaux.", inline=False)
        
        await interaction.followup.send(embed=embed)


async def setup(client):
    await client.add_cog(Leveling_slash(client))

