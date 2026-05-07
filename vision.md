# Shoebox — Vision : si on avait eu un mois de plus

> Ce document capture les idées qu'on aurait développées avec plus de temps et un accès à des APIs publiques. Ce ne sont pas des regrets — c'est une feuille de route pour une V2.

---

## Ce qu'on a aujourd'hui

Un outil local, entièrement autonome : ingestion de fichiers → base SQLite → dashboard Dash → extension Chrome. Zéro dépendance externe au runtime, zéro abonnement, données 100 % privées.

---

## 1. Connexion bancaire temps réel — Plaid ou Flinks

**L'idée.** Remplacer l'import manuel de relevés XLSX/PDF par une connexion directe au compte bancaire. L'utilisateur connecte sa banque une fois, et les transactions arrivent automatiquement chaque nuit.

**API.** [Plaid](https://plaid.com/products/transactions/) (US/CA) ou [Flinks](https://flinks.com/) (spécialisé Canada). Les deux exposent un endpoint `/transactions` avec date, montant, description, catégorie MCC.

**Ce que ça change dans le code.**
- Nouveau service `BankSyncService` qui poll `/transactions` toutes les 24h via un cron APScheduler.
- Les transactions importées passent par le même `IngestionService` existant — seul le parser change (`BankTransactionParser` vs `XLSXParser`).
- Interface de connexion OAuth dans le frontend (une seule page `/connect`).
- Stocker les `access_token` chiffrés dans la DB (colonne `sources.plaid_token`).

**Effort estimé.** 2 semaines — 1 pour l'intégration OAuth/webhook, 1 pour l'UI de connexion et la gestion des tokens.

---

## 2. OCR intelligent — Google Vision ou AWS Textract

**L'idée.** Remplacer Tesseract (règles heuristiques) par un service cloud qui comprend la mise en page des reçus, détecte les zones TVQ/TPS, et retourne des champs structurés directement.

**API.** [Google Cloud Vision](https://cloud.google.com/vision/docs/receipt-understanding) (Document AI) ou [AWS Textract](https://aws.amazon.com/textract/). Les deux ont des modèles spécialisés pour les reçus et les formulaires.

**Ce que ça change dans le code.**
- `CloudOCRParser` implémente `IParser` exactement comme `ImageReceiptParser`.
- Aucun changement dans `IngestionService`, `ReceiptRouter`, ou la DB.
- Feature flag `USE_CLOUD_OCR=true` dans `.env` — basculement sans redémarrage.
- Fallback automatique vers Tesseract si le quota cloud est dépassé.

**Gain concret.** Taux de reconnaissance des montants qui passe de ~70 % (Tesseract sur reçus froissés) à ~97 % (Textract). Moins de corrections manuelles dans le formulaire step 4.

**Effort estimé.** 3 jours — l'architecture est déjà prête (interface `IParser`).

---

## 3. Catégorisation par LLM — Claude API

**L'idée.** Remplacer le moteur à règles (`keywords.py`) par un appel Claude pour les transactions dont le marchand est inconnu. Le LLM comprend "AMZN Mktp CA" → "Logiciels & abonnements" sans dictionnaire codé en dur.

**API.** [Anthropic API](https://docs.anthropic.com/en/api/getting-started) — `claude-haiku-4-5` (rapide, bon marché) pour les classifications en batch.

**Ce que ça change dans le code.**
- `LLMCategorizer` implémente `ICategorizer`.
- Prompt système : "Tu es un comptable canadien. Catégorise cette dépense freelance : {description} {amount}. Réponds avec un seul mot parmi : [liste des Category enum]."
- Cache local des classifications (description → catégorie) pour éviter de re-appeler le LLM sur le même marchand.
- Fallback vers le moteur à règles si pas de clé API.

**Effort estimé.** 1 semaine — surtout le prompt engineering et les tests de cohérence sur les catégories existantes.

---

## 4. Rapport fiscal automatique — Revenu Québec / CRA

**L'idée.** Générer un rapport T2125 (État des résultats des activités d'une entreprise) pré-rempli à partir des données Shoebox. Export PDF + XLSX utilisable directement par un comptable.

**Ce que ça implique.**
- `TaxReportService` qui mappe nos catégories aux lignes T2125 (ex. "Fournitures de bureau" → ligne 8810, "Repas & représentation" → ligne 8523 à 50 %).
- Template XLSX avec les formules CRA, rempli par openpyxl.
- Page `/report` transformée : bouton "Télécharger T2125" au lieu d'un simple tableau.
- Intégration optionnelle avec l'[API de soumission CRA](https://www.canada.ca/en/revenue-agency/services/e-services/digital-services-businesses.html) pour les pros.

**Effort estimé.** 2 semaines — surtout comprendre les règles de déductibilité et les tester sur des cas réels.

---

## 5. Alertes proactives — Email + Slack

**L'idée.** Shoebox envoie un récapitulatif hebdomadaire et des alertes immédiates (facture en retard depuis 30 jours, doublon détecté, dépense personnelle oubliée sur la carte pro).

**APIs.**
- Email : [Resend](https://resend.com/) ou [SendGrid](https://sendgrid.com/) — templates HTML sobres, 1 req/semaine.
- Slack : [Incoming Webhooks](https://api.slack.com/messaging/webhooks) — message structuré avec les KPIs du mois.

**Ce que ça change dans le code.**
- `NotificationService` avec deux adapteurs (`EmailNotifier`, `SlackNotifier`).
- Scheduler APScheduler dans le lifespan FastAPI : cron hebdomadaire le lundi 8h.
- Page `/settings` dans le frontend pour configurer l'email et le webhook Slack.
- Règles d'alerte stockées en DB (seuil montant, délai facture, etc.).

**Effort estimé.** 1 semaine.

---

## 6. Application mobile — React Native + même API

**L'idée.** Prendre une photo d'un reçu depuis l'app mobile → OCR → formulaire pré-rempli → validation en un tap. Le backend FastAPI existant est déjà l'API parfaite pour ça.

**Ce que ça change dans le code.**
- Zéro changement backend — l'endpoint `POST /files/upload` accepte déjà les images.
- App React Native avec `expo-camera` + `expo-image-picker`.
- Même design system (couleurs, typographie) adapté en StyleSheet React Native.
- Auth JWT à ajouter (le seul vrai travail côté backend).

**Effort estimé.** 1 mois — principalement l'app mobile et l'authentification.

---

## 7. Multi-utilisateur & SaaS

**L'idée.** Transformer Shoebox en produit SaaS : chaque freelance a son espace isolé, son propre SQLite (ou PostgreSQL schema), son propre accès.

**Ce que ça implique.**
- Auth : [Auth0](https://auth0.com/) ou Supabase Auth — JWT, pas de gestion de mots de passe maison.
- Isolation des données : `user_id` sur toutes les tables + Row Level Security si PostgreSQL.
- Facturation : [Stripe](https://stripe.com/) — plan Gratuit (1 source, 100 tx/mois) + Pro (illimité, $12/mois).
- Déploiement : Docker Compose → Render ou Railway pour commencer.

**Effort estimé.** 2 mois — c'est une refonte d'architecture, pas une feature.

---

## Résumé des priorités

| Priorité | Feature | Valeur utilisateur | Effort |
|---|---|---|---|
| ★★★ | Connexion bancaire (Plaid/Flinks) | Élimine 80 % du travail manuel | 2 semaines |
| ★★★ | Rapport fiscal T2125 | Raison d'exister pour un comptable | 2 semaines |
| ★★☆ | OCR cloud (Textract) | Moins d'erreurs, moins de corrections | 3 jours |
| ★★☆ | Catégorisation LLM | Moins de règles à maintenir | 1 semaine |
| ★★☆ | Alertes email / Slack | Rétention, valeur passive | 1 semaine |
| ★☆☆ | App mobile | Capture immédiate des reçus | 1 mois |
| ★☆☆ | Multi-utilisateur SaaS | Monétisation | 2 mois |

---

> Le cœur de Shoebox — le pipeline d'ingestion, les interfaces, la séparation des couches — a été conçu dès le départ pour accueillir ces extensions sans réécriture. Chaque API externe s'intègre derrière une interface existante (`IParser`, `ICategorizer`, `IFileStorage`). C'est le vrai investissement de cette version.
