# ============================================================
# ROTAS DE GESTÃO DE LEADS
# ============================================================
# Gerenciamento de leads capturados pelo bot
# ============================================================

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["leads"])
templates = Jinja2Templates(directory="templates")

# Importar banco de dados
from admin_training_routes import get_database
db = get_database()

# ============================================================
# MODELOS
# ============================================================
class Lead(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    canal: str = "whatsapp"
    status: str = "novo"  # novo, contato, negociacao, ganho, perdido
    notes: Optional[str] = None

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_current_user(request: Request):
    username = request.session.get('username')
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username

# ============================================================
# PÁGINA DE LEADS
# ============================================================
@router.get("/leads", response_class=HTMLResponse)
async def leads_page(request: Request):
    """Página de gestão de leads"""
    try:
        username = get_current_user(request)
        
        # Buscar estatísticas de leads
        total_leads = await db.leads.count_documents({})
        
        pipeline_status = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        leads_por_status = await db.leads.aggregate(pipeline_status).to_list(length=10)
        
        stats = {
            "total": total_leads,
            "por_status": {item["_id"]: item["count"] for item in leads_por_status}
        }
        
        return templates.TemplateResponse("leads.html", {
            "request": request,
            "username": username,
            "stats": stats
        })
    except HTTPException:
        return RedirectResponse(url="/admin/login")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar página de leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# API: LISTAR LEADS
# ============================================================
@router.get("/api/leads")
async def get_leads(request: Request, status: Optional[str] = None, canal: Optional[str] = None, limit: int = 100):
    """Retorna lista de leads"""
    try:
        get_current_user(request)
        
        query = {}
        if status:
            query["status"] = status
        if canal:
            query["canal"] = canal
        
        leads = await db.leads.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        # Formatar leads
        for lead in leads:
            lead["_id"] = str(lead["_id"])
            if "created_at" in lead and isinstance(lead["created_at"], datetime):
                lead["created_at"] = lead["created_at"].isoformat()
            if "updated_at" in lead and isinstance(lead["updated_at"], datetime):
                lead["updated_at"] = lead["updated_at"].isoformat()
        
        return JSONResponse(leads)
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar leads: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: CRIAR LEAD
# ============================================================
@router.post("/api/leads")
async def create_lead(request: Request):
    """Cria novo lead"""
    try:
        get_current_user(request)
        data = await request.json()
        
        phone = data.get("phone", "").strip()
        if not phone:
            return JSONResponse({"error": "Telefone é obrigatório"}, status_code=400)
        
        # Verificar se lead já existe
        existing_lead = await db.leads.find_one({"phone": phone})
        if existing_lead:
            return JSONResponse({"error": "Lead já existe"}, status_code=400)
        
        lead = {
            "phone": phone,
            "name": data.get("name", "").strip(),
            "email": data.get("email", "").strip(),
            "canal": data.get("canal", "whatsapp"),
            "status": data.get("status", "novo"),
            "notes": data.get("notes", ""),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = await db.leads.insert_one(lead)
        lead["_id"] = str(result.inserted_id)
        lead["created_at"] = lead["created_at"].isoformat()
        lead["updated_at"] = lead["updated_at"].isoformat()
        
        logger.info(f"✅ Lead criado: {phone}")
        return JSONResponse({"success": True, "lead": lead})
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao criar lead: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: ATUALIZAR LEAD
# ============================================================
@router.put("/api/leads/{phone}")
async def update_lead(request: Request, phone: str):
    """Atualiza lead existente"""
    try:
        get_current_user(request)
        data = await request.json()
        
        update_data = {
            "updated_at": datetime.now()
        }
        
        if "name" in data:
            update_data["name"] = data["name"].strip()
        if "email" in data:
            update_data["email"] = data["email"].strip()
        if "status" in data:
            update_data["status"] = data["status"]
        if "notes" in data:
            update_data["notes"] = data["notes"]
        if "canal" in data:
            update_data["canal"] = data["canal"]
        
        result = await db.leads.update_one(
            {"phone": phone},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Lead atualizado: {phone}")
            return JSONResponse({"success": True, "message": "Lead atualizado"})
        
        return JSONResponse({"error": "Lead não encontrado"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar lead: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: DELETAR LEAD
# ============================================================
@router.delete("/api/leads/{phone}")
async def delete_lead(request: Request, phone: str):
    """Remove lead"""
    try:
        get_current_user(request)
        
        result = await db.leads.delete_one({"phone": phone})
        
        if result.deleted_count > 0:
            logger.info(f"✅ Lead removido: {phone}")
            return JSONResponse({"success": True, "message": "Lead removido"})
        
        return JSONResponse({"error": "Lead não encontrado"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao remover lead: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: BUSCAR LEAD POR TELEFONE
# ============================================================
@router.get("/api/leads/{phone}")
async def get_lead(request: Request, phone: str):
    """Retorna detalhes de um lead específico"""
    try:
        get_current_user(request)
        
        lead = await db.leads.find_one({"phone": phone})
        
        if lead:
            lead["_id"] = str(lead["_id"])
            if "created_at" in lead and isinstance(lead["created_at"], datetime):
                lead["created_at"] = lead["created_at"].isoformat()
            if "updated_at" in lead and isinstance(lead["updated_at"], datetime):
                lead["updated_at"] = lead["updated_at"].isoformat()
            
            return JSONResponse(lead)
        
        return JSONResponse({"error": "Lead não encontrado"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar lead: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: CAPTURAR LEAD AUTOMATICAMENTE
# ============================================================
@router.post("/api/leads/capture")
async def capture_lead(request: Request):
    """Captura lead automaticamente de uma conversa"""
    try:
        data = await request.json()
        
        phone = data.get("phone", "").strip()
        canal = data.get("canal", "whatsapp")
        
        if not phone:
            return JSONResponse({"error": "Telefone é obrigatório"}, status_code=400)
        
        # Verificar se lead já existe
        existing_lead = await db.leads.find_one({"phone": phone})
        if existing_lead:
            return JSONResponse({"success": True, "message": "Lead já existe", "existing": True})
        
        # Criar lead automático
        lead = {
            "phone": phone,
            "canal": canal,
            "status": "novo",
            "notes": "Lead capturado automaticamente",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = await db.leads.insert_one(lead)
        logger.info(f"✅ Lead capturado automaticamente: {phone}")
        
        return JSONResponse({"success": True, "message": "Lead capturado", "existing": False})
    
    except Exception as e:
        logger.error(f"❌ Erro ao capturar lead: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
