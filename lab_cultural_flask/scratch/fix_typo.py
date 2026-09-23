import os

file_path = r'c:\Users\Miguel Oliveira\Documents\GitHub\TrabalhoFinal\Copia\lab_cultural_flask\app\controllers\frontoffice.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace "if not libro:" with "if not livro:"
# Be careful with potential partial matches, though here it's pretty safe
new_content = content.replace('if not libro:', 'if not livro:')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Replacement complete.")
