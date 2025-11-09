# Bot Discord Python

Un bot Discord complet avec de nombreuses fonctionnalités, développé en Python avec discord.py.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Structure du projet](#-structure-du-projet)
- [Version](#-version)
- [Commandes slash](#-commandes-slash)
- [Gestion des erreurs](#️-gestion-des-erreurs)
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
- **`=banword [mot]`** ou **`=addbannedword [mot]`** - Ajoute un mot à la liste des mots bannis (messages perms)
- **`=unbanword [mot]`** ou **`=removebannedword [mot]`** - Retire un mot de la liste des mots bannis (messages perms)
- **`=listbannedwords`** ou **`=bannedwords`** ou **`=bwlist`** - Affiche la liste des mots bannis (messages perms)

### Utilitaire (Utility)
- **`=gpt [question]`** - Utilise GPT pour répondre à une question
- **`=dalle [prompt]`** - Génère une image avec DALL-E
- **`=repeat [#salon ou @user] [message]`** - Envoie un message
- **`=8ball [question]`** - Pose une question à la boule magique
- **`=hilaire`** - Jeu Hilaire
- **`=deldms`** - Supprime tous les DMs du bot (admin perms)
- **`=tts [langue] [volume] [texte]`** - Fait parler le bot (ex: `=tts fr 3.0 Bonjour`)

### Conversion automatique des liens
Le bot convertit automatiquement les liens des réseaux sociaux pour un meilleur affichage dans Discord :
- **TikTok** → `tiktokez.com`
  - Résout automatiquement les liens courts (`vm.tiktok.com`) vers les liens PC complets
  - Supprime les paramètres de requête (`?is_from_webapp=1`, etc.)
  - Supprime le préfixe `www.` pour des liens plus propres
  - Les liens courts sont automatiquement convertis en liens PC avant la transformation
- **Instagram** → `eeinstagram.com`
  - Supprime les paramètres de requête
  - Ne traite pas les liens `/reels/audio/`
- **Twitter/X** → `fxtwitter.com`
  - Convertit les liens `twitter.com` et `x.com` vers `fxtwitter.com`
- **Reddit** → `vxreddit.com`
  - Résout automatiquement les liens courts (`redd.it`) vers les liens PC complets
  - Conserve le préfixe `www.` si présent
  - Supprime les paramètres de requête

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

### Système de mots bannis
Le bot peut automatiquement supprimer les messages contenant des mots interdits :
- Les mots bannis sont stockés dans un fichier JSON (`banned_words.json`)
- Les messages contenant des mots bannis sont automatiquement supprimés
- L'utilisateur reçoit un message privé indiquant le mot interdit détecté
- Tous les utilisateurs sont soumis à ce système (y compris les modérateurs)
- Les commandes ne sont pas bloquées par ce système
- Les modifications (ajout/suppression de mots) sont prises en compte en temps réel, comme pour les warns et levels

## 📦 Installation

### Prérequis
- Python 3.8 ou supérieur
- FFmpeg (pour les fonctionnalités audio)
- Token Discord Bot
- Token OpenAI (pour GPT et DALL-E)
- aiohttp (pour la résolution des liens courts des réseaux sociaux)

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
    'banned_words_json': "./Autres/banned_words.json",
    # Chemins vers les images
    'hilaire2_png': "./Autres/hilaire2.png",
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
│   ├── banned_words.json  # Liste des mots bannis
│   └── *.png, *.jpg       # Images du bot
└── Sounds/                # Fichiers audio pour le soundboard
```

## 📝 Version

**Version actuelle :** Bot V.0912-25

**Status :** 🟢 Stable

**Update Logs :** 
- Refactoring complet du code, optimisation et amélioration de la structure
- Ajout de la résolution automatique des liens courts (TikTok, Reddit)
- Conversion améliorée des liens vers des services d'embed optimisés
- Utilisation d'aiohttp pour des requêtes HTTP asynchrones non-bloquantes
- **Ajout d'un système complet de gestion des erreurs avec messages en français**
- Messages d'erreur cohérents et informatifs pour toutes les commandes
- Gestion centralisée des erreurs (permissions, arguments, cooldowns, etc.)

## 🔧 Commandes slash

Le bot supporte les commandes slash Discord. Notez que les commandes slash peuvent prendre jusqu'à 1 heure pour apparaître après la synchronisation.

Commandes slash disponibles :
- `/ping` - Affiche le ping du bot

## 🛡️ Gestion des erreurs

Le bot inclut un système complet de gestion des erreurs qui fournit des messages clairs et informatifs en français pour toutes les erreurs possibles.

### Types d'erreurs gérées

#### Commandes prefix (`=commande`)
- **Commande inconnue** - Message d'aide avec suggestion d'utiliser `=helps`
- **Permissions insuffisantes** - Liste des permissions manquantes pour l'utilisateur
- **Permissions du bot insuffisantes** - Liste des permissions manquantes pour le bot
- **Argument manquant** - Indication de l'argument requis manquant
- **Argument invalide** - Message d'erreur avec suggestion de vérifier la syntaxe
- **Commande en cooldown** - Affichage du temps d'attente restant
- **Commande réservée au propriétaire** - Message d'accès refusé
- **Commande non disponible en MP** - Indication que la commande ne fonctionne que dans un serveur
- **Erreurs d'exécution** - Gestion des erreurs Discord (Forbidden, NotFound, etc.)

#### Commandes slash (`/commande`)
- Même gestion que les commandes prefix
- Messages en mode `ephemeral` (visibles uniquement par l'utilisateur qui a exécuté la commande)

### Fonctionnalités
- ✅ Messages d'erreur en français avec embeds Discord
- ✅ Suppression automatique des messages de commande dans les channels texte
- ✅ Logging des erreurs dans la console pour le débogage
- ✅ Messages avec suppression automatique après 10 secondes
- ✅ Gestion centralisée et cohérente de toutes les erreurs

### Exemple de messages d'erreur

Lorsqu'une erreur survient, le bot affiche un embed Discord avec :
- Un titre clair indiquant le type d'erreur
- Une description détaillée en français
- Les informations spécifiques (permissions requises, argument manquant, etc.)
- Le footer avec la version du bot

**Exemple :**
```
┌─────────────────────────────────────┐
│  Permissions insuffisantes          │
│                                     │
│  Vous n'avez pas les permissions    │
│  nécessaires pour utiliser cette    │
│  commande.                          │
│                                     │
│  Permissions requises:              │
│  Manage Messages, Kick Members      │
└─────────────────────────────────────┘
```

### Avantages
- **Expérience utilisateur améliorée** - Les utilisateurs comprennent immédiatement pourquoi une commande a échoué
- **Cohérence** - Tous les messages d'erreur suivent le même format et sont en français
- **Débogage facilité** - Les erreurs sont loggées dans la console pour le développement
- **Maintenance simplifiée** - Gestion centralisée dans un seul endroit (`main.py`)

## 📝 Notes

- Les commandes peuvent être utilisées en MP (message privé) selon les permissions
- Le bot supprime automatiquement les commandes après leur exécution dans les salons textuels
- Le système de leveling peut être activé/désactivé par les administrateurs
- Les liens TikTok, Instagram, Twitter/X et Reddit sont automatiquement convertis en formats compatibles pour un meilleur affichage dans Discord
- Le bot résout automatiquement les liens courts (comme `vm.tiktok.com` ou `redd.it`) vers leurs versions PC complètes avant la conversion
- Les paramètres de requête sont automatiquement supprimés pour des liens plus propres

## ⚠️ Avertissements

- Assurez-vous d'avoir les permissions nécessaires pour utiliser les commandes de modération
- Le token du bot et les tokens API doivent être gardés secrets
- Certaines commandes nécessitent des permissions spécifiques (voir la description de chaque commande)

## 🐛 Signalement de bugs

Utilisez la commande `=report [message]` pour signaler un bug ou donner un feedback. Un ticket sera automatiquement créé et envoyé au développeur.

---

Développé avec ❤️ en Python par [NEVAR](https://github.com/NEVARLeVrai)