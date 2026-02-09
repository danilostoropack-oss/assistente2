"""
Banco de dados SQLite para o Assistente Storopack.
Gerencia chamados, mensagens, feedback, manuais e logs.
"""

import sqlite3
import os
import uuid
from datetime import datetime, timedelta
import json


DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'storopack.db')


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.inicializar()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def inicializar(self):
        """Cria as tabelas se nao existirem."""
        conn = self._conn()
        cursor = conn.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS chamados (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                nome_cliente TEXT,
                telefone_cliente TEXT,
                modulo TEXT,
                cidade TEXT DEFAULT '',
                distancia_estimada TEXT DEFAULT '',
                status TEXT DEFAULT 'aberto',
                resolvido_bot INTEGER DEFAULT 0,
                resolvido_tecnico INTEGER DEFAULT 0,
                feedback_comentario TEXT DEFAULT '',
                tecnico_acionado INTEGER DEFAULT 0,
                tecnico_observacao TEXT DEFAULT '',
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                atualizado_em TEXT DEFAULT (datetime('now', 'localtime')),
                encerrado_em TEXT
            );

            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id TEXT,
                remetente TEXT,
                conteudo TEXT,
                criado_em TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (chamado_id) REFERENCES chamados(id)
            );

            CREATE TABLE IF NOT EXISTS manuais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_arquivo TEXT,
                modulo TEXT,
                descricao TEXT,
                tipo TEXT DEFAULT 'pdf',
                caminho TEXT,
                criado_em TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS localizacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                latitude REAL,
                longitude REAL,
                criado_em TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                mensagem TEXT,
                dados TEXT,
                criado_em TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status);
            CREATE INDEX IF NOT EXISTS idx_chamados_modulo ON chamados(modulo);
            CREATE INDEX IF NOT EXISTS idx_chamados_cidade ON chamados(cidade);
            CREATE INDEX IF NOT EXISTS idx_chamados_criado ON chamados(criado_em);
            CREATE INDEX IF NOT EXISTS idx_mensagens_chamado ON mensagens(chamado_id);
            CREATE INDEX IF NOT EXISTS idx_localizacoes_session ON localizacoes(session_id);
        """)

        conn.commit()
        conn.close()

    # ========================= CHAMADOS =========================

    def criar_chamado(self, session_id, modulo, cidade=""):
        """Cria um novo chamado e retorna o ID."""
        chamado_id = str(uuid.uuid4())[:8]
        conn = self._conn()
        conn.execute(
            "INSERT INTO chamados (id, session_id, modulo, cidade) VALUES (?, ?, ?, ?)",
            (chamado_id, session_id, modulo, cidade)
        )
        conn.commit()
        conn.close()
        self._log("chamado_criado", f"Chamado {chamado_id} criado", {
            "modulo": modulo, "cidade": cidade
        })
        return chamado_id

    def salvar_localizacao(self, session_id, latitude, longitude):
        """Salva a localizacao GPS do usuario"""
        conn = self._conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO localizacoes (session_id, latitude, longitude, criado_em)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
            """, (session_id, latitude, longitude))
            conn.commit()
            self._log("info", f"Localizacao salva para session {session_id}")
        except Exception as e:
            conn.rollback()
            self._log("erro", f"Erro ao salvar localizacao: {e}")
            raise
        finally:
            conn.close()

    def atualizar_cidade(self, chamado_id, cidade):
        """Atualiza cidade do chamado."""
        # Removido import circular - distancia calculada externamente se necessario
        conn = self._conn()
        conn.execute(
            "UPDATE chamados SET cidade = ?, atualizado_em = datetime('now','localtime') WHERE id = ?",
            (cidade, chamado_id)
        )
        conn.commit()
        conn.close()

    def registrar_mensagem(self, chamado_id, remetente, conteudo):
        """Registra uma mensagem no chamado."""
        conn = self._conn()
        conn.execute(
            "INSERT INTO mensagens (chamado_id, remetente, conteudo) VALUES (?, ?, ?)",
            (chamado_id, remetente, conteudo)
        )
        conn.execute(
            "UPDATE chamados SET atualizado_em = datetime('now','localtime') WHERE id = ?",
            (chamado_id,)
        )
        conn.commit()
        conn.close()

    def registrar_feedback(self, chamado_id, resolvido, comentario=""):
        """Registra feedback do cliente."""
        status = "resolvido" if resolvido else "nao_resolvido"
        conn = self._conn()
        conn.execute(
            """UPDATE chamados 
               SET resolvido_bot = ?, feedback_comentario = ?, status = ?,
                   encerrado_em = datetime('now','localtime'),
                   atualizado_em = datetime('now','localtime')
               WHERE id = ?""",
            (1 if resolvido else 0, comentario, status, chamado_id)
        )
        conn.commit()
        conn.close()
        self._log("feedback", f"Chamado {chamado_id}: {'resolvido' if resolvido else 'nao resolvido'}", {
            "chamado_id": chamado_id, "resolvido": resolvido, "comentario": comentario
        })

    def acionar_tecnico(self, chamado_id):
        """Marca chamado como pendente para tecnico."""
        conn = self._conn()
        conn.execute(
            """UPDATE chamados 
               SET tecnico_acionado = 1, status = 'pendente_tecnico',
                   atualizado_em = datetime('now','localtime')
               WHERE id = ?""",
            (chamado_id,)
        )
        conn.commit()
        conn.close()
        self._log("tecnico_acionado", f"Tecnico acionado para chamado {chamado_id}", {
            "chamado_id": chamado_id
        })

    def resolver_chamado_tecnico(self, chamado_id, observacao=""):
        """Tecnico resolve o chamado manualmente."""
        conn = self._conn()
        conn.execute(
            """UPDATE chamados 
               SET resolvido_tecnico = 1, tecnico_observacao = ?, status = 'resolvido_tecnico',
                   encerrado_em = datetime('now','localtime'),
                   atualizado_em = datetime('now','localtime')
               WHERE id = ?""",
            (observacao, chamado_id)
        )
        conn.commit()
        conn.close()
        self._log("tecnico_resolveu", f"Tecnico resolveu chamado {chamado_id}", {
            "chamado_id": chamado_id, "observacao": observacao
        })

    # ========================= CONSULTAS =========================

    def get_chamado(self, chamado_id):
        """Retorna detalhes de um chamado com mensagens."""
        conn = self._conn()
        chamado = conn.execute("SELECT * FROM chamados WHERE id = ?", (chamado_id,)).fetchone()
        if not chamado:
            conn.close()
            return None

        mensagens = conn.execute(
            "SELECT * FROM mensagens WHERE chamado_id = ? ORDER BY criado_em",
            (chamado_id,)
        ).fetchall()
        conn.close()

        return {
            "chamado": dict(chamado),
            "mensagens": [dict(m) for m in mensagens]
        }

    def listar_chamados(self, filtros=None):
        """Lista chamados com filtros e paginacao."""
        filtros = filtros or {}
        conn = self._conn()

        where = []
        params = []

        if filtros.get("status"):
            where.append("status = ?")
            params.append(filtros["status"])
        if filtros.get("modulo"):
            where.append("modulo LIKE ?")
            params.append(f"%{filtros['modulo']}%")
        if filtros.get("cidade"):
            where.append("cidade LIKE ?")
            params.append(f"%{filtros['cidade']}%")
        if filtros.get("data_inicio"):
            where.append("criado_em >= ?")
            params.append(filtros["data_inicio"])
        if filtros.get("data_fim"):
            where.append("criado_em <= ?")
            params.append(filtros["data_fim"] + " 23:59:59")

        where_clause = " AND ".join(where) if where else "1=1"

        total = conn.execute(f"SELECT COUNT(*) as total FROM chamados WHERE {where_clause}", params).fetchone()["total"]

        page = filtros.get("page", 1)
        per_page = filtros.get("per_page", 20)
        offset = (page - 1) * per_page

        chamados = conn.execute(
            f"""SELECT * FROM chamados WHERE {where_clause} 
                ORDER BY criado_em DESC LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()

        conn.close()

        return {
            "chamados": [dict(c) for c in chamados],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    def listar_pendentes_tecnico(self):
        """Lista chamados que precisam de atencao do tecnico."""
        conn = self._conn()
        chamados = conn.execute(
            """SELECT c.*, 
                      (SELECT COUNT(*) FROM mensagens WHERE chamado_id = c.id) as total_msgs
               FROM chamados c 
               WHERE c.status = 'pendente_tecnico' 
               ORDER BY c.criado_em DESC"""
        ).fetchall()
        conn.close()
        return [dict(c) for c in chamados]

    def get_estatisticas(self):
        """Retorna estatisticas gerais para o painel."""
        conn = self._conn()

        hoje = datetime.now().strftime("%Y-%m-%d")
        semana = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        mes = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        stats = {}

        stats["total_chamados"] = conn.execute("SELECT COUNT(*) as c FROM chamados").fetchone()["c"]
        stats["chamados_hoje"] = conn.execute(
            "SELECT COUNT(*) as c FROM chamados WHERE criado_em >= ?", (hoje,)
        ).fetchone()["c"]
        stats["chamados_semana"] = conn.execute(
            "SELECT COUNT(*) as c FROM chamados WHERE criado_em >= ?", (semana,)
        ).fetchone()["c"]
        stats["chamados_mes"] = conn.execute(
            "SELECT COUNT(*) as c FROM chamados WHERE criado_em >= ?", (mes,)
        ).fetchone()["c"]

        stats["por_status"] = {}
        for row in conn.execute("SELECT status, COUNT(*) as c FROM chamados GROUP BY status"):
            stats["por_status"][row["status"]] = row["c"]

        stats["por_modulo"] = {}
        for row in conn.execute("SELECT modulo, COUNT(*) as c FROM chamados GROUP BY modulo ORDER BY c DESC"):
            stats["por_modulo"][row["modulo"] or "sem_modulo"] = row["c"]

        stats["por_cidade"] = {}
        for row in conn.execute(
            "SELECT cidade, COUNT(*) as c FROM chamados WHERE cidade != '' GROUP BY cidade ORDER BY c DESC LIMIT 10"
        ):
            stats["por_cidade"][row["cidade"]] = row["c"]

        resolvidos = conn.execute(
            "SELECT COUNT(*) as c FROM chamados WHERE resolvido_bot = 1"
        ).fetchone()["c"]
        total_com_feedback = conn.execute(
            "SELECT COUNT(*) as c FROM chamados WHERE status IN ('resolvido', 'nao_resolvido', 'resolvido_tecnico')"
        ).fetchone()["c"]
        stats["taxa_resolucao_bot"] = round(
            (resolvidos / total_com_feedback * 100) if total_com_feedback > 0 else 0, 1
        )

        stats["pendentes_tecnico"] = conn.execute(
            "SELECT COUNT(*) as c FROM chamados WHERE status = 'pendente_tecnico'"
        ).fetchone()["c"]

        stats["por_dia"] = []
        for row in conn.execute(
            """SELECT DATE(criado_em) as dia, COUNT(*) as c 
               FROM chamados WHERE criado_em >= ? 
               GROUP BY DATE(criado_em) ORDER BY dia""",
            (mes,)
        ):
            stats["por_dia"].append({"dia": row["dia"], "total": row["c"]})

        stats["total_mensagens"] = conn.execute("SELECT COUNT(*) as c FROM mensagens").fetchone()["c"]

        conn.close()
        return stats

    # ========================= MANUAIS =========================

    def registrar_manual(self, nome_arquivo, modulo, descricao, tipo, caminho):
        conn = self._conn()
        conn.execute(
            "INSERT INTO manuais (nome_arquivo, modulo, descricao, tipo, caminho) VALUES (?, ?, ?, ?, ?)",
            (nome_arquivo, modulo, descricao, tipo, caminho)
        )
        conn.commit()
        conn.close()

    def listar_manuais(self):
        conn = self._conn()
        manuais = conn.execute("SELECT * FROM manuais ORDER BY criado_em DESC").fetchall()
        conn.close()
        return [dict(m) for m in manuais]

    # ========================= LOGS =========================

    def _log(self, tipo, mensagem, dados=None):
        try:
            conn = self._conn()
            conn.execute(
                "INSERT INTO logs (tipo, mensagem, dados) VALUES (?, ?, ?)",
                (tipo, mensagem, json.dumps(dados or {}, ensure_ascii=False))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao registrar log: {e}")
