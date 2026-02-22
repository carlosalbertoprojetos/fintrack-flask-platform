"""
Middleware para compatibilidade entre navegadores
"""

from flask import request, g
import re


def browser_compatibility_middleware(app):
    """Middleware para resolver problemas de compatibilidade entre navegadores"""
    
    @app.before_request
    def detect_browser():
        """Detecta o navegador e aplica correções específicas"""
        user_agent = request.headers.get('User-Agent', '')
        g.browser = 'unknown'
        g.browser_version = 'unknown'
        
        # Detectar navegador
        if 'Firefox' in user_agent:
            g.browser = 'firefox'
            match = re.search(r'Firefox/(\d+)', user_agent)
            if match:
                g.browser_version = int(match.group(1))
        elif 'Chrome' in user_agent:
            g.browser = 'chrome'
            match = re.search(r'Chrome/(\d+)', user_agent)
            if match:
                g.browser_version = int(match.group(1))
        elif 'Edge' in user_agent:
            g.browser = 'edge'
            match = re.search(r'Edge/(\d+)', user_agent)
            if match:
                g.browser_version = int(match.group(1))
        elif 'Safari' in user_agent:
            g.browser = 'safari'
            match = re.search(r'Version/(\d+)', user_agent)
            if match:
                g.browser_version = int(match.group(1))
    
    @app.after_request
    def add_compatibility_headers(response):
        """Adiciona headers para compatibilidade entre navegadores"""
        
        # Headers para compatibilidade com Firefox
        if g.browser == 'firefox':
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Headers para compatibilidade com Chrome
        elif g.browser == 'chrome':
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Headers para compatibilidade com Edge
        elif g.browser == 'edge':
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Headers gerais de compatibilidade
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    
    return app
