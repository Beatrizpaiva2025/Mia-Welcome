# ============================================================
# ROTAS ADMINISTRATIVAS PRINCIPAIS
# ============================================================
# Login, Dashboard, Estatísticas
# ============================================================

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

# Importar banco de dados
from admin_training_routes import get_database
db = get_database()

# ============================================================
# CREDENCIAIS (em produção, usar variáveis de ambiente)
# ============================================================
ADMIN_CREDENTIALS = {
    "admin": os.getenv("ADMIN_PASSWORD", "admin123"),
    "legacy": os.getenv("LEGACY_PASSWORD", "legacy123")
}

# ============================================================
# LOGIN
# ============================================================
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Processa login"""
    try:
        username_lower = username.lower()
        
        if username_lower in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username_lower] == password:
            request.session['username'] = username_lower
            logger.info(f"✅ Login bem-sucedido: {username_lower}")
            return RedirectResponse(url="/admin/dashboard", status_code=303)
        else:
            logger.warning(f"❌ Tentativa de login falhou: {username}")
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Usuário ou senha inválidos"
            })
    except Exception as e:
        logger.error(f"❌ Erro no login: {e}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Erro ao processar login"
        })

@router.get("/logout")
async def logout(request: Request):
    """Faz logout"""
    request.session.clear()
    return RedirectResponse(url="/admin/login")

# ============================================================
# DASHBOARD
# ============================================================
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard principal"""
    try:
        username = request.session.get('username')
        if not username:
            return RedirectResponse(url="/admin/login")
        
        # Buscar estatísticas
        stats = await get_stats()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "username": username,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"❌ Erro ao carregar dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# API: ESTATÍSTICAS
# ============================================================
@router.get("/api/stats")
async def get_stats():
    """Retorna estatísticas do sistema"""
    try:
        # Total de conversas
        total_conversas = await db.conversas.count_documents({})
        
        # Conversas hoje
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conversas_hoje = await db.conversas.count_documents({"timestamp": {"$gte": hoje}})
        
        # Conversas por canal
        pipeline_canal = [
            {"$group": {"_id": "$canal", "count": {"$sum": 1}}}
        ]
        conversas_por_canal = await db.conversas.aggregate(pipeline_canal).to_list(length=10)
        
        # Últimas conversas
        ultimas_conversas = await db.conversas.find().sort("timestamp", -1).limit(10).to_list(length=10)
        
        # Formatar conversas
        for conv in ultimas_conversas:
            conv["_id"] = str(conv["_id"])
            conv["timestamp"] = conv["timestamp"].isoformat() if isinstance(conv["timestamp"], datetime) else str(conv["timestamp"])
        
        # Total de leads
        total_leads = await db.leads.count_documents({})
        
        # Leads por status
        pipeline_leads = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        leads_por_status = await db.leads.aggregate(pipeline_leads).to_list(length=10)
        
        # Status dos canais
        whatsapp_status = await db.channel_config.find_one({"canal": "whatsapp"})
        instagram_status = await db.channel_config.find_one({"canal": "instagram"})
        web_status = await db.channel_config.find_one({"canal": "web"})
        
        return JSONResponse({
            "total_conversas": total_conversas,
            "conversas_hoje": conversas_hoje,
            "conversas_por_canal": {item["_id"]: item["count"] for item in conversas_por_canal},
            "ultimas_conversas": ultimas_conversas,
            "total_leads": total_leads,
            "leads_por_status": {item["_id"]: item["count"] for item in leads_por_status},
            "canais": {
                "whatsapp": whatsapp_status.get("enabled", True) if whatsapp_status else True,
                "instagram": instagram_status.get("enabled", False) if instagram_status else False,
                "web": web_status.get("enabled", False) if web_status else False
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: CONVERSAS RECENTES
# ============================================================
@router.get("/api/conversas")
async def get_conversas(request: Request, limit: int = 50, canal: Optional[str] = None):
    """Retorna conversas recentes"""
    try:
        username = request.session.get('username')
        if not username:
            return JSONResponse({"error": "Not authenticated"}, status_code=401)
        
        query = {}
        if canal:
            query["canal"] = canal
        
        conversas = await db.conversas.find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
        
        # Formatar conversas
        for conv in conversas:
            conv["_id"] = str(conv["_id"])
            conv["timestamp"] = conv["timestamp"].isoformat() if isinstance(conv["timestamp"], datetime) else str(conv["timestamp"])
        
        return JSONResponse(conversas)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversas: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: CONVERSAS POR CLIENTE
# ============================================================
@router.get("/api/conversas/{phone}")
async def get_conversas_cliente(request: Request, phone: str, canal: str = "whatsapp"):
    """Retorna histórico de conversas de um cliente específico"""
    try:
        username = request.session.get('username')
        if not username:
            return JSONResponse({"error": "Not authenticated"}, status_code=401)
        
        conversas = await db.conversas.find({"phone": phone, "canal": canal}).sort("timestamp", 1).to_list(length=1000)
        
        # Formatar conversas
        for conv in conversas:
            conv["_id"] = str(conv["_id"])
            conv["timestamp"] = conv["timestamp"].isoformat() if isinstance(conv["timestamp"], datetime) else str(conv["timestamp"])
        
        return JSONResponse(conversas)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversas do cliente: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
