# Shoebox — Vision : si on avait eu un mois de plus

> Ce document capture les idées qu'on aurait développées avec plus de temps et un accès à des APIs publiques. Ce ne sont pas des regrets, c'est une feuille de route pour une V2.

## Ce qu'on a aujourd'hui

Un outil local, entièrement autonome : importation de fichiers, base de données SQLite, tableau de bord Dash, extension Chrome. Zéro dépendance externe au runtime, zéro abonnement, données 100 % privées.

## 1. Connexion bancaire en temps réel — Plaid ou Flinks

**L'idée.** Remplacer l'import manuel de relevés XLSX/PDF par une connexion directe au compte bancaire. L'utilisateur connecte sa banque une fois, et les transactions arrivent automatiquement chaque nuit.

**API.** [Plaid](https://plaid.com/products/transactions/) (US/CA) ou [Flinks](https://flinks.com/) (spécialisé Canada). Les deux exposent un point d'accès `/transactions` avec date, montant, description et catégorie de marchand.

**Ce que ça change dans le code.**

Un nouveau composant chargé de la synchronisation bancaire interrogerait automatiquement le serveur bancaire toutes les 24 heures grâce à une tâche planifiée en arrière-plan — l'équivalent d'un réveil qui se déclenche chaque nuit pour aller chercher les nouvelles transactions à votre place.

Les transactions récupérées passeraient ensuite par le même pipeline d'ingestion que les fichiers importés manuellement. Seul le "lecteur" change : au lieu d'un lecteur de fichier XLSX, on utilise un lecteur de réponse bancaire. Tout le reste (validation, enregistrement en base, catégorisation) reste identique.

Côté interface, une seule nouvelle page `/connect` permettrait à l'utilisateur d'autoriser Shoebox à accéder à sa banque via le protocole OAuth (la même technologie que "Se connecter avec Google"). Les jetons d'accès bancaires seraient stockés chiffrés dans la base de données.

**Effort estimé.** 2 semaines. 1 pour l'intégration de l'autorisation bancaire et la réception des données, 1 pour l'interface de connexion et la gestion sécurisée des jetons.

## 2. Reconnaissance de documents intelligente — Google Vision ou AWS Textract

**L'idée.** Remplacer Tesseract (notre moteur OCR local qui lit les images pixel par pixel avec des règles heuristiques) par un service cloud qui comprend la mise en page des reçus, détecte automatiquement les zones TVQ/TPS, et retourne des champs structurés directement.

**API.** [Google Cloud Vision](https://cloud.google.com/vision/docs/receipt-understanding) (Document AI) ou [AWS Textract](https://aws.amazon.com/textract/). Les deux proposent des modèles entraînés spécifiquement sur les reçus et les formulaires. Il serait aussi possible d'utiliser directement des modèles de langage comme Claude, Gemini ou GPT qui comprennent la mise en page des documents.

**Ce que ça change dans le code.**

Shoebox est conçu autour d'un contrat commun que tous les lecteurs de documents respectent : chaque lecteur (qu'il lise un PDF, une image ou un XLSX) reçoit un fichier et retourne un dictionnaire de champs extraits. Un nouveau lecteur cloud respecterait exactement ce même contrat. En pratique, cela signifie qu'on peut échanger Tesseract contre Textract sans toucher au reste du code : le pipeline d'ingestion, la base de données, les formulaires de validation — rien ne change.

Une option dans le fichier de configuration permettrait de basculer entre Tesseract et le service cloud sans redémarrage. Si le quota cloud est dépassé, le système reviendrait automatiquement sur Tesseract.

**Gain concret.** Le taux de reconnaissance des montants passerait de ~70 % (Tesseract sur des reçus froissés ou mal éclairés) à ~97 % (Textract). Moins de corrections manuelles dans le formulaire d'importation.

**Effort estimé.** 3 jours. L'architecture est déjà prête pour accueillir ce changement.

## 3. Catégorisation automatique par intelligence artificielle — Claude API

**L'idée.** Remplacer le moteur de règles actuel par un modèle de langage pour les transactions dont le marchand est inconnu. Le moteur actuel fonctionne avec un dictionnaire de mots-clés codé en dur : si la description d'une transaction contient "Uber", elle est classée "Transport" ; si elle contient "Amazon", elle est classée "Logiciels". Le problème, c'est que ce dictionnaire ne connaît pas tous les marchands. Un modèle de langage, lui, comprend "AMZN Mktp CA" ou "SQ *CAFÉ DU COIN" sans avoir besoin qu'on lui ait explicitement appris ces raccourcis.

Si on regarde la page Rapport fiscal, dans la catégorie "Non catégorisé", on voit beaucoup de transactions qu'un humain saurait classer immédiatement mais que le moteur à règles ne reconnaît pas faute d'un mot-clé correspondant.

**API.** [Anthropic API](https://docs.anthropic.com/en/api/getting-started) avec `claude-haiku-4-5` (le modèle le plus rapide et économique de la gamme Claude) pour les classifications en lot.

**Ce que ça change dans le code.**

De la même façon que pour les lecteurs de documents, il existe un contrat commun pour les catégoriseurs : recevoir une description et un montant, retourner une catégorie. Un nouveau catégoriseur basé sur un modèle de langage respecterait ce contrat. La logique interne consiste à envoyer une requête au modèle avec une instruction du type : "Tu es un comptable canadien. Catégorise cette dépense freelance : {description} {montant}. Réponds avec une seule catégorie parmi : [liste des catégories disponibles]."

Un cache local mémoriserait les résultats (description → catégorie) pour éviter d'appeler le modèle plusieurs fois pour le même marchand. Si aucune clé API n'est configurée, le système utiliserait automatiquement le moteur à règles existant.

**Effort estimé.** 1 semaine. Surtout pour tester et affiner l'instruction envoyée au modèle, et vérifier que les catégories retournées sont cohérentes avec celles déjà en base.

## 4. Rapport fiscal automatique — Revenu Québec / ARC

**L'idée.** Générer un rapport T2125 (État des résultats des activités d'une entreprise) pré-rempli à partir des données Shoebox. Export PDF et XLSX utilisable directement par un comptable.

**Ce que ça implique.**

Un service de génération fiscale ferait correspondre nos catégories aux lignes du formulaire T2125 (par exemple : "Fournitures de bureau" → ligne 8810, "Repas et représentation" → ligne 8523 à 50 %). Un modèle de fichier XLSX avec les formules de l'ARC serait rempli automatiquement grâce à openpyxl, la bibliothèque qu'on utilise déjà pour lire les relevés bancaires en format tableur.

La page Rapport fiscal actuelle afficherait un bouton "Télécharger T2125" au lieu du simple tableau actuel. En option, une intégration avec l'API de soumission électronique de l'ARC serait possible pour les professionnels.

**Effort estimé.** 2 semaines — principalement pour comprendre les règles de déductibilité et les tester sur des cas réels.

## 5. Alertes proactives — Email et Slack

**L'idée.** Shoebox envoie un récapitulatif hebdomadaire et des alertes immédiates : facture en retard depuis 30 jours, doublon détecté, dépense personnelle oubliée sur la carte pro.

**APIs.**
- Email : [Resend](https://resend.com/) ou [SendGrid](https://sendgrid.com/) — templates HTML sobres, une requête par semaine.
- Slack : [Incoming Webhooks](https://api.slack.com/messaging/webhooks) — message structuré avec les KPIs du mois envoyé dans un canal d'équipe.

**Ce que ça change dans le code.**

Un service de notifications gérerait deux canaux : email et Slack. Une tâche planifiée se déclencherait chaque lundi à 8h en arrière-plan du serveur. Une page de paramètres dans le tableau de bord permettrait de configurer l'adresse email et l'URL du canal Slack. Les règles d'alerte (seuil de montant, délai de facture, etc.) seraient stockées en base de données.

**Effort estimé.** 1 semaine.

## 6. Application mobile — React Native avec la même API

**L'idée.** Prendre une photo d'un reçu depuis l'application mobile, lancer la reconnaissance automatique, valider le formulaire pré-rempli en un seul geste. Le serveur backend existant est déjà l'API parfaite pour ça — il n'y aurait rien à y changer.

**Ce que ça change dans le code.**

Aucun changement côté serveur : l'endpoint d'upload existant accepte déjà les images envoyées depuis n'importe quelle source. L'application mobile serait construite avec React Native, le framework qui permet d'écrire une seule application qui tourne aussi bien sur iOS que sur Android, en utilisant la caméra du téléphone et la galerie de photos. Le même système de couleurs et de typographie que le tableau de bord web serait adapté pour l'écran mobile.

Le seul vrai travail côté serveur serait l'ajout d'une authentification par jeton (le mécanisme standard pour qu'une application mobile prouve son identité auprès d'un serveur sans que l'utilisateur ait à retaper son mot de passe à chaque requête).

**Effort estimé.** 1 mois — principalement l'application mobile et l'authentification.

## 7. Multi-utilisateur et SaaS

**L'idée.** Transformer Shoebox en produit SaaS : chaque freelance a son espace isolé, ses propres données, son propre accès.

**Ce que ça implique.**

L'authentification serait gérée par un service spécialisé comme Auth0 ou Supabase Auth — ce sont des plateformes qui gèrent à notre place les mots de passe, la récupération de compte et la double authentification, évitant d'avoir à implémenter soi-même cette mécanique complexe et sensible.

L'isolation des données serait assurée par un identifiant utilisateur sur chaque ligne de chaque table de la base : chaque requête ne peut voir que les données de l'utilisateur connecté. La facturation passerait par [Stripe](https://stripe.com/) avec deux plans : Gratuit (1 source, 100 transactions par mois) et Pro (illimité, 12 $/mois). Le déploiement se ferait via Docker Compose sur une plateforme cloud comme Render ou Railway.

**Effort estimé.** 2 mois — c'est une refonte d'architecture, pas une fonctionnalité.

## Résumé des priorités

| Priorité | Fonctionnalité | Valeur utilisateur | Effort |
|---|---|---|---|
| ★★★ | Connexion bancaire (Plaid/Flinks) | Élimine 80 % du travail manuel | 2 semaines |
| ★★★ | Rapport fiscal T2125 | Raison d'exister pour un comptable | 2 semaines |
| ★★★ | OCR cloud (Textract) | Moins d'erreurs, moins de corrections | 3 jours |
| ★★ | Catégorisation par modèle de langage | Moins de règles à maintenir | 1 semaine |
| ★★ | Alertes email et Slack | Rétention, valeur passive | 1 semaine |
| ★★ | Application mobile | Capture immédiate des reçus | 1 mois |
| ★ | Multi-utilisateur SaaS | Monétisation | 2 mois |

Le cœur de Shoebox — le pipeline d'ingestion, les contrats communs entre les composants, la séparation des couches — a été conçu dès le départ pour accueillir ces extensions sans réécriture. Chaque service externe s'intègre derrière une interface déjà définie. C'est le vrai investissement de cette version.
