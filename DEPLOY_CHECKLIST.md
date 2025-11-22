# ✅ Checklist de Deploy - Mia Bot

## 📋 Antes do Deploy

### 1. Configurar MongoDB
- [ ] Criar conta no MongoDB Atlas (gratuito)
- [ ] Criar cluster
- [ ] Criar database `mia_bot`
- [ ] Obter connection string (MONGODB_URL)
- [ ] Adicionar IP do Render na whitelist (0.0.0.0/0)

### 2. Configurar OpenAI
- [ ] Criar conta na OpenAI
- [ ] Obter API Key (OPENAI_API_KEY)
- [ ] Verificar créditos disponíveis

### 3. Configurar Z-API (WhatsApp)
- [ ] Criar conta na Z-API
- [ ] Criar instância do WhatsApp
- [ ] Escanear QR Code
- [ ] Obter credenciais:
  - [ ] ZAPI_INSTANCE_ID
  - [ ] ZAPI_TOKEN
  - [ ] ZAPI_CLIENT_TOKEN

### 4. Preparar Repositório GitHub
- [ ] Criar repositório no GitHub
- [ ] Fazer upload dos arquivos do projeto
- [ ] Verificar se .env está no .gitignore

## 🚀 Deploy no Render

### 1. Criar Web Service
- [ ] Acessar render.com
- [ ] Clicar em "New +" → "Web Service"
- [ ] Conectar repositório GitHub
- [ ] Configurar:
  - Name: `mia-bot-legacy`
  - Environment: `Python 3`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 2. Adicionar Variáveis de Ambiente
No Render, ir em "Environment" e adicionar:

```
MONGODB_URL=mongodb+srv://...
OPENAI_API_KEY=sk-...
ZAPI_INSTANCE_ID=...
ZAPI_TOKEN=...
ZAPI_CLIENT_TOKEN=...
SESSION_SECRET_KEY=mia-secret-2024-change-this
ADMIN_PASSWORD=sua_senha_forte
LEGACY_PASSWORD=sua_senha_forte
```

### 3. Deploy
- [ ] Clicar em "Create Web Service"
- [ ] Aguardar deploy (3-5 minutos)
- [ ] Copiar URL fornecida pelo Render

## 🔧 Configuração Pós-Deploy

### 1. Configurar Webhook na Z-API
- [ ] Acessar painel da Z-API
- [ ] Ir em Webhooks
- [ ] Configurar URL: `https://seu-app.onrender.com/webhook/whatsapp`
- [ ] Ativar webhook

### 2. Testar Sistema
- [ ] Acessar: `https://seu-app.onrender.com/admin/login`
- [ ] Fazer login com credenciais configuradas
- [ ] Verificar se dashboard carrega
- [ ] Enviar mensagem de teste no WhatsApp
- [ ] Verificar se bot responde

### 3. Treinar a Mia
- [ ] Ir em "Treinamento"
- [ ] Configurar personalidade
- [ ] Adicionar base de conhecimento
- [ ] Adicionar FAQs
- [ ] Salvar tudo

## ✅ Verificações Finais

- [ ] Bot responde mensagens de texto
- [ ] Bot processa imagens
- [ ] Bot transcreve áudios
- [ ] Transferência para humano funciona
- [ ] Comando '+' reativa IA
- [ ] Dashboard mostra estatísticas
- [ ] Treinamento salva corretamente
- [ ] Leads são capturados
- [ ] Conversas em tempo real funcionam

## 🆘 Troubleshooting

### Bot não responde
1. Verificar se webhook está configurado corretamente
2. Verificar logs no Render
3. Testar endpoint: `https://seu-app.onrender.com/health`

### Erro de conexão MongoDB
1. Verificar se IP está na whitelist
2. Verificar se connection string está correta
3. Verificar se database existe

### Erro OpenAI
1. Verificar se API Key está correta
2. Verificar se há créditos disponíveis
3. Verificar logs de erro

## 📞 Suporte

- Email: suporte@legacytranslations.com
- WhatsApp: +55 18 5720-81139

---

**Desenvolvido com ❤️ para Legacy Translations**
