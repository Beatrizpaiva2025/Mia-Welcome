# ============================================================
# ROTAS DE TREINAMENTO DA MIA
# ============================================================
# Gerenciamento de:
# - Personalidade (objetivos, tom, restrições)
# - Base de Conhecimento
# - FAQs
# ============================================================

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["training"])
templates = Jinja2Templates(directory="templates")

# ============================================================
# CONEXÃO MONGODB
# ============================================================
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(MONGODB_URL)
db = mongo_client.mia_bot

def get_database():
    """Retorna instância do banco de dados"""
    return db

# ============================================================
# MODELOS
# ============================================================
class PersonalityUpdate(BaseModel):
    goals: List[str]
    tone: str
    restrictions: List[str]

class KnowledgeItem(BaseModel):
    title: str
    content: str

class FAQItem(BaseModel):
    question: str
    answer: str

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_current_user(request: Request):
    username = request.session.get('username')
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return username

async def ensure_bot_exists():
    """Garante que o bot Mia existe no banco"""
    bot = await db.bots.find_one({"name": "Mia"})
    if not bot:
        await db.bots.insert_one({
            "name": "Mia",
            "personality": {
                "goals": ["Ajudar clientes com tradução de documentos"],
                "tone": "Profissional, educada e prestativa",
                "restrictions": ["Não fazer traduções completas", "Não dar preços sem analisar documento"]
            },
            "knowledge_base": [],
            "faqs": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        })
        logger.info("✅ Bot Mia criado no banco de dados")

# ============================================================
# PÁGINA DE TREINAMENTO
# ============================================================
@router.get("/training", response_class=HTMLResponse)
async def training_page(request: Request):
    """Página de treinamento da Mia"""
    try:
        username = get_current_user(request)
        await ensure_bot_exists()
        
        bot = await db.bots.find_one({"name": "Mia"})
        
        return templates.TemplateResponse("training.html", {
            "request": request,
            "username": username,
            "bot": bot
        })
    except HTTPException:
        return RedirectResponse(url="/admin/login")
    except Exception as e:
        logger.error(f"❌ Erro ao carregar página de treinamento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# API: BUSCAR DADOS DO BOT
# ============================================================
@router.get("/api/bot")
async def get_bot(request: Request):
    """Retorna dados completos do bot"""
    try:
        get_current_user(request)
        await ensure_bot_exists()
        
        bot = await db.bots.find_one({"name": "Mia"})
        
        if bot:
            bot["_id"] = str(bot["_id"])
            return JSONResponse(bot)
        
        return JSONResponse({"error": "Bot não encontrado"}, status_code=404)
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao buscar bot: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: ATUALIZAR PERSONALIDADE
# ============================================================
@router.post("/api/personality")
async def update_personality(request: Request):
    """Atualiza personalidade da Mia"""
    try:
        get_current_user(request)
        data = await request.json()
        
        goals = data.get("goals", [])
        tone = data.get("tone", "")
        restrictions = data.get("restrictions", [])
        
        if not tone:
            return JSONResponse({"error": "Tom é obrigatório"}, status_code=400)
        
        result = await db.bots.update_one(
            {"name": "Mia"},
            {
                "$set": {
                    "personality.goals": goals,
                    "personality.tone": tone,
                    "personality.restrictions": restrictions,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info("✅ Personalidade atualizada")
            return JSONResponse({"success": True, "message": "Personalidade atualizada com sucesso"})
        
        return JSONResponse({"error": "Nenhuma alteração realizada"}, status_code=400)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar personalidade: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: BASE DE CONHECIMENTO
# ============================================================
@router.post("/api/knowledge")
async def add_knowledge(request: Request):
    """Adiciona item à base de conhecimento"""
    try:
        get_current_user(request)
        data = await request.json()
        
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        
        if not title or not content:
            return JSONResponse({"error": "Título e conteúdo são obrigatórios"}, status_code=400)
        
        knowledge_item = {
            "id": str(datetime.now().timestamp()),
            "title": title,
            "content": content,
            "created_at": datetime.now()
        }
        
        result = await db.bots.update_one(
            {"name": "Mia"},
            {
                "$push": {"knowledge_base": knowledge_item},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Conhecimento adicionado: {title}")
            return JSONResponse({"success": True, "message": "Conhecimento adicionado", "item": knowledge_item})
        
        return JSONResponse({"error": "Erro ao adicionar conhecimento"}, status_code=400)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar conhecimento: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.put("/api/knowledge/{knowledge_id}")
async def update_knowledge(request: Request, knowledge_id: str):
    """Atualiza item da base de conhecimento"""
    try:
        get_current_user(request)
        data = await request.json()
        
        title = data.get("title", "").strip()
        content = data.get("content", "").strip()
        
        if not title or not content:
            return JSONResponse({"error": "Título e conteúdo são obrigatórios"}, status_code=400)
        
        result = await db.bots.update_one(
            {"name": "Mia", "knowledge_base.id": knowledge_id},
            {
                "$set": {
                    "knowledge_base.$.title": title,
                    "knowledge_base.$.content": content,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Conhecimento atualizado: {knowledge_id}")
            return JSONResponse({"success": True, "message": "Conhecimento atualizado"})
        
        return JSONResponse({"error": "Conhecimento não encontrado"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar conhecimento: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/api/knowledge/{knowledge_id}")
async def delete_knowledge(request: Request, knowledge_id: str):
    """Remove item da base de conhecimento"""
    try:
        get_current_user(request)
        
        result = await db.bots.update_one(
            {"name": "Mia"},
            {
                "$pull": {"knowledge_base": {"id": knowledge_id}},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Conhecimento removido: {knowledge_id}")
            return JSONResponse({"success": True, "message": "Conhecimento removido"})
        
        return JSONResponse({"error": "Conhecimento não encontrado"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao remover conhecimento: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

# ============================================================
# API: FAQs
# ============================================================
@router.post("/api/faq")
async def add_faq(request: Request):
    """Adiciona FAQ"""
    try:
        get_current_user(request)
        data = await request.json()
        
        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()
        
        if not question or not answer:
            return JSONResponse({"error": "Pergunta e resposta são obrigatórias"}, status_code=400)
        
        faq_item = {
            "id": str(datetime.now().timestamp()),
            "question": question,
            "answer": answer,
            "created_at": datetime.now()
        }
        
        result = await db.bots.update_one(
            {"name": "Mia"},
            {
                "$push": {"faqs": faq_item},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ FAQ adicionada: {question}")
            return JSONResponse({"success": True, "message": "FAQ adicionada", "item": faq_item})
        
        return JSONResponse({"error": "Erro ao adicionar FAQ"}, status_code=400)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao adicionar FAQ: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.put("/api/faq/{faq_id}")
async def update_faq(request: Request, faq_id: str):
    """Atualiza FAQ"""
    try:
        get_current_user(request)
        data = await request.json()
        
        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()
        
        if not question or not answer:
            return JSONResponse({"error": "Pergunta e resposta são obrigatórias"}, status_code=400)
        
        result = await db.bots.update_one(
            {"name": "Mia", "faqs.id": faq_id},
            {
                "$set": {
                    "faqs.$.question": question,
                    "faqs.$.answer": answer,
                    "updated_at": datetime.now()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ FAQ atualizada: {faq_id}")
            return JSONResponse({"success": True, "message": "FAQ atualizada"})
        
        return JSONResponse({"error": "FAQ não encontrada"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar FAQ: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/api/faq/{faq_id}")
async def delete_faq(request: Request, faq_id: str):
    """Remove FAQ"""
    try:
        get_current_user(request)
        
        result = await db.bots.update_one(
            {"name": "Mia"},
            {
                "$pull": {"faqs": {"id": faq_id}},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ FAQ removida: {faq_id}")
            return JSONResponse({"success": True, "message": "FAQ removida"})
        
        return JSONResponse({"error": "FAQ não encontrada"}, status_code=404)
    
    except HTTPException as e:
        return JSONResponse({"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        logger.error(f"❌ Erro ao remover FAQ: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
