import os

files_to_fix = [
    'app/templates/dashboard.html',
    'app/templates/evaluacion.html',
    'app/templates/consultar_evaluaciones.html',
    'app/templates/admin_noticias.html',
    'app/templates/formulario.html',
    'app/templates/login.html'
]

for file_path in files_to_fix:
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        try:
            # Read with utf-8-sig to automatically handle (and remove) BOM if present
            with open(full_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            if 'Ã' in content:
                print(f"Fixing {file_path}...")
                
                # Check for any other non-latin1 chars that might block the fix
                to_fix = content
                
                # Try restoration
                try:
                    # Windows-1252 is the usual culprit for these corruptions on Windows
                    fixed_content = to_fix.encode('cp1252').decode('utf-8')
                except UnicodeEncodeError:
                     # Fallback to latin1
                    fixed_content = to_fix.encode('latin1').decode('utf-8')
                except UnicodeDecodeError:
                    print(f"Skipping {file_path}: restoration failed.")
                    continue

                # Write back as clean UTF-8 (no BOM preferred, but standard utf-8)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"Fixed {file_path}")
            else:
                print(f"No fix needed for {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
