from dotenv import load_dotenv
import os
import re
import traceback

# LIMPAR VARIÁVEIS DE PROXY DO AMBIENTE
for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    if proxy_var in os.environ:
        del os.environ[proxy_var]

load_dotenv(override=True)

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# ============================ CONFIGURAÇÃO OPENAI ============================

OPENAI_DISPONIVEL = False
client = None

if API_KEY and len(API_KEY) > 10:
    try:
        from openai import OpenAI, RateLimitError
        import httpx
        
        http_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True
        )
        
        client = OpenAI(
            api_key=API_KEY,
            http_client=http_client,
            max_retries=2
        )
        OPENAI_DISPONIVEL = True
        print("[OK] API Key carregada: " + API_KEY[:15] + "..." + API_KEY[-8:])
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar OpenAI: {e}")
        traceback.print_exc()
else:
    print("[AVISO] API Key não configurada")
    try:
        from openai import RateLimitError
    except:
        class RateLimitError(Exception):
            pass

# ============================ CONFIGURAÇÃO DE EQUIPAMENTOS ============================

EQUIPAMENTOS = {
    # AIRplus (sem submenu - entra direto)
    "airplus": {
        "nome_completo": "AIRplus Mini",
        "assistant_id": os.getenv("ASSISTANT_AIRPLUS_MINI", ""),
        "vector_store_id": os.getenv("VECTOR_AIRPLUS_MINI", ""),
    },
    
    # AIRmove
    "airmove_2": {
        "nome_completo": "AIRmove 2",
        "assistant_id": os.getenv("ASSISTANT_AIRMOVE_2", ""),
        "vector_store_id": os.getenv("VECTOR_AIRMOVE_2", ""),
    },
    
    # FOAMplus
    "foamplus": {
        "nome_completo": "FOAMplus Bag Packer",
        "assistant_id": os.getenv("ASSISTANT_FOAMPLUS_BAG", ""),
        "vector_store_id": os.getenv("VECTOR_FOAMPLUS_BAG", ""),
    },
    
    # PAPERplus
    "paperplus_classic": {
        "nome_completo": "PAPERplus Classic",
        "assistant_id": os.getenv("ASSISTANT_PAPERPLUS_CLASSIC", ""),
        "vector_store_id": os.getenv("VECTOR_PAPERPLUS_CLASSIC", ""),
    },
    "paperplus_track": {
        "nome_completo": "PAPERplus Track",
        "assistant_id": os.getenv("ASSISTANT_PAPERPLUS_TRACK", ""),
        "vector_store_id": os.getenv("VECTOR_PAPERPLUS_TRACK", ""),
    },
}

# Mostrar equipamentos configurados
print("\n[INFO] Equipamentos configurados:")
for key, config in EQUIPAMENTOS.items():
    if config["assistant_id"] and config["vector_store_id"]:
        status = "✓"
        print(f"  {status} {config['nome_completo']}")
    else:
        print(f"  ✗ {config['nome_completo']} - NÃO CONFIGURADO")

CONTATO_TELEFONE = "(11) 5677-4699"
CONTATO_EMAIL = "packaging.br@storopack.com"

# ============================ MAPEAMENTO DE VÍDEOS ============================

VIDEOS_LOCAIS = {
    "e1": "/static/erros/e1/",
    "e2": "/static/erros/e2/",
    "e3": "/static/erros/e3/",
    "e4": "/static/erros/e4/",
    "e5": "/static/erros/e5/",
    "e6": "/static/erros/e6/",
    "e7": "/static/erros/e7/",
    "e8": "/static/erros/e8/",
    "e9": "/static/erros/e9/",
    "e10": "/static/erros/e10/",
    "e11": "/static/erros/e11/",
    "calibracao": "/static/videos/calibracao/",
    "selagem": "/static/videos/selagem/",
}

PALAVRAS_SELAGEM = [
    "selagem", "selar", "selo", "vedacao", "vedar", "fio", "resistencia",
    "calibrar", "calibracao", "calibrado", "temperatura", "aquecimento"
]

# ============================ FUNÇÕES AUXILIARES ============================

def limpar_formatacao(texto: str) -> str:
    """Remove markdown e annotations do OpenAI"""
    if not texto:
        return ""
    texto = re.sub(r'[\u3010].*?[\u3011]', '', texto)
    texto = re.sub(r'\u3010.*?\u3011', '', texto)
    texto = texto.replace("**", "")
    texto = texto.replace("*", "")
    texto = texto.replace("```", "")
    texto = texto.replace("###", "")
    texto = texto.replace("##", "")
    texto = texto.replace("#", "")
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()


def processar_videos(texto: str) -> str:
    """Processa marcadores [VIDEO_X] e converte em links"""
    if not texto:
        return ""
    
    marcadores = {
        r'\[VIDEO_E1\]': ('Erro E1', '/static/erros/e1/'),
        r'\[VIDEO_E2\]': ('Erro E2', '/static/erros/e2/'),
        r'\[VIDEO_E3\]': ('Erro E3', '/static/erros/e3/'),
        r'\[VIDEO_E4\]': ('Erro E4', '/static/erros/e4/'),
        r'\[VIDEO_E5\]': ('Erro E5', '/static/erros/e5/'),
        r'\[VIDEO_E6\]': ('Erro E6', '/static/erros/e6/'),
        r'\[VIDEO_E7\]': ('Erro E7', '/static/erros/e7/'),
        r'\[VIDEO_E8\]': ('Erro E8', '/static/erros/e8/'),
        r'\[VIDEO_E9\]': ('Erro E9', '/static/erros/e9/'),
        r'\[VIDEO_E10\]': ('Erro E10', '/static/erros/e10/'),
        r'\[VIDEO_E11\]': ('Erro E11', '/static/erros/e11/'),
        r'\[VIDEO_CALIBRACAO\]': ('Calibração', '/static/videos/calibracao/'),
        r'\[VIDEO_SELAGEM\]': ('Selagem', '/static/videos/selagem/'),
    }
    
    for marcador, (titulo, caminho) in marcadores.items():
        if re.search(marcador, texto):
            if not texto.endswith('\n\n'):
                texto = re.sub(marcador, f'\n\n📹 Ver vídeo: {titulo}\n{caminho}', texto, count=1)
            else:
                texto = re.sub(marcador, f'📹 Ver vídeo: {titulo}\n{caminho}', texto, count=1)
            texto = re.sub(marcador, '', texto)
    
    return texto.strip()


def get_equipamento_config(modulo: str) -> dict:
    """Retorna a configuração do equipamento baseado no módulo"""
    modulo_lower = modulo.lower() if modulo else ""
    
    # Mapeamento direto
    if modulo_lower in EQUIPAMENTOS:
        return EQUIPAMENTOS[modulo_lower]
    
    # Fallback: tentar encontrar por parte do nome
    for key, config in EQUIPAMENTOS.items():
        if modulo_lower.startswith(key[:6]):
            return config
    
    return None


# ============================ RESPOSTA COM ASSISTANTS API ============================

def responder_com_assistants_api(pergunta: str, modulo: str) -> str:
    """Usa a Assistants API específica do equipamento com File Search"""
    if not client:
        return None
    
    config = get_equipamento_config(modulo)
    
    if not config or not config.get("assistant_id"):
        print(f"[AVISO] Equipamento {modulo} não tem assistente configurado")
        return None
    
    assistant_id = config["assistant_id"]
    nome_equipamento = config["nome_completo"]
    
    try:
        print(f"[INFO] Consultando assistente de {nome_equipamento}...")
        
        thread = client.beta.threads.create()
        
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=pergunta
        )
        
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            timeout=30
        )
        
        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            for msg in messages.data:
                if msg.role == "assistant":
                    resposta = limpar_formatacao(msg.content[0].text.value)
                    print(f"[OK] Resposta obtida do manual de {nome_equipamento}")
                    return resposta
        else:
            print(f"[AVISO] Run status: {run.status}")
        
        return None
        
    except Exception as e:
        print(f"[ERRO] Assistants API ({nome_equipamento}): {str(e)[:300]}")
        traceback.print_exc()
        return None


# ============================ RESPOSTA OFFLINE (FALLBACK) ============================

RESPOSTAS_OFFLINE = {
    "e1": "Erro E1 - Sensor de Temperatura\n\nSolução:\n1. Desligue a máquina\n2. Verifique a conexão do sensor NTC\n3. Limpe os contatos\n4. Religue e teste\n\n[VIDEO_E1]",
    "e2": "Erro E2 - Resistência de Selagem\n\nSolução:\n1. Verifique a resistência NTC e fios de selagem\n2. Cheque todas as conexões\n3. Substitua se danificada\n4. Se persistir, pode ser curto-circuito ou fio rompido\n\n[VIDEO_E2]",
    "e3": "Erro E3 - Sensor de Filme\n\nSolução:\n1. Verifique se o filme acabou\n2. Libere filme preso\n3. Limpe o sensor\n4. Reposicione o filme\n\n[VIDEO_E3]",
    "e9": "Erro E9 - Calibração Fora do Limite\n\nSolução:\n1. Rode a calibração (faixa ideal: 2800-5200)\n2. Verifique estabilidade das conexões\n3. Valor alto pode indicar desgaste dos fios de selagem\n4. Reteste após calibração\n\n[VIDEO_E9]\n[VIDEO_CALIBRACAO]",
    "calibracao": "Como Calibrar:\n\n1. A calibração ajusta o sistema de selagem considerando a resistência dos fios\n2. Durante a calibração, os botões não têm efeito\n3. Apenas parar ou desligar interrompe o processo\n4. Após calibrar, valide visualmente a selagem (uniforme e resistente)\n5. Ajuste temperatura, ar e velocidade se necessário\n\n[VIDEO_CALIBRACAO]",
    "selagem": "Problemas de Selagem:\n\n1. Verifique temperatura (125-135°C para maioria dos materiais)\n2. Confira pressão do ar e velocidade\n3. Inspecione fios de selagem (desgaste/oxidação)\n4. Se selagem irregular, recalibre o sistema\n\n[VIDEO_SELAGEM]\n[VIDEO_CALIBRACAO]",
}

def resposta_offline(pergunta: str, modulo: str) -> str:
    """Resposta offline quando API não disponível"""
    pergunta_lower = pergunta.lower()
    config = get_equipamento_config(modulo)
    nome = config["nome_completo"] if config else modulo.upper()
    
    # Detectar erros E1-E11
    for i in range(1, 12):
        codigo = f"e{i}"
        if codigo in pergunta_lower or f"erro {i}" in pergunta_lower:
            return RESPOSTAS_OFFLINE.get(codigo, f"Erro {codigo.upper()} detectado.\n\nLigue: {CONTATO_TELEFONE}")
    
    # Calibração
    if "calibra" in pergunta_lower:
        return RESPOSTAS_OFFLINE.get("calibracao")
    
    # Selagem
    if any(palavra in pergunta_lower for palavra in PALAVRAS_SELAGEM):
        return RESPOSTAS_OFFLINE.get("selagem")
    
    # Saudações
    saudacoes = ["ola", "oi", "bom dia", "boa tarde", "boa noite", "hello", "hi"]
    if any(s in pergunta_lower for s in saudacoes):
        return f"Olá! Sou o assistente técnico Storopack para {nome}.\n\nDescreva o problema ou erro que está aparecendo na máquina."
    
    return (
        f"Sistema offline para {nome}.\n\n"
        "Para suporte completo com acesso aos manuais, verifique:\n"
        "- Conexão com a internet\n"
        "- Configuração da API OpenAI\n\n"
        f"Ou ligue: {CONTATO_TELEFONE}"
    )


# ============================ FUNÇÃO PRINCIPAL ============================

def responder_cliente(pergunta: str, modulo: str = None, video_bytes=None, video_path=None, nome_cliente=None, telefone_cliente=None) -> str:
    """Função principal que consulta o manual específico do equipamento"""
    
    if nome_cliente or telefone_cliente:
        print(f"[INFO] Cliente: {nome_cliente} | Tel: {telefone_cliente}")
    
    pergunta = (pergunta or "").strip()
    if not pergunta:
        saudacao = f"Oi{' ' + nome_cliente.split()[0] if nome_cliente else ''}!"
        return f"{saudacao}\n\nDescreva o problema do equipamento."
    
    if not modulo:
        return "Por favor, selecione o equipamento no menu."
    
    # Obter configuração do equipamento
    config = get_equipamento_config(modulo)
    if not config:
        return f"Equipamento '{modulo}' não reconhecido. Selecione um equipamento válido."
    
    nome_equipamento = config["nome_completo"]
    
    # Se OpenAI não disponível, usar offline
    if not OPENAI_DISPONIVEL or not client:
        print("[INFO] Usando resposta offline (API indisponível)")
        resposta = resposta_offline(pergunta, modulo)
        return processar_videos(resposta)
    
    try:
        # Tentar Assistants API (com PDFs do equipamento)
        texto = responder_com_assistants_api(pergunta, modulo)
        
        # Se falhou, usar offline
        if not texto:
            print(f"[INFO] Assistente de {nome_equipamento} falhou, usando offline")
            resposta = resposta_offline(pergunta, modulo)
            return processar_videos(resposta)
        
        # Processar marcadores de vídeo
        return processar_videos(texto)
    
    except RateLimitError:
        return "Muitas requisições. Tente novamente em alguns segundos."
    except Exception as e:
        print(f"[ERRO] {str(e)[:200]}")
        traceback.print_exc()
        resposta = resposta_offline(pergunta, modulo)
        return processar_videos(resposta)


# ============================ TESTE ============================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ASSISTENTE STOROPACK - SISTEMA MULTI-EQUIPAMENTO")
    print("="*60 + "\n")
    
    print(f"OpenAI disponível: {OPENAI_DISPONIVEL}")
    print(f"Total de equipamentos: {len(EQUIPAMENTOS)}\n")
    
    # Teste
    resposta = responder_cliente(
        "Erro E9 na máquina", 
        modulo="airplus"
    )
    print(resposta)