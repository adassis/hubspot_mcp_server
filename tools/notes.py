# =============================================================
# tools/notes.py — Outils MCP : Notes HubSpot
# =============================================================
# Équivalent de tools/notes.py Pipedrive.
#
# Différences vs Pipedrive :
# - Endpoint unifié /crm/v3/objects/notes (comme tous les objets)
# - Body dans la propriété "hs_note_body"
# - PATCH (pas PUT) pour les mises à jour
# - Associations via API v4 après création
#
# AssociationTypeIds :
# - note → contact : 202
# - note → deal    : 214
# - note → ticket  : 216
# =============================================================

import json
from datetime import datetime, timezone
from utils.hubspot import hubspot_get, hubspot_post, hubspot_patch, hubspot_delete, hubspot_associate

NOTE_PROPERTIES = [
    "hs_note_body", "hs_timestamp",
    "hubspot_owner_id", "createdate", "hs_lastmodifieddate"
]

NOTE_TO_CONTACT_TYPE_ID = 202
NOTE_TO_DEAL_TYPE_ID    = 214
NOTE_TO_TICKET_TYPE_ID  = 216

def register(mcp):

    @mcp.tool()
    def get_notes(limit: int = 50, after: str = "") -> str:
        """
        Liste les notes HubSpot avec pagination optionnelle.

        Args:
            limit : nombre max de notes (défaut: 50, max: 100)
            after : curseur de pagination

        Returns:
            JSON avec la liste des notes.
        """
        try:
            params = {"limit": min(limit, 100), "properties": ",".join(NOTE_PROPERTIES)}
            if after:
                params["after"] = after
            data = hubspot_get("/crm/v3/objects/notes", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def get_note(note_id: str) -> str:
        """
        Retourne le contenu et les détails d'une note spécifique.

        Args:
            note_id : identifiant numérique de la note

        Returns:
            JSON avec le contenu (hs_note_body) et les métadonnées.
        """
        try:
            params = {"properties": ",".join(NOTE_PROPERTIES)}
            data = hubspot_get(f"/crm/v3/objects/notes/{note_id}", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "note_id": note_id}, ensure_ascii=False)

    @mcp.tool()
    def create_note(
        content: str,
        deal_id: str = "",
        contact_id: str = "",
        ticket_id: str = "",
        hubspot_owner_id: str = ""
    ) -> str:
        """
        Crée une note et l'associe aux objets CRM indiqués.

        La note doit être associée à au moins un objet (deal, contact ou ticket).
        Les associations sont créées automatiquement après la création de la note.

        Args:
            content          : contenu texte de la note (obligatoire)
            deal_id          : ID du deal auquel attacher la note
            contact_id       : ID du contact auquel attacher la note
            ticket_id        : ID du ticket auquel attacher la note
            hubspot_owner_id : ID de l'owner de la note

        Returns:
            JSON avec la note créée et le statut des associations.
        """
        try:
            if not deal_id and not contact_id and not ticket_id:
                return json.dumps({
                    "error": "Fournissez au moins deal_id, contact_id ou ticket_id."
                }, ensure_ascii=False)

            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            properties = {"hs_note_body": content, "hs_timestamp": now_iso}
            if hubspot_owner_id:
                properties["hubspot_owner_id"] = hubspot_owner_id

            note_data = hubspot_post("/crm/v3/objects/notes", body={"properties": properties})
            note_id = note_data.get("id")

            associations_results = []
            if note_id:
                for obj_type, obj_id, type_id in [
                    ("deals",    deal_id,    NOTE_TO_DEAL_TYPE_ID),
                    ("contacts", contact_id, NOTE_TO_CONTACT_TYPE_ID),
                    ("tickets",  ticket_id,  NOTE_TO_TICKET_TYPE_ID),
                ]:
                    if obj_id:
                        try:
                            hubspot_associate("notes", note_id, obj_type, obj_id, type_id)
                            associations_results.append({"type": obj_type, "id": obj_id, "status": "ok"})
                        except Exception as assoc_err:
                            associations_results.append({"type": obj_type, "id": obj_id, "status": "error", "error": str(assoc_err)})

            note_data["_associations"] = associations_results
            return json.dumps(note_data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def update_note(note_id: str, content: str) -> str:
        """
        Met à jour le contenu d'une note existante.

        Note : HubSpot utilise PATCH (pas PUT comme Pipedrive v1).

        Args:
            note_id : identifiant de la note (obligatoire)
            content : nouveau contenu texte (obligatoire)

        Returns:
            JSON avec la note mise à jour.
        """
        try:
            data = hubspot_patch(
                f"/crm/v3/objects/notes/{note_id}",
                body={"properties": {"hs_note_body": content}}
            )
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "note_id": note_id}, ensure_ascii=False)

    @mcp.tool()
    def delete_note(note_id: str) -> str:
        """
        Supprime une note HubSpot.

        Args:
            note_id : identifiant de la note à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = hubspot_delete(f"/crm/v3/objects/notes/{note_id}")
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "note_id": note_id}, ensure_ascii=False)