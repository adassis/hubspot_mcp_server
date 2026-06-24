# =============================================================
# utils/hubspot.py — Client HTTP HubSpot centralisé (synchrone)
# =============================================================
# DIFFÉRENCES CLÉS vs Pipedrive :
# - Auth : Authorization: Bearer ... (header) au lieu de ?api_token= (query)
# - Base URL : api.hubapi.com (fixe, pas de sous-domaine)
# - Propriétés dans un objet "properties": {}
# - Pagination via curseur "after" (paging.next.after)
# - DELETE retourne HTTP 204 No Content (pas de JSON)
# =============================================================

import requests
from config import HUBSPOT_ACCESS_TOKEN

BASE_URL = "https://api.hubapi.com"

def _check_credentials():
    if not HUBSPOT_ACCESS_TOKEN:
        raise RuntimeError(
            "HUBSPOT_ACCESS_TOKEN non configuré. "
            "Vérifiez vos variables d'environnement sur Railway."
        )

def _headers() -> dict:
    _check_credentials()
    return {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

def hubspot_get(path: str, params: dict = None) -> dict:
    r = requests.get(BASE_URL + path, headers=_headers(), params=params or {}, timeout=30)
    if not r.ok:
        raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()

def hubspot_post(path: str, body: dict) -> dict:
    r = requests.post(BASE_URL + path, headers=_headers(), json=body, timeout=30)
    if not r.ok:
        raise RuntimeError(f"POST {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()

def hubspot_patch(path: str, body: dict) -> dict:
    r = requests.patch(BASE_URL + path, headers=_headers(), json=body, timeout=30)
    if not r.ok:
        raise RuntimeError(f"PATCH {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()

def hubspot_delete(path: str) -> dict:
    r = requests.delete(BASE_URL + path, headers=_headers(), timeout=30)
    if not r.ok:
        raise RuntimeError(f"DELETE {path} → HTTP {r.status_code}: {r.text[:400]}")
    if r.status_code == 204:
        return {"success": True, "message": "Objet supprimé avec succès."}
    return r.json()

def hubspot_associate(
    from_object_type: str,
    from_object_id: str,
    to_object_type: str,
    to_object_id: str,
    association_type_id: int = None  # ignoré, conservé pour compatibilité
) -> dict:
    """
    Crée une association par défaut entre deux objets CRM HubSpot.
    Utilise l'endpoint /associations/default — pas besoin de typeId.
    
    PUT /crm/objects/2026-03/{from}/{fromId}/associations/default/{to}/{toId}
    """
    path = (
        f"/crm/objects/2026-03/{from_object_type}/{from_object_id}"
        f"/associations/default/{to_object_type}/{to_object_id}"
    )
    r = requests.put(
        BASE_URL + path,
        headers=_headers(),
        timeout=30
    )
    if not r.ok:
        raise RuntimeError(
            f"ASSOCIATE {from_object_type}→{to_object_type} "
            f"→ HTTP {r.status_code}: {r.text[:400]}"
        )
    # PUT /associations/default retourne HTTP 200 avec un body ou HTTP 204
    if r.status_code == 204 or not r.text:
        return {"success": True}
    return r.json()
def hubspot_paginate_all(path: str, params: dict = None, max_items: int = 500) -> list:
    """
    Récupère toutes les pages d'un endpoint HubSpot.
    Pagination via curseur "after" (paging.next.after).
    """
    all_items = []
    base_params = {"limit": 100}
    if params:
        base_params.update(params)

    after = None

    while True:
        if after:
            base_params["after"] = after

        r = requests.get(BASE_URL + path, headers=_headers(), params=base_params, timeout=30)
        if not r.ok:
            raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")

        data = r.json()
        items = data.get("results") or []
        all_items.extend(items)

        paging = data.get("paging") or {}
        after = (paging.get("next") or {}).get("after")

        if not after or len(all_items) >= max_items:
            break

    return all_items[:max_items]
