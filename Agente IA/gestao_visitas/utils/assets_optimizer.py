"""
Otimizador de Assets para PNSB 2024
Minifica CSS, JS e otimiza imagens automaticamente
"""

import os
import re
import json
import gzip
from pathlib import Path
from typing import List, Dict, Any
import hashlib

class AssetsOptimizer:
    """Otimizador de assets estáticos"""
    
    def __init__(self, static_folder: str):
        self.static_folder = Path(static_folder)
        self.optimized_folder = self.static_folder / 'optimized'
        self.optimized_folder.mkdir(exist_ok=True)
        
    def minify_css(self, css_content: str) -> str:
        """Minifica CSS removendo espaços, comentários e quebras"""
        # Remove comentários
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove espaços extras e quebras de linha
        css_content = re.sub(r'\s+', ' ', css_content)
        css_content = re.sub(r';\s*}', '}', css_content)
        css_content = re.sub(r'{\s+', '{', css_content)
        css_content = re.sub(r'}\s+', '}', css_content)
        css_content = re.sub(r':\s+', ':', css_content)
        css_content = re.sub(r';\s+', ';', css_content)
        
        # Remove últimos espaços
        css_content = css_content.strip()
        
        return css_content
    
    def minify_js(self, js_content: str) -> str:
        """Minifica JavaScript básico (sem parser completo)"""
        # Remove comentários de linha
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        
        # Remove comentários de bloco
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove espaços extras mantendo funcionalidade
        js_content = re.sub(r'\s*\n\s*', '\n', js_content)
        js_content = re.sub(r'\s*{\s*', '{', js_content)
        js_content = re.sub(r'\s*}\s*', '}', js_content)
        js_content = re.sub(r'\s*;\s*', ';', js_content)
        js_content = re.sub(r'\s*,\s*', ',', js_content)
        
        # Remove quebras de linha desnecessárias
        lines = [line.strip() for line in js_content.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def optimize_css_files(self) -> Dict[str, Any]:
        """Otimiza todos os arquivos CSS"""
        results = {}
        css_files = list(self.static_folder.glob('**/*.css'))
        
        for css_file in css_files:
            if 'optimized' in str(css_file):
                continue
                
            try:
                with open(css_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                original_size = len(original_content)
                minified_content = self.minify_css(original_content)
                minified_size = len(minified_content)
                
                # Salvar arquivo minificado
                relative_path = css_file.relative_to(self.static_folder)
                optimized_path = self.optimized_folder / relative_path
                optimized_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(optimized_path, 'w', encoding='utf-8') as f:
                    f.write(minified_content)
                
                # Criar versão gzipped
                gzipped_path = str(optimized_path) + '.gz'
                with gzip.open(gzipped_path, 'wt', encoding='utf-8') as f:
                    f.write(minified_content)
                
                reduction = ((original_size - minified_size) / original_size) * 100
                
                results[str(relative_path)] = {
                    'original_size': original_size,
                    'minified_size': minified_size,
                    'reduction_percent': round(reduction, 1),
                    'optimized_path': str(optimized_path)
                }
                
            except Exception as e:
                results[str(css_file)] = {'error': str(e)}
        
        return results
    
    def optimize_js_files(self) -> Dict[str, Any]:
        """Otimiza todos os arquivos JavaScript"""
        results = {}
        js_files = list(self.static_folder.glob('**/*.js'))
        
        for js_file in js_files:
            if 'optimized' in str(js_file):
                continue
                
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                original_size = len(original_content)
                minified_content = self.minify_js(original_content)
                minified_size = len(minified_content)
                
                # Salvar arquivo minificado
                relative_path = js_file.relative_to(self.static_folder)
                optimized_path = self.optimized_folder / relative_path
                optimized_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(optimized_path, 'w', encoding='utf-8') as f:
                    f.write(minified_content)
                
                # Criar versão gzipped
                gzipped_path = str(optimized_path) + '.gz'
                with gzip.open(gzipped_path, 'wt', encoding='utf-8') as f:
                    f.write(minified_content)
                
                reduction = ((original_size - minified_size) / original_size) * 100 if original_size > 0 else 0
                
                results[str(relative_path)] = {
                    'original_size': original_size,
                    'minified_size': minified_size,
                    'reduction_percent': round(reduction, 1),
                    'optimized_path': str(optimized_path)
                }
                
            except Exception as e:
                results[str(js_file)] = {'error': str(e)}
        
        return results
    
    def generate_asset_manifest(self, css_results: Dict, js_results: Dict) -> Dict[str, Any]:
        """Gera manifest com hashes dos arquivos para cache busting"""
        manifest = {
            'version': '1.0',
            'generated_at': str(Path().cwd()),
            'css': {},
            'js': {},
            'stats': {
                'css_files': len(css_results),
                'js_files': len(js_results),
                'total_css_reduction': 0,
                'total_js_reduction': 0
            }
        }
        
        # Processar CSS
        for file_path, result in css_results.items():
            if 'error' not in result:
                file_hash = self._generate_file_hash(result['optimized_path'])
                manifest['css'][file_path] = {
                    'optimized_path': result['optimized_path'],
                    'hash': file_hash,
                    'size_reduction': result['reduction_percent']
                }
                manifest['stats']['total_css_reduction'] += result['reduction_percent']
        
        # Processar JS
        for file_path, result in js_results.items():
            if 'error' not in result:
                file_hash = self._generate_file_hash(result['optimized_path'])
                manifest['js'][file_path] = {
                    'optimized_path': result['optimized_path'],
                    'hash': file_hash,
                    'size_reduction': result['reduction_percent']
                }
                manifest['stats']['total_js_reduction'] += result['reduction_percent']
        
        # Calcular médias
        if manifest['stats']['css_files'] > 0:
            manifest['stats']['avg_css_reduction'] = round(
                manifest['stats']['total_css_reduction'] / manifest['stats']['css_files'], 1
            )
        
        if manifest['stats']['js_files'] > 0:
            manifest['stats']['avg_js_reduction'] = round(
                manifest['stats']['total_js_reduction'] / manifest['stats']['js_files'], 1
            )
        
        # Salvar manifest
        manifest_path = self.optimized_folder / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        return manifest
    
    def _generate_file_hash(self, file_path: str) -> str:
        """Gera hash MD5 do arquivo para cache busting"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()[:8]
        except:
            return 'unknown'
    
    def optimize_all(self) -> Dict[str, Any]:
        """Executa otimização completa de todos os assets"""
        print("🚀 Iniciando otimização de assets PNSB...")
        
        # Otimizar CSS
        print("📄 Otimizando arquivos CSS...")
        css_results = self.optimize_css_files()
        
        # Otimizar JS
        print("📜 Otimizando arquivos JavaScript...")
        js_results = self.optimize_js_files()
        
        # Gerar manifest
        print("📋 Gerando manifest de assets...")
        manifest = self.generate_asset_manifest(css_results, js_results)
        
        return {
            'css_results': css_results,
            'js_results': js_results,
            'manifest': manifest,
            'optimized_folder': str(self.optimized_folder)
        }

def optimize_specific_css(css_path: str) -> Dict[str, Any]:
    """Otimiza um arquivo CSS específico"""
    optimizer = AssetsOptimizer('gestao_visitas/static')
    
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        original_size = len(original_content)
        minified_content = optimizer.minify_css(original_content)
        minified_size = len(minified_content)
        
        # Salvar versão otimizada
        optimized_path = css_path.replace('.css', '.min.css')
        with open(optimized_path, 'w', encoding='utf-8') as f:
            f.write(minified_content)
        
        reduction = ((original_size - minified_size) / original_size) * 100
        
        return {
            'success': True,
            'original_size': original_size,
            'minified_size': minified_size,
            'reduction_percent': round(reduction, 1),
            'optimized_path': optimized_path,
            'savings_kb': round((original_size - minified_size) / 1024, 1)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Executar otimização
    print("🎯 OTIMIZADOR DE ASSETS PNSB 2024")
    print("=" * 50)
    
    static_folder = "gestao_visitas/static"
    
    if not os.path.exists(static_folder):
        print(f"❌ Pasta static não encontrada: {static_folder}")
        exit(1)
    
    optimizer = AssetsOptimizer(static_folder)
    results = optimizer.optimize_all()
    
    print("\n📊 RESULTADOS DA OTIMIZAÇÃO")
    print("-" * 40)
    
    # Mostrar resultados CSS
    css_count = len([r for r in results['css_results'].values() if 'error' not in r])
    if css_count > 0:
        avg_css_reduction = results['manifest']['stats'].get('avg_css_reduction', 0)
        print(f"✅ CSS: {css_count} arquivos otimizados ({avg_css_reduction}% redução média)")
    
    # Mostrar resultados JS
    js_count = len([r for r in results['js_results'].values() if 'error' not in r])
    if js_count > 0:
        avg_js_reduction = results['manifest']['stats'].get('avg_js_reduction', 0)
        print(f"✅ JS: {js_count} arquivos otimizados ({avg_js_reduction}% redução média)")
    
    print(f"📁 Arquivos otimizados salvos em: {results['optimized_folder']}")
    print("🎉 Otimização concluída!")