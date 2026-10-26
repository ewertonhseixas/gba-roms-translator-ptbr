#!/usr/bin/env python3
"""
Validador e Editor Interativo de Tradução (PT-BR)
Framework de Localização de ROMs GBA / Retrô
=================================================
Servidor local (zero dependências externas) que lê e atualiza diretamente
os arquivos .md da pasta "ARQUIVOS md/", permitindo:
  - Selecionar a categoria (arquivo .md) e filtrar por seção/status/busca
  - Filtrar por Ramo de Gênero do Jogador (♂ Masculino / ♀ Feminino / 👥 Compartilhado / NPCs)
  - Filtrar por Personagem agrupado por categoria (Protagonistas, Companheiros, Principais, NPCs, Sistema)
  - Visualizar o texto original em EN-US, o contexto (endereço ROM, personagem,
    seção, observações), a tradução sugerida em PT-BR e a opção alternativa (se houver)
  - Identificar com precisão quem fala e a quem a fala se destina (com sinalização de gênero)
  - Visualizar a régua em tempo real com os limites físicos do GBA (Ideal <=32, Atenção 33-35, Excesso >=36)
  - Compilar a ROM diretamente pela interface web (com log de execução)
  - Editar livremente a tradução (incluindo Nome + Descrição para armas/itens/magias)
  - Confirmar a tradução com 1 clique (ou Ctrl+Enter), salvando direto na linha
    correspondente do arquivo .md e marcando como "✅ Validado".
"""

import json
import os
import re
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
MD_DIR = ROOT_DIR / "ARQUIVOS md"
UI_HTML_PATH = Path(__file__).resolve().parent / "validator_ui.html"
EMBEDDED_JS_PATH = Path(__file__).resolve().parent / "embedded_md_data.js"

# Regex para extrair alternativa inline do tipo: `Texto A` *(ou `Texto B`)* / *(ou Texto B)*
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

# Mapa global de falantes indexado por (script_id, string_id)
GLOBAL_SCRIPT_SPEAKERS: Dict[Tuple[int, int], str] = {}
# Mapa dinâmico de catálogo de personagens do projeto
PROJECT_CHARACTERS: Dict[str, Dict[str, Any]] = {}


def split_md_row(line: str) -> List[str]:
    """Divide uma linha de tabela Markdown '| a | b | c |' nas células internas."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def join_md_row(cells: List[str]) -> str:
    """Reconstrói uma linha de tabela Markdown formatada."""
    return "| " + " | ".join(cells) + " |"


def clean_cell_to_text(raw: str) -> Tuple[str, str, str]:
    """
    Converte o conteúdo bruto de uma célula Markdown em:
      (texto_principal_limpo, alternativa_inline_limpa, nota_extra)
    """
    s = raw.strip()
    opt_text = ""

    m = INLINE_OPT_RE.match(s)
    if m:
        s = m.group(1).strip()
        opt_raw = m.group(2).strip()
        opt_text = _strip_md_formatting(opt_raw)

    main_text = _strip_md_formatting(s)
    return main_text, opt_text, ""


def _strip_md_formatting(s: str) -> str:
    """Converte `<br>` em quebra de linha real e remove crases/negritos de formatação Markdown."""
    parts = re.split(r"<br\s*/?>", s, flags=re.IGNORECASE)
    cleaned_lines = []
    for p in parts:
        p = p.strip()
        p = p.replace("**", "").replace("`", "").strip()
        cleaned_lines.append(p)
    return "\n".join(cleaned_lines)


def text_to_md_cell(text: str, use_backticks: bool = True) -> str:
    """
    Converte o texto editado pelo usuário (com quebras de linha '\n') de volta
    para o formato da célula Markdown (`linha 1`<br>`linha 2`).
    """
    lines = [ln.replace("|", "/").rstrip("\r") for ln in text.split("\n")]
    if not lines:
        return ""
    if use_backticks:
        return "<br>".join(f"`{ln}`" if ln else "" for ln in lines)
    else:
        return "<br>".join(f"**{ln}**" if ln else "" for ln in lines)


def classify_table_columns(headers: List[str]) -> Optional[Dict[str, Any]]:
    """
    Analisa os nomes das colunas do cabeçalho da tabela Markdown e retorna
    o mapeamento semântico das colunas.
    """
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


def load_project_character_catalog() -> None:
    """
    Escaneia catalogo-de-personagens.md ou arquivos de documentação para identificar
    os personagens definidos especificamente para o projeto.
    """
    PROJECT_CHARACTERS.clear()
    cat_file = MD_DIR / "catalogo-de-personagens.md"
    if not cat_file.is_file():
        return

    try:
        text = cat_file.read_text(encoding="utf-8")
        # Procura por seções '### `CHR_...` — Nome ➔ **Display**' ou '### Nome'
        for m in re.finditer(r"###\s+(?:`[^`]+`\s*—\s*)?([^\n➔]+)(?:➔\s*\*\*([^\*]+)\*\*)?", text):
            raw = (m.group(2) or m.group(1)).strip()
            clean = re.sub(r"\(.*?\)", "", raw).strip()
            c_id = clean.lower().replace(" ", "_")
            if c_id and c_id not in PROJECT_CHARACTERS:
                PROJECT_CHARACTERS[c_id] = {
                    "id": c_id,
                    "name": clean,
                    "gender": "neutral",
                    "role": "Personagem do Jogo",
                    "icon": "👤",
                    "category": "Personagens Principais",
                }
    except Exception:
        pass


def build_global_speaker_map() -> None:
    """
    Escaneia arquivos de diálogo com colunas explícitas de personagem para
    construir uma base unificada (script_id, string_id) -> falante.
    """
    GLOBAL_SCRIPT_SPEAKERS.clear()
    load_project_character_catalog()
    for f in MD_DIR.rglob("*.md"):
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
                                GLOBAL_SCRIPT_SPEAKERS[(s_id, str_id)] = clean_sp
        except Exception:
            pass


def list_translation_md_files() -> List[Dict[str, Any]]:
    """Lista todos os arquivos .md de tradução com estatísticas de progresso."""
    files = sorted(MD_DIR.rglob("*.md"), key=lambda p: (p.name, p.as_posix()))
    result = []
    for f in files:
        if f.name.startswith(("00-", "01-")):
            continue
        rel_name = f.relative_to(MD_DIR).as_posix()
        parsed = parse_md_file(f)
        entries = parsed["entries"]
        total = len(entries)
        validated = sum(1 for e in entries if e["validated"])
        result.append({
            "filename": rel_name,
            "title": parsed["title"] or f.stem,
            "total": total,
            "validated": validated,
        })
    return result


def canonicalize_character(
    raw_name: str,
    context: str = "",
    text: str = "",
) -> Tuple[str, str, str, str, str, str]:
    """
    Normaliza um nome de personagem bruto e extrai seus atributos de gênero e categoria.
    Retorna:
      (char_id, display_name, gender, role, icon, category)
      onde gender é 'male' | 'female' | 'both' | 'neutral'
    """
    if not raw_name:
        return "geral", "Cena / Geral", "neutral", "Cena", "🎬", "Cena"

    clean = raw_name.strip()
    c_lower = clean.lower()

    # 1. Escolhas de Diálogo
    if "escolha" in c_lower or "choice" in c_lower:
        if any(k in c_lower for k in ("masc", "homem", "garoto", "cleru", "edgar", "bost")):
            return "choice_male", "Escolha ♂ (Herói)", "male", "Opção de Diálogo (♂)", "🗳️", "Protagonistas & Escolhas"
        if any(k in c_lower for k in ("fem", "mulher", "garota", "pratty", "aera", "prat")):
            return "choice_female", "Escolha ♀ (Heroína)", "female", "Opção de Diálogo (♀)", "🗳️", "Protagonistas & Escolhas"
        return "choice", "Escolha do Jogador", "both", "Opção de Diálogo", "🗳️", "Protagonistas & Escolhas"

    # 2. Protagonistas Canônicos
    if any(k in c_lower for k in ("cleru", "edgar", "bost", "{player} (masc)", "{player} (edgar)", "{player} (cleru)")):
        return "hero_male", "♂ Herói", "male", "Herói (Protagonista)", "♂", "Protagonistas & Escolhas"
    if any(k in c_lower for k in ("pratty", "aera", "prat", "{player} (fem)", "{player} (aera)", "{player} (pratty)")):
        return "hero_female", "♀ Heroína", "female", "Heroína (Protagonista)", "♀", "Protagonistas & Escolhas"

    # 3. Protagonista Compartilhado / Genérico
    if any(k in c_lower for k in ("protagonista", "{player}", "protagonist", "player")):
        ctx_l = (context + " " + text).lower()
        if any(k in ctx_l for k in ("(masc)", "(edgar)", "(cleru)", "ramo cleru", "ramo edgar", "ramo masculino", "hardest steel")):
            return "hero_male", "♂ Herói", "male", "Herói (Protagonista)", "♂", "Protagonistas & Escolhas"
        if any(k in ctx_l for k in ("(fem)", "(aera)", "(pratty)", "ramo pratty", "ramo aera", "ramo feminino", "toughest chain")):
            return "hero_female", "♀ Heroína", "female", "Heroína (Protagonista)", "♀", "Protagonistas & Escolhas"
        return "protagonist", "👥 Protagonista (Ambos)", "both", "Protagonista (Compartilhado)", "👥", "Protagonistas & Escolhas"

    # 4. Companheiros e Guardiões
    if any(k in c_lower for k in ("partner", "parceiro", "guardião", "guardian", "beast")):
        return "partner", "Companheiro(a)", "both", "Companheiro(a) de Jornada", "🐾", "Companheiros & Guardiões"
    if any(k in c_lower for k in ("rasho", "arno")):
        return c_lower, clean.title(), "male", "Companheiro Guerreiro", "🐾", "Companheiros & Guardiões"
    if any(k in c_lower for k in ("sugar", "dinah")):
        return c_lower, clean.title(), "female", "Companheira Mística / Fada", "🧚", "Companheiros & Guardiões"
    if any(k in c_lower for k in ("exeld", "zantek", "run-d")):
        return c_lower, clean.title(), "neutral", "Companheiro Autômato / Mecânico", "🤖", "Companheiros & Guardiões"
    if any(k in c_lower for k in ("loki", "kutty")):
        return c_lower, clean.title(), "male", "Companheiro Espiritual", "😈", "Companheiros & Guardiões"

    # 5. Mentores e Personagens Centrais
    if any(k in c_lower for k in ("mestre", "master", "blaire", "bron")):
        return "mentor", clean.title() if clean else "Mestre / Mentor", "male", "Mestre / Mentor", "🔨", "Personagens Principais"
    if any(k in c_lower for k in ("mãe", "mother", "amariss")):
        return "mother", "Mãe do Protagonista", "female", "Família do Protagonista", "👩", "Personagens Principais"
    if any(k in c_lower for k in ("pai", "father", "shintetsu")):
        return "father", "Pai do Protagonista", "male", "Família do Protagonista", "⚡", "Personagens Principais"
    if any(k in c_lower for k in ("irmão", "irmã", "sibling", "orin")):
        return "sibling", clean.title() if clean else "Irmão(ã)", "both", "Irmão(ã) Adotivo(a)", "🧑", "Personagens Principais"
    if any(k in c_lower for k in ("rival", "sanary", "varil", "ryouga", "tatiana")):
        return clean.lower().replace(" ", "_"), clean.title(), "both", "Rival / Oponente", "⚔️", "Personagens Principais"

    # 6. NPCs e Sistema
    if any(k in c_lower for k in ("lojista", "comerciante", "shopkeeper", "vendedor")):
        return "lojista", "Lojista", "neutral", "Comerciante", "🏪", "NPCs do Jogo"
    if any(k in c_lower for k in ("guarda", "guard", "soldado")):
        return "guarda", "Guarda", "male", "Guarda / Vigia", "💂", "NPCs do Jogo"
    if any(k in c_lower for k in ("invocador", "summoner", "mago")):
        return "invocador", "Invocador", "neutral", "Invocador", "🧙", "NPCs do Jogo"
    if any(k in c_lower for k in ("morador", "villager", "aldeão", "cidadão", "ancião", "elder")):
        return "morador", "Habitante do Local", "neutral", "NPC da Cidade", "👤", "NPCs do Jogo"
    if any(k in c_lower for k in ("sistema", "aviso", "tela", "menu", "status", "system")):
        return "system", "Sistema / Narração", "neutral", "Interface / HUD", "⚙️", "Sistema & Interface"

    clean_name = re.sub(r"\(.*?\)", "", clean).strip()
    c_name = clean_name.title() if clean_name.islower() else clean_name
    c_id = clean_name.lower().replace(" ", "_")

    if c_id in PROJECT_CHARACTERS:
        meta = PROJECT_CHARACTERS[c_id]
        return c_id, meta["name"], meta["gender"], meta["role"], meta["icon"], meta["category"]

    return c_id, c_name, "neutral", "Personagem", "👤", "NPCs do Jogo"


def infer_gender_branch(
    speaker_id: str,
    target_id: str,
    sec: str,
    ctx: str,
    en: str,
    pt: str,
) -> Tuple[str, str]:
    """
    Determina o ramo de gênero do jogador para a linha de diálogo:
      'male'   -> ♂ Ramo Masculino
      'female' -> ♀ Ramo Feminino
      'both'   -> 👥 Ramo Compartilhado (Ambos)
      'npc'    -> 🗣️ Diálogo Geral
      'system' -> ⚙️ Sistema
    """
    # 1. Falante é o herói ou heroína diretamente
    if speaker_id in ("hero_male", "choice_male", "cleru", "edgar"):
        return "male", "♂ Ramo Masculino"
    if speaker_id in ("hero_female", "choice_female", "pratty", "aera"):
        return "female", "♀ Ramo Feminino"

    # 2. Contexto de seção / título
    all_ctx = f"{sec} {ctx}".lower()
    if any(k in all_ctx for k in ("(masc)", "(edgar)", "(cleru)", "(bost)", "ramo cleru", "ramo edgar", "ramo masculino")):
        return "male", "♂ Ramo Masculino"
    if any(k in all_ctx for k in ("(fem)", "(aera)", "(pratty)", "(prat)", "ramo pratty", "ramo aera", "ramo feminino")):
        return "female", "♀ Ramo Feminino"

    # 3. Destinatário é o herói ou heroína diretamente
    if target_id in ("hero_male", "cleru", "edgar"):
        return "male", "♂ Ramo Masculino"
    if target_id in ("hero_female", "pratty", "aera"):
        return "female", "♀ Ramo Feminino"

    # 4. Pistas textuais de gênero em português ou inglês
    text_check = f"{en} {pt}".lower()
    has_male = bool(MALE_CUES.search(text_check))
    has_fem = bool(FEMALE_CUES.search(text_check))
    if has_male and not has_fem and ("{player}" in text_check or target_id in ("protagonist", "player", "hero_male", "hero_female")):
        return "male", "♂ Ramo Masculino"
    if has_fem and not has_male and ("{player}" in text_check or target_id in ("protagonist", "player", "hero_male", "hero_female")):
        return "female", "♀ Ramo Feminino"

    # 5. Fala compartilhada pelo protagonista
    if speaker_id in ("protagonist", "choice") or target_id in ("protagonist", "player"):
        return "both", "👥 Ramo Compartilhado (Ambos)"

    # 6. Sistema ou Mensagem técnica
    if speaker_id == "system":
        return "system", "⚙️ Sistema"

    return "npc", "🗣️ Diálogo Geral"


def enrich_entries(entries: List[Dict[str, Any]], doc_title: str) -> List[Dict[str, Any]]:
    """
    Enriquece as entradas identificando Falante, Destinatário, Gênero do Jogador,
    Papel Narrativo, Ícones e estatísticas completas de personagens da cena.
    """
    if not entries:
        return []

    if not GLOBAL_SCRIPT_SPEAKERS:
        build_global_speaker_map()

    # 1ª Passada: detecta Script Group, Falante Bruto e Atributos Básicos
    for e in entries:
        ref_id = e.get("ref_id", "")
        sec = e.get("section", "")
        ctx = e.get("context", "")
        en = e.get("en_text", "")
        pt = e.get("pt_text", "")

        # Grupo de Script / Cena
        m_scr = re.search(r"#?(\d+)", ref_id) or re.search(r"#?(\d+)", sec)
        if m_scr:
            s_group = f"Script #{int(m_scr.group(1)):04d}"
        elif sec:
            s_group = sec.split("›")[0].strip()
        else:
            s_group = doc_title or "Geral"
        e["script_group"] = s_group

        # Extração de falante
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
                raw_speaker = GLOBAL_SCRIPT_SPEAKERS.get((s_num, str_num), "")

        if not raw_speaker:
            m_text = re.search(r"\*\(([^:)]+):?\)\*", en) or re.search(r"\*\(([^:)]+):?\)\*", pt)
            if m_text:
                raw_speaker = m_text.group(1).strip()
            elif any(k in doc_title.lower() for k in ("interface", "menu", "armas", "itens", "bestiário")):
                raw_speaker = "Sistema"
            else:
                raw_speaker = "Geral"

        s_id, s_name, s_gender, s_role, s_icon, s_cat = canonicalize_character(
            raw_speaker, context=f"{sec} {ctx}", text=f"{en} {pt}"
        )
        e["speaker_raw"] = raw_speaker
        e["speaker"] = s_name
        e["speaker_id"] = s_id
        e["speaker_gender"] = s_gender
        e["actor_role"] = s_role
        e["actor_icon"] = s_icon
        e["actor_category"] = s_cat

        # Pensamento / Monólogo
        clean_en = en.strip()
        is_thought = (clean_en.startswith("(") and clean_en.endswith(")")) or "(Pensamento)" in ctx or "(Monólogo)" in ctx
        e["is_thought"] = is_thought

    # 2ª Passada: Agrupa por cena/script e infere Destinatário e Ramo de Gênero
    groups: Dict[str, List[int]] = {}
    for idx, e in enumerate(entries):
        groups.setdefault(e["script_group"], []).append(idx)

    for s_group, indices in groups.items():
        group_has_male = any(
            entries[i]["speaker_id"] in ("hero_male", "choice_male", "cleru", "edgar")
            or "(masc)" in entries[i]["context"].lower()
            for i in indices
        )
        group_has_female = any(
            entries[i]["speaker_id"] in ("hero_female", "choice_female", "pratty", "aera")
            or "(fem)" in entries[i]["context"].lower()
            for i in indices
        )

        participants: List[str] = []
        for i in indices:
            sp_id = entries[i]["speaker_id"]
            if sp_id not in ("system", "choice", "choice_male", "choice_female", "geral") and sp_id not in participants:
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
            elif sp_id in ("choice", "choice_male", "choice_female"):
                target_name = "Interlocutor da Cena"
                target_id = "interlocutor"
            else:
                candidate_id: Optional[str] = None
                if last_speaker_id and last_speaker_id != sp_id and last_speaker_id not in ("system", "choice", "choice_male", "choice_female"):
                    candidate_id = last_speaker_id
                elif last_non_self_speaker_id and last_non_self_speaker_id != sp_id:
                    candidate_id = last_non_self_speaker_id
                elif len(participants) == 2:
                    candidate_id = participants[1] if participants[0] == sp_id else participants[0]
                elif len(participants) > 1 and sp_id not in ("hero_male", "hero_female", "protagonist"):
                    if group_has_male and not group_has_female:
                        candidate_id = "hero_male"
                    elif group_has_female and not group_has_male:
                        candidate_id = "hero_female"
                    else:
                        candidate_id = "protagonist"

                if candidate_id == sp_id:
                    if last_non_self_speaker_id:
                        candidate_id = last_non_self_speaker_id
                    else:
                        others = [p for p in participants if p != sp_id]
                        candidate_id = others[0] if others else None

                if candidate_id:
                    if candidate_id in ("protagonist", "hero_male", "hero_female"):
                        if MALE_CUES.search(text_combo) and not FEMALE_CUES.search(text_combo):
                            candidate_id = "hero_male"
                        elif FEMALE_CUES.search(text_combo) and not MALE_CUES.search(text_combo):
                            candidate_id = "hero_female"
                        elif group_has_male and not group_has_female:
                            candidate_id = "hero_male"
                        elif group_has_female and not group_has_male:
                            candidate_id = "hero_female"
                    target_id, target_name, _, _, _, _ = canonicalize_character(candidate_id)
                else:
                    target_name = "Cena / Todos"
                    target_id = "geral"

            # Determina o Ramo de Gênero
            branch, branch_label = infer_gender_branch(
                sp_id, target_id, e.get("section", ""), ctx, e.get("en_text", ""), e.get("pt_text", "")
            )

            # Refina destinatário se o ramo for estritamente masculino ou feminino
            if branch == "male" and target_id == "protagonist":
                target_id, target_name, _, _, _, _ = canonicalize_character("hero_male")
            elif branch == "female" and target_id == "protagonist":
                target_id, target_name, _, _, _, _ = canonicalize_character("hero_female")

            e["addressee"] = target_name
            e["addressee_id"] = target_id
            e["gender_branch"] = branch
            e["gender_label"] = branch_label

            # Metadados do destinatário
            t_id, t_name, t_gen, t_role, t_icon, t_cat = canonicalize_character(target_id)
            e["target_role"] = t_role
            e["target_icon"] = t_icon

            if sp_id not in ("system", "choice", "choice_male", "choice_female"):
                if last_speaker_id and last_speaker_id != sp_id:
                    last_non_self_speaker_id = last_speaker_id
                last_speaker_id = sp_id

    # 3ª Passada: Constrói a lista estruturada de personagens para filtros da UI
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
                "spoken": 0,
                "addressed": 0,
                "total": 0,
            }
        char_map[s_id]["spoken"] += 1
        char_map[s_id]["total"] += 1

        t_id = e["addressee_id"]
        if t_id and t_id not in ("thought", "geral", "player", "interlocutor"):
            if t_id not in char_map:
                t_id_c, t_name_c, t_gen_c, t_role_c, t_icon_c, t_cat_c = canonicalize_character(t_id)
                char_map[t_id] = {
                    "id": t_id,
                    "name": t_name_c,
                    "gender": t_gen_c,
                    "role": t_role_c,
                    "icon": t_icon_c,
                    "category": t_cat_c,
                    "spoken": 0,
                    "addressed": 0,
                    "total": 0,
                }
            char_map[t_id]["addressed"] += 1
            char_map[t_id]["total"] += 1

    sorted_chars = sorted(char_map.values(), key=lambda c: (c["total"], c["spoken"]), reverse=True)
    return sorted_chars


def parse_md_file(filepath: Path) -> Dict[str, Any]:
    """
    Lê um arquivo .md e extrai todas as linhas de tabelas de tradução,
    preservando o número exato da linha (`line_index`) para gravação direta.
    """
    text = filepath.read_text(encoding="utf-8")
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

        # Detecta início de tabela Markdown
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
                row_cells = split_md_row(lines[i])
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
                if col_map["pt_desc_col"] is not None and col_map["pt_desc_col"] < len(row_cells):
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
                    if "✅" in st_cell or "validado" in st_cell.lower() or "[x]" in st_cell.lower():
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
                    "has_desc": col_map["pt_desc_col"] is not None,
                    "validated": validated,
                    "status_str": status_str,
                    "use_bold": use_bold,
                })
                i += 1
            continue

        i += 1

    characters = enrich_entries(entries, doc_title)

    rel_name = filepath.relative_to(MD_DIR).as_posix() if filepath.is_relative_to(MD_DIR) else filepath.name
    return {
        "filename": rel_name,
        "title": doc_title,
        "entries": entries,
        "characters": characters,
    }


def update_md_entry(
    filepath: Path,
    line_index: int,
    new_pt_text: str,
    new_pt_desc: Optional[str],
    validated: bool,
) -> Dict[str, Any]:
    """
    Atualiza diretamente a linha `line_index` no arquivo `.md`, salvando o texto
    PT-BR editado e adicionando/atualizando a coluna `| Status |` com `✅ Validado`
    (ou `⏳ Pendente`).
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not (0 <= line_index < len(lines)):
        raise ValueError(f"Linha inválida: {line_index}")

    h_idx = line_index - 1
    while h_idx >= 0 and lines[h_idx].strip().startswith("|"):
        h_idx -= 1
    header_line_idx = h_idx + 1
    sep_line_idx = header_line_idx + 1

    headers = split_md_row(lines[header_line_idx])
    col_map = classify_table_columns(headers)
    if col_map is None:
        raise ValueError("Não foi possível identificar as colunas da tabela.")

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

    row_cells[pt_col] = text_to_md_cell(new_pt_text, use_backticks=use_backticks)

    if col_map["pt_desc_col"] is not None and new_pt_desc is not None:
        row_cells[col_map["pt_desc_col"]] = text_to_md_cell(new_pt_desc, use_backticks=True)

    status_col = col_map["status_col"]
    row_cells[status_col] = "✅ Validado" if validated else "⏳ Pendente"

    lines[line_index] = join_md_row(row_cells)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    export_embedded_js()

    return {
        "ok": True,
        "line_index": line_index,
        "validated": validated,
        "status_str": row_cells[status_col],
    }


def export_embedded_js() -> None:
    """
    Gera o arquivo `tools/embedded_md_data.js` com todos os arquivos .md já
    parseados para que `validator_ui.html` funcione instantaneamente mesmo se
    aberto direto via `file:///...`.
    """
    build_global_speaker_map()
    files = sorted(MD_DIR.rglob("*.md"), key=lambda p: (p.name, p.as_posix()))
    cats = []
    files_map = {}
    for f in files:
        if f.name.startswith(("00-", "01-")):
            continue
        rel_name = f.relative_to(MD_DIR).as_posix()
        parsed = parse_md_file(f)
        entries = parsed["entries"]
        total = len(entries)
        validated = sum(1 for e in entries if e["validated"])
        cats.append({
            "filename": rel_name,
            "title": parsed["title"] or f.stem,
            "total": total,
            "validated": validated,
        })
        files_map[rel_name] = parsed

    payload = {"categories": cats, "files": files_map}
    js_content = "window.EMBEDDED_MD_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    EMBEDDED_JS_PATH.write_text(js_content, encoding="utf-8")


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
        if parsed.path in ("/", "/index.html"):
            html_bytes = UI_HTML_PATH.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html_bytes)
            return

        if parsed.path == "/embedded_md_data.js":
            if not EMBEDDED_JS_PATH.is_file():
                export_embedded_js()
            js_bytes = EMBEDDED_JS_PATH.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(js_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(js_bytes)
            return

        if parsed.path == "/api/categories":
            cats = list_translation_md_files()
            self._send_json({"categories": cats})
            return

        if parsed.path == "/api/file":
            qs = parse_qs(parsed.query)
            fname = qs.get("name", [""])[0]
            fpath = (MD_DIR / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(MD_DIR.resolve()):
                self._send_json({"error": "Arquivo não encontrado."}, status=404)
                return
            data = parse_md_file(fpath)
            self._send_json(data)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/build":
            try:
                build_script = ROOT_DIR / "tools" / "build_ptbr_rom.py"
                build_bat = ROOT_DIR / "Compilar_ROM_PTBR.bat"
                if build_script.is_file():
                    cmd = [sys.executable, str(build_script)]
                elif build_bat.is_file():
                    cmd = ["cmd.exe", "/c", str(build_bat)]
                else:
                    self._send_json({"ok": False, "error": "Script ou rotina de compilação da ROM não encontrada."}, status=404)
                    return

                p = subprocess.run(
                    cmd,
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                if p.returncode == 0:
                    self._send_json({"ok": True, "output": p.stdout})
                else:
                    self._send_json({"ok": False, "error": p.stderr or p.stdout}, status=500)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
            return

        if parsed.path == "/api/save":
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body)

            fname = payload.get("filename", "")
            line_index = int(payload.get("line_index", -1))
            pt_text = payload.get("pt_text", "")
            pt_desc = payload.get("pt_desc", None)
            validated = bool(payload.get("validated", True))

            fpath = (MD_DIR / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(MD_DIR.resolve()):
                self._send_json({"error": "Arquivo inválido."}, status=400)
                return

            try:
                res = update_md_entry(fpath, line_index, pt_text, pt_desc, validated)
                self._send_json(res)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)


def main() -> int:
    build_global_speaker_map()
    export_embedded_js()
    port = int(os.environ.get("VALIDATOR_PORT", "8765"))
    no_browser = "--no-browser" in sys.argv

    server = ThreadingHTTPServer(("127.0.0.1", port), ValidatorRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 72)
    print(" VALIDADOR DE TRADUÇÃO GBA — SUÍTE DE PROCESSOS E ENGENHARIA")
    print("=" * 72)
    print(f" • Pasta monitorada : {MD_DIR}")
    print(f" • Falantes mapeados: {len(GLOBAL_SCRIPT_SPEAKERS)} scripts/linhas")
    print(f" • Acesse no browser: {url}")
    print("=" * 72)

    if not no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
