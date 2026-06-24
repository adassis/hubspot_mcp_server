# =============================================================
# tools/emails.py — Outils MCP : Emails HubSpot
# =============================================================
# Deux outils :
#   1. search_emails  → recherche full-text sur tous les emails
#   2. get_emails     → emails bruts liés à un ticket ou un deal
#
# Logique get_emails (2 étapes) :
#   Étape 1 : GET /crm/v3/objects/{type}/{id}/associations/emails
#             → récupère les IDs des emails associés
#   Étape 2 : POST /crm/v3/objects/emails/batch/read
#             → récupère le contenu complet de ces emails
# =============================================================

import json
from utils.hubspot import hubspot_get, hubspot_post

# ------------------------------------------------------------------
# Propriétés retournées pour chaque email
# hs_email_direction : "EMAIL" (envoyé), "INCOMING_EMAIL" (reçu),
#                      "FORWARDED_EMAIL" (transféré)
# ------------------------------------------------------------------
EMAIL_PROPERTIES = [
    "hs_email_direction",     # sens : envoyé / reçu / transféré
    "hs_email_subject",       # objet de l'email
    "hs_email_text",          # corps en texte brut
    "hs_email_html",          # corps en HTML
    "hs_email_from_email",    # adresse expéditeur
    "hs_email_to_email",      # adresse(s) destinataire(s)
    "hs_email_status",        # SENT, BOUNCED, FAILED...
    "hs_timestamp",           # date/heure de l'email
    "hubspot_owner_id",       # owner HubSpot associé
    "hs_attachment_ids",      # IDs des pièces jointes (si présentes)
]


def register(mcp):

    # ---------------------------------------------------------------
    # TOOL 1 : search_emails
    # Recherche full-text dans tous les emails HubSpot.
    # Utilise l'endpoint POST /crm/v3/objects/emails/search
    # Le champ "query" cherche dans : sujet, corps, expéditeur.
    # Résultats triés du plus récent au plus ancien.
    # ---------------------------------------------------------------
    @mcp.tool()
    def search_emails(query: str, limit: int = 20) -> str:
        """
        Recherche des emails HubSpot par mots-clés (sujet, corps, expéditeur...).

        Exemples de requêtes utiles :
        - "relance" → tous les emails contenant ce mot
        - "devis accepté" → emails mentionnant cette phrase
        - "pierre@client.com" → emails depuis/vers cette adresse

        Args:
            query : terme(s) de recherche libre
            limit : nombre max de résultats (défaut: 20, max: 100)

        Returns:
            JSON avec la liste des emails et leurs propriétés complètes.
        """
        try:
            body = {
                "query": query,                    # terme de recherche
                "limit": min(limit, 100),          # plafond à 100 (limite HubSpot)
                "properties": EMAIL_PROPERTIES,    # propriétés à retourner
                "sorts": [
                    {
                        "propertyName": "hs_timestamp",  # tri par date
                        "direction": "DESCENDING"         # plus récent en premier
                    }
                ]
            }
            data = hubspot_post("/crm/v3/objects/emails/search", body=body)
            return json.dumps(data, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    # ---------------------------------------------------------------
    # TOOL 2 : get_emails
    # Retourne tous les emails associés à un ticket ou un deal.
    #
    # Étape 1 — Associations :
    #   GET /crm/v3/objects/{object_type}/{object_id}/associations/emails
    #   → Retourne une liste d'IDs d'emails liés à l'objet
    #
    # Étape 2 — Batch read :
    #   POST /crm/v3/objects/emails/batch/read
    #   → Récupère le contenu complet de ces emails en une seule requête
    # ---------------------------------------------------------------
    @mcp.tool()
    def get_emails(object_type: str, object_id: str, limit: int = 50) -> str:
        """
        Retourne tous les emails (envoyés et reçus) liés à un ticket ou un deal.

        Args:
            object_type : "tickets" ou "deals"
            object_id   : identifiant numérique du ticket ou du deal
                          (ex: "12345" — visible dans l'URL HubSpot)
            limit       : nombre max d'emails à retourner (défaut: 50)

        Returns:
            JSON avec :
            - object_type / object_id : contexte de la requête
            - total_emails            : nombre d'emails trouvés
            - emails[]                : liste des emails avec toutes leurs propriétés
              Chaque email contient notamment :
              - hs_email_direction : "EMAIL" (envoyé) ou "INCOMING_EMAIL" (reçu)
              - hs_email_subject   : objet
              - hs_email_text      : corps texte brut
              - hs_email_from_email / hs_email_to_email : expéditeur / destinataire
        """
        try:
            # ----------------------------------------------------------
            # ÉTAPE 1 : récupérer les IDs des emails associés à l'objet
            # Endpoint : GET /crm/v3/objects/{type}/{id}/associations/emails
            # ----------------------------------------------------------
            assoc_path = (
                f"/crm/v3/objects/{object_type}/{object_id}/associations/emails"
            )
            assoc_data = hubspot_get(assoc_path)

            # Extraire les IDs depuis la liste "results"
            email_ids = [
                item["id"]
                for item in (assoc_data.get("results") or [])
            ]

            # Cas : aucun email associé
            if not email_ids:
                return json.dumps({
                    "object_type": object_type,
                    "object_id": object_id,
                    "total_emails": 0,
                    "emails": [],
                    "message": "Aucun email associé à cet objet."
                }, ensure_ascii=False, indent=2)

            # Appliquer la limite demandée
            email_ids = email_ids[:limit]

            # ----------------------------------------------------------
            # ÉTAPE 2 : récupérer le contenu des emails en batch
            # Endpoint : POST /crm/v3/objects/emails/batch/read
            # Plus efficace qu'un appel individuel par email
            # ----------------------------------------------------------
            batch_body = {
                "properties": EMAIL_PROPERTIES,
                "inputs": [{"id": eid} for eid in email_ids]
                # ex: [{"id": "111"}, {"id": "222"}, ...]
            }
            emails_data = hubspot_post(
                "/crm/v3/objects/emails/batch/read",
                body=batch_body
            )

            # Construire la réponse finale avec contexte
            result = {
                "object_type": object_type,
                "object_id": object_id,
                "total_emails": len(email_ids),
                "emails": emails_data.get("results") or []
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "object_type": object_type,
                "object_id": object_id
            }, ensure_ascii=False)
