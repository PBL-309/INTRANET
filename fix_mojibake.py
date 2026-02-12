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
    'Ã': 'é', 
    'Ã': 'í', 
    'Ã': 'ó', 
    'Ãº': 'ú',
    'Ã': 'ñ', 
    'Ã': 'Ñ',
    'Ã': 'Á', 
    'Ã': 'É', 
    'Ã': 'Í', 
    'Ã': 'Ó', 
    'Ãš': 'Ú',
    'Â¿': '¿',
    'Â¡': '¡',
    'Ã': 'ü',
    'Ã': 'Å', # Sometimes happens
    'Ã': 'Ö',
    'Ã': 'ä',
    'Ã': 'ö',
    # Common double-byte sequences
    'Â°': '°',
    'Ã ': 'à',
    'Ã': 'È',
    # Specific case seen in logs
    'Ã': 'ñ',
    
    # Handle the case where C3 83 etc might appear (Double corrupted)
    # But usually it's just one level deep for what we've seen.
}

for file_path in files_to_fix:
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        try:
            with open(full_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            new_content = content
            count = 0
            for bad, good in replacements.items():
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
