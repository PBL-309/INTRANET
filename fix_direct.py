# -*- coding: utf-8 -*-
import os

files_to_fix = [
    r'app\templates\evaluacion.html',
    r'app\templates\admin_noticias.html',
    r'app\templates\formulario.html',
    r'app\templates\consultar_evaluaciones.html',
    r'app\templates\dashboard.html',
    r'app\templates\login.html',
]

# Build replacement map dynamically
# The corruption pattern: correct UTF-8 bytes were read as if they were Latin-1/CP1252,
# then re-encoded as UTF-8. So we reverse this.
target_chars = 'áéíóúñÁÉÍÓÚÑüÜ¿¡'
replacements = {}
for ch in target_chars:
    utf8_bytes = ch.encode('utf-8')  # e.g. ó -> b'\xc3\xb3'
    # When interpreted as cp1252: each byte becomes a char
    try:
        mojibake = utf8_bytes.decode('cp1252')  # e.g. b'\xc3\xb3' -> 'Ã³'
    except Exception:
        continue

    # Now that mojibake string, when saved as UTF-8, produces new bytes
    mojibake_utf8 = mojibake.encode('utf-8')  # e.g. 'Ã³' -> b'\xc3\x83\xc2\xb3'

    # But in some files the FIRST corruption already happened and was partially fixed.
    # Let's also handle the pattern where only the 2-byte sequence remains garbled.
    # Pattern seen in grep: ñ³ for ó, ñ± for ñ, ñ© for é, ñ­ for í, ñº for ú
    # This means: ñ (U+00F1) followed by another char.
    # ó = C3 B3 -> was read as: C3->ñ? No...
    # Actually looking at the grep output:  ñ³ for ó means the file literally has U+00F1 U+00B3
    # That's: ñ = \xc3\xb1 and ³ = \xc2\xb3 in UTF-8
    # So the file bytes for "ñ³" are: c3 b1 c2 b3
    # But ó in UTF-8 is c3 b3.
    # Hmm, that doesn't map cleanly.
    # 
    # Let me re-examine. The grep says the file contains the STRING "ñ³" where "ó" should be.
    # So in the file, the characters are literally: ñ (U+00F1) and ³ (U+00B3).
    # Similarly: ñ± for ñ (the correct char), meaning: U+00F1 U+00B1 -> should be U+00F1
    # And: ñ© for é -> U+00F1 U+00A9 -> should be U+00E9
    # And: ñ­ for í -> U+00F1 U+00AD -> should be U+00ED
    # And: ñº for ú -> U+00F1 U+00BA -> should be U+00FA
    pass

# OK so the pattern is clear from the grep results. Let me just hardcode the exact replacements:
direct_replacements = {
    'ñ³': 'ó',
    'ñ±': 'ñ',
    'ñ©': 'é',
    'ñ­': 'í',
    'ñº': 'ú',
    'ñ"': 'Ó',  # uppercase
    'ñ‰': 'É',  # uppercase  
    'ñš': 'Ú',  # uppercase
}

base = os.getcwd()

for file_path in files_to_fix:
    full_path = os.path.join(base, file_path)
    if not os.path.exists(full_path):
        print(f"Not found: {file_path}")
        continue
    
    with open(full_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    new_content = content
    total = 0
    for bad, good in direct_replacements.items():
        c = new_content.count(bad)
        if c > 0:
            total += c
            new_content = new_content.replace(bad, good)
    
    if total > 0:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {total} corruptions in {file_path}")
    else:
        print(f"Clean: {file_path}")
