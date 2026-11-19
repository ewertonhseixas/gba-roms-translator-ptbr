"""Apply the localized battle guide, scene labels and dialogue portraits."""

import struct

from build_expanded_dialogues import compress_lz10
from patch_frontend import INFORMATION, Sprites, TextMasks, box, file_ids, information_header


PLATES = {
    '0008': 'Sol', '0009': 'Kiel', '0010': 'Cassis', '0011': 'Claret',
    '0100': 'Katsuya', '0101': 'Emi', '0102': 'Reid', '0103': 'Gazel',
    '0104': 'Edos', '0105': 'Riple', '0106': 'Jinga', '0107': 'Monaty',
    '0108': 'Lambda', '0113': 'Suon', '0115': 'Akane', '0116': 'Mimoza',
    '0121': 'Keina', '0200': 'Alba', '0201': 'Fizz', '0202': 'Rami',
    '0203': 'Ancião', '0205': 'Líder', '0302': 'Kanon', '0308': 'Soldado',
    '0324': 'Homem de preto',
}

PLACES = {
    1: 'Entrada', 2: 'Cozinha', 3: 'Salão', 4: 'Jardim',
    5: 'Quarto infantil', 6: 'Quarto do Reid', 7: 'Quarto do Gazel',
    8: 'Sótão', 9: 'Quarto 1', 10: 'Quarto 2', 11: 'Quarto 3',
    12: 'Quarto 4', 13: 'Quarto 5', 14: 'Seu quarto', 15: 'Praça da Cidade',
    16: 'Rua Comercial', 17: 'Distrito Comercial', 18: 'Bairro Sul',
    19: 'Bairro Norte', 20: 'Portão da Cidade', 21: 'Bairro Nobre',
    22: 'Distrito Industrial', 23: 'Rio Aruk', 24: 'Planície de Bernett',
    25: 'Floresta de Garef', 26: 'Ruínas do Ritual', 27: 'Ermo',
    28: 'Estrada', 29: 'Rochedo de Maril', 30: 'Ferrovia das Feras',
    31: 'Pico do Dragão da Espada', 32: 'Caverna de Romdo',
    33: 'Planalto de Spinel', 34: 'Vale dos Demônios', 35: 'Local do Ritual',
    36: 'Altar de Invocação', 37: 'Ruínas Mecânicas', 38: 'Pântano da Morte',
    39: 'Botica Akanabe', 40: 'Salão de Audiências', 41: 'Estalagem Espada da Acusação',
    42: 'Floresta da Névoa', 44: 'Circo', 45: 'Atrás do Circo',
    49: 'Pátio da Mansão Maan', 51: 'Dimensão Sombria',
}
GUIDE = (
    ('Batalhas', 34, (21, 71, 236, 121), (152, 63, 55), (248, 232, 201)),
    ('A ou toque na tela para avançar', 11, (12, 160, 244, 175), (249, 231, 195), (72, 46, 26)),
    ('B ou Sair para cancelar', 11, (12, 176, 244, 190), (249, 231, 195), (72, 46, 26)),
)
FLOW = (
    ('Início', 12, (12, 7, 94, 21), (60, 42, 34), None),
    ('Siga estas etapas', 12, (102, 5, 251, 22), (60, 42, 34), None),
    ('Formação', 12, (13, 44, 94, 63), (60, 42, 34), None),
    ('Prepare a equipe', 12, (114, 45, 251, 63), (42, 67, 178), None),
    ('Batalha', 12, (13, 81, 94, 111), (60, 42, 34), None),
    ('Enfrente o inimigo', 12, (114, 87, 251, 109), (42, 67, 178), None),
    ('Resultado', 12, (13, 137, 94, 151), (60, 42, 34), None),
    ('Veja o resultado', 12, (114, 134, 251, 153), (42, 67, 178), None),
    ('1. Etapas da batalha', 14, (3, 160, 176, 191), (245, 226, 192), (49, 37, 31)),
)


def paint_guide(sprite, masks, entries, cover):
    pixels = sprite.render(1)
    palette = sprite.palette

    def color(rgb):
        return min(range(1, 256), key=lambda i: sum(
            (a - b) ** 2 for a, b in zip(rgb, palette[i * 3:i * 3 + 3])
        ))

    for label, size, bounds, fill, outline in entries:
        area = box(*bounds)
        x0, y0, x1, y1 = bounds
        background = pixels[x0, y0]
        if cover and label == 'Batalhas':
            area = box(15, 57, 243, 124)
            background = color((168, 114, 65))
        ink = masks.draw(label, size, True, box(x0 + 1, y0 + 1, x1 - 1, y1 - 1),
                         color(fill), (color(outline),) if outline else ())
        sprite.paint(1, area, ink, background)


def apply(rom):
    ids = file_ids(rom)
    fat = struct.unpack_from('<I', rom, 0x48)[0]
    requests = [('Sair', 8, True)]
    requests += [(label, size, True) for label in PLACES.values() for size in (16, 14, 12, 10, 8)]
    requests += [(name, size, True) for name in PLATES.values() for size in (16, 14, 12, 10, 8)]
    requests += [(name, size, True) for name, size, *_ in GUIDE + FLOW]
    masks = TextMasks('Arial Narrow')
    masks.load(list(dict.fromkeys(requests)))

    def update(name, edit):
        path = f'{name}.narc'
        item = ids[path]
        start, end = struct.unpack_from('<II', rom, fat + 8 * item)
        sprite = Sprites(rom[start:end])
        edit(sprite)
        payload = compress_lz10(bytes(sprite.data))
        rom.extend(bytes(-len(rom) % 4))
        start = len(rom)
        rom.extend(payload)
        struct.pack_into('<II', rom, fat + 8 * item, start, len(rom))

    def fit_label(label, bounds, fill, stroke):
        for size in (16, 14, 12, 10, 8):
            try:
                return masks.draw(label, size, True, bounds, fill, stroke)
            except AssertionError:
                continue
        raise ValueError(f'Texto fora da área gráfica: {label}')

    def place(sprite, label):
        cell = next(i for i, c in enumerate(sprite.cells) if c)
        width, height, *_ = sprite.layout(cell)
        bounds = box(2, 1, width - 2, height - 1)
        ink = fit_label(label, bounds, 15, (1, 1))
        sprite.paint(cell, box(0, 0, width, height), ink)

    def exit_button(sprite):
        for i in range(1, 5):
            region = box(7, 5, 25, 18)
            ink = masks.draw('Sair', 8, True, region, 5)
            sprite.paint(i, region, ink, background=6)

    def plate(sprite, id_, label):
        _, _, x0, y0 = sprite.layout(1)
        first, stop = {
            '0008': (1, 5), '0009': (6, 12), '0010': (1, 7),
            '0011': (3, 13), '0105': (1, 8), '0106': (1, 7),
            '0107': (0, 8), '0108': (6, 12), '0121': (1, 7),
        }.get(id_, (0, None))
        objects = []
        for obj in sorted(sprite.cells[1], key=lambda obj: obj['tile']):
            if obj['tile'] < first:
                continue
            if stop is not None and obj['tile'] >= stop or obj['y'] < 60:
                break
            objects.append(obj)
        assert objects and objects[0]['tile'] == first
        left = min(o['x'] for o in objects)
        width = max(o['x'] + o['w'] for o in objects) - left
        x, y = left - x0, min(o['y'] for o in objects) - y0
        tile_bytes = (1 << sprite.shift) * 32
        target = set()
        for obj in objects:
            start = sprite.start + obj['tile'] * tile_bytes
            target.update(range(start, start + obj['w'] * obj['h']))
        bounds = box(x + 1, y + 1, x + width - 1, y + 23)
        ink = fit_label(label, bounds, 239, (225, 225))
        for px, py, offset, shift, bank in sprite.pixels(1):
            if offset in target:
                assert shift == bank == 0
                sprite.data[offset] = ink.get((px, py), 0)

    for id_, label in PLACES.items():
        update(f'chaptersub/ev00_{id_:03d}', lambda sprite: place(sprite, label))
    headers = TextMasks()
    headers.load([(INFORMATION, 7, True)])
    update('system/ev0010', lambda sprite: information_header(sprite, headers))
    for id_, label in PLATES.items():
        update(f'evface/ec{id_}', lambda sprite: plate(sprite, id_, label))
    update('help/help0_sp_sub01', lambda sprite: paint_guide(sprite, masks, GUIDE, True))
    update('help/help0_sp_main0101', lambda sprite: paint_guide(sprite, masks, FLOW, False))
    update('help/help0_sp_main_sys', exit_button)
