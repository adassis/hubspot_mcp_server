# =============================================================
# server.py — Point d'entrée du serveur MCP HubSpot
# =============================================================
# Pour ajouter un nouvel outil :
# 1. Créer tools/mon_outil.py avec une fonction register(mcp)
# 2. Ajouter l'import + l'appel register() ci-dessous
# =============================================================

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import PORT, MCP_BEARER_TOKEN

import tools.deals
import tools.tickets
import tools.contacts
import tools.notes
import tools.tasks
import tools.owners
import tools.emails 

mcp = FastMCP(
    name="hubspot-server",
    host="0.0.0.0",
    port=PORT,
    instructions=(
        "Serveur MCP HubSpot CRM. "
        "Outils disponibles : gestion des deals (opportunités commerciales), "
        "tickets (support client), contacts, notes, tâches et owners (utilisateurs). "
        "Les deals et les tickets sont deux objets distincts sur HubSpot : "
        "utilisez deals pour les opportunités sales, tickets pour les demandes support. "
        "Toutes les associations (lier une note à un deal, etc.) sont gérées automatiquement."
    )
)

tools.deals.register(mcp)
tools.tickets.register(mcp)
tools.contacts.register(mcp)
tools.notes.register(mcp)
tools.tasks.register(mcp)
tools.owners.register(mcp)
tools.emails.register(mcp)

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if MCP_BEARER_TOKEN:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth[7:].strip() != MCP_BEARER_TOKEN:
                return JSONResponse({"error": "Non autorisé"}, status_code=401)
        return await call_next(request)

if __name__ == "__main__":
    print(f"🚀 Serveur MCP HubSpot démarré sur le port {PORT}")
    print(f"🔐 Auth : {'Activée' if MCP_BEARER_TOKEN else 'DÉSACTIVÉE'}")
    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
