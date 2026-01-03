{
    "name": "Gestion des Courriels",
    "version": "17.0.4.0.0",
    "summary": "Module de gestion des courriels avec interface style Outlook",
    "description": """
        Module complet de gestion des courriels pour Odoo 17.
        
        Fonctionnalités:
        - Interface style Outlook avec 3 panneaux
        - Création et envoi de courriels
        - Réception des emails via IMAP
        - Gestion des dossiers (Boîte de réception, Envoyés, Brouillons, Archives, Spam)
        - Étiquettes personnalisables (Urgent, RH, Facture, Client, Interne)
        - Suivi des statuts (brouillon, envoyé, lu, archivé)
        - Gestion des priorités
        - Pièces jointes
        - Intégration SMTP pour l'envoi
    """,
    "category": "Productivity",
    "author": "EMSI - Projet de fin d'études",
    "website": "",
    "license": "LGPL-3",
    "depends": ["base", "mail", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_dossier_data.xml",
        "data/mail_etiquette_data.xml",
        "views/mail_courriel_views.xml",
        "views/mail_dossier_views.xml",
        "views/mail_etiquette_views.xml",
        "views/mail_client_action.xml",
        "views/menu_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "mail_courriel/static/src/css/mail_client.css",
            "mail_courriel/static/src/js/mail_client.js",
            "mail_courriel/static/src/xml/mail_client.xml",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
