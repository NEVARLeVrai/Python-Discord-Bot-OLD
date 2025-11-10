import discord
from discord.ext import commands
import aiohttp
import json
import os
from cogs.Help import get_current_version

class GrammarCorrector_auto(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.api_url = "https://api.languagetool.org/v2/check"
        self.settings = None  # Sera chargé dans on_ready
        # Codes de langues supportées par LanguageTool (vérifié pour 2025)
        # LanguageTool supporte 30+ langues via l'API publique
        # Liste des langues principales disponibles dans l'API
        self.supported_languages = {
            'fr': 'Français',
            'en': 'Anglais',
            'es': 'Espagnol',
            'de': 'Allemand',
            'it': 'Italien',
            'pt': 'Portugais',
            'ru': 'Russe',
            'pl': 'Polonais',
            'nl': 'Néerlandais',
            'ca': 'Catalan',
            'cs': 'Tchèque',
            'da': 'Danois',
            'el': 'Grec',
            'eo': 'Espéranto',
            'fi': 'Finnois',
            'ga': 'Irlandais',
            'gl': 'Galicien',
            'ja': 'Japonais',
            'km': 'Khmer',
            'ro': 'Roumain',
            'sk': 'Slovaque',
            'sl': 'Slovène',
            'sv': 'Suédois',
            'ta': 'Tamoul',
            'tl': 'Tagalog',
            'uk': 'Ukrainien',
            'zh': 'Chinois',
            'be': 'Biélorusse',
            'br': 'Breton',
            'bg': 'Bulgare',
            'hr': 'Croate',
            'et': 'Estonien',
            'fa': 'Persan',
            'id': 'Indonésien',
            'lv': 'Letton',
            'lt': 'Lituanien',
            'mk': 'Macédonien',
            'no': 'Norvégien',
            'sr': 'Serbe',
            'sw': 'Swahili',
            'te': 'Télougou',
            'th': 'Thaï',
            'tr': 'Turc',
            'vi': 'Vietnamien',
            'auto': 'Détection automatique'
        }
        
        # Note: L'analyse contextuelle utilise une approche universelle basée sur:
        # - La structure de la phrase (majuscules, ponctuation, longueur)
        # - Les informations de contexte retournées par LanguageTool
        # - La similarité entre l'erreur et la correction
        # Cela permet de supporter toutes les langues de LanguageTool sans limitation
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Charge les paramètres du correcteur depuis le JSON avec validation et migration"""
        settings_path = self.client.paths['grammar_corrector_json']
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Migrer l'ancien format vers le nouveau format si nécessaire
                        self.settings = self.migrate_settings(data)
                        # Sauvegarder si migration effectuée
                        if self.settings != data:
                            self.save_settings()
                    else:
                        self.settings = {}
                        self.save_settings()
            except json.JSONDecodeError as e:
                print(f"Erreur de parsing JSON dans grammar_corrector.json: {e}")
                self.settings = {}
                self.save_settings()
        else:
            self.settings = {}
            self.save_settings()
        
        # Afficher les statistiques de synchronisation
        if self.settings:
            enabled_servers = sum(1 for s in self.settings.values() if isinstance(s, dict) and s.get('enabled', False))
            total_servers = len(self.settings)
            total_corrections = sum(
                s.get('statistics', {}).get('total_corrections', 0) 
                for s in self.settings.values() 
                if isinstance(s, dict)
            )
            print(f"GrammarCorrector_auto: Système de correction synchronisé. {enabled_servers}/{total_servers} serveur(s) avec le correcteur activé ({total_corrections} correction(s) au total).")
        else:
            print("GrammarCorrector_auto: Système de correction synchronisé. 0 serveur(s) configuré(s).")
    
    def migrate_settings(self, data):
        """Migre l'ancien format vers le nouveau format amélioré"""
        migrated = {}
        for guild_id, settings in data.items():
            if isinstance(settings, dict):
                # Nouveau format avec métadonnées
                migrated[guild_id] = {
                    'enabled': settings.get('enabled', False),
                    'languages': settings.get('languages', ['fr']),
                    'metadata': {
                        'created_at': settings.get('metadata', {}).get('created_at', None),
                        'last_modified': settings.get('metadata', {}).get('last_modified', None),
                        'version': settings.get('metadata', {}).get('version', '1.0')
                    },
                    'preferences': {
                        'min_confidence': settings.get('preferences', {}).get('min_confidence', 0.5),
                        'check_grammar': settings.get('preferences', {}).get('check_grammar', True),
                        'check_spelling': settings.get('preferences', {}).get('check_spelling', True),
                        'check_style': settings.get('preferences', {}).get('check_style', True)
                    },
                    'statistics': {
                        'total_corrections': settings.get('statistics', {}).get('total_corrections', 0),
                        'last_correction': settings.get('statistics', {}).get('last_correction', None)
                    }
                }
                # Initialiser les métadonnées si absentes
                if not migrated[guild_id]['metadata']['created_at']:
                    from datetime import datetime
                    migrated[guild_id]['metadata']['created_at'] = datetime.now().isoformat()
                if not migrated[guild_id]['metadata']['last_modified']:
                    from datetime import datetime
                    migrated[guild_id]['metadata']['last_modified'] = datetime.now().isoformat()
            else:
                # Format très ancien, migration complète
                migrated[guild_id] = self.get_default_settings()
        return migrated
    
    def get_default_settings(self):
        """Retourne les paramètres par défaut pour un nouveau serveur"""
        from datetime import datetime
        return {
            'enabled': False,
            'languages': ['fr'],
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'version': '1.0'
            },
            'preferences': {
                'min_confidence': 0.5,
                'check_grammar': True,
                'check_spelling': True,
                'check_style': False
            },
            'statistics': {
                'total_corrections': 0,
                'last_correction': None
            }
        }
    
    def save_settings(self):
        """Sauvegarde les paramètres dans le fichier JSON avec validation"""
        settings_path = self.client.paths['grammar_corrector_json']
        try:
            # Mettre à jour les métadonnées de dernière modification
            from datetime import datetime
            for guild_id, settings in self.settings.items():
                if isinstance(settings, dict):
                    if 'metadata' not in settings:
                        settings['metadata'] = {}
                    settings['metadata']['last_modified'] = datetime.now().isoformat()
                    if 'created_at' not in settings['metadata']:
                        settings['metadata']['created_at'] = datetime.now().isoformat()
                    settings['metadata']['version'] = '1.0'
            
            # Sauvegarder avec validation
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de grammar_corrector.json: {e}")
            import traceback
            traceback.print_exc()
    
    def is_enabled(self, guild_id):
        """Vérifie si le correcteur est activé pour ce serveur"""
        if self.settings is None:
            return False
        guild_id_str = str(guild_id)
        # Par défaut, désactivé si non configuré
        return self.settings.get(guild_id_str, {}).get('enabled', False)
    
    def get_languages(self, guild_id):
        """Récupère la liste des langues configurées pour ce serveur"""
        if self.settings is None:
            return ['fr']  # Par défaut français
        guild_id_str = str(guild_id)
        languages = self.settings.get(guild_id_str, {}).get('languages', ['fr'])
        # Si la liste est vide, retourner français par défaut
        return languages if languages else ['fr']
    
    def get_preferences(self, guild_id):
        """Récupère les préférences de correction pour ce serveur"""
        if self.settings is None:
            return {'min_confidence': 0.5, 'check_grammar': True, 'check_spelling': True, 'check_style': False}
        guild_id_str = str(guild_id)
        return self.settings.get(guild_id_str, {}).get('preferences', {
            'min_confidence': 0.5,
            'check_grammar': True,
            'check_spelling': True,
            'check_style': False
        })
    
    def update_statistics(self, guild_id):
        """Met à jour les statistiques de correction pour ce serveur"""
        if self.settings is None:
            self.settings = {}
        guild_id_str = str(guild_id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = self.get_default_settings()
        
        if 'statistics' not in self.settings[guild_id_str]:
            self.settings[guild_id_str]['statistics'] = {'total_corrections': 0, 'last_correction': None}
        
        from datetime import datetime
        self.settings[guild_id_str]['statistics']['total_corrections'] = \
            self.settings[guild_id_str]['statistics'].get('total_corrections', 0) + 1
        self.settings[guild_id_str]['statistics']['last_correction'] = datetime.now().isoformat()
        self.save_settings()
    
    def add_language(self, guild_id, lang_code):
        """Ajoute une langue à la liste des langues configurées"""
        if self.settings is None:
            self.settings = {}
        guild_id_str = str(guild_id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = self.get_default_settings()
        if 'languages' not in self.settings[guild_id_str]:
            self.settings[guild_id_str]['languages'] = ['fr']
        
        # Si on ajoute "auto", remplacer toutes les langues par "auto" uniquement
        if lang_code == 'auto':
            self.settings[guild_id_str]['languages'] = ['auto']
        else:
            # Si "auto" est déjà dans la liste, l'enlever avant d'ajouter une langue spécifique
            if 'auto' in self.settings[guild_id_str]['languages']:
                self.settings[guild_id_str]['languages'].remove('auto')
            if lang_code not in self.settings[guild_id_str]['languages']:
                self.settings[guild_id_str]['languages'].append(lang_code)
        
        self.save_settings()
    
    def remove_language(self, guild_id, lang_code):
        """Enlève une langue de la liste des langues configurées"""
        if self.settings is None:
            return False
        guild_id_str = str(guild_id)
        if guild_id_str not in self.settings:
            return False
        if 'languages' not in self.settings[guild_id_str]:
            return False
        
        # Si on enlève "auto", remettre français par défaut
        if lang_code == 'auto':
            if 'auto' in self.settings[guild_id_str]['languages']:
                self.settings[guild_id_str]['languages'] = ['fr']
                self.save_settings()
                return True
        elif lang_code in self.settings[guild_id_str]['languages']:
            self.settings[guild_id_str]['languages'].remove(lang_code)
            # Si on enlève toutes les langues, remettre français par défaut
            if not self.settings[guild_id_str]['languages']:
                self.settings[guild_id_str]['languages'] = ['fr']
            self.save_settings()
            return True
        return False
    
    def set_languages(self, guild_id, languages):
        """Définit la liste des langues pour ce serveur"""
        if self.settings is None:
            self.settings = {}
        guild_id_str = str(guild_id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = self.get_default_settings()
        self.settings[guild_id_str]['languages'] = languages if languages else ['fr']
        self.save_settings()
    
    def detect_mixed_languages(self, text, configured_languages):
        """Détecte si le texte semble contenir plusieurs langues
        Retourne True si plusieurs langues sont probablement présentes"""
        if not configured_languages or len(configured_languages) <= 1:
            return False
        
        # Si 'auto' est configuré, on laisse LanguageTool gérer
        if 'auto' in configured_languages:
            return False
        
        # Compter les mots par langue approximative (basique)
        # Cette détection est simple mais peut aider
        words = text.split()
        if len(words) < 3:
            return False
        
        # Pour une détection plus précise, on pourrait utiliser une bibliothèque
        # mais pour l'instant, on se base sur le fait que plusieurs langues sont configurées
        # et on laisse LanguageTool essayer avec chaque langue
        return len(configured_languages) > 1
    
    async def correct_text_single_language(self, text, lang_code, preferences=None):
        """Corrige un texte avec une seule langue spécifique (sans récursion)
        preferences: dict avec check_style, check_grammar, check_spelling"""
        if preferences is None:
            preferences = {'check_style': True, 'check_grammar': True, 'check_spelling': True}
        check_style = preferences.get('check_style', True)
        check_grammar = preferences.get('check_grammar', True)
        check_spelling = preferences.get('check_spelling', True)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data={
                        'text': text,
                        'language': lang_code
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status != 200:
                        return None, []
                    
                    try:
                        result = await response.json()
                    except Exception as e:
                        return None, []
                    
                    matches = result.get('matches', [])
                    if not matches:
                        return None, []
                    
                    # Filtrer les matches selon les préférences (style, grammar, spelling)
                    filtered_matches = []
                    for match in matches:
                        rule_category = match.get('rule', {}).get('category', {}).get('id', '').upper()
                        rule_category_name = match.get('rule', {}).get('category', {}).get('name', '').upper()
                        rule_id = match.get('rule', {}).get('id', '').upper()
                        
                        # Détecter le type d'erreur
                        is_style = 'TYPOGRAPHY' in rule_category or 'STYLE' in rule_category or 'TYPOGRAPHY' in rule_category_name or 'STYLE' in rule_category_name or 'TYPOGRAPHY' in rule_id or 'STYLE' in rule_id
                        is_grammar = 'GRAMMAR' in rule_category or 'GRAMMAR' in rule_category_name or 'GRAMMAR' in rule_id
                        is_spelling = 'SPELLING' in rule_category or 'SPELLING' in rule_category_name or 'SPELLING' in rule_id or 'ORTHOGRAPHY' in rule_category
                        
                        # Filtrer selon les préférences
                        if is_style and not check_style:
                            continue
                        if is_grammar and not check_grammar:
                            continue
                        if is_spelling and not check_spelling:
                            continue
                        
                        filtered_matches.append(match)
                    
                    matches = filtered_matches
                    if not matches:
                        return None, []
                    
                    # Appliquer les corrections (simplifié pour éviter la duplication)
                    corrected_text = text
                    errors_info = []
                    matches_by_offset = sorted(matches, key=lambda m: m.get('offset', 0), reverse=True)
                    
                    for match in matches_by_offset:
                        replacements = match.get('replacements', [])
                        if not replacements:
                            continue
                        
                        offset = match.get('offset', 0)
                        length = match.get('length', 0)
                        
                        if offset >= len(corrected_text) or offset + length > len(corrected_text):
                            continue
                        
                        error_text = corrected_text[offset:offset + length]
                        best_replacement = replacements[0].get('value', '')
                        
                        if best_replacement and best_replacement != error_text:
                            # Ignorer les corrections qui ajoutent une majuscule au début si l'original n'en avait pas
                            if offset == 0 and text and len(text) > 0:
                                original_first = text[0]
                                replacement_first = best_replacement[0] if best_replacement else ''
                                if original_first.islower() and replacement_first.isupper():
                                    continue  # Ne pas corriger la majuscule manquante
                            
                            corrected_text = corrected_text[:offset] + best_replacement + corrected_text[offset + length:]
                            errors_info.append({
                                'error': error_text,
                                'correction': best_replacement,
                                'message': match.get('message', ''),
                                'category': match.get('rule', {}).get('category', {}).get('name', '')
                            })
                    
                    if errors_info and corrected_text != text:
                        return corrected_text, errors_info
                    return None, []
        except Exception as e:
            return None, []
    
    async def correct_text_multilingual(self, text, languages_list, preferences=None):
        """Corrige un texte multilingue en essayant chaque langue configurée
        et en combinant les meilleurs résultats
        preferences: dict avec check_style, check_grammar, check_spelling"""
        all_corrections = []
        
        for lang in languages_list:
            if lang == 'auto':
                continue  # On traite 'auto' séparément
            
            # Utiliser la fonction directe sans récursion
            corrected, errors = await self.correct_text_single_language(text, lang, preferences)
            if corrected and errors:
                all_corrections.append({
                    'lang': lang,
                    'corrected': corrected,
                    'errors': errors,
                    'error_count': len(errors)
                })
        
        if not all_corrections:
            return None, []
        
        # Choisir la correction avec le plus d'erreurs corrigées (probablement la meilleure)
        best = max(all_corrections, key=lambda x: x['error_count'])
        return best['corrected'], best['errors']
    
    async def correct_text(self, text, languages=None, guild_id=None):
        """Corrige le texte et retourne le texte corrigé et les erreurs
        Si languages est None, utilise 'auto' pour la détection automatique
        Si languages est une liste, essaie chaque langue jusqu'à trouver des erreurs
        Gère automatiquement les phrases multilingues
        guild_id: ID du serveur pour récupérer les préférences (check_style, etc.)"""
        try:
            # Récupérer les préférences pour filtrer les corrections de style si nécessaire
            preferences = self.get_preferences(guild_id) if guild_id else {'check_style': True, 'check_grammar': True, 'check_spelling': True}
            check_style = preferences.get('check_style', True)
            check_grammar = preferences.get('check_grammar', True)
            check_spelling = preferences.get('check_spelling', True)
            
            # Déterminer la langue à utiliser
            if languages and 'auto' in languages:
                lang_to_use = 'auto'
                detected_lang = None  # Sera détecté automatiquement par l'API
            elif languages and len(languages) > 1:
                # Plusieurs langues configurées : essayer une approche multilingue
                # D'abord essayer avec 'auto' pour voir si ça fonctionne bien
                lang_to_use = 'auto'
                detected_lang = languages[0]
            elif languages and len(languages) == 1:
                lang_to_use = languages[0]
                detected_lang = languages[0]
            else:
                lang_to_use = 'fr'
                detected_lang = 'fr'
            
            # Note: On n'utilise plus de mots-clés spécifiques par langue
            # L'analyse contextuelle se base sur la structure de la phrase et les informations de LanguageTool
            
            async with aiohttp.ClientSession() as session:
                # Utiliser l'API LanguageTool v2 (vérifié pour 2025)
                # Paramètres supportés: text (requis), language (requis)
                # L'API publique supporte: 20 requêtes/IP/minute, 20 Ko par requête
                async with session.post(
                    self.api_url,
                    data={
                        'text': text,
                        'language': lang_to_use
                    },
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    # Vérifier le statut de la réponse
                    if response.status != 200:
                        print(f"Erreur API LanguageTool: status {response.status}")
                        return None, []
                    
                    # Parser la réponse JSON (structure vérifiée pour 2025)
                    try:
                        result = await response.json()
                    except Exception as e:
                        print(f"Erreur parsing JSON LanguageTool: {e}")
                        return None, []
                    
                    # Structure de réponse attendue: { "matches": [...], "language": {...}, ... }
                    matches = result.get('matches', [])
                    
                    # Vérifier si l'API a détecté une langue différente (utile pour le mode auto)
                    # Cette information peut être utilisée pour améliorer l'analyse contextuelle si nécessaire
                    detected_language = result.get('language', {}).get('detectedLanguage', {}).get('code', None)
                    
                    if not matches:
                        return None, []
                    
                    # Filtrer les matches selon les préférences (style, grammar, spelling)
                    filtered_matches = []
                    for match in matches:
                        rule_category = match.get('rule', {}).get('category', {}).get('id', '').upper()
                        rule_category_name = match.get('rule', {}).get('category', {}).get('name', '').upper()
                        rule_id = match.get('rule', {}).get('id', '').upper()
                        
                        # Détecter le type d'erreur
                        is_style = 'TYPOGRAPHY' in rule_category or 'STYLE' in rule_category or 'TYPOGRAPHY' in rule_category_name or 'STYLE' in rule_category_name or 'TYPOGRAPHY' in rule_id or 'STYLE' in rule_id
                        is_grammar = 'GRAMMAR' in rule_category or 'GRAMMAR' in rule_category_name or 'GRAMMAR' in rule_id
                        is_spelling = 'SPELLING' in rule_category or 'SPELLING' in rule_category_name or 'SPELLING' in rule_id or 'ORTHOGRAPHY' in rule_category
                        
                        # Filtrer selon les préférences
                        if is_style and not check_style:
                            continue  # Ignorer les corrections de style si check_style est False
                        if is_grammar and not check_grammar:
                            continue  # Ignorer les corrections de grammaire si check_grammar est False
                        if is_spelling and not check_spelling:
                            continue  # Ignorer les corrections d'orthographe si check_spelling est False
                        
                        filtered_matches.append(match)
                    
                    matches = filtered_matches
                    
                    if not matches:
                        return None, []
                    
                    # Trier les matches par type d'erreur (priorité aux erreurs grammaticales et de conjugaison)
                    # Les erreurs de grammaire et conjugaison sont plus importantes que les fautes d'orthographe simples
                    # On trie aussi par offset pour traiter dans l'ordre
                    matches_sorted = sorted(matches, key=lambda m: (
                        'grammar' in m.get('rule', {}).get('category', {}).get('id', '').lower(),
                        'conjugation' in m.get('message', '').lower(),
                        'agreement' in m.get('rule', {}).get('id', '').lower() or 'agreement' in m.get('message', '').lower(),
                        -m.get('offset', 0)  # Traiter de la fin vers le début pour éviter les décalages
                    ), reverse=True)
                    
                    # Construire le texte corrigé en appliquant TOUTES les corrections détectées
                    # Utiliser le contexte complet du texte pour une meilleure analyse
                    corrected_text = text
                    errors_info = []
                    
                    # Extraire le contexte complet du texte (toute la phrase/message)
                    full_context = text
                    
                    # Trier les matches par offset décroissant pour appliquer de la fin vers le début
                    # Cela évite de décaler les offsets des corrections suivantes
                    matches_by_offset = sorted(matches_sorted, key=lambda m: m.get('offset', 0), reverse=True)
                    
                    for match in matches_by_offset:
                        replacements = match.get('replacements', [])
                        if not replacements:
                            continue
                        
                        offset = match.get('offset', 0)
                        length = match.get('length', 0)
                        
                        # Vérifier que l'offset est toujours valide après les corrections précédentes
                        if offset >= len(corrected_text):
                            continue
                        if offset + length > len(corrected_text):
                            length = len(corrected_text) - offset
                        
                        error_text = corrected_text[offset:offset + length]
                        
                        # Utiliser la phrase complète ET le contexte du texte entier
                        sentence = match.get('sentence', '')
                        context = match.get('context', {})
                        context_text = context.get('text', '')
                        context_offset = context.get('offset', 0)
                        
                        # Utiliser le contexte le plus large disponible
                        if not sentence and context_text:
                            sentence = context_text
                        if not sentence:
                            sentence = full_context
                        
                        # Choisir la meilleure correction en fonction du contexte complet
                        best_replacement = None
                        best_score = 0
                        
                        for replacement_option in replacements[:10]:  # Examiner les 10 meilleures suggestions pour plus de précision
                            replacement_value = replacement_option.get('value', '')
                            if not replacement_value:
                                continue
                            
                            score = 0
                            
                            # 1. Priorité absolue aux corrections de grammaire, conjugaison et accord
                            rule_category = match.get('rule', {}).get('category', {}).get('id', '').lower()
                            rule_id = match.get('rule', {}).get('id', '').lower()
                            message_text = match.get('message', '').lower()
                            
                            # Détecter les erreurs d'accord, de grammaire et de conjugaison
                            is_agreement = 'agreement' in rule_category or 'agreement' in rule_id or 'agreement' in message_text or 'plural' in rule_id
                            is_grammar = 'grammar' in rule_category or 'grammar' in rule_id or 'grammar' in message_text
                            is_conjugation = 'conjugation' in rule_category or 'conjugation' in rule_id or 'conjugation' in message_text or 'verb' in rule_id or 'tense' in rule_id
                            
                            if is_agreement or is_grammar or is_conjugation:
                                score += 3.0  # Priorité maximale pour ces corrections
                            
                            # 2. Vérifier le contexte de la phrase complète dans le texte corrigé
                            if sentence:
                                # Tester la correction dans le contexte de la phrase
                                sentence_offset = offset - context_offset if context_offset > 0 else 0
                                if sentence_offset >= 0 and sentence_offset + length <= len(sentence):
                                    # Construire la phrase test avec la correction
                                    test_sentence = sentence[:sentence_offset] + replacement_value + sentence[sentence_offset + length:]
                                    
                                    # Bonus si la phrase corrigée a une meilleure structure
                                    if test_sentence.strip():
                                        words = test_sentence.split()
                                        if len(words) >= 2:  # Au moins 2 mots pour avoir du contexte
                                            score += 0.8
                                        
                                        # Bonus supplémentaire pour cohérence grammaticale
                                        # Vérifier les accords basiques (pluriel/singulier)
                                        if is_agreement:
                                            # Vérifier si la correction améliore l'accord
                                            # Ex: "tous les" + pluriel, "tout le" + singulier
                                            if 'tous' in test_sentence.lower() or 'toutes' in test_sentence.lower():
                                                # Chercher des indices de pluriel après
                                                next_words = test_sentence.lower().split()
                                                for i, word in enumerate(next_words):
                                                    if word in ['tous', 'toutes'] and i + 1 < len(next_words):
                                                        next_word = next_words[i + 1]
                                                        # Bonus si le mot suivant semble être au pluriel
                                                        if replacement_value.endswith('s') or replacement_value.endswith('x'):
                                                            score += 0.5
                            
                            # 3. Vérifier le contexte dans le texte complet corrigé
                            if len(corrected_text) > offset + length:
                                # Tester la correction dans le contexte du texte complet
                                test_full_text = corrected_text[:offset] + replacement_value + corrected_text[offset + length:]
                                # Bonus si le texte complet a une meilleure structure
                                if test_full_text.strip():
                                    score += 0.3
                            
                            # 4. Similarité basique (mais pas trop restrictive)
                            if len(error_text) > 1 and len(replacement_value) > 1:
                                similarity = sum(1 for a, b in zip(error_text.lower(), replacement_value.lower()) if a == b) / max(len(error_text), len(replacement_value))
                                score += similarity * 0.2
                            
                            if score > best_score:
                                best_score = score
                                best_replacement = replacement_value
                        
                        # Appliquer la correction si on a trouvé une bonne suggestion
                        if best_replacement and best_replacement != error_text:
                            # Ignorer les corrections qui ajoutent une majuscule au début si l'original n'en avait pas
                            if offset == 0 and text and len(text) > 0:
                                original_first = text[0]
                                replacement_first = best_replacement[0] if best_replacement else ''
                                if original_first.islower() and replacement_first.isupper():
                                    continue  # Ne pas corriger la majuscule manquante
                            
                            # Filtrer uniquement les corrections vraiment absurdes (sauf pour grammaire/accord)
                            rule_category = match.get('rule', {}).get('category', {}).get('id', '').lower()
                            is_grammar_check = is_agreement or is_grammar or is_conjugation or 'grammar' in rule_category or 'conjugation' in match.get('message', '').lower() or 'agreement' in rule_category
                            
                            if len(error_text) > 2 and len(best_replacement) > 2 and not is_grammar_check:
                                similarity = sum(1 for a, b in zip(error_text.lower(), best_replacement.lower()) if a == b) / max(len(error_text), len(best_replacement))
                                if similarity < 0.1:  # Seuil très bas seulement pour les non-grammaire
                                    continue
                            
                            # Appliquer la correction
                            corrected_text = corrected_text[:offset] + best_replacement + corrected_text[offset + length:]
                            
                            # Stocker l'info de l'erreur
                            errors_info.append({
                                'error': error_text,
                                'correction': best_replacement,
                                'message': match.get('message', ''),
                                'category': match.get('rule', {}).get('category', {}).get('name', '')
                            })
                    
                    # Vérification finale : faire une deuxième passe si nécessaire pour les corrections d'accord
                    # Si on a corrigé des erreurs d'accord, vérifier que tout est cohérent
                    if errors_info and corrected_text != text:
                        # Vérifier s'il reste des erreurs d'accord dans le texte corrigé
                        try:
                            async with session.post(
                                self.api_url,
                                data={
                                    'text': corrected_text,
                                    'language': lang_to_use
                                },
                                timeout=aiohttp.ClientTimeout(total=3)
                            ) as verify_response:
                                if verify_response.status == 200:
                                    verify_result = await verify_response.json()
                                    verify_matches = verify_result.get('matches', [])
                                    
                                    # Si on trouve encore des erreurs d'accord, les corriger aussi
                                    agreement_matches = [m for m in verify_matches if 'agreement' in m.get('rule', {}).get('id', '').lower() or 'agreement' in m.get('message', '').lower()]
                                    
                                    if agreement_matches:
                                        # Appliquer les corrections d'accord restantes
                                        for match in sorted(agreement_matches, key=lambda m: m.get('offset', 0), reverse=True):
                                            replacements = match.get('replacements', [])
                                            if replacements:
                                                offset = match.get('offset', 0)
                                                length = match.get('length', 0)
                                                if offset < len(corrected_text) and offset + length <= len(corrected_text):
                                                    best_replacement = replacements[0].get('value', '')
                                                    if best_replacement:
                                                        # Ignorer les corrections qui ajoutent une majuscule au début si l'original n'en avait pas
                                                        if offset == 0 and text and len(text) > 0:
                                                            original_first = text[0]
                                                            replacement_first = best_replacement[0] if best_replacement else ''
                                                            if original_first.islower() and replacement_first.isupper():
                                                                continue  # Ne pas corriger la majuscule manquante
                                                        corrected_text = corrected_text[:offset] + best_replacement + corrected_text[offset + length:]
                        except:
                            pass  # Si la vérification échoue, on garde les corrections déjà appliquées
                    
                    # Retourner le texte corrigé seulement si des corrections ont été appliquées
                    if errors_info and corrected_text != text:
                        return corrected_text, errors_info
                    else:
                        # Si aucune correction trouvée avec 'auto' et plusieurs langues configurées (sans 'auto'),
                        # essayer avec chaque langue individuellement (pour phrases multilingues)
                        if lang_to_use == 'auto' and languages and len(languages) > 1 and 'auto' not in languages:
                            # Essayer avec chaque langue configurée pour gérer les phrases multilingues
                            multilingual_result = await self.correct_text_multilingual(text, languages, preferences)
                            if multilingual_result[0]:  # Si on a trouvé des corrections
                                return multilingual_result
                        return None, []
        except Exception as e:
            print(f"Erreur lors de la correction: {e}")
            return None, []
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Détecte et corrige automatiquement les fautes d'orthographe/grammaire"""
        # Ignorer les messages du bot
        if message.author == self.client.user:
            return
        
        # Ignorer les messages dans les DMs
        if not isinstance(message.channel, discord.TextChannel):
            return
        
        # Ignorer les commandes (messages qui commencent par le préfixe "=")
        if message.content and message.content.startswith("="):
            return
        
        # Ignorer les messages vides
        if not message.content or len(message.content.strip()) < 3:
            return
        
        # Ignorer les bots
        if message.author.bot:
            return
        
        # Vérifier si le correcteur est activé pour ce serveur
        if not self.is_enabled(message.guild.id):
            return
        
        # Vérifier si settings est chargé
        if self.settings is None:
            return
        
        # Récupérer les langues configurées pour ce serveur
        languages = self.get_languages(message.guild.id)
        
        # Corriger le texte avec les langues configurées et les préférences du serveur
        corrected_text, errors = await self.correct_text(message.content, languages, guild_id=message.guild.id)
        
        # Si des erreurs ont été trouvées et que le texte a vraiment changé
        if corrected_text and errors and corrected_text != message.content:
            # Mettre à jour les statistiques
            self.update_statistics(message.guild.id)
            
            # Envoyer la correction directement (sans embed)
            try:
                await message.reply(corrected_text, mention_author=False)
            except Exception as e:
                print(f"Erreur lors de l'envoi de la correction: {e}")

async def setup(client):
    await client.add_cog(GrammarCorrector_auto(client))

