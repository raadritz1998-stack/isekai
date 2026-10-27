import os
import re

def scrub_text(text):
    # Dictionaries of modern words and their fantasy equivalents
    replacements = {
        r'\bmetrics\b': 'measurements',
        r'\bmetric\b': 'measurement',
        r'\bhypothesis\b': 'theory',
        r'\bhypotheses\b': 'theories',
        r'\bresearch\b': 'studies',
        r'\balgorithm\b': 'pattern',
        r'\balgorithms\b': 'patterns',
        r'\bvariable\b': 'factor',
        r'\bvariables\b': 'factors',
        r'\bdata stream\b': 'flow of information',
        r'\bdata streams\b': 'flows of information',
        r'\bdata extraction\b': 'knowledge gathering',
        r'\bdata\b': 'knowledge',
        r'\bdatabase\b': 'archive',
        r'\bdatabases\b': 'archives',
        r'\bgeometric proofs\b': 'arcane geometries',
        r'\bgeometric proofs\b': 'arcane geometries',
        r'\bgeometric proof\b': 'arcane geometry',
        r'\bgeometric\b': 'runic',
        r'\bsynthetic network\b': 'artificial web',
        r'\bsynthetic networks\b': 'artificial webs',
        r'\bsynthetic\b': 'artificial',
        r'\bsub-routine\b': 'thought-thread',
        r'\bsub-routines\b': 'thought-threads',
        r'\bsubroutine\b': 'thought-thread',
        r'\bsubroutines\b': 'thought-threads',
        r'\bstructural blueprint\b': 'foundational design',
        r'\bblueprint\b': 'design',
        r'\bwavelengths\b': 'frequencies of magic',
        r'\bwavelength\b': 'frequency of magic',
        r'\btelemetry\b': 'scrying focus',
        r'\bbandwidth\b': 'capacity',
        r'\binterface\b': 'connection',
        r'\bsystemic\b': 'inherent',
        r'\bparameter\b': 'boundary',
        r'\bparameters\b': 'boundaries',
        r'\bprotocols\b': 'directives',
        r'\bprotocol\b': 'directive',
        r'\bprocessing\b': 'analyzing',
        r'\bsensor\b': 'ward',
        r'\bsensors\b': 'wards',
        r'\bsensory network\b': 'warding web',
        r'\banalytical\b': 'calculating',
        r'\bextrapolated\b': 'deduced',
        r'\boperational structure\b': 'command hierarchy',
        r'\bsystemic hesitation\b': 'widespread hesitation',
        r'\bpsychological distress\b': 'mental strain',
        r'\bfrequencies\b': 'resonances',
        r'\bfrequency\b': 'resonance',
        r'\bmagical kinetic wave\b': 'wave of kinetic force'
    }
    
    for pattern, replacement in replacements.items():
        # Case insensitive replacement preserving original capitalization if possible (simplistic)
        # Using a function to preserve case of the first letter
        def match_case(m):
            word = m.group(0)
            if word.istitle():
                return replacement.capitalize()
            elif word.isupper():
                return replacement.upper()
            return replacement
            
        text = re.sub(pattern, match_case, text, flags=re.IGNORECASE)
        
    return text

def process_volume(vol_dir):
    chapters_dir = os.path.join(vol_dir, "chapters")
    if not os.path.exists(chapters_dir):
        return
        
    for filename in os.listdir(chapters_dir):
        if not filename.endswith(".md"):
            continue
            
        filepath = os.path.join(chapters_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = scrub_text(content)
        
        if content != new_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Scrubbed modern terms from {filepath}")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY_DIR = os.path.join(ROOT_DIR, "a_god_in_the_garden")

if __name__ == "__main__":
    import sys
    target_vols = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            v_num = int(arg) if arg.isdigit() else arg
            target_vols.append(f"volume_{int(v_num):02d}")
    else:
        target_vols = [f"volume_{i:02d}" for i in range(1, 7)]

    for v in target_vols:
        v_path = os.path.join(STORY_DIR, v)
        if os.path.exists(v_path):
            process_volume(v_path)
    print("Done scrubbing.")
