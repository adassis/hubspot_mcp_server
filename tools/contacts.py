# =============================================================
# tools/contacts.py — Outils MCP : Contacts HubSpot
# =============================================================
# Équivalent de tools/persons.py Pipedrive.
# "Persons" Pipedrive = "Contacts" HubSpot.
#
# Différences vs Pipedrive :
# - name unique → firstname + lastname séparés
# - Recherche via POST /search
# =============================================================

import json
from utils.hubspot import hubspot_get, hubspot_post, hubspot_patch, hubspot_delete

CONTACT_PROPERTIES = [
    "firstname", "lastname", "email", "phone",
    "company", "jobtitle", "hubspot_owner_id",
    "createdate", "hs_lastmodifieddate",
    "lifecyclestage", "associatedcompanyid"
]

def register(mcp):

    @mcp.tool()
    def get_contacts(limit: int = 50, after: str = "") -> str:
        """
        Liste les contacts HubSpot avec pagination optionnelle.

        Args:
            limit : nombre max de contacts (défaut: 50, max: 100)
            after : curseur de pagination

        Returns:
            JSON avec la liste des contacts.
        """
        try:
            params = {"limit": min(limit, 100), "properties": ",".join(CONTACT_PROPERTIES)}
            if after:
                params["after"] = after
            data = hubspot_get("/crm/v3/objects/contacts", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def search_contacts(term: str, limit: int = 20) -> str:
        """
        Recherche des contacts par terme textuel (nom, email, téléphone, entreprise).

        Args:
            term  : terme de recherche
            limit : nombre max de résultats (défaut: 20)

        Returns:
            JSON avec les contacts correspondants.
        """
        try:
            body = {"query": term, "limit": min(limit, 100), "properties": CONTACT_PROPERTIES}
            data = hubspot_post("/crm/v3/objects/contacts/search", body=body)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def get_contact(contact_id: str) -> str:
        """
        Retourne les détails complets d'un contact.

        Args:
            contact_id : identifiant numérique du contact

        Returns:
            JSON avec toutes les propriétés du contact.
        """
        try:
            params = {"properties": ",".join(CONTACT_PROPERTIES)}
            data = hubspot_get(f"/crm/v3/objects/contacts/{contact_id}", params=params)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "contact_id": contact_id}, ensure_ascii=False)

    @mcp.tool()
    def create_contact(
        firstname: str,
        lastname: str = "",
        email: str = "",
        phone: str = "",
        company: str = "",
        jobtitle: str = "",
        hubspot_owner_id: str = ""
    ) -> str:
        """
        Crée un nouveau contact dans HubSpot.

        Note : contrairement à Pipedrive (champ "name" unique),
        HubSpot sépare le prénom (firstname) et le nom (lastname).

        Args:
            firstname        : prénom du contact (obligatoire)
            lastname         : nom de famille
            email            : adresse email principale
            phone            : numéro de téléphone
            company          : nom de l'entreprise (texte libre)
            jobtitle         : intitulé du poste
            hubspot_owner_id : ID de l'owner (via list_hubspot_owners)

        Returns:
            JSON avec le contact créé et son identifiant.
        """
        try:
            properties = {"firstname": firstname}
            if lastname:          properties["lastname"] = lastname
            if email:             properties["email"] = email
            if phone:             properties["phone"] = phone
            if company:           properties["company"] = company
            if jobtitle:          properties["jobtitle"] = jobtitle
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id

            data = hubspot_post("/crm/v3/objects/contacts", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    @mcp.tool()
    def update_contact(
        contact_id: str,
        firstname: str = "",
        lastname: str = "",
        email: str = "",
        phone: str = "",
        company: str = "",
        jobtitle: str = "",
        hubspot_owner_id: str = ""
    ) -> str:
        """
        Met à jour un contact existant. Seuls les champs fournis sont modifiés.

        Args:
            contact_id       : identifiant du contact (obligatoire)
            firstname        : nouveau prénom
            lastname         : nouveau nom
            email            : nouvel email
            phone            : nouveau téléphone
            company          : nouveau nom d'entreprise
            jobtitle         : nouveau poste
            hubspot_owner_id : nouvel owner

        Returns:
            JSON avec le contact mis à jour.
        """
        try:
            properties = {}
            if firstname:         properties["firstname"] = firstname
            if lastname:          properties["lastname"] = lastname
            if email:             properties["email"] = email
            if phone:             properties["phone"] = phone
            if company:           properties["company"] = company
            if jobtitle:          properties["jobtitle"] = jobtitle
            if hubspot_owner_id:  properties["hubspot_owner_id"] = hubspot_owner_id

            if not properties:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = hubspot_patch(f"/crm/v3/objects/contacts/{contact_id}", body={"properties": properties})
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "contact_id": contact_id}, ensure_ascii=False)

    @mcp.tool()
    def delete_contact(contact_id: str) -> str:
        """
        Supprime un contact HubSpot.

        Args:
            contact_id : identifiant du contact à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = hubspot_delete(f"/crm/v3/objects/contacts/{contact_id}")
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "contact_id": contact_id}, ensure_ascii=False)