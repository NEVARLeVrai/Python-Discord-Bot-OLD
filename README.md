# Bot Discord Python

Un bot Discord complet avec de nombreuses fonctionnalités, développé en Python avec discord.py.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Structure du projet](#-structure-du-projet)
- [Version](#-version)
- [Commandes slash](#-commandes-slash)
- [Notes](#-notes)
- [Avertissements](#️-avertissements)
- [Signalement de bugs](#-signalement-de-bugs)

## 🚀 Fonctionnalités

### Commandes générales
- **`=helps`** - Affiche toutes les commandes disponibles
- **`=ping`** - Affiche le ping du bot en ms
- **`/ping`** - Commande slash pour afficher le ping
- **`=version`** ou **`=v`** - Affiche la version du bot
- **`=report [message]`** - Signale un bug ou donne un feedback
- **`=stop`** - Arrête le bot (owner only)

### Modération (Mods)
- **`=clear [nombre]`** - Supprime des messages (max 70, messages perms)
- **`=warn [@user] [raison] [nombre]`** - Avertit un membre (messages perms)
- **`=resetwarn [@user]`** - Reset les warns d'un membre (messages perms)
- **`=warnboard`** - Affiche le leaderboard des warns
- **`=kick [@user] [raison]`** - Expulse un membre (kick perms)
- **`=ban [@user ou ID] [raison]`** - Bannit un membre (ban perms)
- **`=unban [ID]`** - Débannit un membre (ban perms)
- **`=cleanraidsimple [nom]`** - Supprime un salon par nom (messages perms)
- **`=cleanraidmultiple [date] [heure]`** - Supprime des salons par date (messages perms)
- **`=giverole [@user] [@role]`** - Donne un rôle (owner only)
- **`=removerole [@user] [@role]`** - Enlève un rôle (owner only)
- **`=mp [@user ou ID] [message]`** - Envoie un message privé
- **`=spam [nombre] [#salon ou mention] [message]`** - Spam des messages (admin perms)

### Utilitaire (Utility)
- **`=gpt [question]`** - Utilise GPT pour répondre à une question
- **`=dalle [prompt]`** - Génère une image avec DALL-E
- **`=repeat [#salon ou @user] [message]`** - Envoie un message
- **`=8ball [question]`** - Pose une question à la boule magique
- **`=hilaire`** - Jeu Hilaire
- **`=deldms`** - Supprime tous les DMs du bot (admin perms)
- **`=tts [langue] [volume] [texte]`** - Fait parler le bot (ex: `=tts fr 3.0 Bonjour`)

### Soundboard
- **`=slist`** - Liste tous les sons disponibles
- **`=splay [numéro]`** - Joue un son (ex: `=splay 1`)
- **`=sjoin`** - Fait rejoindre le bot au salon vocal (besoin d'être en vocal)
- **`=sleave`** - Fait quitter le bot du salon vocal
- **`=sstop`** - Arrête le son en cours
- **`=srandom`** - Joue des sons aléatoires toutes les 1-5 minutes
- **`=srandomskip`** - Skip le son aléatoire en cours
- **`=srandomstop`** - Arrête la lecture aléatoire
- **`=vkick [@user]`** - Expulse un utilisateur du vocal (admin perms)

### YouTube
- **`=play [URL]`** - Joue une vidéo YouTube
- **`=search [recherche]`** - Recherche une vidéo YouTube
- **`=skip`** - Skip la vidéo en cours
- **`=stopm`** - Arrête la lecture
- **`=pause`** - Met en pause la vidéo
- **`=resume`** - Reprend la vidéo
- **`=queue`** - Affiche la file d'attente
- **`=clearq`** - Vide la file d'attente
- **`=loop`** - Active/désactive la boucle
- **`=leave`** - Déconnecte le bot du vocal

### Leveling
- **`=level [@user]`** - Voir votre niveau ou celui d'un utilisateur (optionnel)
- **`=resetlevel`** - Reset tous les niveaux (messages perms)
- **`=levelsettings`** - Active/désactive le système de leveling (admins perms)

### Système de warns automatique
Le bot applique automatiquement des sanctions selon le nombre de warns :
- **5 warns** : Timeout de 10 minutes
- **10 warns** : Timeout de 10 minutes
- **15 warns** : Kick automatique
- **20 warns** : Ban automatique

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur
- FFmpeg (pour les fonctionnalités audio)
- Token Discord Bot
- Token OpenAI (pour GPT et DALL-E)

### Étapes d'installation

1. **Cloner le repository** (ou télécharger les fichiers)
   ```bash
   git clone <repository-url>
   cd bot_discord
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les chemins**
   
   Modifiez les chemins dans `main.py` selon votre configuration :
   ```python
   PATHS = {
       'token_file': "chemin/vers/token.txt",
       'gpt_token_file': "chemin/vers/tokengpt.txt",
       'ffmpeg_exe': "chemin/vers/ffmpeg.exe",
       # ... autres chemins
   }
   ```

4. **Créer les fichiers nécessaires**
   - `token.txt` - Contient le token Discord du bot
   - `tokengpt.txt` - Contient le token OpenAI
   - Dossier `Sounds/` - Pour les fichiers audio du soundboard

5. **Lancer le bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Invitation du bot
Assurez-vous d'inviter le bot avec les scopes suivants :
- `bot`
- `applications.commands`

### Permissions requises
- Lire les messages
- Envoyer des messages
- Gérer les messages
- Expulser des membres
- Bannir des membres
- Se connecter (aux salons vocaux)
- Parler (dans les salons vocaux)
- Utiliser la commande de détection d'activité externe

### Configuration dans `main.py`

Le bot utilise un système de configuration centralisée :

```python
PATHS = {
    'token_file': "...",
    'gpt_token_file': "...",
    'ffmpeg_exe': "...",
    # Chemins vers les fichiers de données
    'warns_json': "./Autres/warns.json",
    'levels_json': "./Autres/levels.json",
    # Chemins vers les images
    'hilaire2_png': "./Autres/hilaire2.png",
    # ...
}

CONFIG = {
    'webhook_url': "...",
    'target_user_id': 123456789,
}
```

## 📁 Structure du projet

```
bot_discord/
├── main.py                 # Fichier principal du bot
├── requirements.txt        # Dépendances Python
├── cogs/                   # Modules (cogs) du bot
│   ├── Help.py            # Commandes d'aide et version
│   ├── Mods.py            # Commandes de modération
│   ├── Utility.py         # Commandes utilitaires (GPT, DALL-E, etc.)
│   ├── Soundboard.py      # Commandes du soundboard
│   ├── Youtube.py         # Commandes YouTube
│   ├── Leveling.py        # Système de niveaux
│   └── Test.py            # Cog de test
├── Autres/                # Fichiers de données et ressources
│   ├── warns.json         # Données des warns
│   ├── levels.json        # Données des niveaux
│   └── *.png, *.jpg       # Images du bot
└── Sounds/                # Fichiers audio pour le soundboard
```

## 📝 Version

**Version actuelle :** Bot V.2910-25

**Update Logs :** `optimization, fixed bugs and added new commands`

## 🔧 Commandes slash

Le bot supporte les commandes slash Discord. Notez que les commandes slash peuvent prendre jusqu'à 1 heure pour apparaître après la synchronisation.

Commandes slash disponibles :
- `/ping` - Affiche le ping du bot

## 📝 Notes

- Les commandes peuvent être utilisées en MP (message privé) selon les permissions
- Le bot supprime automatiquement les commandes après leur exécution dans les salons textuels
- Le système de leveling peut être activé/désactivé par les administrateurs
- Les liens TikTok, Instagram, Twitter/X sont automatiquement convertis en formats compatibles

## ⚠️ Avertissements

- Assurez-vous d'avoir les permissions nécessaires pour utiliser les commandes de modération
- Le token du bot et les tokens API doivent être gardés secrets
- Certaines commandes nécessitent des permissions spécifiques (voir la description de chaque commande)

## 🐛 Signalement de bugs

Utilisez la commande `=report [message]` pour signaler un bug ou donner un feedback. Un ticket sera automatiquement créé et envoyé au développeur.

---

Développé avec ❤️ en Python par [NEVAR](https://github.com/NEVARLeVrai)