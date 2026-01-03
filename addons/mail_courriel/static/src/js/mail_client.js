/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MailCourrielClient extends Component {
    static template = "mail_courriel.MailCourrielClient";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            dossiers: [],
            courriels: [],
            selectedDossier: null,
            selectedCourriel: null,
            loading: true,
            searchQuery: "",
            // États IA
            aiLoading: false,
            aiResult: null,
            aiResultType: null,  // 'summary' ou 'reply'
            showAiDraftModal: false,
            aiDraftPrompt: "",
            aiDraftResult: null,
        });

        onWillStart(async () => {
            await this.loadDossiers();
            if (this.state.dossiers.length > 0) {
                const inbox = this.state.dossiers.find(d => d.code === 'inbox') || this.state.dossiers[0];
                await this.selectDossier(inbox);
            }
            this.state.loading = false;
        });
    }

    async loadDossiers() {
        try {
            this.state.dossiers = await this.orm.searchRead(
                "mail.dossier",
                [],
                ["id", "name", "code", "icon", "courriel_count", "courriel_non_lu_count", "color"],
                { order: "sequence" }
            );
        } catch (e) {
            console.error("Error loading folders:", e);
        }
    }

    async selectDossier(dossier) {
        this.state.selectedDossier = dossier;
        this.state.selectedCourriel = null;
        this.state.aiResult = null;
        try {
            this.state.courriels = await this.orm.searchRead(
                "mail.courriel",
                [["dossier_id", "=", dossier.id]],
                ["id", "name", "expediteur_id", "expediteur_email", "date_envoi", "statut", "priorite", "contenu", "is_entrant", "attachment_count"],
                { order: "date_envoi desc", limit: 100 }
            );
        } catch (e) {
            console.error("Error loading emails:", e);
        }
    }

    async selectCourriel(courriel) {
        this.state.selectedCourriel = courriel;
        this.state.aiResult = null;
        if (courriel.statut === 'envoye' && courriel.is_entrant) {
            try {
                await this.orm.call("mail.courriel", "action_marquer_lu", [[courriel.id]]);
                courriel.statut = 'lu';
                await this.loadDossiers();
            } catch (e) {
                console.error("Error marking as read:", e);
            }
        }
    }

    async nouveauCourriel() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mail.courriel",
            views: [[false, "form"]],
            target: "current",
            context: { default_statut: "brouillon" }
        });
    }

    async openCourriel(courriel) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mail.courriel",
            res_id: courriel.id,
            views: [[false, "form"]],
            target: "current"
        });
    }

    async refreshEmails() {
        if (this.state.selectedDossier) {
            await this.selectDossier(this.state.selectedDossier);
        }
        await this.loadDossiers();
    }

    // ============================================
    // FONCTIONS IA
    // ============================================

    async aiSummarize() {
        if (!this.state.selectedCourriel) return;

        this.state.aiLoading = true;
        this.state.aiResult = null;

        try {
            const result = await this.orm.call(
                "mail.ai",
                "summarize_email",
                [this.state.selectedCourriel.name || "", this.state.selectedCourriel.contenu || ""]
            );
            this.state.aiResult = result;
            this.state.aiResultType = 'summary';
            this.notification.add("Résumé généré avec succès", { type: "success" });
        } catch (e) {
            console.error("AI Summarize error:", e);
            this.notification.add("Erreur lors de la génération du résumé: " + (e.message || e), { type: "danger" });
        } finally {
            this.state.aiLoading = false;
        }
    }

    async aiSuggestReply() {
        if (!this.state.selectedCourriel) return;

        this.state.aiLoading = true;
        this.state.aiResult = null;

        try {
            const senderName = this.getSenderName(this.state.selectedCourriel);
            const result = await this.orm.call(
                "mail.ai",
                "suggest_reply",
                [
                    this.state.selectedCourriel.name || "",
                    this.state.selectedCourriel.contenu || "",
                    senderName
                ]
            );
            this.state.aiResult = result;
            this.state.aiResultType = 'reply';
            this.notification.add("Réponse suggérée générée", { type: "success" });
        } catch (e) {
            console.error("AI Suggest Reply error:", e);
            this.notification.add("Erreur lors de la génération de la réponse: " + (e.message || e), { type: "danger" });
        } finally {
            this.state.aiLoading = false;
        }
    }

    closeAiResult() {
        this.state.aiResult = null;
        this.state.aiResultType = null;
    }

    async useAiReply() {
        if (!this.state.aiResult) return;

        // Ouvrir un nouveau courriel avec la réponse pré-remplie
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mail.courriel",
            views: [[false, "form"]],
            target: "current",
            context: {
                default_statut: "brouillon",
                default_name: "Re: " + (this.state.selectedCourriel?.name || ""),
                default_contenu: this.state.aiResult,
                default_destinataire_ids: this.state.selectedCourriel?.expediteur_id ?
                    [[4, this.state.selectedCourriel.expediteur_id[0]]] : [],
            }
        });
    }

    // Modal rédaction IA
    openAiDraftModal() {
        this.state.showAiDraftModal = true;
        this.state.aiDraftPrompt = "";
        this.state.aiDraftResult = null;
    }

    closeAiDraftModal() {
        this.state.showAiDraftModal = false;
        this.state.aiDraftPrompt = "";
        this.state.aiDraftResult = null;
    }

    async generateAiDraft() {
        if (!this.state.aiDraftPrompt) return;

        this.state.aiLoading = true;

        try {
            const result = await this.orm.call(
                "mail.ai",
                "draft_email",
                [this.state.aiDraftPrompt]
            );
            this.state.aiDraftResult = result;
            this.notification.add("Email généré avec succès", { type: "success" });
        } catch (e) {
            console.error("AI Draft error:", e);
            this.notification.add("Erreur lors de la génération: " + (e.message || e), { type: "danger" });
        } finally {
            this.state.aiLoading = false;
        }
    }

    async useAiDraft() {
        if (!this.state.aiDraftResult) return;

        // Générer un sujet basé sur le contenu
        let subject = "";
        try {
            subject = await this.orm.call(
                "mail.ai",
                "generate_subject",
                [this.state.aiDraftResult]
            );
        } catch (e) {
            subject = "Nouveau message";
        }

        // Ouvrir le formulaire avec le contenu pré-rempli
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mail.courriel",
            views: [[false, "form"]],
            target: "current",
            context: {
                default_statut: "brouillon",
                default_name: subject,
                default_contenu: this.state.aiDraftResult,
            }
        });

        this.closeAiDraftModal();
    }

    // ============================================
    // NAVIGATION
    // ============================================

    async openEtiquettes() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Étiquettes",
            res_model: "mail.etiquette",
            views: [[false, "list"], [false, "form"]],
            target: "current"
        });
    }

    async openVueClassique() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Tous les courriels",
            res_model: "mail.courriel",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            target: "current"
        });
    }

    async openDossierConfig() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Gestion des dossiers",
            res_model: "mail.dossier",
            views: [[false, "list"], [false, "form"]],
            target: "current"
        });
    }

    async openEtiquetteConfig() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Gestion des étiquettes",
            res_model: "mail.etiquette",
            views: [[false, "list"], [false, "form"]],
            target: "current"
        });
    }

    async openSettings() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Configuration",
            res_model: "res.config.settings",
            views: [[false, "form"]],
            target: "current",
            context: { module: "mail_courriel" }
        });
    }

    // ============================================
    // UTILITAIRES
    // ============================================

    getIconClass(code) {
        const icons = {
            inbox: "fa-inbox",
            sent: "fa-paper-plane",
            draft: "fa-file-text-o",
            archive: "fa-archive",
            spam: "fa-ban",
        };
        return icons[code] || "fa-folder";
    }

    getStatutBadge(statut) {
        const badges = {
            brouillon: { class: "bg-warning", text: "Brouillon" },
            envoye: { class: "bg-primary", text: "Non lu" },
            lu: { class: "bg-info", text: "Lu" },
            archive: { class: "bg-secondary", text: "Archivé" },
            echec: { class: "bg-danger", text: "Échec" },
        };
        return badges[statut] || { class: "bg-secondary", text: statut };
    }

    getPrioriteIcon(priorite) {
        if (priorite === "3") return "🔴";
        if (priorite === "2") return "🟠";
        return "";
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return date.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
        } else if (diffDays === 1) {
            return "Hier";
        } else if (diffDays < 7) {
            return date.toLocaleDateString("fr-FR", { weekday: "short" });
        }
        return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
    }

    formatFullDate(dateStr) {
        if (!dateStr) return "";
        return new Date(dateStr).toLocaleString("fr-FR", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    stripHtml(html) {
        if (!html) return "";
        const tmp = document.createElement("div");
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || "";
    }

    getPreviewText(html, maxLength = 100) {
        const text = this.stripHtml(html);
        return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
    }

    getSenderInitial(courriel) {
        if (courriel.expediteur_id && courriel.expediteur_id[1]) {
            return courriel.expediteur_id[1].charAt(0).toUpperCase();
        }
        if (courriel.expediteur_email) {
            return courriel.expediteur_email.charAt(0).toUpperCase();
        }
        return "?";
    }

    getSenderName(courriel) {
        if (courriel.expediteur_id && courriel.expediteur_id[1]) {
            return courriel.expediteur_id[1];
        }
        return courriel.expediteur_email || "Expéditeur inconnu";
    }
}

registry.category("actions").add("mail_courriel.client_action", MailCourrielClient);
