# ============================================================
# ROTAS DE CONTROLE DO BOT
# ============================================================
# Controle de:
# - Ligar/Desligar Bot
# - Ativar/Desativar Canais
# - Conversas em Tempo Real
# - Modo de Atendimento (IA/Humano)
# ============================================================

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["controle"])
templates = Jinja2Templates(directory="templates")

# Importar banco de dados
from admin_training_routes import get_database
db = get_database()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_current_user(request: Request):
    username = request.session.get('username')
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username

# ============================================================
# PÁGINA DE CONTROLE
# ============================================================
@router.get("/controle", response_class=HTMLResponse)
async def controle_page(request: Request):
    """Página de controle do bot"""
    try:
        username = get_current_user(request)
        
        # Buscar status do bot
        bot_config = await db.bot_config.find_one({"_id": "global_status"})
        bot_enabled = bot_config.get("enabled", True) if bot_config else True
        
        # Buscar status dos canais
        whatsapp_config = await db.channel_config.find_one({"canal": "whatsapp"})
        instagram_config = await db.channel_config.find_one({"canal": "instagram"})
        web_config = await db.channel_config.find_one({"canal": "web"})
        
        canais = {
            "whatsapp": whatsapp_config.get("enabled", True) if whatsapp_config else True,
            "instagram": instagram_config.get("enabled", False) if instagram_config else False,
            "web": web_config.get("enabled", False) if web_config else False
        }
        
        return templates.TemplateResponse("controle.html", {
            "request": request,
            "username": username,
            "bot_enabled": bot_enabled,
            "canais": canais
        })
    except HTTPException:
        return RedirectResponse(url="/admin/login")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar página de controle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# API: LIGAR/DESLIGAR BOT
# ============================================================
@router.post("/api/bot/toggle")
async def toggle_bot(request: Request):
    """Liga ou desliga o bot"""
    try:
        get_current_user(request)
        data = await request.json()
        enabled = data.get("enabled", True)
        
        await db.bot_config.update_one(
            {"_id": "global_status"},
            {"$set": {"enabled": enabled, "last_update": datetime.now()}},
            upsert=True
        )
        
        status_text = "ATIVADO" if enabled else "DESATIVADO"
        logger.info(f"✅ Bot {status_text}")
        
        return JSONResponse({
            "success": True,
            "enabled": enabled,
            "message": f"Bot {status_text.lower()} com sucesso"
        })
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao alternar bot: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: ATIVAR/DESATIVAR CANAL
# ============================================================
@router.post("/api/canal/toggle")
async def toggle_canal(request: Request):
    """Ativa ou desativa um canal"""
    try:
        get_current_user(request)
        data = await request.json()
        canal = data.get("canal", "").lower()
        enabled = data.get("enabled", False)
        
        if canal not in ["whatsapp", "instagram", "web"]:
            return JSONResponse({"error": "Canal inválido"}, status_code=400)
        
        await db.channel_config.update_one(
            {"canal": canal},
            {"$set": {"enabled": enabled, "last_update": datetime.now()}},
            upsert=True
        )
        
        status_text = "ATIVADO" if enabled else "DESATIVADO"
        logger.info(f"✅ Canal {canal} {status_text}")
        
        return JSONResponse({
            "success": True,
            "canal": canal,
            "enabled": enabled,
            "message": f"Canal {canal} {status_text.lower()} com sucesso"
        })
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao alternar canal: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: CONVERSAS EM TEMPO REAL
# ============================================================
@router.get("/api/conversas/tempo-real")
async def conversas_tempo_real(request: Request):
    """Retorna conversas ativas/recentes para monitoramento"""
    try:
        get_current_user(request)
        
        # Buscar conversas das últimas 24 horas
        ontem = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Agrupar por cliente (phone) e pegar última mensagem
        pipeline = [
            {"$match": {"timestamp": {"$gte": ontem}}},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": {"phone": "$phone", "canal": "$canal"},
                "last_message": {"$first": "$message"},
                "last_timestamp": {"$first": "$timestamp"},
                "last_role": {"$first": "$role"},
                "mode": {"$first": "$mode"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_timestamp": -1}},
            {"$limit": 50}
        ]
        
        conversas = await db.conversas.aggregate(pipeline).to_list(length=50)
        
        # Formatar resultado
        result = []
        for conv in conversas:
            result.append({
                "phone": conv["_id"]["phone"],
                "canal": conv["_id"]["canal"],
                "last_message": conv["last_message"],
                "last_timestamp": conv["last_timestamp"].isoformat() if isinstance(conv["last_timestamp"], datetime) else str(conv["last_timestamp"]),
                "last_role": conv["last_role"],
                "mode": conv.get("mode", "ai"),
                "message_count": conv["message_count"]
            })
        
        return JSONResponse(result)
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar conversas em tempo real: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: TRANSFERIR PARA HUMANO/IA
# ============================================================
@router.post("/api/conversa/transfer")
async def transfer_conversa(request: Request):
    """Transfere conversa entre IA e humano"""
    try:
        get_current_user(request)
        data = await request.json()
        
        phone = data.get("phone", "")
        canal = data.get("canal", "whatsapp")
        mode = data.get("mode", "ai")  # "ai" ou "human"
        
        if not phone:
            return JSONResponse({"error": "Telefone é obrigatório"}, status_code=400)
        
        if mode not in ["ai", "human"]:
            return JSONResponse({"error": "Modo inválido"}, status_code=400)
        
        # Atualizar modo de todas as conversas deste cliente
        result = await db.conversas.update_many(
            {"phone": phone, "canal": canal},
            {"$set": {"mode": mode, "transferred_at": datetime.now()}}
        )
        
        mode_text = "IA" if mode == "ai" else "HUMANO"
        logger.info(f"✅ Conversa {phone} ({canal}) transferida para {mode_text}")
        
        return JSONResponse({
            "success": True,
            "phone": phone,
            "canal": canal,
            "mode": mode,
            "message": f"Conversa transferida para {mode_text}"
        })
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao transferir conversa: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# PÁGINA: CONVERSAS EM TEMPO REAL
# ============================================================
@router.get("/conversas-tempo-real", response_class=HTMLResponse)
async def conversas_tempo_real_page(request: Request):
    """Página de monitoramento de conversas em tempo real"""
    try:
        username = get_current_user(request)
        
        return templates.TemplateResponse("conversas_tempo_real.html", {
            "request": request,
            "username": username
        })
    except HTTPException:
        return RedirectResponse(url="/admin/login")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar página de conversas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
