import os
import logging
import time
import docker
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackContext
from threading import Thread
from datetime import datetime
from pymongo import MongoClient
import redis
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações via variáveis de ambiente
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
CHAT_ID = os.getenv('CHAT_ID', '')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

# Verificação das credenciais essenciais
if not TELEGRAM_TOKEN or not CHAT_ID:
    logger.error("TELEGRAM_TOKEN e CHAT_ID são obrigatórios no arquivo .env!")
    raise ValueError("Credenciais do Telegram não configuradas")

# Inicialização segura dos clients
try:
    client = docker.from_env()
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # Conexão com MongoDB (opcional)
    mongo_client = None
    if MONGO_URI and MONGO_URI != 'mongodb://mongo:27017/':
        try:
            mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            mongo_client.server_info()
            logger.info("Conexão com MongoDB estabelecida")
        except Exception as e:
            logger.warning(f"Falha ao conectar ao MongoDB: {e}")

    # Conexão com Redis (opcional)
    redis_client = None
    if REDIS_URL and REDIS_URL != 'redis://redis:6379/0':
        try:
            redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=5)
            redis_client.ping()
            logger.info("Conexão com Redis estabelecida")
        except Exception as e:
            logger.warning(f"Falha ao conectar ao Redis: {e}")

except Exception as e:
    logger.error(f"Erro na inicialização: {e}")
    raise

class ContainerMonitor:
    @staticmethod
    def get_container_health(container):
        """Obtém o status de saúde do container"""
        try:
            return container.attrs['State']['Health']['Status'].upper()
        except:
            return container.status.upper()

    @staticmethod
    def format_container_message(container, event_type="criado"):
        """Formata mensagem padronizada para containers"""
        try:
            image_tag = container.image.tags[0] if container.image.tags else 'N/A'
            return (
                f"🚨 *Container {event_type.upper()}*\n"
                f"⏰ *Hora:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"🆔 *ID:* `{container.short_id}`\n"
                f"📛 *Nome:* {container.name}\n"
                f"🐳 *Imagem:* {image_tag}\n"
                f"🔧 *Status:* {container.status.upper()}\n"
                f"🏷 *Labels:* {container.labels or 'Nenhum'}"
            )
        except Exception as e:
            logger.error(f"Erro ao formatar container: {e}")
            return None

    def monitor_containers(self):
        """Monitora eventos de containers com persistência"""
        while True:
            try:
                events = client.events(decode=True)
                for event in events:
                    if event['Type'] == 'container':
                        self.process_container_event(event)
            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                time.sleep(10)

    def process_container_event(self, event):
        """Processa e registra eventos de container"""
        try:
            container = client.containers.get(event['id'])
            action = event['Action']
            
            if mongo_client:
                self.store_event(container, action)
            
            if action in ['create', 'die', 'health_status']:
                self.notify_event(container, action)
        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}")

    def store_event(self, container, action):
        """Armazena eventos no MongoDB"""
        try:
            db = mongo_client['docker_monitor']
            db.events.insert_one({
                'container_id': container.id,
                'name': container.name,
                'action': action,
                'timestamp': datetime.now(),
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else None
            })
        except Exception as e:
            logger.error(f"Erro ao armazenar evento no MongoDB: {e}")

    def notify_event(self, container, action):
        """Envia notificação para o Telegram"""
        action_map = {
            'create': 'criado',
            'die': 'encerrado',
            'health_status': 'status de saúde alterado'
        }
        message = self.format_container_message(container, action_map.get(action, action))
        if message:
            try:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=message,
                    parse_mode='Markdown'
                )
                if redis_client:
                    redis_client.incr('notification_count')
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {e}")

async def check_containers(update: Update, context: CallbackContext):
    """Comando /verificar com cache no Redis"""
    try:
        if redis_client:
            cached = redis_client.get('containers_status')
            if cached:
                await update.message.reply_text(cached.decode(), parse_mode='Markdown')
                return

        containers = client.containers.list(all=True)
        if not containers:
            await update.message.reply_text("Nenhum container encontrado.")
            return

        message = ["📊 *Status dos Containers* (atualizado em {})\n".format(
            datetime.now().strftime('%d/%m/%Y %H:%M:%S'))]
        
        for container in containers:
            health = ContainerMonitor.get_container_health(container)
            message.append(
                f"• *{container.name}* (`{container.short_id}`)\n"
                f"  ⚙️ *Status:* {health}\n"
                f"  🖥 *Imagem:* {container.image.tags[0] if container.image.tags else 'N/A'}\n"
            )

        full_message = '\n'.join(message)
        if redis_client:
            redis_client.setex('containers_status', 30, full_message)
        await update.message.reply_text(full_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Erro no comando /verificar: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao verificar os containers.")

async def start(update: Update, context: CallbackContext):
    """Comando /start com estatísticas"""
    try:
        stats = {
            'notifications': int(redis_client.get('notification_count')) if redis_client else 0,
            'containers': len(client.containers.list())
        }
        
        await update.message.reply_text(
            f"🤖 *Docker Monitor Bot*\n\n"
            f"📊 Estatísticas:\n"
            f"• Notificações enviadas: {stats['notifications']}\n"
            f"• Containers ativos: {stats['containers']}\n\n"
            f"Use /verificar para listar os containers",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Erro no comando /start: {e}")
        await update.message.reply_text("Bot iniciado. Use /verificar para listar containers.")

def main():
    monitor = ContainerMonitor()
    
    # Thread de monitoramento
    Thread(target=monitor.monitor_containers, daemon=True).start()

    # Configuração do bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verificar", check_containers))

    # Inicia o bot
    application.run_polling()
    logger.info("Bot iniciado com sucesso")

if __name__ == '__main__':
    main()