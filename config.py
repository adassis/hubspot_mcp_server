# =============================================================
# config.py — Configuration du serveur MCP HubSpot
# =============================================================

import os

PORT = int(os.environ.get("PORT", 8000))
MCP_BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "")
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")