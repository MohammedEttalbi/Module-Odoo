# 📧 Gestion Intelligente des Courriels - Odoo 17

> Module Odoo 17 de gestion des emails avec interface moderne et assistance IA (LLaMA via Ollama)

![Odoo Version](https://img.shields.io/badge/Odoo-17.0-purple)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![AI](https://img.shields.io/badge/AI-LLaMA%203.2-orange)

## 🎯 Description

Ce module offre une solution complète de gestion des courriels dans Odoo 17, combinant une interface utilisateur moderne avec des fonctionnalités d'intelligence artificielle pour améliorer la productivité.

### ✨ Fonctionnalités principales

| Fonctionnalité | Description |
|----------------|-------------|
| 📬 **Interface 3 panneaux** | Layout à 3 panneaux (dossiers, liste, lecture) |
| 🤖 **IA Intégrée** | Résumé automatique, suggestion de réponse, rédaction assistée |
| 📁 **Gestion des dossiers** | Inbox, Envoyés, Brouillons, Archives, Spam |
| 🏷️ **Étiquettes** | Organisation avec labels colorés (Urgent, RH, Client, etc.) |
| 📤 **SMTP/IMAP** | Envoi et réception d'emails configurables |
| 📎 **Pièces jointes** | Support complet des attachements |

## 🏗️ Architecture

```
mail_courriel/
├── __manifest__.py          # Configuration du module
├── models/
│   ├── mail_courriel.py     # Modèle principal des emails
│   ├── mail_dossier.py      # Gestion des dossiers
│   ├── mail_etiquette.py    # Système d'étiquettes
│   └── mail_ai.py           # Service IA (Ollama/LLaMA)
├── views/
│   ├── mail_courriel_views.xml
│   ├── mail_dossier_views.xml
│   ├── mail_etiquette_views.xml
│   └── mail_client_action.xml
├── static/src/
│   ├── css/mail_client.css
│   ├── js/mail_client.js    # Composant OWL
│   └── xml/mail_client.xml
├── security/
│   └── ir.model.access.csv
└── data/
    ├── mail_dossier_data.xml
    └── mail_etiquette_data.xml
```

## 🚀 Installation

### Prérequis

- Docker & Docker Compose
- Ollama (pour les fonctionnalités IA)
- Git

### Étapes d'installation

**1. Cloner le repository**
```bash
git clone https://github.com/votre-username/odoo-mail-courriel.git
cd odoo-mail-courriel
```

**2. Installer Ollama et le modèle LLaMA**
```bash
# Télécharger Ollama depuis https://ollama.ai
ollama pull llama3.2:latest
ollama serve
```

**3. Lancer Docker Compose**
```bash
docker-compose up -d
```

**4. Accéder à Odoo**
```
http://localhost:8069
```

**5. Installer le module**
- Aller dans **Applications**
- Rechercher "**Gestion des Courriels**"
- Cliquer sur **Installer**

## ⚙️ Configuration

### Docker Compose

```yaml
version: "3.8"

services:
  db:
    image: postgres:16
    container_name: odoo_db
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
    volumes:
      - odoo-db-data:/var/lib/postgresql/data

  odoo17:
    image: odoo:17.0
    container_name: odoo_app
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - odoo-web-data:/var/lib/odoo
      - ./config:/etc/odoo
      - ./addons:/mnt/extra-addons
    command: >
      odoo -d odoo_db -u mail_courriel --dev=xml
```

### Configuration Email

| Paramètre | Valeur exemple |
|-----------|----------------|
| **SMTP Server** | smtp.gmail.com |
| **SMTP Port** | 587 (TLS) |
| **IMAP Server** | imap.gmail.com |
| **IMAP Port** | 993 (SSL) |

### Configuration IA (Ollama)

Le service IA se connecte automatiquement à Ollama via :
```
http://host.docker.internal:11434
```

## 🤖 Fonctionnalités IA

### 1. Résumé automatique
Génère un résumé concis de l'email en 2-3 phrases.

### 2. Suggestion de réponse
Propose une réponse professionnelle adaptée au contexte.

### 3. Rédaction assistée
Crée un email complet à partir d'une simple instruction.

### 4. Génération d'objet
Suggère un objet pertinent basé sur le contenu.


## 🛠️ Développement

### Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | Odoo 17 / Python 3.10+ |
| Frontend | OWL (Odoo Web Library) |
| Base de données | PostgreSQL 16 |
| IA | Ollama + LLaMA 3.2 |
| Conteneurisation | Docker |

### Commandes utiles

```bash
# Voir les logs Odoo
docker-compose logs -f odoo17

# Redémarrer Odoo
docker-compose restart odoo17

# Arrêter les conteneurs
docker-compose down

# Mise à jour du module
docker-compose exec odoo17 odoo -u mail_courriel -d odoo_db --stop-after-init
```

## 📚 Documentation

- [Rapport technique complet](rapport/Rapport.pdf)

## 👥 Auteurs

**EMSI - Projet de fin d'études 5IIR**

