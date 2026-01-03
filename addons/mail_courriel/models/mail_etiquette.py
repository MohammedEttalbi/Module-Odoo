from odoo import models, fields


class MailEtiquette(models.Model):
    _name = "mail.etiquette"
    _description = "Étiquette de courriel"
    _order = "sequence, name"

    name = fields.Char(
        string="Nom",
        required=True,
        translate=True
    )
    
    color = fields.Integer(
        string="Couleur",
        default=0,
        help="Couleur de l'étiquette (0-11)"
    )
    
    sequence = fields.Integer(
        string="Séquence",
        default=10
    )
    
    description = fields.Text(
        string="Description"
    )
    
    active = fields.Boolean(
        string="Actif",
        default=True
    )
    
    courriel_ids = fields.Many2many(
        "mail.courriel",
        "mail_courriel_etiquette_rel",
        "etiquette_id",
        "courriel_id",
        string="Courriels"
    )
    
    courriel_count = fields.Integer(
        string="Nombre de courriels",
        compute="_compute_courriel_count"
    )

    def _compute_courriel_count(self):
        for etiquette in self:
            etiquette.courriel_count = len(etiquette.courriel_ids)

    def action_view_courriels(self):
        """Ouvrir la liste des courriels avec cette étiquette"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Courriels - {self.name}",
            "res_model": "mail.courriel",
            "view_mode": "tree,form",
            "domain": [("etiquette_ids", "in", [self.id])],
        }
