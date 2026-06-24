# =============================================================
# tools/owners.py — Outils MCP : Owners HubSpot
# =============================================================
# Équivalent de tools/users.py Pipedrive.
# "Users" Pipedrive = "Owners" HubSpot.
#
# Différences vs Pipedrive :
# - Endpoint : /crm/v3/owners (pas /users)
# - Nom : firstName + lastName séparés (pas "name")
# - Actif : "archived" = false (vs "active_flag" = true)
# =============================================================

import json
from utils.hubspot import hubspot_get

def register(mcp):

    @mcp.tool()
    def list_hubspot_owners(include_archived: bool = False) -> str:
        """
        Liste tous les owners (utilisateurs) du compte HubSpot.

        Utilisez cet outil pour trouver le hubspot_owner_id d'un utilisateur
        avant de lui assigner un deal, ticket, tâche ou note.

        Args:
            include_archived : inclure les owners désactivés (défaut: False)

        Returns:
            JSON avec la liste des owners : id, firstName, lastName, email, archived.
        """
        try:
            params = {}
            if include_archived:
                params["archived"] = "true"

            data = hubspot_get("/crm/v3/owners", params=params)
            owners_raw = data.get("results") or []

            if not owners_raw:
                return json.dumps({"message": "Aucun owner trouvé."}, ensure_ascii=False)

            owners = [
                {
                    "id":        o.get("id"),
                    "firstName": o.get("firstName", ""),
                    "lastName":  o.get("lastName", ""),
                    "email":     o.get("email", ""),
                    "archived":  o.get("archived", False)
                }
                for o in owners_raw
            ]

            return json.dumps(owners, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)