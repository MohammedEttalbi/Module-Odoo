import requests
import json
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailAI(models.AbstractModel):
    _name = "mail.ai"
    _description = "Service IA pour les courriels (LLaMA via Ollama)"

    # Configuration Ollama
    OLLAMA_URL = "http://host.docker.internal:11434"
    MODEL = "llama3.2:latest"
    TIMEOUT = 120  # secondes

    @api.model
    def _call_ollama(self, prompt, system_prompt=None):
        """
        Appelle l'API Ollama avec un prompt donné.
        """
        url = f"{self.OLLAMA_URL}/api/generate"
        
        payload = {
            "model": self.MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            _logger.info(f"Appel Ollama: {self.MODEL}")
            response = requests.post(url, json=payload, timeout=self.TIMEOUT)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.Timeout:
            _logger.error("Timeout lors de l'appel Ollama")
            raise UserError("Le modèle IA met trop de temps à répondre. Veuillez réessayer.")
        except requests.exceptions.ConnectionError:
            _logger.error("Impossible de se connecter à Ollama")
            raise UserError("Impossible de se connecter au service IA. Vérifiez qu'Ollama est en cours d'exécution.")
        except Exception as e:
            _logger.error(f"Erreur Ollama: {str(e)}")
            raise UserError(f"Erreur lors de l'appel IA: {str(e)}")

    @api.model
    def summarize_email(self, subject, content):
        """
        Génère un résumé court d'un email.
        """
        # Nettoyer le contenu HTML
        clean_content = self._strip_html(content)
        
        system_prompt = """Tu es un assistant qui résume des emails de manière concise.
Génère un résumé en 2-3 phrases maximum en français.
Conserve les informations clés: qui, quoi, quand, demandes importantes."""

        prompt = f"""Résume cet email:

Objet: {subject}

Contenu:
{clean_content[:2000]}

Résumé:"""

        return self._call_ollama(prompt, system_prompt)

    @api.model
    def suggest_reply(self, subject, content, sender_name):
        """
        Suggère une réponse professionnelle à un email.
        """
        clean_content = self._strip_html(content)
        
        system_prompt = """Tu es un assistant professionnel qui aide à rédiger des réponses d'emails.
Génère une réponse polie, professionnelle et en français.
La réponse doit être courte (3-5 phrases) mais complète.
Commence directement par la salutation."""

        prompt = f"""Génère une réponse professionnelle à cet email:

De: {sender_name}
Objet: {subject}

Message reçu:
{clean_content[:1500]}

Réponse suggérée:"""

        return self._call_ollama(prompt, system_prompt)

    @api.model
    def draft_email(self, user_prompt, context=None):
        """
        Rédige un email à partir d'une instruction utilisateur.
        """
        system_prompt = """Tu es un assistant qui rédige des emails professionnels en français.
Génère un email complet avec:
- Une salutation appropriée
- Le corps du message clair et professionnel
- Une formule de politesse
Ne génère pas l'objet, seulement le contenu du message."""

        full_prompt = f"""Rédige un email professionnel basé sur cette demande:

{user_prompt}

Email:"""

        return self._call_ollama(full_prompt, system_prompt)

    @api.model
    def generate_subject(self, content):
        """
        Génère un objet d'email basé sur le contenu.
        """
        clean_content = self._strip_html(content)
        
        system_prompt = "Tu génères des objets d'emails courts et pertinents en français. Maximum 10 mots."
        
        prompt = f"""Génère un objet d'email pour ce contenu:

{clean_content[:500]}

Objet:"""

        return self._call_ollama(prompt, system_prompt)

    def _strip_html(self, html_content):
        """
        Supprime les balises HTML du contenu.
        """
        if not html_content:
            return ""
        
        import re
        # Supprimer les balises HTML
        clean = re.sub(r'<[^>]+>', '', html_content)
        # Supprimer les espaces multiples
        clean = re.sub(r'\s+', ' ', clean)
        # Décoder les entités HTML basiques
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&amp;', '&')
        clean = clean.replace('&lt;', '<')
        clean = clean.replace('&gt;', '>')
        clean = clean.replace('&quot;', '"')
        
        return clean.strip()


class MailCourrielAI(models.Model):
    _inherit = "mail.courriel"

    ai_summary = fields.Text(
        string="Résumé IA",
        readonly=True,
        help="Résumé généré automatiquement par l'IA"
    )
    
    ai_suggested_reply = fields.Html(
        string="Réponse suggérée",
        readonly=True,
        help="Réponse suggérée par l'IA"
    )

    def action_ai_summarize(self):
        """
        Action pour résumer l'email avec l'IA.
        """
        self.ensure_one()
        ai_service = self.env["mail.ai"]
        
        summary = ai_service.summarize_email(self.name, self.contenu)
        self.ai_summary = summary
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Résumé IA',
                'message': summary,
                'type': 'success',
                'sticky': True,
            }
        }

    def action_ai_suggest_reply(self):
        """
        Action pour suggérer une réponse avec l'IA.
        """
        self.ensure_one()
        ai_service = self.env["mail.ai"]
        
        sender_name = self.expediteur_id.name if self.expediteur_id else self.expediteur_email
        suggested_reply = ai_service.suggest_reply(self.name, self.contenu, sender_name)
        
        self.ai_suggested_reply = f"<p>{suggested_reply.replace(chr(10), '</p><p>')}</p>"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Réponse suggérée',
                'message': 'La réponse a été générée. Consultez le champ "Réponse suggérée".',
                'type': 'success',
            }
        }
