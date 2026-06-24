# =============================================================
# tools/deals.py — Outils MCP : Deals HubSpot
# =============================================================
# Équivalent de tools/deals.py Pipedrive.
# Deals = opportunités commerciales (pipeline sales).
#
# Différences vs Pipedrive :
# - Propriétés dans {"properties": {}}
# - Recherche via POST /search
# - Pas de "status" open/won/lost → dealstage + pipeline
# - closedate au format ISO : YYYY-MM-DDTHH:MM:SS.000Z
# =============================================================

import json
from utils.hubspot import hubspot_get, hubspot_post, hubspot_patch, hubspot_delete

DEAL_PROPERTIES = [
    "dealname", "amount", "dealstage", "pipeline",
    "closedate", "hubspot_owner_id", "description",
    "hs_deal_stage_probability", "createdate", "hs_lastmodifieddate"
]

def register(mcp):

    @mcp.tool()
    def get_deals(limit: int = 50, after: str = "") -> str:
        """
        Liste les deals HubSpot avec pagination optionnelle.

        Args:
            limit : nombre max de deals (défaut: 50, max: 100)
            after : curseur de pagination (paging.next.after de la réponse précédente)

        Returns:
            JSON avec la liste des deals.
        """
        try:
            params = {"limit": min(limit, 100), "properties": ",".join(DEAL_PROPERTIES)}
            if after:
                params["after"] = after
            data = hubspot_get("/crm/v3/objects/deals", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def search_deals(term: str, limit: int = 20) -> str:
        """
        Recherche des deals par terme textuel (nom, description...).

        Args:
            term  : terme de recherche
            limit : nombre max de résultats (défaut: 20)

        Returns:
            JSON avec les deals correspondants.
        """
        try:
            body = {"query": term, "limit": min(limit, 100), "properties": DEAL_PROPERTIES}
            data = hubspot_post("/crm/v3/objects/deals/search", body=body)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def get_deal(deal_id: str) -> str:
        """
        Retourne tous les détails d'un deal spécifique.

        Args:
            deal_id : identifiant numérique du deal

        Returns:
            JSON avec toutes les propriétés du deal.
        """
        try:
            params = {"properties": ",".join(DEAL_PROPERTIES)}
            data = hubspot_get(f"/crm/v3/objects/deals/{deal_id}", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)

    @mcp.tool()
    def create_deal(
        dealname: str,
        amount: str = "",
        pipeline: str = "default",
        dealstage: str = "",
        closedate: str = "",
        hubspot_owner_id: str = "",
        description: str = ""
    ) -> str:
        """
        Crée un nouveau deal dans HubSpot.

        Args:
            dealname         : nom du deal (obligatoire)
            amount           : valeur monétaire (ex: "15000")
            pipeline         : ID du pipeline (défaut: "default")
            dealstage        : ID de l'étape du pipeline
                               Valeurs communes : "appointmentscheduled",
                               "qualifiedtobuy", "presentationscheduled",
                               "decisionmakerboughtin", "contractsent",
                               "closedwon", "closedlost"
            closedate        : date de clôture prévue (YYYY-MM-DD)
            hubspot_owner_id : ID de l'owner (via list_hubspot_owners)
            description      : description libre

        Returns:
            JSON avec le deal créé et son identifiant.
        """
        try:
            properties = {"dealname": dealname, "pipeline": pipeline}
            if amount:            properties["amount"] = amount
            if dealstage:         properties["dealstage"] = dealstage
            if closedate:         properties["closedate"] = f"{closedate}T00:00:00.000Z"
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id
            if description:       properties["description"] = description

            data = hubspot_post("/crm/v3/objects/deals", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def update_deal(
        deal_id: str,
        dealname: str = "",
        amount: str = "",
        pipeline: str = "",
        dealstage: str = "",
        closedate: str = "",
        hubspot_owner_id: str = "",
        description: str = ""
    ) -> str:
        """
        Met à jour un deal existant. Seuls les champs fournis sont modifiés.

        Args:
            deal_id          : identifiant du deal (obligatoire)
            dealname         : nouveau nom
            amount           : nouvelle valeur
            pipeline         : nouveau pipeline
            dealstage        : nouvelle étape
            closedate        : nouvelle date de clôture (YYYY-MM-DD)
            hubspot_owner_id : nouvel owner
            description      : nouvelle description

        Returns:
            JSON avec le deal mis à jour.
        """
        try:
            properties = {}
            if dealname:          properties["dealname"] = dealname
            if amount:            properties["amount"] = amount
            if pipeline:          properties["pipeline"] = pipeline
            if dealstage:         properties["dealstage"] = dealstage
            if closedate:         properties["closedate"] = f"{closedate}T00:00:00.000Z"
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id
            if description:       properties["description"] = description

            if not properties:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = hubspot_patch(f"/crm/v3/objects/deals/{deal_id}", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)

    @mcp.tool()
    def delete_deal(deal_id: str) -> str:
        """
        Supprime un deal HubSpot.

        Args:
            deal_id : identifiant du deal à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = hubspot_delete(f"/crm/v3/objects/deals/{deal_id}")
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)