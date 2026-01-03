from odoo import models, fields, api
from odoo.exceptions import UserError
import email
import re


class MailCourriel(models.Model):
    _name = "mail.courriel"
    _description = "Courriel"
    _order = "date_envoi desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Champs principaux
    name = fields.Char(
        string="Objet",
        required=True,
        tracking=True
    )
    
    expediteur_id = fields.Many2one(
        "res.partner",
        string="Expéditeur",
        default=lambda self: self.env.user.partner_id,
        tracking=True
    )
    
    expediteur_email = fields.Char(
        string="Email expéditeur"
    )
    
    destinataire_ids = fields.Many2many(
        "res.partner",
        "mail_courriel_destinataire_rel",
        "courriel_id",
        "partner_id",
        string="Destinataires",
    )
    
    destinataire_email = fields.Char(
        string="Email destinataire"
    )
    
    cc_ids = fields.Many2many(
        "res.partner",
        "mail_courriel_cc_rel",
        "courriel_id",
        "partner_id",
        string="CC"
    )
    
    contenu = fields.Html(
        string="Contenu",
        sanitize=True
    )
    
    date_envoi = fields.Datetime(
        string="Date d'envoi",
        default=fields.Datetime.now,
        tracking=True
    )
    
    date_reception = fields.Datetime(
        string="Date de réception"
    )
    
    # Statut et priorité
    statut = fields.Selection([
        ("brouillon", "Brouillon"),
        ("a_envoyer", "À envoyer"),
        ("envoye", "Envoyé"),
        ("lu", "Lu"),
        ("archive", "Archivé"),
        ("echec", "Échec d'envoi"),
    ], string="Statut", default="brouillon", tracking=True)
    
    priorite = fields.Selection([
        ("0", "Basse"),
        ("1", "Normale"),
        ("2", "Haute"),
        ("3", "Urgente"),
    ], string="Priorité", default="1")
    
    # Relations
    dossier_id = fields.Many2one(
        "mail.dossier",
        string="Dossier",
        default=lambda self: self._get_default_dossier(),
        tracking=True
    )
    
    etiquette_ids = fields.Many2many(
        "mail.etiquette",
        "mail_courriel_etiquette_rel",
        "courriel_id",
        "etiquette_id",
        string="Étiquettes"
    )
    
    # Pièces jointes
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "mail_courriel_attachment_rel",
        "courriel_id",
        "attachment_id",
        string="Pièces jointes"
    )
    
    attachment_count = fields.Integer(
        string="Nombre de pièces jointes",
        compute="_compute_attachment_count"
    )
    
    # Champs techniques
    is_entrant = fields.Boolean(
        string="Courriel entrant",
        default=False
    )
    
    mail_mail_id = fields.Many2one(
        "mail.mail",
        string="Mail Odoo",
        readonly=True
    )
    
    message_id = fields.Char(
        string="Message-ID",
        readonly=True,
        help="Identifiant unique du message email"
    )
    
    error_message = fields.Text(
        string="Message d'erreur",
        readonly=True
    )

    @api.model
    def _get_default_dossier(self):
        """Retourne le dossier Brouillons par défaut"""
        return self.env["mail.dossier"].search([("code", "=", "draft")], limit=1)

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Crée un nouveau courriel à partir d'un email entrant (fetchmail/IMAP).
        Cette méthode est appelée automatiquement par Odoo lors de la réception d'emails.
        """
        if custom_values is None:
            custom_values = {}
        
        # Extraire les informations du message
        subject = msg_dict.get('subject', 'Sans objet')
        email_from = msg_dict.get('email_from', '')
        email_to = msg_dict.get('to', '')
        body = msg_dict.get('body', '')
        message_id = msg_dict.get('message_id', '')
        date = msg_dict.get('date', fields.Datetime.now())
        
        # Trouver ou créer le partenaire expéditeur
        partner_from = self._find_or_create_partner(email_from)
        
        # Trouver le dossier Inbox (Boîte de réception)
        dossier_inbox = self.env["mail.dossier"].search([("code", "=", "inbox")], limit=1)
        
        # Préparer les valeurs du courriel entrant
        values = {
            'name': subject or 'Sans objet',
            'expediteur_id': partner_from.id if partner_from else False,
            'expediteur_email': email_from,
            'destinataire_email': email_to,
            'contenu': body,
            'date_reception': date,
            'date_envoi': date,
            'is_entrant': True,
            'statut': 'envoye',  # Statut "non lu" pour email reçu
            'dossier_id': dossier_inbox.id if dossier_inbox else False,
            'message_id': message_id,
        }
        values.update(custom_values)
        
        # Créer directement l'enregistrement sans passer par super()
        # pour éviter les comportements par défaut de mail.thread
        record = self.create(values)
        return record

    @api.model
    def _find_or_create_partner(self, email_address):
        """Trouve ou crée un partenaire à partir d'une adresse email"""
        if not email_address:
            return False
        
        # Extraire l'email de la chaîne (peut être "Name <email@example.com>")
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', email_address)
        if not email_match:
            return False
        
        clean_email = email_match.group(0).lower()
        
        # Chercher un partenaire existant
        partner = self.env['res.partner'].search([
            ('email', '=ilike', clean_email)
        ], limit=1)
        
        if not partner:
            # Extraire le nom si présent
            name_match = re.match(r'^"?([^"<]+)"?\s*<', email_address)
            name = name_match.group(1).strip() if name_match else clean_email
            
            partner = self.env['res.partner'].create({
                'name': name,
                'email': clean_email,
            })
        
        return partner

    def action_envoyer(self):
        """Envoyer le courriel via SMTP"""
        for courriel in self:
            if not courriel.destinataire_ids:
                raise UserError("Veuillez sélectionner au moins un destinataire.")
            
            # Créer le mail.mail
            mail_values = {
                "subject": courriel.name,
                "body_html": courriel.contenu,
                "email_from": courriel.expediteur_id.email or self.env.user.email,
                "recipient_ids": [(6, 0, courriel.destinataire_ids.ids)],
                "attachment_ids": [(6, 0, courriel.attachment_ids.ids)],
            }
            
            mail = self.env["mail.mail"].create(mail_values)
            courriel.mail_mail_id = mail.id
            courriel.statut = "a_envoyer"
            
            # Envoyer immédiatement
            try:
                mail.send()
                if mail.state == "sent":
                    courriel.statut = "envoye"
                    courriel.date_envoi = fields.Datetime.now()
                    # Déplacer vers Envoyés
                    dossier_envoyes = self.env["mail.dossier"].search([("code", "=", "sent")], limit=1)
                    if dossier_envoyes:
                        courriel.dossier_id = dossier_envoyes
                else:
                    courriel.statut = "echec"
                    courriel.error_message = mail.failure_reason
            except Exception as e:
                courriel.statut = "echec"
                courriel.error_message = str(e)
        
        return True

    def action_archiver(self):
        """Archiver le courriel"""
        dossier_archive = self.env["mail.dossier"].search([("code", "=", "archive")], limit=1)
        for courriel in self:
            courriel.statut = "archive"
            if dossier_archive:
                courriel.dossier_id = dossier_archive
        return True

    def action_marquer_lu(self):
        """Marquer le courriel comme lu"""
        for courriel in self:
            if courriel.statut in ["envoye", "brouillon"]:
                courriel.statut = "lu"
        return True

    def action_marquer_non_lu(self):
        """Marquer le courriel comme non lu"""
        for courriel in self:
            if courriel.statut == "lu":
                courriel.statut = "envoye"
        return True

    def action_spam(self):
        """Déplacer vers Spam"""
        dossier_spam = self.env["mail.dossier"].search([("code", "=", "spam")], limit=1)
        for courriel in self:
            if dossier_spam:
                courriel.dossier_id = dossier_spam
        return True

    def action_restaurer(self):
        """Restaurer depuis les archives ou spam"""
        dossier_inbox = self.env["mail.dossier"].search([("code", "=", "inbox")], limit=1)
        for courriel in self:
            courriel.statut = "lu" if courriel.is_entrant else "envoye"
            if dossier_inbox:
                courriel.dossier_id = dossier_inbox
        return True

    @api.model
    def fetch_incoming_emails(self):
        """
        Action planifiée pour récupérer les emails entrants.
        À appeler via un cron job.
        """
        fetchmail_servers = self.env['fetchmail.server'].search([('state', '=', 'done')])
        for server in fetchmail_servers:
            server.fetch_mail()
        return True
