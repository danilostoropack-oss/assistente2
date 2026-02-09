"""
Analisador de Video com Google Gemini para Storopack
Versao otimizada que usa Gemini 2.5 Flash para analisar videos diretamente
"""

import os
import base64
import json
import tempfile
from dotenv import load_dotenv

load_dotenv(override=True)

# Base de conhecimento de erros visuais por modulo
ERROS_VISUAIS = {
    "airplus": {
        "E1": {
            "nome": "Erro de Sensor de Filme",
            "sinais": ["LED vermelho aceso", "display mostrando E1", "filme desalinhado"],
            "solucao": "1. Desligue a maquina\n2. Verifique o alinhamento do filme\n3. Limpe o sensor com pano seco\n4. Religue e teste",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        },
        "E2": {
            "nome": "Falha na Selagem",
            "sinais": ["almofadas nao selam corretamente", "vazamento de ar", "selagem fraca"],
            "solucao": "1. Verifique a temperatura de selagem\n2. Limpe a barra de selagem\n3. Ajuste a pressao\n4. Teste com novo filme",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        },
        "E3": {
            "nome": "Problema de Pressao de Ar",
            "sinais": ["almofadas murchas", "som de vazamento", "mangueiras soltas", "display E3"],
            "solucao": "1. Verifique conexoes de ar\n2. Cheque mangueiras\n3. Limpe filtro de ar\n4. Ajuste pressao no regulador",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        },
        "E4": {
            "nome": "Erro no Sensor de Corte",
            "sinais": ["filme nao corta", "corte irregular", "lamina travada"],
            "solucao": "1. Desligue a maquina\n2. Verifique a lamina de corte\n3. Limpe residuos\n4. Substitua lamina se necessario",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        },
        "E5": {
            "nome": "Superaquecimento",
            "sinais": ["maquina muito quente", "cheiro de queimado", "desligamento automatico"],
            "solucao": "1. Desligue imediatamente\n2. Aguarde 30 minutos\n3. Verifique ventilacao\n4. Limpe filtros de ar",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        },
        "travamento": {
            "nome": "Travamento de Filme",
            "sinais": ["filme preso", "filme embolado", "maquina parada"],
            "solucao": "1. Desligue a maquina\n2. Abra a tampa\n3. Remova o filme preso\n4. Realinhe o filme\n5. Feche e teste",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        }
    },
    "paperplus": {
        "papel_preso": {
            "nome": "Papel Preso",
            "sinais": ["papel amassado", "papel nao sai", "travamento"],
            "solucao": "1. Desligue a maquina\n2. Abra a tampa traseira\n3. Remova o papel preso\n4. Verifique rolos\n5. Recarregue o papel",
            "video": "https://www.youtube.com/watch?v=a8iCa46yRu4"
        },
        "corte_irregular": {
            "nome": "Corte Irregular",
            "sinais": ["bordas irregulares", "corte torto", "lamina gasta"],
            "solucao": "1. Verifique a lamina\n2. Limpe residuos\n3. Ajuste a pressao\n4. Substitua lamina se necessario",
            "video": "https://www.youtube.com/watch?v=a8iCa46yRu4"
        }
    },
    "foamplus": {
        "espuma_nao_expande": {
            "nome": "Espuma Nao Expande",
            "sinais": ["espuma liquida", "nao forma volume", "mistura incorreta"],
            "solucao": "1. Verifique os quimicos\n2. Cheque a proporcao\n3. Limpe os bicos\n4. Ajuste a temperatura",
            "video": "https://www.youtube.com/watch?v=bhVK8KCJihs"
        },
        "vazamento": {
            "nome": "Vazamento de Quimico",
            "sinais": ["liquido escorrendo", "poca no chao", "conexoes molhadas"],
            "solucao": "1. Desligue imediatamente\n2. Ventile a area\n3. Limpe o vazamento\n4. Verifique conexoes\n5. Chame suporte tecnico",
            "video": "https://www.youtube.com/watch?v=bhVK8KCJihs"
        }
    },
    "airmove": {
        "E1": {
            "nome": "Erro de Sensor",
            "sinais": ["LED vermelho", "display E1"],
            "solucao": "1. Desligue a maquina\n2. Verifique sensores\n3. Limpe com pano seco\n4. Religue",
            "video": "https://www.youtube.com/watch?v=IbG1o-UbrtI"
        }
    }
}


def analisar_com_gemini(video_bytes, modulo, descricao=""):
    """
    Analisa video diretamente com Google Gemini 2.5 Flash.
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None, "GOOGLE_API_KEY nao configurada no arquivo .env"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        erros_modulo = ERROS_VISUAIS.get(modulo.split('_')[0], {})
        erros_lista = "\n".join([f"- {k}: {v['nome']} (sinais: {', '.join(v['sinais'])})" 
                                  for k, v in erros_modulo.items()])
        
        prompt = f"""Voce e um tecnico especialista em equipamentos Storopack.
Analise este video de um equipamento {modulo.upper()} e identifique possiveis erros.

ERROS CONHECIDOS:
{erros_lista}

{f'DESCRICAO DO CLIENTE: {descricao}' if descricao else ''}

INSTRUCOES:
1. Assista TODO o video com atencao
2. Procure por LEDs acesos, displays com codigos de erro, pecas travadas, vazamentos, etc
3. Compare com os erros conhecidos acima

Responda APENAS com JSON valido (sem markdown, sem ```):
{{
    "erro_identificado": "codigo_do_erro ou null",
    "confianca": "alta/media/baixa",
    "sinais_detectados": ["sinal1", "sinal2"],
    "descricao": "breve descricao do que foi visto no video"
}}"""

        print("[INFO] Enviando video para Gemini...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(video_bytes)
            temp_path = tmp_file.name
        
        try:
            video_file = genai.upload_file(temp_path)
            print(f"[INFO] Video enviado. Aguardando processamento...")
            
            import time
            while video_file.state.name == "PROCESSING":
                time.sleep(1)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                return None, "Falha no processamento do video pelo Gemini"
            
            print("[INFO] Analisando com IA...")
            response = model.generate_content([prompt, video_file])
            texto = response.text
            
            texto = texto.replace("```json", "").replace("```", "").strip()
            resultado = json.loads(texto)
            
            genai.delete_file(video_file.name)
            
            return resultado, None
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
    except ImportError:
        return None, "google-generativeai nao instalado. Execute: pip install google-generativeai"
    except json.JSONDecodeError as e:
        return {"erro_identificado": None, "descricao": texto if 'texto' in locals() else "Erro ao parsear resposta"}, None
    except Exception as e:
        return None, f"Erro no Gemini: {str(e)}"


def formatar_resposta(resultado, modulo):
    """Formata a resposta da analise para exibicao."""
    
    if not resultado:
        return "Nao foi possivel analisar o video.\n\nDescreva o problema por texto ou ligue: (11) 5677-4699"
    
    erro_id = resultado.get("erro_identificado")
    confianca = resultado.get("confianca", "baixa").upper()
    sinais = resultado.get("sinais_detectados", [])
    descricao = resultado.get("descricao", "")
    
    modulo_base = modulo.split('_')[0]
    erros_modulo = ERROS_VISUAIS.get(modulo_base, {})
    
    resposta = "ANALISE DO VIDEO\n\n"
    resposta += f"Confianca: {confianca}\n\n"
    
    if erro_id and erro_id in erros_modulo:
        erro_info = erros_modulo[erro_id]
        resposta += f"Erro Identificado: {erro_info['nome']}\n\n"
        
        if sinais:
            resposta += "Sinais Detectados:\n"
            for sinal in sinais:
                resposta += f"- {sinal}\n"
            resposta += "\n"
        
        resposta += "---\n\n"
        resposta += f"SOLUCAO:\n\n{erro_info['solucao']}\n\n"
        
        if erro_info.get('video'):
            resposta += f"Video de apoio:\n{erro_info['video']}\n\n"
    else:
        resposta += f"Observacao: {descricao}\n\n"
        resposta += "Nao foi possivel identificar um erro especifico.\n"
        resposta += "Por favor, descreva o problema com mais detalhes.\n\n"
    
    resposta += "Se precisar de ajuda: (11) 5677-4699"
    
    return resposta


def analisar_video_erro(video_bytes=None, video_path=None, modulo="airplus", descricao_cliente=""):
    """
    Funcao principal para analisar video de erro.
    """
    
    if video_path:
        try:
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
        except Exception as e:
            return f"Erro ao ler video: {str(e)}"
    
    if not video_bytes:
        return "Nenhum video fornecido."
    
    max_size = 100 * 1024 * 1024
    if len(video_bytes) > max_size:
        return "Video muito grande (maximo 100MB).\n\nEnvie um video menor ou descreva o problema por texto."
    
    print(f"[INFO] Video recebido: {len(video_bytes)/1024/1024:.2f}MB")
    
    resultado, erro = analisar_com_gemini(video_bytes, modulo, descricao_cliente)
    
    if erro:
        return f"{erro}\n\nDescreva o problema por texto ou ligue: (11) 5677-4699"
    
    return formatar_resposta(resultado, modulo)


if __name__ == "__main__":
    print("Video Analyzer para Storopack (Google Gemini)")
    print("Modulos disponiveis:", list(ERROS_VISUAIS.keys()))
