import struct
from pathlib import Path

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
md_path = Path(__file__).resolve().parent.parent / "ARQUIVOS md" / "00_Interface_Menus_Selecao_e_Sistema.md"
rom = rom_path.read_bytes()

# Build map of all 32-bit pointers pointing into 0x0808E000..0x08095000
ptr_map = {}
for off in range(0, len(rom) - 4, 4):
    val = struct.unpack_from('<I', rom, off)[0]
    if 0x0808E000 <= val < 0x08095000:
        if val not in ptr_map:
            ptr_map[val] = []
        ptr_map[val].append(0x08000000 + off)

def decode_sjis_at(off):
    chars = []
    p = off
    while p + 1 < len(rom):
        w = struct.unpack_from('>H', rom, p)[0]
        p += 2
        if w == 0: break
        elif 0x8260 <= w <= 0x8279: chars.append(chr(ord('A') + w - 0x8260))
        elif 0x8281 <= w <= 0x829A: chars.append(chr(ord('a') + w - 0x8281))
        elif 0x824F <= w <= 0x8258: chars.append(chr(ord('0') + w - 0x824F))
        elif w == 0x8140: chars.append(' ')
        elif w == 0x8143: chars.append(',')
        elif w == 0x8144: chars.append('.')
        elif w == 0x8148: chars.append('?')
        elif w == 0x8149: chars.append('!')
        elif w == 0x8166: chars.append("'")
        elif w == 0x8168: chars.append('"')
        elif w == 0x8163: chars.append('…')
        elif w == 0x817C: chars.append('-')
        elif w == 0x815E: chars.append('/')
        elif w == 0x819A: chars.append('☆')
        elif w == 0x81F4: chars.append('♪')
        else: return None
    s = ''.join(chars).strip()
    return s if len(s) > 0 else None

UI_TRANSLATIONS = {
    "Back  OK": "Voltar  OK",
    "No": "Não",
    "Yes": "Sim",
    "Is this okay?": "Tudo bem assim?",
    "Arno": "Arno",
    "Dinah": "Dinah",
    "Loki": "Loki",
    "EXeLD": "EXeLD",
    "Aera": "Aera",
    "Edgar": "Edgar",
    "Empty": "Vazio",
    "wore off": "acabou",
    "Guard": "Defesa",
    "Level Up!": "Level Up!",
    "Allocate Ability Points": "Distribuir Pontos de Habilidade",
    "Is it okay to leave Ability Points": "Tudo bem deixar Pontos de Habilidade",
    "unallocated?": "não distribuídos?",
    "Items Gained": "Itens Obtidos",
    "Learned": "Aprendeu",
    "Learned Additional Magic!": "Aprendeu Magia Adicional!",
    "Learned New Magic!": "Aprendeu Nova Magia!",
    "Would you like to save?": "Gostaria de salvar?",
    "Exit": "Sair",
    "Save": "Salvar",
    "Rabbit Rampage": "Rabbit Rampage",
    "Gabriel Mode": "Gabriel Mode",
    "Summon Night 2": "Summon Night 2",
    "Cameo Battle": "Cameo Battle",
    "GUNVALD vs. Borgrim": "GUNVALD vs. Borgrim",
    "Boss Rush": "Boss Rush",
    "Rival Rush": "Rival Rush",
    "Sound Test": "Sound Test",
    "VOICE": "VOZ",
    "BGM": "MÚSICA",
    "Help": "Ajuda",
    "Best Time": "Melhor Tempo",
    "Change Equipment": "Mudar Equipamento",
    "Start": "Iniciar",
    "Support": "Suporte",
    "Equipment": "Equipamento",
    "Finished saving data.": "Dados salvos com sucesso.",
    "Finished loading data.": "Dados carregados com sucesso.",
    "Failed to save data.": "Falha ao salvar dados.",
    "Failed to load data.": "Falha ao carregar dados.",
    "Return to Item Menu.": "Retornar ao Menu de Itens.",
    "This data can't be used.": "Estes dados não podem ser usados.",
    "Fishing Points": "Pontos de Pesca",
    "Money": "Dinheiro",
    "Stored Weapons": "Armas Guardadas",
    "Bestiary": "Bestiário",
    "Techniques": "Técnicas",
    "Craftknight Rank": "Rank de Craftknight",
    "Create": "Criar",
    "Sell": "Vender",
    "Buy": "Comprar",
    "Weapon": "Arma",
    "Item": "Item",
    "Quest": "Missão",
    "Wpn Mat": "Mat Arma",
    "Equip": "Equipar",
    "Special": "Especial",
    "Itm Mat": "Mat Item",
    "Recover": "Recuperar",
    "You don't have enough money.": "Você não tem dinheiro suficiente.",
    "You don't have enough points.": "Você não tem pontos suficientes.",
    "You can't carry any more.": "Você não pode carregar mais nada.",
    "There's nothing left to sell.": "Não há mais nada para vender.",
    "There is nothing you can sell.": "Não há nada que você possa vender.",
    "You don't have enough materials": "Você não tem materiais suficientes",
    "How many ?": "Quantos?",
    "Is it okay to sell?": "Tudo bem vender?",
    "Legend": "Lenda",
    "Hero": "Herói",
    "Master": "Master",
    "Famous": "Famoso",
    "Pro": "Profissional",
    "Amateur": "Amador",
    "Apprentice": "Aprendiz",
    "Status": "Status",
    "Magic": "Magia",
    "Options": "Opções",
    "Quest Items": "Itens Chave",
    "Drill Type": "Broca",
    "Knuckle Type": "Soqueira",
    "Spear Type": "Lança",
    "Axe Type": "Machado",
    "Sword Type": "Espada",
    "You don't have any items.": "Você não tem nenhum item.",
    "You don't have any weapons.": "Você não tem nenhuma arma.",
    "You can't use any magic.": "Você não pode usar nenhuma magia.",
    "You can't change equipment.": "Você não pode mudar equipamento.",
    "You have no techniques.": "Você não tem técnicas.",
    "You have no Quest Items.": "Você não tem Itens Chave.",
    "Discard how many?": "Descartar quantos?",
    "Is it okay to use?": "Tudo bem usar?",
    "Is it okay to discard?": "Tudo bem descartar?",
    "Are you sure?": "Tem certeza?",
    "Adjust Color": "Ajustar Cor",
    "Adjust Sound": "Ajustar Som",
    "Field": "Campo",
    "Press A Button to reset to default": "Pressione Botão A para padrão",
    "Adjust the brightness": "Ajustar o brilho",
    "Select Menu Screen Color Mode": "Selecionar modo de cor do Menu",
    "Select Basic Movement": "Selecionar movimento básico",
    "Walk or Run": "Andar ou Correr",
    "Adjust the Voice volume": "Ajustar volume da Voz",
    "Adjust the Sound Effects volume": "Ajustar volume dos Efeitos",
    "Adjust the BGM volume": "Ajustar volume da Música",
    "Walk  Run": "Andar  Correr",
    "received!": "recebido!",
    "paid.": "pago.",
    "Unequip": "Desequipar",
    "Item needs repairs before equipping.": "O item precisa de reparos antes.",
    "Quest Item": "Item Chave",
    "Discard": "Descartar",
    "Use": "Usar",
    "Battle": "Batalha",
    "Any": "Qualquer",
    "Attack": "Ataque",
    "The item has been used.": "O item foi utilizado.",
    "You have no weapons.": "Você não tem armas.",
    "You can't discard this weapon.": "Você não pode descartar esta arma.",
    "Weapon must be repaired first.": "A arma deve ser reparada antes.",
    "Return to the Item List.": "Retornar à lista de itens.",
}

lines_out = [
    "# 🖥️ Interface, Menus, Criação de Personagem e Sistema",
    "",
    "> [!NOTE]",
    "> Tabelas estáticas de interface e sistema da ROM (endereços 0x0808E000 .. 0x08095000).",
    "",
    "| Endereço ROM | Texto Original (Inglês) | Tradução PT-BR | Status |",
    "| :--- | :--- | :--- | :---: |",
]

added = 0
for target_addr, refs in sorted(ptr_map.items()):
    off = target_addr - 0x08000000
    t = decode_sjis_at(off)
    if t and len(t) >= 2 and not t.startswith("A B C"):
        pt = UI_TRANSLATIONS.get(t, "")
        status = "✅ Validado" if pt else "⏳ Pendente"
        lines_out.append(f"| `0x{target_addr:08X}` | {t} | {pt} | {status} |")
        added += 1

md_path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
print(f"Gerado {md_path.name} com {added} entradas de interface!")
