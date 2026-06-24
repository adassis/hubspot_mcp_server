# =============================================================
# tools/tasks.py — Outils MCP : Tâches HubSpot
# =============================================================
# Équivalent de tools/activities.py Pipedrive.
# "Activities" Pipedrive = "Tasks" HubSpot.
#
# Différences vs Pipedrive :
# - Types : "TODO", "EMAIL", "CALL" (vs call/meeting/task/email/deadline)
# - Statuts : "NOT_STARTED", "IN_PROGRESS", "WAITING", "COMPLETED", "DEFERRED"
# - Date d'échéance : hs_timestamp (ISO 8601)
# - Associations via API v4 après création
#
# AssociationTypeIds :
# - task → contact : 204
# - task → deal    : 216
# - task → ticket  : 278
# =============================================================

import json
from utils.hubspot import hubspot_get, hubspot_post, hubspot_patch, hubspot_delete, hubspot_associate

TASK_PROPERTIES = [
    "hs_task_subject", "hs_task_body", "hs_task_status",
    "hs_task_type", "hs_task_priority", "hs_timestamp",
    "hubspot_owner_id", "createdate", "hs_lastmodifieddate"
]

TASK_TO_CONTACT_TYPE_ID = 204
TASK_TO_DEAL_TYPE_ID    = 216
TASK_TO_TICKET_TYPE_ID  = 278

def register(mcp):

    @mcp.tool()
    def get_tasks(limit: int = 50, after: str = "") -> str:
        """
        Liste les tâches HubSpot avec pagination optionnelle.

        Args:
            limit : nombre max de tâches (défaut: 50, max: 100)
            after : curseur de pagination

        Returns:
            JSON avec la liste des tâches.
        """
        try:
            params = {"limit": min(limit, 100), "properties": ",".join(TASK_PROPERTIES)}
            if after:
                params["after"] = after
            data = hubspot_get("/crm/v3/objects/tasks", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def get_task(task_id: str) -> str:
        """
        Retourne les détails d'une tâche spécifique.

        Args:
            task_id : identifiant numérique de la tâche

        Returns:
            JSON avec toutes les informations de la tâche.
        """
        try:
            params = {"properties": ",".join(TASK_PROPERTIES)}
            data = hubspot_get(f"/crm/v3/objects/tasks/{task_id}", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "task_id": task_id}, ensure_ascii=False)

    @mcp.tool()
    def create_task(
        subject: str,
        task_type: str = "TODO",
        status: str = "NOT_STARTED",
        priority: str = "MEDIUM",
        due_date: str = "",
        body: str = "",
        deal_id: str = "",
        contact_id: str = "",
        ticket_id: str = "",
        hubspot_owner_id: str = ""
    ) -> str:
        """
        Crée une tâche et l'associe aux objets CRM indiqués.

        Args:
            subject          : titre/sujet de la tâche (obligatoire)
            task_type        : "TODO" (défaut), "EMAIL", "CALL"
            status           : "NOT_STARTED" (défaut), "IN_PROGRESS",
                               "WAITING", "COMPLETED", "DEFERRED"
            priority         : "LOW", "MEDIUM" (défaut), "HIGH"
            due_date         : date d'échéance (YYYY-MM-DD)
            body             : description / notes de la tâche
            deal_id          : ID du deal à associer
            contact_id       : ID du contact à associer
            ticket_id        : ID du ticket à associer
            hubspot_owner_id : ID du responsable (via list_hubspot_owners)

        Returns:
            JSON avec la tâche créée et le statut des associations.
        """
        try:
            properties = {
                "hs_task_subject":   subject,
                "hs_task_type":      task_type,
                "hs_task_status":    status,
                "hs_task_priority":  priority
            }
            if due_date:          properties["hs_timestamp"] = f"{due_date}T09:00:00.000Z"
            if body:              properties["hs_task_body"] = body
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id

            task_data = hubspot_post("/crm/v3/objects/tasks", body={"properties": properties})
            task_id = task_data.get("id")

            associations_results = []
            if task_id:
                for obj_type, obj_id, type_id in [
                    ("deals",    deal_id,    TASK_TO_DEAL_TYPE_ID),
                    ("contacts", contact_id, TASK_TO_CONTACT_TYPE_ID),
                    ("tickets",  ticket_id,  TASK_TO_TICKET_TYPE_ID),
                ]:
                    if obj_id:
                        try:
                            hubspot_associate("tasks", task_id, obj_type, obj_id, type_id)
                            associations_results.append({"type": obj_type, "id": obj_id, "status": "ok"})
                        except Exception as assoc_err:
                            associations_results.append({"type": obj_type, "id": obj_id, "status": "error", "error": str(assoc_err)})

            task_data["_associations"] = associations_results
            return json.dumps(task_data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def update_task(
        task_id: str,
        subject: str = "",
        task_type: str = "",
        status: str = "",
        priority: str = "",
        due_date: str = "",
        body: str = "",
        hubspot_owner_id: str = ""
    ) -> str:
        """
        Met à jour une tâche existante. Seuls les champs fournis sont modifiés.
        Pour marquer comme terminée : status="COMPLETED".

        Args:
            task_id          : identifiant de la tâche (obligatoire)
            subject          : nouveau sujet
            task_type        : nouveau type ("TODO", "EMAIL", "CALL")
            status           : nouveau statut
            priority         : nouvelle priorité
            due_date         : nouvelle date d'échéance (YYYY-MM-DD)
            body             : nouvelles notes
            hubspot_owner_id : nouvel owner

        Returns:
            JSON avec la tâche mise à jour.
        """
        try:
            properties = {}
            if subject:           properties["hs_task_subject"] = subject
            if task_type:         properties["hs_task_type"] = task_type
            if status:            properties["hs_task_status"] = status
            if priority:          properties["hs_task_priority"] = priority
            if due_date:          properties["hs_timestamp"] = f"{due_date}T09:00:00.000Z"
            if body:              properties["hs_task_body"] = body
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id

            if not properties:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = hubspot_patch(f"/crm/v3/objects/tasks/{task_id}", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "task_id": task_id}, ensure_ascii=False)

    @mcp.tool()
    def delete_task(task_id: str) -> str:
        """
        Supprime une tâche HubSpot.

        Args:
            task_id : identifiant de la tâche à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = hubspot_delete(f"/crm/v3/objects/tasks/{task_id}")
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "task_id": task_id}, ensure_ascii=False)