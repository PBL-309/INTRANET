
import os

files_to_fix = [
    'app/templates/dashboard.html',
    'app/templates/evaluacion.html',
    'app/templates/consultar_evaluaciones.html',
    'app/templates/admin_noticias.html',
    'app/templates/formulario.html',
    'app/templates/login.html'
]

# Map of (Mojibake_Bytes, Correct_Bytes)
# Generated based on "UTF-8 bytes interpreted as CP1252, then saved as UTF-8"
mappings = [
    # Lowercase vowels + n
    (b'\xc3\x83\xc2\xa1', b'\xc3\xa1'), # á
    (b'\xc3\x83\xc2\xa9', b'\xc3\xa9'), # é
    (b'\xc3\x83\xc2\xad', b'\xc3\xad'), # í
    (b'\xc3\x83\xc2\xb3', b'\xc3\xb3'), # ó
    (b'\xc3\x83\xc2\xba', b'\xc3\xba'), # ú
    (b'\xc3\x83\xc2\xb1', b'\xc3\xb1'), # ñ
    
    # Uppercase
    (b'\xc3\x83\xc2\x81', b'\xc3\x81'), # Á
    (b'\xc3\x83\xe2\x80\xb0', b'\xc3\x89'), # É
    (b'\xc3\x83\xc2\x8d', b'\xc3\x8d'), # Í
    (b'\xc3\x83\xe2\x80\x9c', b'\xc3\x93'), # Ó
    (b'\xc3\x83\xc5\xa1', b'\xc3\x9a'), # Ú
    (b'\xc3\x83\xe2\x80\x98', b'\xc3\x91'), # Ñ

    # Symbols
    (b'\xc3\x82\xc2\xbf', b'\xc2\xbf'), # ¿
    (b'\xc3\x82\xc2\xa1', b'\xc2\xa1'), # ¡
]

for file_path in files_to_fix:
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        try:
            with open(full_path, 'rb') as f:
                content = f.read()

            new_content = content
            count = 0
            
            for bad, good in mappings:
                if bad in new_content:
                    c = new_content.count(bad)
                    count += c
                    new_content = new_content.replace(bad, good)
            
            if count > 0:
                print(f"Fixed {count} instances in {file_path}")
                with open(full_path, 'wb') as f:
                    f.write(new_content)
            else:
                print(f"Clean: {file_path}")

        except Exception as e:
            print(f"Error {file_path}: {e}")
