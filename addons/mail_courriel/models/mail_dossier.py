from odoo import models, fields, api


class MailDossier(models.Model):
    _name = "mail.dossier"
    _description = "Dossier de courriels"
    _order = "sequence, id"

    name = fields.Char(
        string="Nom",
        required=True,
        translate=True
    )
    
    code = fields.Char(
        string="Code technique",
        required=True,
        help="Code unique pour identifier le dossier (inbox, sent, draft, archive, spam)"
    )
    
    icon = fields.Char(
        string="Icône",
        default="fa-folder",
        help="Classe Font Awesome pour l'icône (ex: fa-inbox, fa-paper-plane)"
    )
    
    sequence = fields.Integer(
        string="Séquence",
        default=10
    )
    
    color = fields.Integer(
        string="Couleur",
        default=0
    )
    
    description = fields.Text(
        string="Description"
    )
    
    is_system = fields.Boolean(
        string="Dossier système",
        default=False,
        help="Les dossiers système ne peuvent pas être supprimés"
    )
    
    courriel_ids = fields.One2many(
        "mail.courriel",
        "dossier_id",
        string="Courriels"
    )
    
    courriel_count = fields.Integer(
        string="Nombre de courriels",
        compute="_compute_courriel_count"
    )
    
    courriel_non_lu_count = fields.Integer(
        string="Non lus",
        compute="_compute_courriel_count"
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Le code du dossier doit être unique !")
    ]

    @api.depends("courriel_ids", "courriel_ids.statut")
    def _compute_courriel_count(self):
        for dossier in self:
            courriels = dossier.courriel_ids
            dossier.courriel_count = len(courriels)
            dossier.courriel_non_lu_count = len(courriels.filtered(lambda c: c.statut not in ["lu", "archive"]))

    def action_view_courriels(self):
        """Ouvrir la liste des courriels du dossier"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.name,
            "res_model": "mail.courriel",
            "view_mode": "tree,form",
            "domain": [("dossier_id", "=", self.id)],
            "context": {"default_dossier_id": self.id},
        }

    @api.ondelete(at_uninstall=False)
    def _unlink_except_system(self):
        for dossier in self:
            if dossier.is_system:
                raise models.ValidationError(
                    f"Le dossier système '{dossier.name}' ne peut pas être supprimé."
                )
