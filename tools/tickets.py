# =============================================================
# tools/tickets.py — Outils MCP : Tickets HubSpot
# =============================================================
# NOUVEAU — pas d'équivalent dans le MCP Pipedrive.
# Tickets = demandes support / service client (Service Hub).
# Pipeline distinct des Deals (Sales Hub).
#
# Champs principaux :
# - subject            : titre du ticket
# - content            : description
# - hs_pipeline        : ID du pipeline (défaut "0")
# - hs_pipeline_stage  : ID de l'étape ("1"=New, "2"=Waiting on contact,
#                        "3"=Waiting on us, "4"=Closed)
# - hubspot_owner_id   : agent responsable
# - hs_ticket_priority : "LOW", "MEDIUM", "HIGH"
# =============================================================

import json
from utils.hubspot import hubspot_get, hubspot_post, hubspot_patch, hubspot_delete

TICKET_PROPERTIES = [
    "subject", "content", "hs_pipeline", "hs_pipeline_stage",
    "hubspot_owner_id", "hs_ticket_priority",
    "createdate", "hs_lastmodifieddate", "hs_resolution", "closed_date"
]

def register(mcp):

    @mcp.tool()
    def get_tickets(limit: int = 50, after: str = "") -> str:
        """
        Liste les tickets HubSpot avec pagination optionnelle.

        Args:
            limit : nombre max de tickets (défaut: 50, max: 100)
            after : curseur de pagination

        Returns:
            JSON avec la liste des tickets.
        """
        try:
            params = {"limit": min(limit, 100), "properties": ",".join(TICKET_PROPERTIES)}
            if after:
                params["after"] = after
            data = hubspot_get("/crm/v3/objects/tickets", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def search_tickets(term: str, limit: int = 20) -> str:
        """
        Recherche des tickets par terme textuel (sujet, contenu...).

        Args:
            term  : terme de recherche
            limit : nombre max de résultats (défaut: 20)

        Returns:
            JSON avec les tickets correspondants.
        """
        try:
            body = {"query": term, "limit": min(limit, 100), "properties": TICKET_PROPERTIES}
            data = hubspot_post("/crm/v3/objects/tickets/search", body=body)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def get_ticket(ticket_id: str) -> str:
        """
        Retourne tous les détails d'un ticket spécifique.

        Args:
            ticket_id : identifiant numérique du ticket

        Returns:
            JSON avec toutes les propriétés du ticket.
        """
        try:
            params = {"properties": ",".join(TICKET_PROPERTIES)}
            data = hubspot_get(f"/crm/v3/objects/tickets/{ticket_id}", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "ticket_id": ticket_id}, ensure_ascii=False)

    @mcp.tool()
    def create_ticket(
        subject: str,
        content: str = "",
        hs_pipeline: str = "0",
        hs_pipeline_stage: str = "1",
        hubspot_owner_id: str = "",
        hs_ticket_priority: str = "MEDIUM"
    ) -> str:
        """
        Crée un nouveau ticket dans HubSpot.

        Args:
            subject            : titre du ticket (obligatoire)
            content            : description / corps du ticket
            hs_pipeline        : ID du pipeline service (défaut: "0")
            hs_pipeline_stage  : ID de l'étape initiale (défaut: "1" = New)
                                 Valeurs communes : "1"=New,
                                 "2"=Waiting on contact,
                                 "3"=Waiting on us, "4"=Closed
            hubspot_owner_id   : ID de l'agent responsable
            hs_ticket_priority : "LOW", "MEDIUM" (défaut), "HIGH"

        Returns:
            JSON avec le ticket créé et son identifiant.
        """
        try:
            properties = {
                "subject": subject,
                "hs_pipeline": hs_pipeline,
                "hs_pipeline_stage": hs_pipeline_stage,
                "hs_ticket_priority": hs_ticket_priority
            }
            if content:           properties["content"] = content
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id

            data = hubspot_post("/crm/v3/objects/tickets", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def update_ticket(
        ticket_id: str,
        subject: str = "",
        content: str = "",
        hs_pipeline: str = "",
        hs_pipeline_stage: str = "",
        hubspot_owner_id: str = "",
        hs_ticket_priority: str = ""
    ) -> str:
        """
        Met à jour un ticket existant. Seuls les champs fournis sont modifiés.

        Args:
            ticket_id          : identifiant du ticket (obligatoire)
            subject            : nouveau titre
            content            : nouveau contenu
            hs_pipeline        : nouveau pipeline
            hs_pipeline_stage  : nouvelle étape (pour changer le statut)
            hubspot_owner_id   : nouvel owner
            hs_ticket_priority : nouvelle priorité ("LOW", "MEDIUM", "HIGH")

        Returns:
            JSON avec le ticket mis à jour.
        """
        try:
            properties = {}
            if subject:             properties["subject"] = subject
            if content:             properties["content"] = content
            if hs_pipeline:         properties["hs_pipeline"] = hs_pipeline
            if hs_pipeline_stage:   properties["hs_pipeline_stage"] = hs_pipeline_stage
            if hubspot_owner_id:    properties["hubspot_owner_id"] = hubspot_owner_id
            if hs_ticket_priority:  properties["hs_ticket_priority"] = hs_ticket_priority

            if not properties:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = hubspot_patch(f"/crm/v3/objects/tickets/{ticket_id}", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "ticket_id": ticket_id}, ensure_ascii=False)

    @mcp.tool()
    def delete_ticket(ticket_id: str) -> str:
        """
        Supprime un ticket HubSpot.

        Args:
            ticket_id : identifiant du ticket à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = hubspot_delete(f"/crm/v3/objects/tickets/{ticket_id}")
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "ticket_id": ticket_id}, ensure_ascii=False)