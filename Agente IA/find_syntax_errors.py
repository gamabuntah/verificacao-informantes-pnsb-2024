#!/usr/bin/env python3
import re

def find_syntax_errors(filename):
    """Find exact locations of syntax errors in JavaScript"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract script block 2 (where the error is)
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, content, re.DOTALL)
    
    if len(scripts) < 2:
        print("Not enough script blocks found")
        return
    
    script = scripts[1]  # Script block 2
    lines = script.split('\n')
    
    brace_count = 0
    paren_count = 0
    bracket_count = 0
    
    print("=== Tracking Braces and Parentheses ===")
    
    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()
        
        # Skip comments
        if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            continue
        
        # Count changes
        brace_change = line.count('{') - line.count('}')
        paren_change = line.count('(') - line.count(')')
        bracket_change = line.count('[') - line.count(']')
        
        brace_count += brace_change
        paren_count += paren_change
        bracket_count += bracket_change
        
        # Report lines with significant changes or when count goes negative
        if (brace_change != 0 or paren_change != 0 or bracket_change != 0 or 
            brace_count < 0 or paren_count < 0 or bracket_count < 0):
            print(f"Line {line_num:4d}: B={brace_count:3d} P={paren_count:3d} Br={bracket_count:3d} | {original_line.rstrip()}")
    
    print(f"\nFinal counts: Braces={brace_count}, Parens={paren_count}, Brackets={bracket_count}")
    
    # Now let's find the last few lines to see where the issue is
    print("\n=== Last 20 lines of script block 2 ===")
    for i, line in enumerate(lines[-20:], len(lines)-19):
        print(f"Line {i:4d}: {line.rstrip()}")

if __name__ == "__main__":
    find_syntax_errors('gestao_visitas/templates/mapa_progresso.html')