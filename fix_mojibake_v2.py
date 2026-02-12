
import os

files_to_fix = [
    'app/templates/dashboard.html',
    'app/templates/evaluacion.html',
    'app/templates/consultar_evaluaciones.html',
    'app/templates/admin_noticias.html',
    'app/templates/formulario.html',
    'app/templates/login.html'
]

replacements = {
    'Ã¡': 'á', 
    'Ã©': 'é', 
    'Ã\xad': 'í',  # escaping for safety in case of source encoding issues
    'Ã³': 'ó', 
    'Ãº': 'ú',
    'Ã±': 'ñ', 
    'Ã‘': 'Ñ',
    'Ã\x81': 'Á', 
    'Ã‰': 'É', 
    'Ã\x8d': 'Í', 
    'Ã“': 'Ó', 
    'Ãš': 'Ú',
    'Â¿': '¿',
    'Â¡': '¡',
    'Ã¼': 'ü',
}

# Unicode codepoints for the "Mojibake" characters often seen
# ó (C3 B3) -> Ã (C3) + ³ (B3)
# í (C3 AD) -> Ã (C3) + SHY (AD) or similar
# á (C3 A1) -> Ã (C3) + ¡ (A1)
# é (C3 A9) -> Ã (C3) + © (A9)
# ú (C3 BA) -> Ã (C3) + º (BA)
# ñ (C3 B1) -> Ã (C3) + ± (B1)

# Let's use bytes for search/replace to be absolutely sure.
# We are looking for UTF-8 bytes of (Mojibake chars).
# Mojibake string: "Ã³"
# UTF-8 bytes of Mojibake string: C3 83 C2 B3
# Target: "ó"
# UTF-8 bytes of Target: C3 B3

# So we want to replace b'\xc3\x83\xc2\xb3' with b'\xc3\xb3'

byte_replacements = {
    # Lowercase
    b'\xc3\x83\xc2\xa1': b'\xc3\xa1', # á defined as Ã (C3 83) + ¡ (C2 A1)
    b'\xc3\x83\xc2\xa9': b'\xc3\xa9', # é
    b'\xc3\x83\xc2\xad': b'\xc3\xad', # í  (Ã + soft hyphen?) No, A1 is ¡. AD is SHY.
    # Wait.
    # If the file has 'Ã' (C3 83) and '³' (C2 B3).
    # Then we replace that sequence.
    
    # Let's trust the string replacement but careful with the source code.
    # We will build the bad strings dynamically to avoid source encoding issues.
}

def get_bad_string(utf8_byte_seq):
    # This simulates what happened: 
    # 1. We had a byte sequence (e.g. C3 B3 for ó)
    # 2. It was interpreted as latin-1 chars: Ã (C3) and ³ (B3)
    # 3. Those chars were saved as UTF-8: C3 83 (Ã) and C2 B3 (³)
    
    # So we want to find the utf-8 string corresponding to "C3 83 C2 B3"
    # And replace it with "ó"
    
    # Input: target char e.g. 'ó'
    pass

target_chars = 'áéíóúñÁÉÍÓÚÑü¿¡'
replacements = {}

for char in target_chars:
    # 1. Get utf-8 bytes of the GOOD char
    good_bytes = char.encode('utf-8')
    
    # 2. Interpret those bytes as Latin-1 string
    # This creates the "Mojibake String" that we see on screen (e.g. Ã³)
    try:
        bad_string = good_bytes.decode('latin-1') 
    except:
        # If latin-1 decodes fails, try cp1252
        bad_string = good_bytes.decode('cp1252')
        
    replacements[bad_string] = char

# Add special cases if needed
replacements['Ã­'] = 'í' # Force this one as it's common and tricky (SHY)

for file_path in files_to_fix:
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            new_content = content
            count = 0
            
            # Sort by length descending to replace longest corruptions first if any overlap
            for bad, good in sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True):
                if bad in new_content:
                    c = new_content.count(bad)
                    count += c
                    new_content = new_content.replace(bad, good)
            
            if count > 0:
                print(f"Fixed {count} corruption instances in {file_path}")
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            else:
                print(f"No corruptions found in {file_path}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
