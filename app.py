from flask import Flask, request, jsonify, send_from_directory, session, Response
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import json
import os
import hashlib
import math
import traceback

# Obter o diretório atual do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder='static', template_folder='.')
app.secret_key = os.environ.get('SECRET_KEY', 'storopack_secret_key_2025')
CORS(app)

# Configurações
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '826541')
DB_PATH = os.path.join(BASE_DIR, "data", "storopack.db")
STOROPACK_LAT = -23.67376
STOROPACK_LNG = -46.69436

# ============================ IMPORTAR ASSISTENTE ============================
# Importação segura do assistente - não quebra se der erro
try:
    from assistente import responder_cliente
    ASSISTENTE_OK = True
    print("[OK] Módulo assistente carregado")
except Exception as e:
    ASSISTENTE_OK = False
    print(f"[AVISO] Módulo assistente não carregou: {e}")
    print("[AVISO] O chat vai usar respostas offline")
    
    def responder_cliente(pergunta="", modulo=None, video_bytes=None, video_path=None, nome_cliente=None, telefone_cliente=None):
        """Fallback quando o assistente não está disponível"""
        return (
            "⚠️ O assistente está temporariamente indisponível.\n\n"
            "Possíveis causas:\n"
            "• API Key da OpenAI não configurada\n"
            "• Dependências não instaladas\n"
            "• Erro de conexão com a API\n\n"
            "Entre em contato: (11) 5677-4699"
        )

# ============================ BANCO DE DADOS ============================

def init_db():
    """Inicializa o banco de dados"""
    # Criar diretório data se não existir
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Verificar se consegue escrever na pasta
    if not os.access(data_dir, os.W_OK):
        print(f"[AVISO] Sem permissão de escrita em {data_dir}")
        # Usar /tmp como fallback
        global DB_PATH
        DB_PATH = "/tmp/storopack.db"
        print(f"[INFO] Usando banco de dados temporário: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Tabela de chamados
    c.execute('''CREATE TABLE IF NOT EXISTS chamados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        nome_cliente TEXT,
        telefone_cliente TEXT,
        modulo TEXT,
        status TEXT DEFAULT 'aberto',
        latitude REAL,
        longitude REAL,
        distancia_km REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabela de mensagens
    c.execute('''CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chamado_id INTEGER,
        tipo TEXT,
        conteudo TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (chamado_id) REFERENCES chamados (id)
    )''')
    
    # Tabela de contatos
    c.execute('''CREATE TABLE IF NOT EXISTS contatos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE,
        nome TEXT,
        telefone TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()
    print("[OK] Banco de dados inicializado")

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula distância em km usando fórmula de Haversine"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Função exportada para outros módulos
def estimar_distancia(cidade):
    """Estima distância baseado no nome da cidade"""
    return ""

# ============================ ROTAS PRINCIPAIS ============================

@app.route('/')
def index():
    """Página principal"""
    try:
        index_path = os.path.join(BASE_DIR, 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content, mimetype='text/html; charset=utf-8')
        else:
            return f"Erro: index.html não encontrado em {BASE_DIR}", 404
    except Exception as e:
        print(f"[ERRO] Ao carregar index.html: {e}")
        return f"Erro ao carregar página: {str(e)}", 500

@app.route('/admin')
def admin():
    """Página admin"""
    try:
        admin_path = os.path.join(BASE_DIR, 'admin.html')
        if os.path.exists(admin_path):
            with open(admin_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content, mimetype='text/html; charset=utf-8')
        else:
            return f"Erro: admin.html não encontrado em {BASE_DIR}", 404
    except Exception as e:
        print(f"[ERRO] Ao carregar admin.html: {e}")
        return f"Erro ao carregar página: {str(e)}", 500

@app.route('/static/<path:path>')
def serve_static(path):
    """Servir arquivos estáticos"""
    try:
        static_dir = os.path.join(BASE_DIR, 'static')
        return send_from_directory(static_dir, path)
    except Exception as e:
        return f"Arquivo não encontrado: {path}", 404

# ============================ REGISTRO DE CONTATO ============================

@app.route('/registrar-contato', methods=['POST'])
def registrar_contato():
    """Registra informações de contato do cliente"""
    try:
        data = request.json
        session_id = data.get('session_id')
        nome = data.get('nome')
        telefone = data.get('telefone')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO contatos (session_id, nome, telefone)
                     VALUES (?, ?, ?)''', (session_id, nome, telefone))
        conn.commit()
        conn.close()
        
        return jsonify({'sucesso': True})
    except Exception as e:
        print(f"[ERRO] Registrar contato: {str(e)}")
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

# ============================ CHAT ============================

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint principal do chat"""
    try:
        data = request.json
        mensagem = data.get('mensagem', '').strip()
        modulo = data.get('modulo')
        session_id = data.get('session_id')
        chamado_id = data.get('chamado_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        nome_cliente = data.get('nome_cliente')
        telefone_cliente = data.get('telefone_cliente')
        
        print(f"[CHAT] Modulo: {modulo} | Msg: {mensagem[:80]}...")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Criar ou recuperar chamado
        if not chamado_id:
            distancia_km = None
            if latitude and longitude:
                try:
                    distancia_km = calcular_distancia(
                        float(latitude), float(longitude), 
                        STOROPACK_LAT, STOROPACK_LNG
                    )
                except:
                    pass
            
            c.execute('''INSERT INTO chamados 
                        (session_id, nome_cliente, telefone_cliente, modulo, latitude, longitude, distancia_km)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (session_id, nome_cliente, telefone_cliente, modulo, latitude, longitude, distancia_km))
            chamado_id = c.lastrowid
            conn.commit()
        
        # Salvar mensagem do usuário
        c.execute('''INSERT INTO mensagens (chamado_id, tipo, conteudo)
                     VALUES (?, ?, ?)''', (chamado_id, 'user', mensagem))
        conn.commit()
        
        # Gerar resposta
        try:
            resposta = responder_cliente(
                pergunta=mensagem,
                modulo=modulo,
                nome_cliente=nome_cliente,
                telefone_cliente=telefone_cliente
            )
        except Exception as api_err:
            print(f"[ERRO] API do assistente: {api_err}")
            traceback.print_exc()
            resposta = (
                "Desculpe, ocorreu um erro ao processar sua mensagem.\n\n"
                "Por favor, tente novamente ou entre em contato:\n"
                "(11) 5677-4699"
            )
        
        # Salvar resposta
        c.execute('''INSERT INTO mensagens (chamado_id, tipo, conteudo)
                     VALUES (?, ?, ?)''', (chamado_id, 'assistant', resposta))
        c.execute('''UPDATE chamados 
                     SET atualizado_em = CURRENT_TIMESTAMP
                     WHERE id = ?''', (chamado_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'resposta': resposta,
            'chamado_id': chamado_id
        })
        
    except Exception as e:
        print(f"[ERRO] Chat: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'resposta': "Erro ao processar mensagem. Tente novamente.",
            'erro': str(e)
        }), 500

# ============================ LOCALIZAÇÃO ============================

@app.route('/salvar-localizacao', methods=['POST'])
def salvar_localizacao():
    """Salva localização do cliente"""
    try:
        data = request.json
        chamado_id = data.get('chamado_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if chamado_id and latitude and longitude:
            distancia_km = calcular_distancia(
                float(latitude), float(longitude),
                STOROPACK_LAT, STOROPACK_LNG
            )
            
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''UPDATE chamados 
                         SET latitude = ?, longitude = ?, distancia_km = ?
                         WHERE id = ?''',
                     (latitude, longitude, distancia_km, chamado_id))
            conn.commit()
            conn.close()
        
        return jsonify({'sucesso': True})
    except Exception as e:
        print(f"[ERRO] Salvar localização: {str(e)}")
        return jsonify({'sucesso': False}), 500

# ============================ ANÁLISE DE VÍDEO ============================

@app.route('/analyze-video', methods=['POST'])
def analyze_video():
    """Analisa vídeo enviado pelo usuário"""
    try:
        if 'video' not in request.files:
            return jsonify({'erro': 'Nenhum vídeo enviado'}), 400
        
        video = request.files['video']
        modulo = request.form.get('modulo', '')
        
        if video.filename == '':
            return jsonify({'erro': 'Arquivo vazio'}), 400
        
        # Salvar vídeo temporariamente
        temp_dir = os.path.join(BASE_DIR, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        video_path = os.path.join(temp_dir, f"video_{datetime.now().timestamp()}.mp4")
        video.save(video_path)
        
        print(f"[VIDEO] Analisando vídeo para módulo: {modulo}")
        
        # Tentar usar o assistente com vídeo
        try:
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            
            resposta = responder_cliente(
                pergunta="Analise este vídeo e identifique o problema.",
                modulo=modulo,
                video_bytes=video_bytes,
                video_path=video_path
            )
        except Exception as e:
            print(f"[ERRO] Análise de vídeo: {e}")
            resposta = (
                "⚠️ Não foi possível analisar o vídeo automaticamente.\n\n"
                "Por favor, descreva o problema que está aparecendo:\n"
                "- Erro no display?\n"
                "- Problema de selagem?\n"
                "- Travamento?\n\n"
                "Ou ligue: (11) 5677-4699"
            )
        
        # Remover vídeo temporário
        try:
            os.remove(video_path)
        except:
            pass
        
        return jsonify({'resposta': resposta})
        
    except Exception as e:
        print(f"[ERRO] Endpoint analyze-video: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'erro': 'Erro ao processar vídeo',
            'resposta': 'Erro ao analisar vídeo. Por favor, descreva o problema por texto.'
        }), 500

# ============================ FEEDBACK ============================

@app.route('/feedback', methods=['POST'])
def feedback():
    """Registra feedback do cliente"""
    try:
        data = request.json
        chamado_id = data.get('chamado_id')
        resolvido = data.get('resolvido')
        comentario = data.get('comentario', '')
        
        status = 'resolvido' if resolvido else 'nao_resolvido'
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''UPDATE chamados 
                     SET status = ?, atualizado_em = CURRENT_TIMESTAMP
                     WHERE id = ?''',
                 (status, chamado_id))
        
        if comentario:
            c.execute('''INSERT INTO mensagens (chamado_id, tipo, conteudo)
                         VALUES (?, ?, ?)''',
                     (chamado_id, 'feedback', comentario))
        
        conn.commit()
        conn.close()
        
        return jsonify({'sucesso': True})
    except Exception as e:
        print(f"[ERRO] Feedback: {str(e)}")
        return jsonify({'sucesso': False}), 500

# ============================ ADMIN ============================

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Login do admin"""
    try:
        data = request.json
        senha = data.get('senha')
        if senha == ADMIN_PASSWORD:
            session['admin'] = True
            return jsonify({'sucesso': True})
        else:
            return jsonify({'sucesso': False})
    except Exception as e:
        print(f"[ERRO] Admin login: {str(e)}")
        return jsonify({'sucesso': False}), 500

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """Estatísticas gerais"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM chamados')
        total_chamados = c.fetchone()['total']
        
        c.execute('''SELECT COUNT(*) as hoje FROM chamados 
                     WHERE DATE(criado_em) = DATE('now')''')
        chamados_hoje = c.fetchone()['hoje']
        
        c.execute('''SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'resolvido' THEN 1 ELSE 0 END) as resolvidos
                     FROM chamados''')
        row = c.fetchone()
        taxa_resolucao_bot = int((row['resolvidos'] / row['total'] * 100)) if row['total'] > 0 else 0
        
        c.execute('''SELECT COUNT(*) as pendentes FROM chamados 
                     WHERE status = 'pendente_tecnico' ''')
        pendentes_tecnico = c.fetchone()['pendentes']
        
        c.execute('''SELECT AVG(distancia_km) as media FROM chamados 
                     WHERE distancia_km IS NOT NULL''')
        distancia_media = c.fetchone()['media'] or 0
        
        conn.close()
        
        return jsonify({
            'total_chamados': total_chamados,
            'chamados_hoje': chamados_hoje,
            'taxa_resolucao_bot': taxa_resolucao_bot,
            'pendentes_tecnico': pendentes_tecnico,
            'distancia_media_km': round(distancia_media, 1)
        })
    except Exception as e:
        print(f"[ERRO] Admin stats: {str(e)}")
        return jsonify({}), 500

@app.route('/admin/chamados', methods=['GET'])
def admin_chamados():
    """Lista de chamados com filtros"""
    try:
        status = request.args.get('status')
        modulo = request.args.get('modulo')
        data = request.args.get('data')
        per_page = int(request.args.get('per_page', 20))
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = '''SELECT c.*, 
                         (SELECT COUNT(*) FROM mensagens WHERE chamado_id = c.id) as total_msgs
                   FROM chamados c
                   WHERE 1=1'''
        params = []
        
        if status:
            query += ' AND c.status = ?'
            params.append(status)
        if modulo:
            query += ' AND c.modulo LIKE ?'
            params.append(f'{modulo}%')
        if data:
            query += ' AND DATE(c.criado_em) = ?'
            params.append(data)
        
        query += ' ORDER BY c.atualizado_em DESC LIMIT ?'
        params.append(per_page)
        
        c.execute(query, params)
        chamados = [dict(row) for row in c.fetchall()]
        conn.close()
        
        return jsonify({'chamados': chamados})
    except Exception as e:
        print(f"[ERRO] Admin chamados: {str(e)}")
        return jsonify({'chamados': []}), 500

@app.route('/admin/pendentes-tecnico', methods=['GET'])
def admin_pendentes():
    """Chamados pendentes para técnico"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''SELECT c.*, 
                           (SELECT COUNT(*) FROM mensagens WHERE chamado_id = c.id) as total_msgs
                     FROM chamados c
                     WHERE c.status = 'pendente_tecnico'
                     ORDER BY c.atualizado_em DESC''')
        pendentes = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify(pendentes)
    except Exception as e:
        print(f"[ERRO] Admin pendentes: {str(e)}")
        return jsonify([]), 500

@app.route('/admin/chamado/<int:chamado_id>', methods=['GET'])
def admin_chamado_detalhes(chamado_id):
    """Detalhes completos de um chamado"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''SELECT c.*,
                           (SELECT COUNT(*) FROM mensagens WHERE chamado_id = c.id) as total_msgs
                     FROM chamados c
                     WHERE c.id = ?''', (chamado_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({'erro': 'Chamado não encontrado'}), 404
        
        chamado = dict(row)
        
        c.execute('''SELECT * FROM mensagens 
                     WHERE chamado_id = ?
                     ORDER BY criado_em ASC''', (chamado_id,))
        mensagens = [dict(r) for r in c.fetchall()]
        chamado['mensagens'] = mensagens
        conn.close()
        
        return jsonify(chamado)
    except Exception as e:
        print(f"[ERRO] Admin chamado detalhes: {str(e)}")
        return jsonify({}), 500

@app.route('/admin/chamado/<int:chamado_id>/status', methods=['PUT'])
def admin_alterar_status(chamado_id):
    """Alterar status do chamado"""
    try:
        data = request.json
        novo_status = data.get('status')
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''UPDATE chamados 
                     SET status = ?, atualizado_em = CURRENT_TIMESTAMP
                     WHERE id = ?''', (novo_status, chamado_id))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True})
    except Exception as e:
        print(f"[ERRO] Alterar status: {str(e)}")
        return jsonify({'sucesso': False}), 500

@app.route('/admin/chamado/<int:chamado_id>', methods=['DELETE'])
def admin_excluir_chamado(chamado_id):
    """Excluir chamado"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM mensagens WHERE chamado_id = ?', (chamado_id,))
        c.execute('DELETE FROM chamados WHERE id = ?', (chamado_id,))
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True})
    except Exception as e:
        print(f"[ERRO] Excluir chamado: {str(e)}")
        return jsonify({'sucesso': False}), 500

@app.route('/reiniciar', methods=['POST'])
def reiniciar():
    """Endpoint para reiniciar"""
    return jsonify({'sucesso': True})

# ============================ HEALTH CHECK ============================

@app.route('/health')
def health():
    """Endpoint de health check para o Render"""
    return jsonify({
        'status': 'ok',
        'assistente': 'ok' if ASSISTENTE_OK else 'offline'
    })

# ============================ INICIALIZAÇÃO AUTOMÁTICA ============================

# Inicializar banco de dados automaticamente quando o módulo é carregado
# (Funciona tanto com Flask dev server quanto com Gunicorn)
try:
    init_db()
    print("[OK] Banco de dados inicializado automaticamente")
except Exception as e:
    print(f"[ERRO] Falha ao inicializar banco: {e}")
    traceback.print_exc()

# Criar pastas necessárias
try:
    for pasta in ['static', 'static/erros', 'temp', 'logs', 'uploads', 'uploads/pdfs', 'uploads/videos']:
        os.makedirs(os.path.join(BASE_DIR, pasta), exist_ok=True)
except Exception as e:
    print(f"[AVISO] Não foi possível criar todas as pastas: {e}")

# ============================ INICIALIZAÇÃO ============================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  STOROPACK - ASSISTENTE TECNICO")
    print("="*60)
    print(f"\n  Diretorio base: {BASE_DIR}")
    
    # Verificar arquivos HTML
    index_exists = os.path.exists(os.path.join(BASE_DIR, 'index.html'))
    admin_exists = os.path.exists(os.path.join(BASE_DIR, 'admin.html'))
    
    print(f"\n  index.html: {'OK' if index_exists else 'NAO ENCONTRADO'}")
    print(f"  admin.html: {'OK' if admin_exists else 'NAO ENCONTRADO'}")
    print(f"  Assistente: {'OK' if ASSISTENTE_OK else 'OFFLINE (modo fallback)'}")
    
    # Configuração para Render (usa PORT da variável de ambiente)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n  Chat:  http://localhost:{port}")
    print(f"  Admin: http://localhost:{port}/admin")
    print(f"  Senha: {ADMIN_PASSWORD}")
    print("\n" + "="*60 + "\n")
    
    # Iniciar servidor
    # Em produção (Render), gunicorn vai rodar o app
    # Em desenvolvimento local, usa o servidor Flask
    app.run(debug=False, host='0.0.0.0', port=port)