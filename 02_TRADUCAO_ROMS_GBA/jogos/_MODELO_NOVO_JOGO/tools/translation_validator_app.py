#!/usr/bin/env python3
"""
GBA Localization Studio — Suite de Validação, QA Gate & Engenharia (PT-BR)
==========================================================================
Arquitetura de Estúdio em 3 Tiers (Claude-Code-Game-Studios + Protocolos Mestres)
Servidor de altíssima performance (com cache em memória por mtime) e zero dependências
externas que lê e atualiza diretamente os arquivos .md de qualquer jogo do estúdio.

Principais Recursos da Nova Versão (Studio Edition v2.0):
  1. [MULTI-PROJETO DINÂMICO] Alternância em tempo real entre jogos da pasta `jogos/`
     (Summon Night 1, 2, 3, _MODELO_NOVO_JOGO ou novos projetos) sem reiniciar o servidor.
  2. [CACHE INTELIGENTE O(1)] Indexação ultra-rápida baseada em timestamp (`st_mtime_ns`):
     salvar 1 linha (ou validar lote inteiro) é instantâneo (< 10ms), eliminando re-scans lentos.
  3. [QUALITY GATE 5 BARREIRAS INTEGRADO] Execução em tempo real (por linha e por arquivo) das
     5 barreiras do `qa_gate_hook.py`:
       - Gate 1: Paridade de Tags Dinâmicas ({PLAYER}, {PARTNER}, {SIBLING}, [0x05], etc.)
       - Gate 2: Barreira Anti-Overflow (Ideal 1-32c, Soft 33-35c, Hard Limit >35c)
       - Gate 3: Prevenção de Orfandade Textual (monossílabos soltos no fim da linha antes de <br>)
       - Gate 4: Política Rígida de Abreviações (bloqueia internetês/abreviações em diálogos)
       - Gate 5: Neutralidade de Gênero Sistêmica em {PLAYER} e detecção de Inglês Residual
  4. [BÍBLIA DE PERSONAGENS & GLOSSÁRIO CIRÚRGICO] Extração automática de Tom de Voz (Character Voice),
     Registros de Fala, Biografia e Termos do Glossário presentes na frase atual.
  5. [OPERAÇÕES EM LOTE & EXPORTAÇÃO DE PROMPTS] Aprovação em lote de linhas sem erros de QA
     e geração instantânea de Prompt Cirúrgico (`token_optimizer_batcher`) para IA.
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Caminhos estruturais do estúdio
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_GAME_DIR = SCRIPT_DIR.parent
JOGOS_ROOT_DIR = DEFAULT_GAME_DIR.parent
STUDIO_ROOT_DIR = JOGOS_ROOT_DIR.parent
PROTOCOLO_EXTRACAO_DIR = STUDIO_ROOT_DIR / "protocolo_extracao"
PROTOCOLO_TRADUCAO_DIR = STUDIO_ROOT_DIR / "protocolo_traducao"
GLOBAL_GLOSSARY_PATH = PROTOCOLO_TRADUCAO_DIR / "GLOSSARIO_GLOBAL_SUMMON_NIGHT.md"

# Regex para extrair alternativa inline: `Texto A` *(ou `Texto B`)*
INLINE_OPT_RE = re.compile(
    r"^(.*?)\s*\*?\(\s*ou\s+([^)]+?)\s*\)\*?\s*$",
    re.IGNORECASE | re.DOTALL,
)

# Pistas linguísticas para inferência de gênero do interlocutor
MALE_CUES = re.compile(
    r"\b(garoto|menino|filho|irmãozinho|maninho|garotinho|rapaz|senhor|amigo|cansado|envergonhado|pronto|sozinho|preparado|ele|dele|irmão|homem|herói)\b",
    re.IGNORECASE,
)
FEMALE_CUES = re.compile(
    r"\b(garota|menina|filha|irmãzinha|maninha|garotinha|senhorita|amiga|cansada|envergonhada|pronta|sozinha|preparada|ela|dela|irmã|mulher|heroína)\b",
    re.IGNORECASE,
)

BRON_HEURISTIC_RE = re.compile(
    r"\b(ya|yer|climb aboard|yer head|ain't|mumblin'|askin'|bater perna|moleque|anda logo|yer self)\b",
    re.IGNORECASE,
)
BLAIRE_HEURISTIC_RE = re.compile(
    r"\b(blaire|forja|martelo|oficina|ferro|bigorna|moleque|guri|bater perna|anda logo|preguiçoso|trabalho duro)\b",
    re.IGNORECASE,
)

# ============================================================================
# REGRAS DO QUALITY GATE (5 BARREIRAS DO STUDIO)
# ============================================================================
FORBIDDEN_DIALOGUE_ABBREVS = [
    (re.compile(r"(?<!-)\bvc\b(?!-)", re.I), "vc"),
    (re.compile(r"(?<!-)\bvcs\b(?!-)", re.I), "vcs"),
    (re.compile(r"(?<!-)\bpq\b(?!-)", re.I), "pq"),
    (re.compile(r"(?<!-)\btb\b(?!-)", re.I), "tb"),
    (re.compile(r"(?<!-)\btbm\b(?!-)", re.I), "tbm"),
    (re.compile(r"(?<!-)\bctz\b(?!-)", re.I), "ctz"),
    (re.compile(r"(?<!-)\bblz\b(?!-)", re.I), "blz"),
    (re.compile(r"(?<!-)\bvlw\b(?!-)", re.I), "vlw"),
    (re.compile(r"(?<!-)\bflw\b(?!-)", re.I), "flw"),
    (re.compile(r"(?<!-)\bq\b(?!-)", re.I), "q"),
    (re.compile(r"\bp/\b", re.I), "p/"),
    (re.compile(r"\bc/\b", re.I), "c/"),
    (re.compile(r"\batq\.", re.I), "atq."),
    (re.compile(r"\bdef\.", re.I), "def."),
    (re.compile(r"\brecup\.", re.I), "recup."),
    (re.compile(r"\besp\.", re.I), "esp."),
    (re.compile(r"\bmin\.", re.I), "min."),
    (re.compile(r"\belem\.", re.I), "elem."),
]

ORPHAN_WORDS = {
    "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "em", "no", "na", "e", "ou", "que", "se", "por", "com", "para", "ao", "à"
}

GENDER_SUSPECT_PATTERNS = [
    (re.compile(r"\bvocê está cansado\b", re.I), "Use forma neutra: 'O cansaço bateu?' ou 'Já está sem fôlego?'"),
    (re.compile(r"\bvocê está pronto\b", re.I), "Use forma neutra: 'Tudo pronto?' ou 'Já se preparou?'"),
    (re.compile(r"\bvocê é muito rápido\b", re.I), "Use forma neutra: 'Você age com muita rapidez!'"),
    (re.compile(r"\bvocê é muito corajoso\b", re.I), "Use forma neutra: 'Você tem muita coragem!'"),
    (re.compile(r"\bvocê é muito habilidoso\b", re.I), "Use forma neutra: 'Sua habilidade é impressionante!'"),
    (re.compile(r"\bbem-vindo\b", re.I), "Se dirigido a {PLAYER}, use: 'Boas-vindas!' ou 'Que bom ver você!'"),
    (re.compile(r"\bobrigado/a\b", re.I), "Proibido barra de gênero: use 'Agradeço de coração!' ou 'Meus agradecimentos!'"),
    (re.compile(r"\bcansado\(a\)\b|\bpronto\(a\)\b|\bsozinho\(a\)\b", re.I), "Proibido parênteses de gênero (a): reescreva com substantivos abstratos"),
    (re.compile(r"\bo \{player\}\b|\ba \{player\}\b|\bdo \{player\}\b|\bda \{player\}\b|\bao \{player\}\b|\bpelo \{player\}\b", re.I), "Choque de artigo com {PLAYER}: remova o artigo antes da variável"),
]

RESIDUAL_ENGLISH_PATTERNS = [
    re.compile(r"\bCraftknight\b"),
    re.compile(r"\bCraftlord\b"),
    re.compile(r"\bSummon Beast\b"),
    re.compile(r"\bGuardian Beast\b"),
    re.compile(r"\bSummon Stray\b"),
    re.compile(r"\bSilver Guild\b"),
    re.compile(r"\bGold Guild\b"),
    re.compile(r"\bCentral Tower\b"),
    re.compile(r"\bMarine Dungeon\b"),
    re.compile(r"\bBosque Labyrinth\b"),
    re.compile(r"\bKagro Volcano\b"),
    re.compile(r"\bHuh\?"),
    re.compile(r"\bSigh\b"),
    re.compile(r"\bGulp\b"),
    re.compile(r"\bYikes\b"),
]

CANONICAL_ABBREVIATIONS = [
    {"term": "Ataque / Poder", "abbr": "ATQ", "example": "ATQ +15"},
    {"term": "Defesa", "abbr": "DEF", "example": "DEF +8"},
    {"term": "Agilidade", "abbr": "AGI", "example": "AGI +5"},
    {"term": "Durabilidade", "abbr": "DUR", "example": "DUR 120"},
    {"term": "Pontos de Vida", "abbr": "HP", "example": "Recup. 50 HP"},
    {"term": "Recuperação", "abbr": "Recup.", "example": "Recup. HP"},
    {"term": "Especial", "abbr": "Esp.", "example": "Técnica Esp."},
    {"term": "Elemento", "abbr": "Elem.", "example": "Dano Elem."},
    {"term": "Espada / Machado / Lança", "abbr": "Esp. / Mach. / Lanç.", "example": "Esp. de Ferro"},
    {"term": "Soqueira / Broca", "abbr": "Soq. / Broc.", "example": "Soq. de Aço"},
    {"term": "Minério", "abbr": "Min.", "example": "Min. Místico"},
    {"term": "Nível / Andar", "abbr": "Nv. / A", "example": "Nv. 25 / 2A"},
]

# ============================================================================
# PERFIS DE JOGOS CONHECIDOS E ESTADO ATIVO DO SERVIDOR
# ============================================================================
GAME_PROFILES: Dict[str, Dict[str, Any]] = {
    "Summon_Night_Swordcraft_Story_1": {
        "id": "Summon_Night_Swordcraft_Story_1",
        "short_code": "SN1",
        "title": "Summon Night: Swordcraft Story 1",
        "platform": "GBA",
        "product_code": "AGB-AB4E-USA",
        "male_hero": ("cleru", "♂ Cleru", "Herói (Aprendiz de Forjador)"),
        "female_hero": ("pratty", "♀ Pratty", "Heroína (Aprendiz de Forjadora)"),
        "hard_limit": 35,
        "soft_limit": 33,
    },
    "Summon_Night_Swordcraft_Story_2": {
        "id": "Summon_Night_Swordcraft_Story_2",
        "short_code": "SN2",
        "title": "Summon Night: Swordcraft Story 2",
        "platform": "GBA",
        "product_code": "AGB-BSKE-USA",
        "male_hero": ("edgar", "♂ Edgar", "Herói (Aprendiz de Forjador)"),
        "female_hero": ("aera", "♀ Aera", "Heroína (Aprendiz de Forjadora)"),
        "hard_limit": 35,
        "soft_limit": 33,
    },
    "Summon_Night_Swordcraft_Story_3": {
        "id": "Summon_Night_Swordcraft_Story_3",
        "short_code": "SN3",
        "title": "Summon Night: Swordcraft Story 3 (Pedra do Início)",
        "platform": "GBA",
        "product_code": "AGB-B3CJ-JPN",
        "male_hero": ("ritchie", "♂ Ritchie", "Herói (Aprendiz de Cavaleiro Forjador)"),
        "female_hero": ("rif", "♀ Rif", "Heroína (Aprendiz de Cavaleira Forjadora)"),
        "hard_limit": 35,
        "soft_limit": 33,
    },
    "_MODELO_NOVO_JOGO": {
        "id": "_MODELO_NOVO_JOGO",
        "short_code": "GBA",
        "title": "Template / Novo Projeto GBA",
        "platform": "GBA",
        "product_code": "AGB-XXXX-USA",
        "male_hero": ("hero_male", "♂ Herói", "Protagonista Masculino"),
        "female_hero": ("hero_female", "♀ Heroína", "Protagonista Feminina"),
        "hard_limit": 35,
        "soft_limit": 33,
    },
}


class StudioProjectContext:
    """Gerencia o estado e o cache em memória de um projeto de jogo específico."""

    def __init__(self, game_dir: Path) -> None:
        self.game_dir = game_dir.resolve()
        self.game_id = self.game_dir.name
        self.md_dir = self.game_dir / "ARQUIVOS md"
        self.tools_dir = self.game_dir / "tools"
        self.embedded_js_path = self.tools_dir / "embedded_md_data.js"
        self.ui_html_path = self.tools_dir / "validator_ui.html"

        base_prof = GAME_PROFILES.get(self.game_id, GAME_PROFILES["_MODELO_NOVO_JOGO"]).copy()
        if self.game_id not in GAME_PROFILES:
            base_prof["id"] = self.game_id
            base_prof["short_code"] = "".join(w[0] for w in self.game_id.split("_") if w)[:3].upper() or "GBA"
            base_prof["title"] = self.game_id.replace("_", " ")
        self.profile = base_prof

        # Cache de arquivos parseados: rel_name -> {"mtime": int, "data": dict}
        self.file_cache: Dict[str, Dict[str, Any]] = {}
        self.global_script_speakers: Dict[Tuple[int, int], str] = {}
        self.character_bible: Dict[str, Dict[str, Any]] = {}
        self.voice_matrix: List[Dict[str, str]] = []
        self.glossary_terms: List[Dict[str, str]] = []
        self._initialized = False
        self._lock = threading.Lock()

    def ensure_initialized(self, force: bool = False) -> None:
        with self._lock:
            if self._initialized and not force:
                return
            self._load_character_bible()
            self._load_glossaries()
            self._build_global_speaker_map()
            self._initialized = True

    def _load_character_bible(self) -> None:
        """Extrai as fichas completas e matriz de vozes do catalogo-de-personagens.md."""
        self.character_bible.clear()
        self.voice_matrix.clear()
        cat_file = self.md_dir / "catalogo-de-personagens.md"
        if not cat_file.is_file():
            return

        try:
            text = cat_file.read_text(encoding="utf-8", errors="ignore")
            lines = text.splitlines()

            # 1. Extrai tabelas de Matriz de Registros / Sumário
            in_table = False
            headers: List[str] = []
            for line in lines:
                s = line.strip()
                if s.startswith("|") and ("---" in s or ":---" in s):
                    in_table = True
                    continue
                if s.startswith("|") and not in_table:
                    headers = [h.lower() for h in split_md_row(s)]
                    continue
                if in_table:
                    if not s.startswith("|"):
                        in_table = False
                        headers = []
                        continue
                    cells = split_md_row(s)
                    if len(cells) >= 3 and any("registro" in h for h in headers):
                        reg = _strip_md_formatting(cells[0])
                        carac = _strip_md_formatting(cells[1])
                        assoc = _strip_md_formatting(cells[2]) if len(cells) > 2 else ""
                        if reg:
                            self.voice_matrix.append({
                                "register": reg,
                                "traits": carac,
                                "characters": assoc,
                            })

            # 2. Extrai blocos ### de fichas de personagens
            sections = re.split(r"\n(?=###\s+)", text)
            for sec in sections:
                if not sec.strip().startswith("###"):
                    continue
                sec_lines = sec.strip().splitlines()
                header_line = sec_lines[0].lstrip("#").strip()

                # Exemplo: `CHR_01` — Cleru (クレル) ➔ **Cleru**
                m_arrow = re.search(r"➔\s*\*\*([^\*]+)\*\*", header_line)
                if m_arrow:
                    disp_name = m_arrow.group(1).strip()
                else:
                    disp_name = re.sub(r"^`[^`]+`\s*[—\-]\s*", "", header_line).strip()
                    disp_name = re.sub(r"\(.*?\)", "", disp_name).strip()

                if not disp_name or "Modelo de Ficha" in disp_name or "[Nome" in disp_name:
                    continue

                body = "\n".join(sec_lines[1:])
                role_match = re.search(r"\*\*(?:Papel|Arquétipo|Perfil|Função)[^:]*:\*\*\s*([^\n]+)", body, re.I)
                origin_match = re.search(r"\*\*(?:Afiliação|Origem)[^:]*:\*\*\s*([^\n]+)", body, re.I)
                tone_match = re.search(r"\*\*(?:Tom de Voz|Diretrizes de Tradução|Idioleto)[^:]*:\*\*\s*([^\n]+(?:\n\s*\*[^\n]+)*)", body, re.I)
                idiom_match = re.search(r"\*\*(?:Idioleto PT-BR|Bordões|Expressões)[^:]*:\*\*\s*([^\n]+)", body, re.I)
                example_match = re.search(r"\*(?:Exemplo|Exemplo Prático|Bordões)[^:]*:\*\s*([^\n]+)", body, re.I)

                role_str = _strip_md_formatting(role_match.group(1)) if role_match else "Personagem da Obra"
                origin_str = _strip_md_formatting(origin_match.group(1)) if origin_match else ""
                tone_str = _strip_md_formatting(tone_match.group(1)).replace("\n", " ") if tone_match else ""
                idiom_str = _strip_md_formatting(idiom_match.group(1)) if idiom_match else ""
                ex_str = _strip_md_formatting(example_match.group(1)) if example_match else ""

                # Procura se o personagem está associado na matriz de voz
                matched_reg = ""
                clean_short = re.sub(r"\(.*?\)", "", disp_name).strip()
                for vm in self.voice_matrix:
                    if clean_short.lower() in vm["characters"].lower():
                        matched_reg = f"{vm['register']}: {vm['traits']}"
                        break

                if not tone_str and matched_reg:
                    tone_str = matched_reg

                key = clean_short.lower().replace(" ", "_")
                self.character_bible[key] = {
                    "id": key,
                    "name": disp_name,
                    "role": role_str,
                    "affiliation": origin_str,
                    "voice_register": matched_reg,
                    "voice_guidelines": tone_str or matched_reg or "Manter naturalidade dramática e coesão em PT-BR.",
                    "idiom": idiom_str,
                    "example": ex_str,
                }
        except Exception:
            pass

    def _load_glossaries(self) -> None:
        """Carrega termos do glossário local (02-glossario...) e do Glossário Global da franquia."""
        self.glossary_terms.clear()
        seen_orig = set()

        def parse_glossary_md(fpath: Path, source_label: str) -> None:
            if not fpath.is_file():
                return
            try:
                lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                in_table = False
                orig_col, pt_col, short_col, ctx_col = 0, 1, None, None
                for line in lines:
                    s = line.strip()
                    if s.startswith("|") and ("---" in s or ":---" in s):
                        in_table = True
                        continue
                    if s.startswith("|") and not in_table:
                        headers = [h.lower() for h in split_md_row(s)]
                        orig_col, pt_col, short_col, ctx_col = None, None, None, None
                        for idx, h in enumerate(headers):
                            if orig_col is None and any(k in h for k in ("original", "inglês", "termo", "categoria", "nome oficial")):
                                orig_col = idx
                            elif pt_col is None and any(k in h for k in ("canônic", "1ª apresentação", "tradução", "sugerid", "pt-br", "menus")):
                                pt_col = idx
                            elif short_col is None and any(k in h for k in ("forma curta", "uso comum", "diálogo")):
                                short_col = idx
                            elif ctx_col is None and any(k in h for k in ("definição", "contexto", "observa", "papel", "tipo", "efeito")):
                                ctx_col = idx
                        continue
                    if in_table:
                        if not s.startswith("|"):
                            in_table = False
                            continue
                        cells = split_md_row(s)
                        if orig_col is not None and pt_col is not None and len(cells) > max(orig_col, pt_col):
                            orig_raw = _strip_md_formatting(cells[orig_col])
                            # Limpa anotações entre parênteses do termo original como 'Stray Summon ("Stray")'
                            orig_clean = re.sub(r"\(\*.*?\*\)", "", orig_raw).strip()
                            pt_clean = _strip_md_formatting(cells[pt_col])
                            short_clean = _strip_md_formatting(cells[short_col]) if short_col is not None and len(cells) > short_col else ""
                            ctx_clean = _strip_md_formatting(cells[ctx_col]) if ctx_col is not None and len(cells) > ctx_col else ""

                            if not orig_clean or len(orig_clean) < 2 or orig_clean.startswith("0x"):
                                continue
                            low_key = orig_clean.lower()
                            if low_key not in seen_orig:
                                seen_orig.add(low_key)
                                self.glossary_terms.append({
                                    "original": orig_clean,
                                    "pt_br": pt_clean,
                                    "short_form": short_clean,
                                    "context": ctx_clean,
                                    "source": source_label,
                                })
            except Exception:
                pass

        # 1. Glossário Local do Jogo
        if self.md_dir.is_dir():
            for gf in sorted(self.md_dir.glob("02-*")):
                parse_glossary_md(gf, "Glossário Local")

        # 2. Glossário Global Summon Night
        if GLOBAL_GLOSSARY_PATH.is_file():
            parse_glossary_md(GLOBAL_GLOSSARY_PATH, "Glossário Global")

    def _build_global_speaker_map(self) -> None:
        self.global_script_speakers.clear()
        if not self.md_dir.is_dir():
            return
        for f in self.md_dir.rglob("*.md"):
            fname = f.name
            if fname.startswith(("00-", "01-", "02-", "03-", "04-", "05-", "06-", "07-")):
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                    for line in fp:
                        if not line.startswith("|") or "---" in line or "Original" in line:
                            continue
                        cols = [c.strip() for c in line.split("|")[1:-1]]
                        if len(cols) >= 3:
                            m = re.search(r"#?(\d+)\s*\[?(\d+)\]?", cols[0])
                            if m:
                                s_id = int(m.group(1))
                                str_id = int(m.group(2))
                                clean_sp = cols[1].replace("**", "").replace("`", "").strip()
                                if clean_sp and not clean_sp.lower().startswith("0x") and not clean_sp.lower().startswith("opcode"):
                                    self.global_script_speakers[(s_id, str_id)] = clean_sp
            except Exception:
                pass


# Gerenciador global de projetos carregados
PROJECTS_REGISTRY: Dict[str, StudioProjectContext] = {}
ACTIVE_PROJECT: Optional[StudioProjectContext] = None


def get_or_load_project(game_id: Optional[str] = None) -> StudioProjectContext:
    global ACTIVE_PROJECT
    if not game_id and ACTIVE_PROJECT is not None:
        ACTIVE_PROJECT.ensure_initialized()
        return ACTIVE_PROJECT

    target_dir = DEFAULT_GAME_DIR
    if game_id and JOGOS_ROOT_DIR.is_dir():
        cand = JOGOS_ROOT_DIR / game_id
        if cand.is_dir() and (cand / "ARQUIVOS md").is_dir():
            target_dir = cand

    gid = target_dir.name
    if gid not in PROJECTS_REGISTRY:
        PROJECTS_REGISTRY[gid] = StudioProjectContext(target_dir)

    proj = PROJECTS_REGISTRY[gid]
    proj.ensure_initialized()
    ACTIVE_PROJECT = proj
    return proj


def list_available_projects() -> List[Dict[str, Any]]:
    """Lista todos os jogos disponíveis na pasta `02_TRADUCAO_ROMS_GBA/jogos/`."""
    projects = []
    if not JOGOS_ROOT_DIR.is_dir():
        proj = get_or_load_project()
        return [{
            "id": proj.game_id,
            "short_code": proj.profile["short_code"],
            "title": proj.profile["title"],
            "active": True,
        }]

    active_id = ACTIVE_PROJECT.game_id if ACTIVE_PROJECT else DEFAULT_GAME_DIR.name
    for d in sorted(JOGOS_ROOT_DIR.iterdir(), key=lambda p: (p.name.startswith("_"), p.name)):
        if d.is_dir() and (d / "ARQUIVOS md").is_dir():
            prof = GAME_PROFILES.get(d.name, {
                "id": d.name,
                "short_code": "".join(w[0] for w in d.name.split("_") if w)[:3].upper() or "GBA",
                "title": d.name.replace("_", " "),
            })
            projects.append({
                "id": d.name,
                "short_code": prof["short_code"],
                "title": prof["title"],
                "active": d.name == active_id,
            })
    return projects


# ============================================================================
# FUNÇÕES UTILITÁRIAS DE MARKDOWN E TABELAS
# ============================================================================
def split_md_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def join_md_row(cells: List[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _strip_md_formatting(s: str) -> str:
    parts = re.split(r"<br\s*/?>", s, flags=re.IGNORECASE)
    cleaned_lines = []
    for p in parts:
        p = p.strip()
        p = p.replace("**", "").replace("`", "").strip()
        cleaned_lines.append(p)
    return "\n".join(cleaned_lines)


def clean_cell_to_text(raw: str) -> Tuple[str, str, str]:
    s = raw.strip()
    opt_text = ""
    m = INLINE_OPT_RE.match(s)
    if m:
        s = m.group(1).strip()
        opt_raw = m.group(2).strip()
        opt_text = _strip_md_formatting(opt_raw)
    main_text = _strip_md_formatting(s)
    return main_text, opt_text, ""


def text_to_md_cell(text: str, use_backticks: bool = True) -> str:
    lines = [ln.replace("|", "/").rstrip("\r") for ln in text.split("\n")]
    if not lines:
        return ""
    if use_backticks:
        return "<br>".join(f"`{ln}`" if ln else "" for ln in lines)
    else:
        return "<br>".join(f"**{ln}**" if ln else "" for ln in lines)


def classify_table_columns(headers: List[str]) -> Optional[Dict[str, Any]]:
    h_lower = [h.lower() for h in headers]

    has_en = any("original" in h or "en-us" in h or "padrão" in h or "inglês" in h for h in h_lower)
    has_pt = any("sugerid" in h or "pt-br" in h or "tradução" in h or "português" in h for h in h_lower)
    if not (has_en and has_pt):
        return None

    mapping: Dict[str, Any] = {
        "id_col": None,
        "speaker_col": None,
        "en_col": None,
        "en_desc_col": None,
        "pt_col": None,
        "pt_desc_col": None,
        "opt_col": None,
        "context_cols": [],
        "status_col": None,
    }

    for idx, h in enumerate(h_lower):
        if "status" in h or "validado" in h:
            mapping["status_col"] = idx
        elif ("descrição original" in h) or ("desc" in h and "original" in h):
            mapping["en_desc_col"] = idx
        elif ("descrição sugerida" in h) or ("desc" in h and "sugerid" in h):
            mapping["pt_desc_col"] = idx
        elif "original" in h or "en-us" in h or "padrão (en" in h or "texto original" in h:
            if mapping["en_col"] is None:
                mapping["en_col"] = idx
        elif "alternativa" in h or "opção b" in h:
            mapping["opt_col"] = idx
        elif "sugerid" in h or "pt-br" in h or "tradução" in h:
            if mapping["pt_col"] is None:
                mapping["pt_col"] = idx
        elif any(k in h for k in ("personagem", "falante", "interlocutor", "ator")):
            mapping["speaker_col"] = idx
        elif any(k in h for k in ("endereço", "offset", "tag no script", "script / offset", "id", "tag", "código", "ponteiro")):
            if mapping["id_col"] is None:
                mapping["id_col"] = idx
            else:
                mapping["context_cols"].append(idx)
        elif "contexto" in h and any(k in " ".join(h_lower) for k in ("id", "offset", "script", "endereço")):
            if mapping["speaker_col"] is None:
                mapping["speaker_col"] = idx
            else:
                mapping["context_cols"].append(idx)
        else:
            mapping["context_cols"].append(idx)

    if mapping["pt_col"] is None and mapping["pt_desc_col"] is not None:
        mapping["pt_col"] = mapping["pt_desc_col"]

    if mapping["en_col"] is None or mapping["pt_col"] is None:
        return None

    return mapping


# ============================================================================
# QUALITY GATE POR ENTRADA E POR ARQUIVO (5 BARREIRAS)
# ============================================================================
def extract_dynamic_tags(text: str) -> List[str]:
    curly = re.findall(r"\{[A-Za-z0-9_]+\}", text)
    square = re.findall(r"\[0x[0-9A-Fa-f]+\]", text)
    return sorted(curly + square)


def is_system_or_item_filename(filename: str) -> bool:
    name_low = Path(filename).name.lower()
    return any(k in name_low for k in ("00_", "02-", "03-", "04-", "05-", "06-", "07-", "sistema", "interface", "itens", "armas", "bestiario", "equipamento"))


def evaluate_entry_qa(
    en_text: str,
    pt_text: str,
    pt_desc: str = "",
    is_story_dialogue: bool = True,
    hard_limit: int = 35,
    soft_limit: int = 33,
    neighbor_tags_ok: bool = False,
) -> List[Dict[str, str]]:
    """
    Avalia as 5 barreiras do Quality Gate em uma entrada individual.
    Retorna lista de issues: [{"gate": "GATE 2", "severity": "error"|"warn", "msg": "..."}]
    """
    issues: List[Dict[str, str]] = []
    if not pt_text.strip():
        issues.append({
            "gate": "GATE 0: VAZIO",
            "severity": "error",
            "msg": "Tradução em branco.",
        })
        return issues

    # Gate 1: Tags Dinâmicas
    if not neighbor_tags_ok:
        en_tags = extract_dynamic_tags(en_text)
        pt_tags = extract_dynamic_tags(pt_text)
        if en_tags != pt_tags:
            # Ignora se a linha for definição de variável em tabela de glossário
            if not (en_text.startswith("{") and en_text.endswith("}")):
                issues.append({
                    "gate": "GATE 1: TAGS",
                    "severity": "error",
                    "msg": f"Divergência de tags! Original: {en_tags or 'nenhuma'} vs PT-BR: {pt_tags or 'nenhuma'}",
                })

    # Gate 2 & Gate 3: Limite de Caracteres e Orfandade Textual
    pt_lines = [ln for ln in pt_text.split("\n") if ln.strip()]
    for idx, ln in enumerate(pt_lines):
        c_len = len(ln)
        if c_len > hard_limit:
            issues.append({
                "gate": "GATE 2: OVERFLOW",
                "severity": "error",
                "msg": f"Linha {idx+1} tem {c_len} chars (Máx={hard_limit}, Excesso=+{c_len - hard_limit})",
            })
        elif c_len >= soft_limit:
            issues.append({
                "gate": "GATE 2: SOFT LIMIT",
                "severity": "warn",
                "msg": f"Linha {idx+1} na zona de atenção ({c_len}/{hard_limit} chars)",
            })

        # Gate 3: Orfandade no fim da linha antes de <br>
        if idx < len(pt_lines) - 1:
            words = ln.split()
            if words:
                last_word = re.sub(r"[^\wÀ-ÿ]", "", words[-1]).lower()
                if last_word in ORPHAN_WORDS:
                    issues.append({
                        "gate": "GATE 3: ORFANDADE",
                        "severity": "warn",
                        "msg": f"Palavra curta '{words[-1]}' isolada no fim da Linha {idx+1} antes da quebra",
                    })

    # Verifica descrição se houver (limite de 36 chars por linha de descrição)
    if pt_desc:
        desc_lines = [ln for ln in pt_desc.split("\n") if ln.strip()]
        for idx, dln in enumerate(desc_lines):
            if len(dln) > 36:
                issues.append({
                    "gate": "GATE 2: DESC OVERFLOW",
                    "severity": "error",
                    "msg": f"Descrição Linha {idx+1} tem {len(dln)} chars (Máx=36)",
                })

    # Gate 4: Política Rígida de Abreviações em Diálogos
    if is_story_dialogue:
        for pat, abbr_label in FORBIDDEN_DIALOGUE_ABBREVS:
            if pat.search(pt_text):
                issues.append({
                    "gate": "GATE 4: ABREVIAÇÃO",
                    "severity": "error",
                    "msg": f"Abreviação '{abbr_label}' proibida em diálogos narrativos!",
                })

    # Gate 5: Neutralidade de Gênero Sistêmica & Inglês Residual
    for pat, tip in GENDER_SUSPECT_PATTERNS:
        if pat.search(pt_text):
            issues.append({
                "gate": "GATE 5: NEUTRALIDADE",
                "severity": "warn",
                "msg": tip,
            })

    for eng_pat in RESIDUAL_ENGLISH_PATTERNS:
        m_eng = eng_pat.search(pt_text)
        if m_eng:
            issues.append({
                "gate": "GATE 5: INGLÊS RESIDUAL",
                "severity": "warn",
                "msg": f"Termo em inglês residual detectado: '{m_eng.group(0)}'",
            })

    return issues


# ============================================================================
# IDENTIFICAÇÃO DE PERSONAGENS MULTI-JOGO (SN1, SN2, SN3 & GENÉRICO)
# ============================================================================
def canonicalize_character(
    raw_name: str,
    context: str = "",
    text: str = "",
    proj: Optional[StudioProjectContext] = None,
) -> Tuple[str, str, str, str, str, str]:
    """
    Normaliza um nome de personagem bruto e extrai seus atributos:
      (char_id, display_name, gender, role, icon, category)
    Suporta todos os personagens de Summon Night 1, 2, 3 e Catálogo Dinâmico.
    """
    if proj is None:
        proj = get_or_load_project()

    male_id, male_disp, male_role = proj.profile["male_hero"]
    fem_id, fem_disp, fem_role = proj.profile["female_hero"]

    if not raw_name:
        return "geral", "Cena / Geral", "neutral", "Cena", "🎬", "Cena"

    clean = raw_name.strip()
    c_lower = clean.lower()

    # 1. Escolhas de Diálogo
    if "escolha" in c_lower or "choice" in c_lower:
        if any(k in c_lower for k in ("bost", "cleru", "edgar", "ritchie", "ritchburn", "masc")):
            return f"choice_{male_id}", f"Escolha ({male_disp})", "male", "Opção de Diálogo (♂)", "🗳️", "Protagonistas & Escolhas"
        if any(k in c_lower for k in ("prat", "pratty", "aera", "rif", "rifmonica", "fem")):
            return f"choice_{fem_id}", f"Escolha ({fem_disp})", "female", "Opção de Diálogo (♀)", "🗳️", "Protagonistas & Escolhas"
        return "choice", "Escolha do Jogador", "both", "Opção de Diálogo", "🗳️", "Protagonistas & Escolhas"

    # 2. Protagonista Masculino
    if any(k in c_lower for k in ("cleru", "bost", "edgar", "ritchie", "ritchburn", "{player} (masc)")):
        return male_id, male_disp, "male", male_role, "♂", "Protagonistas & Escolhas"

    # 3. Protagonista Feminina
    if any(k in c_lower for k in ("pratty", "prat", "aera", "rif", "rifmonica", "{player} (fem)")):
        return fem_id, fem_disp, "female", fem_role, "♀", "Protagonistas & Escolhas"

    # 4. Protagonista Compartilhado / Neutro
    if any(k in c_lower for k in ("protagonista", "{player}", "protagonist", "player")):
        ctx_l = (context + " " + text).lower()
        if any(k in ctx_l for k in ("(bost)", "(cleru)", "(edgar)", "(ritchie)", "ramo cleru", "ramo edgar", "ramo ritchie", "hardest steel")):
            return male_id, male_disp, "male", male_role, "♂", "Protagonistas & Escolhas"
        if any(k in ctx_l for k in ("(prat)", "(pratty)", "(aera)", "(rif)", "ramo pratty", "ramo aera", "ramo rif", "toughest chain")):
            return fem_id, fem_disp, "female", fem_role, "♀", "Protagonistas & Escolhas"
        return "protagonist", "👥 Protagonista (Ambos)", "both", "Protagonista (Compartilhado)", "👥", "Protagonistas & Escolhas"

    # 5. Feras Guardiãs (SN1, SN2, SN3)
    if "rasho" in c_lower:
        return "rasho", "Rasho", "male", "Fera Guardiã (Oni / Fogo)", "👹", "Feras Guardiãs"
    if "sugar" in c_lower:
        return "sugar", "Sugar", "female", "Fera Guardiã (Fada / Água)", "🧚", "Feras Guardiãs"
    if "kutty" in c_lower:
        return "kutty", "Kutty", "neutral", "Fera Guardiã (Besta / Vento)", "🐾", "Feras Guardiãs"
    if any(k in c_lower for k in ("zantek", "run-da")):
        return "zantek", "Zantek", "neutral", "Fera Guardiã (Mecânico / Raio)", "🤖", "Feras Guardiãs"
    if "exeld" in c_lower:
        return "exeld", "EXeLD", "neutral", "Fera Guardiã (Mecânico / Loreilal)", "🤖", "Feras Guardiãs"
    if "dinah" in c_lower:
        return "dinah", "Dinah", "female", "Fera Guardiã (Fada Demônio / Sapureth)", "🧚", "Feras Guardiãs"
    if "arno" in c_lower:
        return "arno", "Arno", "male", "Fera Guardiã (Besta Sagrada / Silturn)", "🐾", "Feras Guardiãs"
    if "loki" in c_lower:
        return "loki", "Loki", "male", "Fera Guardiã (Demônio Trapaceiro / Maetropa)", "😈", "Feras Guardiãs"
    if any(k in c_lower for k in ("run-dor", "randor", "rundor")):
        return "rundor", "RUN-DOR", "neutral", "Fera Guardiã (Máquinas / Loreilal)", "🤖", "Feras Guardiãs"
    if "enzi" in c_lower:
        return "enzi", "Enzi", "male", "Fera Guardiã (Espírito de Fogo / Silturn)", "🔥", "Feras Guardiãs"
    if any(k in c_lower for k in ("killfith", "killf")):
        return "killfith", "Killfith", "male", "Fera Guardiã (Besta / Maetropa)", "🐾", "Feras Guardiãs"
    if any(k in c_lower for k in ("rufeel", "ruchell")):
        return "rufeel", "Rufeel", "male", "Fera Guardiã (Demônio / Yueterno)", "😈", "Feras Guardiãs"
    if "{partner}" in c_lower or "partner" in c_lower or "fera guardiã" in c_lower:
        return "partner", "🐾 Fera Guardiã ({PARTNER})", "both", "Parceiro de Pacto", "🐾", "Feras Guardiãs"

    # 6. Mentores, Família e Personagens Principais (SN1, SN2, SN3)
    if any(k in c_lower for k in ("amariss", "mãe", "mother")):
        return "amariss", "Amariss (Mãe)", "female", "Mãe do Protagonista", "👩", "Personagens Principais"
    if any(k in c_lower for k in ("mestre bron", "bron", "master bron")):
        return "bron", "Mestre Bron", "male", "Mestre Forjador", "🔨", "Personagens Principais"
    if any(k in c_lower for k in ("mestre blaire", "blaire", "master blaire")):
        return "blaire", "Mestre Blaire", "male", "Mestre Forjador / Pai Adotivo", "🔨", "Personagens Principais"
    if any(k in c_lower for k in ("mestre rob", "rob", "master rob", "oyakata")):
        return "rob", "Mestre Rob", "male", "Mestre Forjador / Mentor", "🔨", "Personagens Principais"
    if "murno" in c_lower or "myūno" in c_lower:
        return "murno", "Murno", "female", "Heroína Central / Guardiã da Pedra", "💎", "Personagens Principais"
    if "orin" in c_lower or "{sibling}" in c_lower:
        return "orin", "Orin", "both", "Irmão(ã) Adotivo(a)", "🧑", "Personagens Principais"
    if "ryouga" in c_lower:
        return "ryouga", "Ryouga", "male", "Rival / Amigo de Infância", "⚔️", "Personagens Principais"
    if "sanary" in c_lower:
        return "sanary", "Sanary", "female", "Rival / Cavaleira", "⚔️", "Personagens Principais"
    if "varil" in c_lower:
        return "varil", "Varil", "male", "Rival / Cavaleiro", "🛡️", "Personagens Principais"
    if "tatiana" in c_lower:
        return "tatiana", "Tatiana", "female", "Rival Forjadora / Pesquisadora", "🎀", "Personagens Principais"
    if "v.e" in c_lower or "vee" in c_lower:
        return "ve", "V.E", "female", "Rival Ferreira / Companheira", "⚔️", "Personagens Principais"
    if "lemmy" in c_lower or "remi" in c_lower:
        return "lemmy", "Lemmy", "female", "Aliada Intelectual / Artesã", "💡", "Personagens Principais"
    if "jade" in c_lower:
        return "jade", "Jade", "male", "Espadachim Nobre", "🗡️", "Personagens Principais"
    if "tier" in c_lower:
        return "tier", "Tier", "male", "Jovem Artesão Ligeiro", "⚡", "Personagens Principais"
    if "zakk" in c_lower or "zack" in c_lower:
        return "zakk", "Zakk", "male", "Artesão Parceiro", "🔧", "Personagens Principais"
    if "govan" in c_lower or "gouvan" in c_lower:
        return "govan", "Govan", "male", "Guerreiro da Pedra Demoníaca", "🛡️", "Personagens Principais"
    if "anise" in c_lower:
        return "anise", "Anise", "female", "Antagonista / Manipuladora", "🦹", "Personagens Principais"
    if "chaves" in c_lower:
        return "chaves", "Chaves", "male", "Oponente do Torneio", "🗡️", "Personagens Principais"
    if "kenon" in c_lower:
        return "kenon", "Kenon", "male", "Arqueiro / Invocador", "🏹", "Personagens Principais"
    if "razzy" in c_lower:
        return "razzy", "Razzy", "female", "Amiga / Invocadora", "✨", "Personagens Principais"
    if "ariel" in c_lower:
        return "ariel", "Ariel", "female", "Invocadora", "🔮", "Personagens Principais"
    if "lynn" in c_lower:
        return "lynn", "Lynn", "female", "Aliada / Curandeira", "👧", "Personagens Principais"
    if "gabriel" in c_lower:
        return "gabriel", "Gabriel", "male", "Espadachim Guardião", "🗡️", "Personagens Principais"
    if "nina" in c_lower:
        return "nina", "Nina", "female", "Invocadora Mirim", "🔮", "Personagens Principais"
    if "goura" in c_lower:
        return "goura", "Goura", "neutral", "Demônio Ancestral Selado", "👹", "Personagens Principais"
    if "gedo" in c_lower:
        return "gedo", "Gedo", "male", "Líder da Ordem / Vilão", "🦹", "Personagens Principais"
    if "zeed" in c_lower:
        return "zeed", "Zeed", "male", "Conspirador Mascarado", "🦹", "Personagens Principais"
    if "parista" in c_lower:
        return "parista", "Parista", "female", "Entidade Primordial", "🐉", "Personagens Principais"

    # 7. Lordes do Ofício & Mestres de Oficina
    if "sakuro" in c_lower:
        return "sakuro", "Sakuro (Lorde Safira)", "male", "Lorde da Safira", "💎", "Lordes & Mestres"
    if "lubert" in c_lower:
        return "lubert", "Lubert (Lorde Jade)", "male", "Lorde do Jade", "🌿", "Lordes & Mestres"
    if "ureksa" in c_lower:
        return "ureksa", "Ureksa (Lorde Âmbar)", "female", "Lorde do Âmbar", "🟡", "Lordes & Mestres"
    if "kouren" in c_lower:
        return "kouren", "Kouren (Lorde Rubi)", "female", "Lorde do Rubi", "🔴", "Lordes & Mestres"
    if any(k in c_lower for k in ("shintetsu", "pai", "father")):
        return "shintetsu", "Shintetsu (Pai)", "male", "Lorde Lendário / Pai", "⚡", "Lordes & Mestres"
    if "bostaph" in c_lower:
        return "bostaph", "Don Bostaph", "male", "Líder da Oficina Bostaph", "🎩", "Lordes & Mestres"
    if "gallahan" in c_lower:
        return "gallahan", "Gallahan", "male", "Mestre da Oficina Gallahan", "🛠️", "Lordes & Mestres"
    if "benson" in c_lower:
        return "benson", "Benson", "male", "Mestre da Oficina Benson", "🏭", "Lordes & Mestres"

    # 8. NPCs e Sistema
    if "lojista" in c_lower or "shopkeeper" in c_lower or "comerciante" in c_lower:
        return "lojista", "Lojista", "neutral", "Comerciante Local", "🏪", "NPCs & Habitantes"
    if "invocador" in c_lower or "summoner" in c_lower:
        return "invocador", "Invocador", "neutral", "Invocador", "🧙", "NPCs & Habitantes"
    if "guarda" in c_lower or "guard" in c_lower or "soldado" in c_lower:
        return "guarda", "Guarda", "male", "Guarda / Vigia", "💂", "NPCs & Habitantes"
    if any(k in c_lower for k in ("sistema", "aviso", "tela", "menu", "status", "system")):
        return "system", "Sistema / Interface", "neutral", "Interface / HUD", "⚙️", "Sistema & Interface"

    clean_name = re.sub(r"\(.*?\)", "", clean).strip()
    c_name = clean_name.title() if clean_name.islower() else clean_name
    c_id = clean_name.lower().replace(" ", "_")

    if c_id in proj.character_bible:
        b_entry = proj.character_bible[c_id]
        return c_id, b_entry["name"], "neutral", b_entry["role"], "👤", "Personagens Principais"

    return c_id, c_name, "neutral", "Personagem", "👤", "NPCs & Habitantes"


def infer_gender_branch(
    speaker_id: str,
    target_id: str,
    sec: str,
    ctx: str,
    en: str,
    pt: str,
    proj: StudioProjectContext,
) -> Tuple[str, str]:
    male_id, male_disp, _ = proj.profile["male_hero"]
    fem_id, fem_disp, _ = proj.profile["female_hero"]
    male_label = f"♂ Ramo Masculino ({male_disp.replace('♂ ', '')})"
    fem_label = f"♀ Ramo Feminino ({fem_disp.replace('♀ ', '')})"

    if speaker_id in (male_id, f"choice_{male_id}", "cleru", "edgar", "ritchie", "hero_male"):
        return "male", male_label
    if speaker_id in (fem_id, f"choice_{fem_id}", "pratty", "aera", "rif", "hero_female"):
        return "female", fem_label

    all_ctx = f"{sec} {ctx}".lower()
    if any(k in all_ctx for k in ("(bost)", "(cleru)", "(edgar)", "(ritchie)", "(masc)", "ramo cleru", "ramo edgar", "ramo ritchie")):
        return "male", male_label
    if any(k in all_ctx for k in ("(prat)", "(pratty)", "(aera)", "(rif)", "(fem)", "ramo pratty", "ramo aera", "ramo rif")):
        return "female", fem_label

    text_check = f"{en} {pt}".lower()
    if "hardest steel" in text_check or "aço mais duro" in text_check:
        return "male", male_label
    if "toughest chain" in text_check or "corrente mais resistente" in text_check:
        return "female", fem_label

    if target_id in (male_id, "cleru", "edgar", "ritchie", "hero_male"):
        return "male", male_label
    if target_id in (fem_id, "pratty", "aera", "rif", "hero_female"):
        return "female", fem_label

    has_male = bool(MALE_CUES.search(text_check))
    has_fem = bool(FEMALE_CUES.search(text_check))
    if has_male and not has_fem and ("{player}" in text_check or target_id in ("protagonist", "player")):
        return "male", male_label
    if has_fem and not has_male and ("{player}" in text_check or target_id in ("protagonist", "player")):
        return "female", fem_label

    if speaker_id in ("protagonist", "choice") or target_id in ("protagonist", "player"):
        return "both", "👥 Ramo Compartilhado (Ambos)"

    if speaker_id == "system":
        return "system", "⚙️ Sistema & UI"

    return "npc", "🗣️ Diálogo Geral"


def enrich_entries(
    entries: List[Dict[str, Any]],
    doc_title: str,
    rel_filename: str,
    proj: StudioProjectContext,
) -> List[Dict[str, Any]]:
    if not entries:
        return []

    male_id, _, _ = proj.profile["male_hero"]
    fem_id, _, _ = proj.profile["female_hero"]
    hard_limit = proj.profile.get("hard_limit", 35)
    soft_limit = proj.profile.get("soft_limit", 33)
    is_story = not is_system_or_item_filename(rel_filename)

    # Pré-calcula resolução de tags entre linhas consecutivas do mesmo script
    n_entries = len(entries)
    neighbor_tags_ok = [False] * n_entries
    for idx in range(n_entries - 1):
        r1, r2 = entries[idx], entries[idx + 1]
        m1 = re.search(r"(#?\d+)\s*\[?(\d+)\]?", r1.get("ref_id", ""))
        m2 = re.search(r"(#?\d+)\s*\[?(\d+)\]?", r2.get("ref_id", ""))
        if m1 and m2 and m1.group(1) == m2.group(1) and abs(int(m2.group(2)) - int(m1.group(2))) <= 2:
            c_en = sorted(extract_dynamic_tags(r1["en_text"]) + extract_dynamic_tags(r2["en_text"]))
            c_pt = sorted(extract_dynamic_tags(r1["pt_text"]) + extract_dynamic_tags(r2["pt_text"]))
            if c_en == c_pt:
                neighbor_tags_ok[idx] = True
                neighbor_tags_ok[idx + 1] = True

    # 1ª Passada: Script Group, Falante e QA
    for idx, e in enumerate(entries):
        ref_id = e.get("ref_id", "")
        sec = e.get("section", "")
        ctx = e.get("context", "")
        en = e.get("en_text", "")
        pt = e.get("pt_text", "")
        pt_desc = e.get("pt_desc", "")

        m_scr = re.search(r"#?(\d+)", ref_id) or re.search(r"#?(\d+)", sec)
        if m_scr and is_story:
            s_group = f"Script #{int(m_scr.group(1)):04d}"
        elif sec:
            s_group = sec.split("›")[0].strip()
        else:
            s_group = doc_title or "Geral"
        e["script_group"] = s_group

        raw_speaker = e.get("raw_speaker_extracted", "")
        if not raw_speaker:
            m_ctx = re.search(r"(?:Personagem|Contexto|Falante)(?:\s*/\s*Contexto)?:\s*([^|]+)", ctx, re.I)
            if m_ctx:
                cand = m_ctx.group(1).strip()
                if not cand.lower().startswith("0x") and not cand.lower().startswith("opcode"):
                    raw_speaker = cand

        if not raw_speaker:
            m_id = re.search(r"#?(\d+)\s*\[?(\d+)\]?", ref_id)
            if m_id:
                s_num = int(m_id.group(1))
                str_num = int(m_id.group(2))
                raw_speaker = proj.global_script_speakers.get((s_num, str_num), "")

        if not raw_speaker:
            m_text = re.search(r"\*\(([^:)]+):?\)\*", en) or re.search(r"\*\(([^:)]+):?\)\*", pt)
            if m_text:
                raw_speaker = m_text.group(1).strip()
            elif not is_story or any(k in doc_title.lower() for k in ("interface", "menu", "armas", "itens", "bestiário")):
                raw_speaker = "Sistema"
            elif proj.game_id == "Summon_Night_Swordcraft_Story_1" and (BRON_HEURISTIC_RE.search(en) or BRON_HEURISTIC_RE.search(pt)):
                raw_speaker = "Mestre Bron"
            elif proj.game_id == "Summon_Night_Swordcraft_Story_2" and (BLAIRE_HEURISTIC_RE.search(en) or BLAIRE_HEURISTIC_RE.search(pt)):
                raw_speaker = "Mestre Blaire"
            else:
                raw_speaker = "Geral"

        s_id, s_name, s_gender, s_role, s_icon, s_cat = canonicalize_character(
            raw_speaker, context=f"{sec} {ctx}", text=f"{en} {pt}", proj=proj
        )
        e["speaker_raw"] = raw_speaker
        e["speaker"] = s_name
        e["speaker_id"] = s_id
        e["speaker_gender"] = s_gender
        e["actor_role"] = s_role
        e["actor_icon"] = s_icon
        e["actor_category"] = s_cat

        # Vincula diretriz de Tom de Voz (Character Voice) da Bíblia de Personagens
        bible_info = proj.character_bible.get(s_id)
        if not bible_info:
            for b_key, b_val in proj.character_bible.items():
                if b_key in s_id or s_id in b_key:
                    bible_info = b_val
                    break
        e["voice_guide"] = bible_info["voice_guidelines"] if bible_info else ""
        e["voice_example"] = bible_info["example"] if bible_info else ""

        clean_en = en.strip()
        e["is_thought"] = (clean_en.startswith("(") and clean_en.endswith(")")) or "(Pensamento)" in ctx or "(Monólogo)" in ctx

        # Avalia Quality Gate para a linha
        e["is_story_dialogue"] = is_story
        e["qa_issues"] = evaluate_entry_qa(
            en_text=en,
            pt_text=pt,
            pt_desc=pt_desc,
            is_story_dialogue=is_story,
            hard_limit=hard_limit,
            soft_limit=soft_limit,
            neighbor_tags_ok=neighbor_tags_ok[idx],
        )
        e["has_qa_error"] = any(iss["severity"] == "error" for iss in e["qa_issues"])
        e["has_qa_warn"] = any(iss["severity"] == "warn" for iss in e["qa_issues"])

    # 2ª Passada: Agrupa por cena/script e infere Destinatário e Ramo de Gênero
    groups: Dict[str, List[int]] = {}
    for idx, e in enumerate(entries):
        groups.setdefault(e["script_group"], []).append(idx)

    for s_group, indices in groups.items():
        group_has_male = any(
            entries[i]["speaker_id"] in (male_id, f"choice_{male_id}")
            or "hardest steel" in entries[i]["en_text"].lower()
            or f"({male_id})" in entries[i]["context"].lower()
            or "(bost)" in entries[i]["context"].lower()
            for i in indices
        )
        group_has_female = any(
            entries[i]["speaker_id"] in (fem_id, f"choice_{fem_id}")
            or "toughest chain" in entries[i]["en_text"].lower()
            or f"({fem_id})" in entries[i]["context"].lower()
            or "(prat)" in entries[i]["context"].lower()
            for i in indices
        )

        participants: List[str] = []
        for i in indices:
            sp_id = entries[i]["speaker_id"]
            if sp_id not in ("system", "choice", f"choice_{male_id}", f"choice_{fem_id}", "geral") and sp_id not in participants:
                participants.append(sp_id)

        last_speaker_id: Optional[str] = None
        last_non_self_speaker_id: Optional[str] = None

        for i in indices:
            e = entries[i]
            sp_id = e["speaker_id"]
            ctx = e.get("context", "")
            text_combo = f"{e.get('pt_text', '')} {e.get('en_text', '')}"

            target_id = ""
            target_name = ""

            if e["is_thought"]:
                target_name = "💭 Pensamento (Monólogo)"
                target_id = "thought"
            elif sp_id == "system":
                target_name = "Jogador"
                target_id = "player"
            elif sp_id.startswith("choice"):
                target_name = "Interlocutor da Cena"
                target_id = "interlocutor"
            else:
                candidate_id: Optional[str] = None
                if last_speaker_id and last_speaker_id != sp_id and not last_speaker_id.startswith("choice") and last_speaker_id != "system":
                    candidate_id = last_speaker_id
                elif last_non_self_speaker_id and last_non_self_speaker_id != sp_id:
                    candidate_id = last_non_self_speaker_id
                elif len(participants) == 2:
                    candidate_id = participants[1] if participants[0] == sp_id else participants[0]
                elif len(participants) > 1 and sp_id not in (male_id, fem_id, "protagonist"):
                    if group_has_male and not group_has_female:
                        candidate_id = male_id
                    elif group_has_female and not group_has_male:
                        candidate_id = fem_id
                    else:
                        candidate_id = "protagonist"

                if candidate_id == sp_id:
                    if last_non_self_speaker_id:
                        candidate_id = last_non_self_speaker_id
                    else:
                        others = [p for p in participants if p != sp_id]
                        candidate_id = others[0] if others else None

                if candidate_id:
                    if candidate_id in ("protagonist", male_id, fem_id):
                        if MALE_CUES.search(text_combo) and not FEMALE_CUES.search(text_combo):
                            candidate_id = male_id
                        elif FEMALE_CUES.search(text_combo) and not MALE_CUES.search(text_combo):
                            candidate_id = fem_id
                        elif group_has_male and not group_has_female:
                            candidate_id = male_id
                        elif group_has_female and not group_has_male:
                            candidate_id = fem_id
                    target_id, target_name, _, _, _, _ = canonicalize_character(candidate_id, proj=proj)
                else:
                    target_name = "Cena / Todos"
                    target_id = "geral"

            branch, branch_label = infer_gender_branch(
                sp_id, target_id, e.get("section", ""), ctx, e.get("en_text", ""), e.get("pt_text", ""), proj
            )

            if branch == "male" and target_id == "protagonist":
                target_id, target_name, _, _, _, _ = canonicalize_character(male_id, proj=proj)
            elif branch == "female" and target_id == "protagonist":
                target_id, target_name, _, _, _, _ = canonicalize_character(fem_id, proj=proj)

            e["addressee"] = target_name
            e["addressee_id"] = target_id
            e["gender_branch"] = branch
            e["gender_label"] = branch_label

            _, _, _, t_role, t_icon, _ = canonicalize_character(target_id, proj=proj)
            e["target_role"] = t_role
            e["target_icon"] = t_icon

            if not sp_id.startswith("choice") and sp_id != "system":
                if last_speaker_id and last_speaker_id != sp_id:
                    last_non_self_speaker_id = last_speaker_id
                last_speaker_id = sp_id

    # 3ª Passada: Estatísticas de personagens da cena
    char_map: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        s_id = e["speaker_id"]
        if s_id not in char_map:
            char_map[s_id] = {
                "id": s_id,
                "name": e["speaker"],
                "gender": e["speaker_gender"],
                "role": e["actor_role"],
                "icon": e["actor_icon"],
                "category": e["actor_category"],
                "voice_guide": e.get("voice_guide", ""),
                "spoken": 0,
                "addressed": 0,
                "total": 0,
            }
        char_map[s_id]["spoken"] += 1
        char_map[s_id]["total"] += 1

        t_id = e["addressee_id"]
        if t_id and t_id not in ("thought", "geral", "player", "interlocutor"):
            if t_id not in char_map:
                t_id_c, t_name_c, t_gen_c, t_role_c, t_icon_c, t_cat_c = canonicalize_character(t_id, proj=proj)
                char_map[t_id] = {
                    "id": t_id,
                    "name": t_name_c,
                    "gender": t_gen_c,
                    "role": t_role_c,
                    "icon": t_icon_c,
                    "category": t_cat_c,
                    "voice_guide": proj.character_bible.get(t_id, {}).get("voice_guidelines", ""),
                    "spoken": 0,
                    "addressed": 0,
                    "total": 0,
                }
            char_map[t_id]["addressed"] += 1
            char_map[t_id]["total"] += 1

    return sorted(char_map.values(), key=lambda c: (c["total"], c["spoken"]), reverse=True)


# ============================================================================
# PARSER COM CACHE INTELIGENTE EM MEMÓRIA (O(1) POR MTIME)
# ============================================================================
def parse_md_file(filepath: Path, proj: Optional[StudioProjectContext] = None, force_reload: bool = False) -> Dict[str, Any]:
    if proj is None:
        proj = get_or_load_project()

    filepath = filepath.resolve()
    rel_name = filepath.relative_to(proj.md_dir.resolve()).as_posix() if filepath.is_relative_to(proj.md_dir.resolve()) else filepath.name

    try:
        mtime = filepath.stat().st_mtime_ns
    except OSError:
        mtime = 0

    if not force_reload and rel_name in proj.file_cache:
        cached = proj.file_cache[rel_name]
        if cached["mtime"] == mtime:
            return cached["data"]

    text = filepath.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    doc_title = ""
    current_h2 = ""
    current_h3 = ""
    entries: List[Dict[str, Any]] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()

        if line.startswith("# ") and not doc_title:
            doc_title = line[2:].strip()
            i += 1
            continue
        if line.startswith("## "):
            current_h2 = line[3:].strip()
            current_h3 = ""
            i += 1
            continue
        if line.startswith("### "):
            current_h3 = line[4:].strip()
            i += 1
            continue

        if line.startswith("|") and (i + 1 < n) and re.match(r"^\|\s*:?---", lines[i + 1].strip()):
            header_line_idx = i
            sep_line_idx = i + 1
            headers = split_md_row(lines[header_line_idx])
            col_map = classify_table_columns(headers)

            i += 2
            if col_map is None:
                while i < n and lines[i].strip().startswith("|"):
                    i += 1
                continue

            while i < n and lines[i].strip().startswith("|"):
                # Verifica se encontrou um novo cabeçalho colado
                row_cells = split_md_row(lines[i])
                if (i + 1 < n) and re.match(r"^\|\s*:?---", lines[i + 1].strip()):
                    break

                while len(row_cells) < len(headers):
                    row_cells.append("")

                en_raw = row_cells[col_map["en_col"]]
                pt_raw = row_cells[col_map["pt_col"]]

                en_text, _, _ = clean_cell_to_text(en_raw)
                pt_text, inline_opt, _ = clean_cell_to_text(pt_raw)

                en_desc = ""
                pt_desc = ""
                if col_map["en_desc_col"] is not None and col_map["en_desc_col"] < len(row_cells):
                    en_desc, _, _ = clean_cell_to_text(row_cells[col_map["en_desc_col"]])
                if col_map["pt_desc_col"] is not None and col_map["pt_desc_col"] < len(row_cells) and col_map["pt_desc_col"] != col_map["pt_col"]:
                    pt_desc, _, _ = clean_cell_to_text(row_cells[col_map["pt_desc_col"]])

                opt_text = inline_opt
                if col_map["opt_col"] is not None and col_map["opt_col"] < len(row_cells):
                    col_opt_clean, _, _ = clean_cell_to_text(row_cells[col_map["opt_col"]])
                    if col_opt_clean:
                        opt_text = col_opt_clean

                ref_id = ""
                if col_map["id_col"] is not None and col_map["id_col"] < len(row_cells):
                    ref_id = _strip_md_formatting(row_cells[col_map["id_col"]])

                raw_sp_extracted = ""
                if col_map["speaker_col"] is not None and col_map["speaker_col"] < len(row_cells):
                    raw_sp_extracted = _strip_md_formatting(row_cells[col_map["speaker_col"]])

                ctx_parts = []
                for c_idx in col_map["context_cols"]:
                    if c_idx < len(row_cells) and row_cells[c_idx].strip():
                        col_label = headers[c_idx]
                        val_clean = _strip_md_formatting(row_cells[c_idx])
                        ctx_parts.append(f"{col_label}: {val_clean}")

                section_label = current_h2
                if current_h3:
                    section_label = f"{current_h2} › {current_h3}"

                validated = False
                status_str = "⏳ Pendente"
                if col_map["status_col"] is not None and col_map["status_col"] < len(row_cells):
                    st_cell = row_cells[col_map["status_col"]]
                    if any(w in st_cell.lower() for w in ("✅", "🟢", "validado", "canônico", "[x]")):
                        validated = True
                        status_str = "✅ Validado"
                elif col_map["status_col"] is None and pt_text.strip() and not pt_text.startswith("["):
                    validated = True
                    status_str = "✅ Validado"

                use_bold = pt_raw.strip().startswith("**")

                entries.append({
                    "line_index": i,
                    "header_line_index": header_line_idx,
                    "sep_line_index": sep_line_idx,
                    "section": section_label,
                    "ref_id": ref_id,
                    "raw_speaker_extracted": raw_sp_extracted,
                    "context": " | ".join(ctx_parts) if ctx_parts else section_label,
                    "en_text": en_text,
                    "en_desc": en_desc,
                    "pt_text": pt_text,
                    "pt_desc": pt_desc,
                    "opt_text": opt_text,
                    "has_desc": (col_map["pt_desc_col"] is not None and col_map["pt_desc_col"] != col_map["pt_col"]),
                    "validated": validated,
                    "status_str": status_str,
                    "use_bold": use_bold,
                })
                i += 1
            continue

        i += 1

    characters = enrich_entries(entries, doc_title, rel_name, proj)
    total = len(entries)
    validated_count = sum(1 for e in entries if e["validated"])
    qa_errors_count = sum(1 for e in entries if e.get("has_qa_error"))
    qa_warns_count = sum(1 for e in entries if e.get("has_qa_warn"))

    result = {
        "filename": rel_name,
        "title": doc_title or filepath.stem,
        "total": total,
        "validated": validated_count,
        "qa_errors": qa_errors_count,
        "qa_warnings": qa_warns_count,
        "is_story_dialogue": not is_system_or_item_filename(rel_name),
        "entries": entries,
        "characters": characters,
    }

    proj.file_cache[rel_name] = {"mtime": mtime, "data": result}
    return result


def list_translation_md_files(proj: Optional[StudioProjectContext] = None) -> List[Dict[str, Any]]:
    if proj is None:
        proj = get_or_load_project()

    if not proj.md_dir.is_dir():
        return []

    files = sorted(proj.md_dir.rglob("*.md"), key=lambda p: (p.name, p.as_posix()))
    result = []
    for f in files:
        # Ignora arquivos meramente documentais sem tabelas de tradução
        if any(k in f.name.lower() for k in ("00-indice", "01-status", "catalogo-de-personagens", "estudo-de-metricas", "controle-de-imagens", "relatorio")):
            continue
        parsed = parse_md_file(f, proj=proj)
        if parsed["total"] == 0:
            continue
        result.append({
            "filename": parsed["filename"],
            "title": parsed["title"],
            "total": parsed["total"],
            "validated": parsed["validated"],
            "qa_errors": parsed["qa_errors"],
            "qa_warnings": parsed["qa_warnings"],
            "is_story_dialogue": parsed["is_story_dialogue"],
        })
    return result


def update_md_entries_batch(
    filepath: Path,
    updates: List[Dict[str, Any]],
    proj: Optional[StudioProjectContext] = None,
) -> Dict[str, Any]:
    """
    Atualiza uma ou múltiplas linhas de `filepath` em uma única operação de disco atômica,
    invalidando apenas o cache daquele arquivo específico (performance O(1)).
    Cada item em `updates`: {"line_index": int, "pt_text": Optional[str], "pt_desc": Optional[str], "validated": bool}
    """
    if proj is None:
        proj = get_or_load_project()

    filepath = filepath.resolve()
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    for upd in updates:
        line_index = int(upd["line_index"])
        if not (0 <= line_index < len(lines)):
            continue

        h_idx = line_index - 1
        while h_idx >= 0 and lines[h_idx].strip().startswith("|"):
            h_idx -= 1
        header_line_idx = h_idx + 1
        sep_line_idx = header_line_idx + 1

        headers = split_md_row(lines[header_line_idx])
        col_map = classify_table_columns(headers)
        if col_map is None:
            continue

        if col_map["status_col"] is None:
            headers.append("Status")
            lines[header_line_idx] = join_md_row(headers)

            sep_cells = split_md_row(lines[sep_line_idx])
            sep_cells.append(":---:")
            lines[sep_line_idx] = join_md_row(sep_cells)

            r_idx = sep_line_idx + 1
            while r_idx < len(lines) and lines[r_idx].strip().startswith("|"):
                r_cells = split_md_row(lines[r_idx])
                while len(r_cells) < len(headers) - 1:
                    r_cells.append("")
                r_cells.append("⏳ Pendente")
                lines[r_idx] = join_md_row(r_cells)
                r_idx += 1

            col_map["status_col"] = len(headers) - 1

        row_cells = split_md_row(lines[line_index])
        while len(row_cells) < len(headers):
            row_cells.append("")

        pt_col = col_map["pt_col"]
        old_pt_raw = row_cells[pt_col].strip()
        use_backticks = not old_pt_raw.startswith("**")

        if upd.get("pt_text") is not None:
            row_cells[pt_col] = text_to_md_cell(upd["pt_text"], use_backticks=use_backticks)

        if col_map["pt_desc_col"] is not None and col_map["pt_desc_col"] != pt_col and upd.get("pt_desc") is not None:
            row_cells[col_map["pt_desc_col"]] = text_to_md_cell(upd["pt_desc"], use_backticks=True)

        validated = bool(upd.get("validated", True))
        status_col = col_map["status_col"]
        row_cells[status_col] = "✅ Validado" if validated else "⏳ Pendente"
        lines[line_index] = join_md_row(row_cells)

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Re-parseia apenas o arquivo modificado no cache em memória
    updated_parsed = parse_md_file(filepath, proj=proj, force_reload=True)
    return {
        "ok": True,
        "updated_count": len(updates),
        "file_summary": {
            "filename": updated_parsed["filename"],
            "total": updated_parsed["total"],
            "validated": updated_parsed["validated"],
            "qa_errors": updated_parsed["qa_errors"],
            "qa_warnings": updated_parsed["qa_warnings"],
        },
    }


def export_embedded_js(proj: Optional[StudioProjectContext] = None) -> None:
    """Exporta `tools/embedded_md_data.js` usando o cache em memória."""
    if proj is None:
        proj = get_or_load_project()

    cats = list_translation_md_files(proj)
    files_map = {}
    for c in cats:
        rel_name = c["filename"]
        if rel_name in proj.file_cache:
            files_map[rel_name] = proj.file_cache[rel_name]["data"]
        else:
            files_map[rel_name] = parse_md_file(proj.md_dir / rel_name, proj=proj)

    payload = {
        "project": proj.profile,
        "categories": cats,
        "files": files_map,
        "character_bible": proj.character_bible,
        "voice_matrix": proj.voice_matrix,
        "glossary_terms": proj.glossary_terms,
        "canonical_abbreviations": CANONICAL_ABBREVIATIONS,
    }
    js_content = "window.EMBEDDED_MD_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    proj.embedded_js_path.write_text(js_content, encoding="utf-8")


# ============================================================================
# GERADOR DE PROMPT CIRÚRGICO (TOKEN ECONOMY INTEGRADO)
# ============================================================================
def generate_surgical_batch_prompt(
    proj: StudioProjectContext,
    filename: str,
    start_idx: int = 0,
    chunk_size: int = 35,
    only_pending: bool = True,
) -> Dict[str, Any]:
    fpath = (proj.md_dir / filename).resolve()
    parsed = parse_md_file(fpath, proj=proj)
    entries = parsed["entries"]

    if only_pending:
        pool = [e for e in entries if not e["validated"] or e.get("has_qa_error")]
        if not pool:
            pool = entries
    else:
        pool = entries

    chunk = pool[start_idx : start_idx + chunk_size]
    if not chunk:
        chunk = entries[:chunk_size]

    chunk_text = " ".join(f"{e['en_text']} {e['pt_text']} {e['speaker']}" for e in chunk).lower()

    matched_terms = []
    for g in proj.glossary_terms:
        orig_low = g["original"].lower()
        if len(orig_low) > 2 and orig_low in chunk_text:
            matched_terms.append(g)

    matched_speakers = {}
    for e in chunk:
        sid = e["speaker_id"]
        if sid not in matched_speakers:
            matched_speakers[sid] = {
                "name": e["speaker"],
                "role": e["actor_role"],
                "voice": e.get("voice_guide") or "Coloquial natural e fluido em PT-BR",
            }

    hard_limit = proj.profile.get("hard_limit", 35)
    prompt_lines = [
        f"### 🎯 Sprint de Tradução & Revisão GBA — {proj.profile['title']}",
        f"**Arquivo:** `{filename}` ({len(chunk)} entradas selecionadas)",
        "",
        "#### 📐 Regras Invioláveis do GBA Localization Studio:",
        f"- **Métricas de Linha:** Separe linhas na mesma caixa com `<br>`. Zona Ideal: **1 a 32 caracteres**. Hard Limit absoluto: **{hard_limit} caracteres/linha**.",
        "- **Neutralidade de Gênero Sistêmica:** Jamais use adjetivos masculinos/femininos diretos para `{PLAYER}` (use substantivos abstratos: *'O cansaço bateu?'*, *'Tudo pronto?'*, *'Boas-vindas!'*, *'Agradeço de coração!'*).",
        "- **Política de Abreviações:** Zero abreviações (`vc`, `tb`, `pq`, `atq.`) em diálogos narrativos.",
        "- **Prevenção de Orfandade:** Nunca deixe artigos/preposições curtas (`o`, `a`, `de`, `em`, `e`, `que`) isolados no fim da linha antes de `<br>`.",
        "",
    ]

    if matched_speakers:
        prompt_lines.append("#### 🎭 Vozes dos Personagens neste Lote (`catalogo-de-personagens.md`):")
        for sp in matched_speakers.values():
            prompt_lines.append(f"- **{sp['name']}** ({sp['role']}): {sp['voice']}")
        prompt_lines.append("")

    if matched_terms:
        prompt_lines.append("#### 📖 Termos do Glossário Detectados neste Lote:")
        for t in matched_terms[:18]:
            short_note = f" (Curto/UI: `{t['short_form']}`)" if t.get("short_form") else ""
            prompt_lines.append(f"- `{t['original']}` ➔ **`{t['pt_br']}`**{short_note}")
        prompt_lines.append("")

    prompt_lines.append("#### 📋 Lote de Falas:")
    prompt_lines.append("| Linha MD | ID | Falante ➔ Alvo | Original (EN) | Tradução PT-BR |")
    prompt_lines.append("| :---: | :--- | :--- | :--- | :--- |")
    for e in chunk:
        en_flat = e["en_text"].replace("\n", "<br>").replace("|", "/")
        pt_flat = e["pt_text"].replace("\n", "<br>").replace("|", "/") or "[Traduzir]"
        prompt_lines.append(f"| L{e['line_index']+1} | `{e['ref_id']}` | {e['speaker']} ➔ {e['addressee']} | `{en_flat}` | `{pt_flat}` |")

    return {
        "ok": True,
        "count": len(chunk),
        "matched_terms_count": len(matched_terms),
        "matched_speakers_count": len(matched_speakers),
        "prompt": "\n".join(prompt_lines),
    }


# ============================================================================
# SERVIDOR HTTP MULTI-PROJETO
# ============================================================================
class ValidatorRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        game_param = qs.get("game", [None])[0]
        proj = get_or_load_project(game_param)

        if parsed.path in ("/", "/index.html"):
            ui_path = proj.ui_html_path if proj.ui_html_path.is_file() else (SCRIPT_DIR / "validator_ui.html")
            html_bytes = ui_path.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html_bytes)
            return

        if parsed.path == "/embedded_md_data.js":
            if not proj.embedded_js_path.is_file():
                export_embedded_js(proj)
            js_bytes = proj.embedded_js_path.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(js_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(js_bytes)
            return

        if parsed.path == "/api/projects":
            self._send_json({
                "projects": list_available_projects(),
                "active_project": proj.profile,
            })
            return

        if parsed.path == "/api/studio_context":
            self._send_json({
                "project": proj.profile,
                "character_bible": proj.character_bible,
                "voice_matrix": proj.voice_matrix,
                "glossary_terms": proj.glossary_terms,
                "canonical_abbreviations": CANONICAL_ABBREVIATIONS,
            })
            return

        if parsed.path == "/api/categories":
            cats = list_translation_md_files(proj)
            self._send_json({
                "project": proj.profile,
                "categories": cats,
            })
            return

        if parsed.path == "/api/file":
            fname = qs.get("name", [""])[0]
            fpath = (proj.md_dir / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(proj.md_dir.resolve()):
                self._send_json({"error": "Arquivo não encontrado."}, status=404)
                return
            data = parse_md_file(fpath, proj=proj)
            self._send_json(data)
            return

        if parsed.path == "/api/global_search":
            query = qs.get("q", [""])[0].strip().lower()
            limit = int(qs.get("limit", ["300"])[0])
            if not query:
                self._send_json({"ok": True, "query": "", "total_matches": 0, "files_matched": 0, "results": []})
                return

            cats = list_translation_md_files(proj)
            results = []
            total_matches = 0
            files_matched_set = set()

            for c in cats:
                fdata = parse_md_file(proj.md_dir / c["filename"], proj=proj)
                for idx_in_file, e in enumerate(fdata["entries"]):
                    hay = (
                        f"{e.get('ref_id', '')} {e.get('en_text', '')} {e.get('pt_text', '')} "
                        f"{e.get('en_desc', '')} {e.get('pt_desc', '')} {e.get('section', '')} "
                        f"{e.get('speaker', '')} {e.get('addressee', '')}"
                    ).lower()
                    if query in hay:
                        total_matches += 1
                        files_matched_set.add(c["filename"])
                        if len(results) < limit:
                            results.append({
                                "filename": c["filename"],
                                "file_title": c["title"],
                                "entry_index": idx_in_file,
                                "line_index": e["line_index"],
                                "line_number": e["line_index"] + 1,
                                "ref_id": e.get("ref_id", ""),
                                "section": e.get("section", ""),
                                "speaker": e.get("speaker", ""),
                                "speaker_id": e.get("speaker_id", ""),
                                "addressee": e.get("addressee", ""),
                                "en_text": e.get("en_text", ""),
                                "pt_text": e.get("pt_text", ""),
                                "validated": e.get("validated", False),
                                "has_qa_error": e.get("has_qa_error", False),
                                "has_qa_warn": e.get("has_qa_warn", False),
                            })

            self._send_json({
                "ok": True,
                "project": proj.profile,
                "query": query,
                "total_matches": total_matches,
                "files_matched": len(files_matched_set),
                "truncated": total_matches > limit,
                "results": results,
            })
            return

        if parsed.path == "/api/qa_audit":
            fname = qs.get("name", [""])[0]
            cats = list_translation_md_files(proj)
            target_cats = [c for c in cats if not fname or c["filename"] == fname]

            files_report = []
            total_errs = 0
            total_warns = 0
            total_rows = 0
            total_valid = 0

            for c in target_cats:
                fdata = parse_md_file(proj.md_dir / c["filename"], proj=proj)
                file_issues = []
                for e in fdata["entries"]:
                    for iss in e.get("qa_issues", []):
                        file_issues.append({
                            "line_index": e["line_index"],
                            "line_number": e["line_index"] + 1,
                            "ref_id": e["ref_id"],
                            "speaker": e["speaker"],
                            "gate": iss["gate"],
                            "severity": iss["severity"],
                            "msg": iss["msg"],
                            "pt_text": e["pt_text"],
                        })
                total_errs += fdata["qa_errors"]
                total_warns += fdata["qa_warnings"]
                total_rows += fdata["total"]
                total_valid += fdata["validated"]
                files_report.append({
                    "filename": c["filename"],
                    "title": c["title"],
                    "total": fdata["total"],
                    "validated": fdata["validated"],
                    "qa_errors": fdata["qa_errors"],
                    "qa_warnings": fdata["qa_warnings"],
                    "issues": file_issues[:150],
                })

            self._send_json({
                "ok": True,
                "project": proj.profile,
                "total_rows": total_rows,
                "total_validated": total_valid,
                "total_errors": total_errs,
                "total_warnings": total_warns,
                "files": files_report,
            })
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(raw_body) if raw_body else {}
        except Exception:
            payload = {}

        game_id = payload.get("game")
        proj = get_or_load_project(game_id)

        if parsed.path == "/api/switch_project":
            target_game = payload.get("game_id", "")
            proj = get_or_load_project(target_game)
            cats = list_translation_md_files(proj)
            self._send_json({
                "ok": True,
                "project": proj.profile,
                "projects": list_available_projects(),
                "categories": cats,
                "character_bible": proj.character_bible,
                "voice_matrix": proj.voice_matrix,
                "glossary_terms": proj.glossary_terms,
                "canonical_abbreviations": CANONICAL_ABBREVIATIONS,
            })
            return

        if parsed.path == "/api/save":
            fname = payload.get("filename", "")
            line_index = int(payload.get("line_index", -1))
            pt_text = payload.get("pt_text", "")
            pt_desc = payload.get("pt_desc", None)
            validated = bool(payload.get("validated", True))

            fpath = (proj.md_dir / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(proj.md_dir.resolve()):
                self._send_json({"error": "Arquivo inválido."}, status=400)
                return

            try:
                res = update_md_entries_batch(
                    fpath,
                    [{"line_index": line_index, "pt_text": pt_text, "pt_desc": pt_desc, "validated": validated}],
                    proj=proj,
                )
                # Busca a entrada recém-atualizada com o QA recalculado
                updated_file = proj.file_cache[fname]["data"]
                updated_entry = next((e for e in updated_file["entries"] if e["line_index"] == line_index), None)
                self._send_json({
                    "ok": True,
                    "line_index": line_index,
                    "validated": validated,
                    "status_str": "✅ Validado" if validated else "⏳ Pendente",
                    "entry": updated_entry,
                    "file_summary": res["file_summary"],
                })
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        if parsed.path == "/api/batch_save":
            fname = payload.get("filename", "")
            updates = payload.get("updates", [])
            fpath = (proj.md_dir / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(proj.md_dir.resolve()):
                self._send_json({"error": "Arquivo inválido."}, status=400)
                return
            try:
                res = update_md_entries_batch(fpath, updates, proj=proj)
                self._send_json(res)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        if parsed.path == "/api/surgical_prompt":
            fname = payload.get("filename", "")
            start_idx = int(payload.get("start_index", 0))
            chunk_size = int(payload.get("chunk_size", 35))
            only_pending = bool(payload.get("only_pending", True))
            try:
                res = generate_surgical_batch_prompt(proj, fname, start_idx, chunk_size, only_pending)
                self._send_json(res)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
            return

        if parsed.path == "/api/export_embedded":
            try:
                export_embedded_js(proj)
                self._send_json({"ok": True, "path": str(proj.embedded_js_path)})
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
            return

        if parsed.path == "/api/build":
            try:
                build_script = proj.tools_dir / "build_ptbr_rom.py"
                build_bat = proj.game_dir / "Compilar_ROM_PTBR.bat"
                if build_script.is_file():
                    cmd = [sys.executable, "-X", "utf8", str(build_script)]
                elif build_bat.is_file():
                    cmd = ["cmd.exe", "/c", str(build_bat)]
                else:
                    self._send_json({"ok": False, "error": "Script build_ptbr_rom.py não encontrado neste projeto."}, status=404)
                    return

                p = subprocess.run(
                    cmd,
                    cwd=str(proj.game_dir),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if p.returncode == 0:
                    self._send_json({"ok": True, "output": p.stdout})
                else:
                    self._send_json({"ok": False, "error": p.stderr or p.stdout}, status=500)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)


def find_available_port(preferred_port: int) -> int:
    import socket
    for p in range(preferred_port, preferred_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return preferred_port


def main() -> int:
    proj = get_or_load_project()
    t0 = time.perf_counter()
    cats = list_translation_md_files(proj)
    export_embedded_js(proj)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    if "--export-js-only" in sys.argv:
        print(f"✅ [GBA Studio] embedded_md_data.js exportado em {elapsed_ms:.0f}ms ({len(cats)} arquivos)!")
        return 0

    default_port = "8766" if "Story_2" in proj.game_id else ("8767" if "Story_3" in proj.game_id else "8765")
    pref_port = int(os.environ.get("VALIDATOR_PORT", default_port))
    port = find_available_port(pref_port)
    no_browser = "--no-browser" in sys.argv

    server = ThreadingHTTPServer(("127.0.0.1", port), ValidatorRequestHandler)
    url = f"http://127.0.0.1:{port}"

    total_entries = sum(c["total"] for c in cats)
    total_valid = sum(c["validated"] for c in cats)
    total_qa_err = sum(c["qa_errors"] for c in cats)

    print("=" * 78)
    print(f" 🎮 GBA LOCALIZATION STUDIO — VALIDADOR & QUALITY GATE SUITE v2.0")
    print("=" * 78)
    print(f" • Projeto Ativo     : {proj.profile['title']} [{proj.profile['short_code']}]")
    print(f" • Pasta Monitorada  : {proj.md_dir}")
    print(f" • Arquivos / Linhas : {len(cats)} arquivos | {total_valid:,}/{total_entries:,} validadas")
    print(f" • Bíblia & Glossário: {len(proj.character_bible)} fichas de voz | {len(proj.glossary_terms)} termos canônicos")
    print(f" • Status QA Gate    : {total_qa_err} erro(s) crítico(s) detectado(s) | Indexado em {elapsed_ms:.0f}ms")
    print(f" • Interface Web     : {url}")
    print("=" * 78)

    if not no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando GBA Localization Studio Server...")
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
