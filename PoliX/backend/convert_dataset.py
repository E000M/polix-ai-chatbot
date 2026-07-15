# convert_dataset.py
import json
import re

# Lexo dataset-in tuaj (nëse është në një skedar)
# Ose kopjo-paste përmbajtjen në një variabël
dataset_text = """Pyetja: Si kontaktohet sekretaria e Universitetit POLIS?  
Përgjigjja: Me email te sekretaria: info@universitetipolis.edu.al ose contact@universitetipolis.edu.al dhe në telefon +355 4 240 74 20 / 240 74 21. :contentReference[oaicite:1]{index=1}

... (vazhdo me të gjitha pyetjet)"""

# Funksioni për të pastruar tekstin
def clean_text(text):
    # Hiq referencat e citimeve
    text = re.sub(r':contentReference\[.*?\]\{index=\d+\}', '', text)
    # Hiq "Pyetja:" dhe "Përgjigjja:"
    text = re.sub(r'Pyetja:\s*', '', text)
    text = re.sub(r'Përgjigjja:\s*', '', text)
    # Hiq linjat e zbrazëta të shumta
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

# Nëse dataset-i është në një skedar JSON, përdorni këtë:
def convert_json_to_txt(json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("INFORMACION I PLOTË PËR UNIVERSITETIN POLIS\n")
        f.write("="*50 + "\n\n")
        
        # Grupimi i pyetjeve sipas kategorive
        categories = {
            "KONTAKTE DHE LOKACION": [],
            "PROGRAMET E STUDIMIT": [],
            "APLIKIMI DHE PRANIMI": [],
            "BURSAT DHE FINANCIMI": [],
            "AKREDITIMI DHE NJOHJA": [],
            "SHËRBIMET PËR STUDENTËT": []
        }
        
        # Vendosni pyetjet në kategoritë e duhura (manualisht ose me analizë)
        # Për thjeshtësi, do t'i shkruajmë të gjitha njëra pas tjetrës
        f.write("PYETJE DHE PËRGJIGJE TË SHQESËVE TË ZAKONSHME\n\n")
        
        for item in data:
            question = clean_text(item.get("question", ""))
            answer = clean_text(item.get("answer", ""))
            
            if question and answer:
                f.write(f"Q: {question}\n")
                f.write(f"A: {answer}\n\n")
    
    print(f"U krijua {output_file} me sukses!")

# Nëse keni skedarin dataset.json:
# convert_json_to_txt('dataset.json', 'polis_data.txt')

# Ose, për dataset-in tuaj të kopjuar:
lines = dataset_text.strip().split('\n\n')
with open('polis_data.txt', 'w', encoding='utf-8') as f:
    f.write("INFORMACION KOMPLET PËR UNIVERSITETIN POLIS\n")
    f.write("=" * 60 + "\n\n")
    
    f.write("KY ESHTË NJË BURIM INFORMACIONI PËR UNIVERSITETIN POLIS NË TIRANË.\n\n")
    
    f.write("SEKSIONI 1: KONTAKTE DHE LOKACION\n")
    f.write("-" * 40 + "\n")
    
    for line in lines:
        if "Pyetja:" in line and "Përgjigjja:" in line:
            # Ndarja e pyetjes dhe përgjigjes
            parts = line.split('Përgjigjja:')
            if len(parts) == 2:
                question = parts[0].replace('Pyetja:', '').strip()
                answer = parts[1].strip()
                
                # Pastro referencat
                answer = re.sub(r':contentReference\[.*?\]\{index=\d+\}', '', answer)
                
                # Shkruaj në një format më të lexueshëm
                f.write(f"• {question}\n")
                f.write(f"  {answer}\n\n")

print("Skedari polis_data.txt u krijua me sukses!")