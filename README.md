Docker Monitor Bot with Telegram
Docker + Telegram Logo

Um bot de monitoramento que envia notificações para o Telegram quando containers Docker são criados, iniciados ou parados, com capacidade de verificar o status de todos os containers.

✨ Funcionalidades
🔔 Notificações em tempo real para eventos de containers

📊 Verificação manual via comando /verificar

🗃️ Persistência de eventos no MongoDB

⚡ Cache de consultas no Redis

🔍 Monitoramento de containers internos e externos

🚀 Como Executar
Pré-requisitos
Docker e Docker Compose instalados

Conta no Telegram e token de bot (obtenha com @BotFather)

Chat ID (obtenha com @userinfobot)

Configuração
Clone o repositório:

bash
Copy
git clone https://github.com/seu-usuario/docker-monitor-bot.git
cd docker-monitor-bot
Crie o arquivo .env baseado no exemplo:

bash
Copy
cp .env.example .env
Edite o .env com suas credenciais:

env
Copy
# Telegram
TELEGRAM_TOKEN=seu_token_aqui
CHAT_ID=seu_chat_id

# MongoDB
MONGO_USER=admin
MONGO_PASS=senha_forte
MONGO_URI=mongodb://admin:senha_forte@mongo:27017/admin?authSource=admin

# Redis
REDIS_PASS=outra_senha_forte
REDIS_URL=redis://:outra_senha_forte@redis:6379/0
Execução
bash
Copy
docker-compose --env-file .env up --build -d
🛠️ Uso
Comandos do Telegram
/start - Mostra mensagem de boas-vindas e estatísticas

/verificar - Lista todos os containers com seus status

Monitorar Containers Externos
Para monitorar containers fora do compose, execute-os com a label especial:

bash
Copy
docker run -d --label monitor=true nginx:alpine
🧰 Estrutura do Projeto
Copy
docker-monitor-bot/
├── .env.example       # Modelo de variáveis de ambiente
├── docker-compose.yml # Configuração dos serviços
├── Dockerfile         # Build da aplicação
├── main.py            # Código principal
└── requirements.txt   # Dependências Python
🤝 Contribuição
Contribuições são bem-vindas! Siga estes passos:

Faça um fork do projeto

Crie uma branch (git checkout -b feature/nova-feature)

Commit suas mudanças (git commit -m 'Adiciona nova feature')

Push para a branch (git push origin feature/nova-feature)

Abra um Pull Request

📄 Licença
Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

Desenvolvido com ❤️ por [Igor Rocha] 

📌 Notas Adicionais
Para monitorar containers em outros hosts Docker, modifique a URL no código

Configure webhooks para melhor desempenho em produção

Considere adicionar autenticação adicional para comandos sensíveis

📊 Dashboard Opcional
Para visualização avançada, considere integrar com:

Grafana para métricas

Portainer para gestão visual

💡 Dica: Use docker-compose logs -f monitor para ver os logs em tempo real durante o desenvolvimento.
