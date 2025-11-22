# 🤖 Mia Bot - Sistema Multi-Canal

Sistema de atendimento inteligente com IA para WhatsApp, Instagram e Web Chat.

## 📋 Funcionalidades

### ✅ Bot Inteligente
- **Mensagens de texto** com OpenAI GPT-4
- **Imagens** (GPT-4 Vision) - Análise de documentos
- **Áudios** (Whisper) - Transcrição de voz
- **PDFs** - Extração de texto + Vision
- **Atendimento Humano** - Transferência inteligente
- **Multi-canal** - WhatsApp (ativo), Instagram e Web (preparados)

### 🎯 Painel Administrativo
- **Dashboard** com estatísticas em tempo real
- **Controle do Bot** - Ligar/desligar, pausar
- **Gerenciamento de Canais** - Ativar/desativar WhatsApp, Instagram, Web
- **Conversas em Tempo Real** - Monitoramento de atendimentos
- **Treinamento da Mia** - Personalidade, FAQs, Base de Conhecimento
- **Gestão de Leads** - Captura e acompanhamento
- **Login Seguro** - Admin e Legacy

## 🚀 Deploy no Render

### 1. Criar conta no Render
- Acesse [render.com](https://render.com)
- Crie uma conta gratuita

### 2. Criar Web Service
1. Clique em "New +" → "Web Service"
2. Conecte seu repositório GitHub
3. Configure:
   - **Name**: `mia-bot-legacy`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. Configurar Variáveis de Ambiente
No Render, vá em "Environment" e adicione:

```
MONGODB_URL=mongodb+srv://...
OPENAI_API_KEY=sk-...
ZAPI_INSTANCE_ID=...
ZAPI_TOKEN=...
ZAPI_CLIENT_TOKEN=...
SESSION_SECRET_KEY=mia-secret-2024
ADMIN_PASSWORD=sua_senha_admin
LEGACY_PASSWORD=sua_senha_legacy
```

### 4. Deploy
- Clique em "Create Web Service"
- Aguarde o deploy (3-5 minutos)
- Acesse a URL fornecida pelo Render

## 🔧 Configuração Local

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

### 3. Executar
```bash
python main.py
```

### 4. Acessar
```
http://localhost:8000/admin/login
```

**Credenciais padrão:**
- Admin: `admin` / `admin123`
- Legacy: `legacy` / `legacy123`

## 📱 Configurar WhatsApp (Z-API)

### 1. Criar conta na Z-API
- Acesse [z-api.io](https://z-api.io)
- Crie uma instância do WhatsApp

### 2. Obter credenciais
- `ZAPI_INSTANCE_ID`: ID da instância
- `ZAPI_TOKEN`: Token de acesso
- `ZAPI_CLIENT_TOKEN`: Client Token

### 3. Configurar Webhook
Na Z-API, configure o webhook para:
```
https://seu-app.onrender.com/webhook/whatsapp
```

## 🎓 Treinar a Mia

### 1. Acessar Painel Admin
```
https://seu-app.onrender.com/admin/login
```

### 2. Ir em "Treinamento"
- **Personalidade**: Defina objetivos, tom e restrições
- **Base de Conhecimento**: Adicione informações sobre seus serviços
- **FAQs**: Cadastre perguntas e respostas frequentes

### 3. Salvar
Todas as alterações são aplicadas imediatamente!

## 🔄 Ativar Instagram (Futuro)

### 1. Criar App no Meta Developers
- Acesse [developers.facebook.com](https://developers.facebook.com)
- Crie um app com permissões do Instagram

### 2. Obter credenciais
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_PAGE_ID`

### 3. Configurar Webhook
```
https://seu-app.onrender.com/webhook/instagram
```

### 4. Ativar no Painel
- Vá em "Controle do Bot"
- Clique em "Ativar" no card do Instagram

## 💻 Ativar Web Chat (Futuro)

### 1. Configurar variável
```
WEBCHAT_ENABLED=true
```

### 2. Adicionar widget no seu site
```html
<script src="https://seu-app.onrender.com/static/webchat.js"></script>
<div id="mia-webchat"></div>
```

### 3. Ativar no Painel
- Vá em "Controle do Bot"
- Clique em "Ativar" no card do Web Chat

## 🛠️ Estrutura do Projeto

```
mia-whatsapp-bot-novo/
├── main.py                      # Aplicação principal
├── admin_routes.py              # Rotas de login e dashboard
├── admin_training_routes.py     # Rotas de treinamento
├── admin_controle_routes.py     # Rotas de controle
├── admin_leads_routes.py        # Rotas de leads
├── requirements.txt             # Dependências
├── .env.example                 # Exemplo de variáveis
├── README.md                    # Esta documentação
├── templates/                   # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── controle.html
│   ├── training.html
│   ├── conversas_tempo_real.html
│   └── leads.html
└── static/                      # Arquivos estáticos (CSS, JS)
```

## 📊 MongoDB Collections

### `bots`
Armazena configuração e treinamento da Mia
```json
{
  "name": "Mia",
  "personality": {
    "goals": ["..."],
    "tone": "...",
    "restrictions": ["..."]
  },
  "knowledge_base": [...],
  "faqs": [...]
}
```

### `conversas`
Histórico de todas as conversas
```json
{
  "phone": "5511999999999",
  "message": "...",
  "role": "user|assistant",
  "canal": "whatsapp|instagram|web",
  "timestamp": "...",
  "mode": "ai|human"
}
```

### `leads`
Leads capturados
```json
{
  "phone": "5511999999999",
  "name": "...",
  "email": "...",
  "canal": "whatsapp",
  "status": "novo|contato|negociacao|ganho|perdido",
  "notes": "..."
}
```

### `bot_config`
Configurações globais
```json
{
  "_id": "global_status",
  "enabled": true,
  "last_update": "..."
}
```

### `channel_config`
Status dos canais
```json
{
  "canal": "whatsapp|instagram|web",
  "enabled": true,
  "last_update": "..."
}
```

## 🔐 Segurança

- **Senhas**: Altere as senhas padrão em produção
- **SESSION_SECRET_KEY**: Use uma chave forte e única
- **HTTPS**: O Render fornece HTTPS automaticamente
- **Variáveis de Ambiente**: Nunca commite o arquivo `.env`

## 📞 Suporte

Para dúvidas ou problemas:
- Email: suporte@legacytranslations.com
- WhatsApp: +55 18 5720-81139

## 📝 Licença

© 2024 Legacy Translations. Todos os direitos reservados.

---

**Desenvolvido com ❤️ para Legacy Translations**
