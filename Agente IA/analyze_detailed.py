#!/usr/bin/env python3
import re

def analyze_syntax_detailed(filename):
    """Detailed syntax analysis to find exact missing braces/parentheses"""
    
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
    
    # Stack to track open braces, parentheses
    stack = []
    
    print("=== Detailed Syntax Analysis ===")
    
    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()
        
        # Skip comments
        if line.startswith('//') or line.startswith('/*') or line.startswith('*'):
            continue
        
        # Process each character
        for char_pos, char in enumerate(original_line):
            if char in '({[':
                stack.append((char, line_num, char_pos, original_line.strip()[:50]))
            elif char in ')}]':
                if not stack:
                    print(f"ERROR: Unexpected closing '{char}' at line {line_num}:{char_pos}")
                    continue
                
                opening = stack.pop()
                expected = {'(': ')', '{': '}', '[': ']'}
                
                if expected[opening[0]] != char:
                    print(f"ERROR: Mismatched brace. Expected '{expected[opening[0]]}' but found '{char}' at line {line_num}:{char_pos}")
                    print(f"       Opening was '{opening[0]}' at line {opening[1]}:{opening[2]} - {opening[3]}")
    
    print(f"\n=== Unclosed Elements ({len(stack)} total) ===")
    for opening in stack:
        char, line_num, char_pos, line_preview = opening
        closing = {'(': ')', '{': '}', '[': ']'}[char]
        print(f"Missing '{closing}' for '{char}' opened at line {line_num:4d}:{char_pos:3d} - {line_preview}")
    
    return stack

if __name__ == "__main__":
    missing = analyze_syntax_detailed('gestao_visitas/templates/mapa_progresso.html')
    
    if missing:
        print(f"\n=== Solution ===")
        print("Add these closing characters at the end of script block 2:")
        for opening in reversed(missing):
            char = opening[0]
            closing = {'(': ')', '{': '}', '[': ']'}[char]
            print(f"  {closing}  // Close {char} from line {opening[1]}")