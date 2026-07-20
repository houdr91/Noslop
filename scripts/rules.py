# -*- coding: utf-8 -*-
"""Deterministic rules for noslop. Editable without touching the scanner.
Each rule is a tuple (category, description, regex_pattern, flags).
category: 'broken' | 'fishy' | 'minor'
flags: combination of re.IGNORECASE | re.MULTILINE | re.DOTALL etc.
"""

import re

# Categories
BROKEN = "broken"
FISHY = "fishy"
MINOR = "minor"

# Backwards-compatible aliases (kept for any external reference)
ROJO = BROKEN
AMBER = FISHY
MENOR = MINOR

# ---------------------------------------------------------------------------
# A. ENLACES y navegacion
# ---------------------------------------------------------------------------
ENLACES = [
    (ROJO, 'href="#" placeholder', r'\bhref\s*=\s*["\']#["\']', re.I),
    (ROJO, 'href vacio', r'\bhref\s*=\s*["\']["\']', re.I),
    (ROJO, 'href javascript:void(0)', r'\bhref\s*=\s*["\']javascript:void\(0\)["\']', re.I),
    (ROJO, 'dominio placeholder (example.com etc)',
        r'\b(?:href|src)\s*=\s*["\']https?://(?:www\.)?(?:example\.com|yourdomain\.com|mysite\.com|foo\.com|placeholder\.[a-z]+|insert-url\.[a-z]+|your-link\.[a-z]+|your-url\.[a-z]+|insert-link-here\.[a-z]+)',
        re.I),
    (AMBER, 'linkedin handle generico (yourname/username)',
        r'linkedin\.com/in/(?:yourname|username|your-name|your-handle|tunombre|tunick|yourbrand|uoynombre)(?:["/\?#]|$)',
        re.I),
    (AMBER, 'linkedin handle ausente o muy corto',
        r'linkedin\.com/in/(?:["/\?#]|$)|linkedin\.com/in/[\w.\-]{1,3}(?:["/\?#]|$)',
        re.I),
    (AMBER, 'github handle generico',
        r'github\.com/(?:yourusername|username|your-username|your-handle|yourbrand|tunombre|tunick)(?:["/\?#]|$)',
        re.I),
    (AMBER, 'github handle ausente',
        r'github\.com/(?:["/\?#]|$)',
        re.I),
    (AMBER, 'twitter/x handle generico',
        r'(?:twitter|x)\.com/(?:yourusername|username|your-username|your-handle|home|yourbrand|tunombre|tunick)(?:["/\?#]|$)',
        re.I),
    (ROJO, 'mailto sin destino',
        r'\bmailto:\s*["\']|mailto:\s*(?:["\']|$|<)', re.I),
    (ROJO, 'mailto placeholder test@',
        r'mailto:(?:test@test\.com|email@example\.com|you@example\.com|youremail@example\.com|hello@example\.com|your@email\.[a-z]+|user@example\.com)',
        re.I),
    (ROJO, 'tel placeholder',
        r'tel:\s*(?:\+?1?\s*\(?\s*555[\)\s\-]*\d{3}[\s\-]*\d{4}|0{3}[\s\-]*0{3}[\s\-]*0{4}|\+34\s*6{3}\s*6{3}\s*6{3}|\+34\s*6{3}\s*0{3}\s*0{3})',
        re.I),
    (ROJO, 'tel sin numero',
        r'\btel:\s*["\']|\btel:\s*$',
        re.I),
]

# ---------------------------------------------------------------------------
# B. TEXTUAL placeholder / Lorem / seed
# ---------------------------------------------------------------------------
LOREM = r'\b(?:lorem\s+ipsum|dolor\s+sit\s+amet|consectetur\s+adipiscing|ut\s+enim\s+ad\s+minim)\b'

TEXTO_PLACEHOLDER = [
    (ROJO, 'lorem ipsum detectado', LOREM, re.I),
    (ROJO, 'placeholder literal', r'\b(?:placeholder\s+text|insert\s+text\s+here|your\s+text\s+here|replace\s+this)\b', re.I),
    (ROJO, 'marcador TODO/FIXME/TBD/WIP en contenido',
        r'\b(?:TODO|FIXME|XXX|TBD|WIP)\b(?!\s*=)', re.I),
    (ROJO, 'corchetes placeholder [Your ...] [Insert ...]',
        r'\[(?:Your|Insert|Name|Email|Phone|T[ií]tulo\s+aqu[ií]|descripcion|Description|Your\s+name|Your\s+email)\b[^\]]*\]',
        re.I),
    (ROJO, 'angle placeholder <your name>',
        r'<(?:your\s+name|email\s+here|your\s+email|your\s+link|insert\s+here|your\s+text)\s*>',
        re.I),
]

# ---------------------------------------------------------------------------
# C. DATOS INVENTADOS / skill bars
# ---------------------------------------------------------------------------
# Skill bars con width inline
SKILL_WIDTH_INLINE = re.compile(r'(?i)style\s*=\s*["\'][^"\']*width:\s*(\d{1,3})%', re.I)
SKILL_DATA_LEVEL = re.compile(r'(?i)data-(?:level|value|percent|skill)\s*=\s*["\']?(\d{1,3})', re.I)
ARIA_VALUENOW = re.compile(r'(?i)aria-valuenow\s*=\s*["\']?(\d{1,3})', re.I)
SKILL_LABEL_PCT = re.compile(
    r'(?i)(?:<[^>]+?>\s*)?([A-Za-z][A-Za-z0-9_#\.\+\- ]{1,40}?)\s*</?\s*[a-z0-9]+\s*>\s*[:\-]?\s*(\d{1,3})\s*%',
    re.I
)

# Regex rapida para detectar porcentajes magicos en texto (en cualquier momento del doc)
PCT_MAGICO_HI = re.compile(r'\b(9[5-9]|100)\s*%', re.I)

# ---------------------------------------------------------------------------
# D. CONTENIDO GENERICO scribe-tier (texto suelto)
# ---------------------------------------------------------------------------
CONTENIDO_GENERICO = [
    (AMBER, 'frase "moderna y elegante" style',
        r'\b(?:moderna\s+y\s+elegante|elegante\s+y\s+funcional|clean\s+and\s+modern|modern\s+clean\s+beautiful|web\s+app\s+moderna)\b',
        re.I),
    (AMBER, 'frase "creada con amor/pasion"',
        r'\b(?:creada?\s+con\s+(?:amor|pasi[oó]n)|built\s+with\s+love)\b', re.I),
    (AMBER, 'frase de bienvenida genérica',
        r'\b(?:welcome\s*!\s*$|hola\s+y\s+bienvenid[oa]|hey\s+there|hi\s+there|bienvenid[oa]\s+a?\s*mi\s+(?:portfolio|sitio|web))',
        re.I),
    (AMBER, 'frase "este es mi portfolio/sitio"',
        r'\b(?:este\s+es\s+mi\s+(?:portfolio|sitio|web)|esta\s+es\s+mi\s+web\s+personal)\b', re.I),
    (AMBER, 'frase "esta aplicacion demuestra"',
        r'\b(?:esta?\s+(?:aplicaci[oó]n|web|p[aá]gina)\s+(?:demuestra|muestra|ilustra)\b|the\s+follow(?:ing)?\s+project\s+demonstrates)\b',
        re.I),
    (AMBER, 'modern. clean. beautiful. triple',
        r'\b(?:modern|clean|beautiful|simplicity|elegant)(?:\.|\,)\s+(?:modern|clean|beautiful|simplicity|elegant)(?:\.|\,)\s+(?:modern|clean|beautiful|simplicity|elegant)\b',
        re.I),
    (AMBER, 'datos de ejemplo declarados',
        r'\b(?:random\s+data|sample\s+data|datos\s+de\s+ejemplo|demo\s+data|dummy\s+data|data\s+generated\s+from)\b',
        re.I),
    (AMBER, 'powered by',
        r'\bpowered\s+by\b', re.I),
    (AMBER, 'boceto de la',
        r'\bboceto\s+de\s+la?\s+(?:aplicaci[oó]n|web|idea)\b', re.I),
    (AMBER, 'desliza/scroll para ver mas',
        r'\b(?:desliza|scroll)\s+para\s+ver\s+m[aá]s\b', re.I),
    (AMBER, 'built with X and heart emoji',
        r'built\s+with\s+(?:react|vue|next\.js|svelte|astro|tailwind|html|css)[^.]*[hf]eart|built\s+with\s+[a-z][a-z\.]*\s+and\s+[\u2764\U0001F499\U0001F495]',
        re.I),
]

# ---------------------------------------------------------------------------
# E. META / SEO
# ---------------------------------------------------------------------------
META_PLACEHOLDER = [
    (AMBER, 'title placeholder',
        r'<title[^>]*>\s*(?:your\s+awesome\s+site|my\s+website|new\s+app|new\s+project|untitled|document|p[aá]gina|mi\s+web|sitio|website)\s*</title>',
        re.I),
    (AMBER, 'meta description placeholder',
        r'<meta\s+name=["\']description["\'][^>]*content=["\'](?:[^"\']{0,15}|la?\s+descripci[oó]n\s+de\s+tu\s+(?:sitio|portfolio)|la?\s+descripcion\s+de\s+tu\s+portfolio|your\s+description\s+here|[^"\']*lorem[^"\']*)["\']',
        re.I),
    (AMBER, 'meta author placeholder',
        r'<meta\s+name=["\']author["\'][^>]*content=["\'](?:your\s+name|john\s+doe|jane\s+doe|tu\s+nombre)["\']',
        re.I),
    (MENOR, 'meta description ausente',
        r'(?s)(?!.*<meta\s+name=["\']description["\']).*<head>',
        re.I),
    (MENOR, 'lang ausente en <html>',
        r'<html(?![^>]*\slang\s*=)', re.I),
    (MENOR, 'favicon data:, vacio',
        r'<link[^>]*rel=["\'](?:icon|shortcut\s+icon)["\'][^>]*href=["\']data\:\s*,?["\']',
        re.I),
    (AMBER, 'og:image placeholder assets/og.png (puede no existir)',
        r'<meta\s+property=["\']og:image["\'][^>]*content=["\'](?:assets/og\.png|og\.png|images/og\.png)["\']',
        re.I),
    (ROJO, 'og title default Website',
        r'<meta\s+property=["\']og:title["\'][^>]*content=["\'](?:website|untitled|new\s+app|mi\s+web)["\']',
        re.I),
    (AMBER, 'canonical a example.com',
        r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']https?://(?:www\.)?example\.com',
        re.I),
    (AMBER, 'schema.org Person con name Your Name',
        r'"@type"\s*:\s*"Person"[^}]*"name"\s*:\s*"(?:Your\s+Name|John\s+Doe|Jane\s+Doe)"',
        re.I),
]

# ---------------------------------------------------------------------------
# F. IMAGENES y assets
# ---------------------------------------------------------------------------
IMAGENES = [
    (ROJO, 'src vacio en img', r'<img[^>]*\bsrc\s*=\s*["\']["\']', re.I),
    (ROJO, 'img con src="#"', r'<img[^>]*\bsrc\s*=\s*["\']#["\']', re.I),
    (ROJO, 'placeholder image service',
        r'\bsrc\s*=\s*["\']https?://(?:placehold\.co|via\.placeholder\.com|dummyimage\.com|placeholder\.com|placehold\.it)',
        re.I),
    (AMBER, 'picsum photos', r'\bsrc\s*=\s*["\']https?://picsum\.photos', re.I),
    (AMBER, 'source.unsplash random deprecated',
        r'\bsrc\s*=\s*["\']https?://source\.unsplash\.com', re.I),
    (MENOR, 'alt vacio en img', r'<img(?![^>]*\balt\s*=\s*["\'][^"\']+["\'])[^>]*>', re.I),
    (AMBER, 'alt placeholder (image/placeholder/foto/logo)',
        r'<img[^>]*\balt\s*=\s*["\'](?:image|placeholder|imagen|foto|logo|photo)["\']',
        re.I),
]

# ---------------------------------------------------------------------------
# G. FORMS / JSX
# ---------------------------------------------------------------------------
FORMS_JSX = [
    (ROJO, 'formulario action="#" o action=""',
        r'<form[^>]*\baction\s*=\s*["\'](?:#|)["\']',
        re.I),
    (ROJO, 'form method POST con action roto',
        r'<form[^>]*\bmethod\s*=\s*["\']post["\'][^>]*\baction\s*=\s*["\'](?:#|)["\']',
        re.I),
    (AMBER, 'input placeholder your email/name',
        r'<input[^>]*\bplaceholder\s*=\s*["\'](?:your\s+(?:email|name|message|phone)|tu\s+(?:email|nombre|mensaje|tel[eé]fono))["\']',
        re.I),
    (AMBER, 'useState cadena vacia cerca de Hero/About/Contact',
        r'useState\s*\(\s*["\']["\']\s*\)',
        re.I),
    (AMBER, 'onClick vacio',
        r'onClick\s*=\s*\{\s*(?:\(\)\s*=>\s*\{\s*\}|undefined)\s*\}',
        re.I),
    (ROJO, 'console.log TODO/test en codigo',
        r'console\.log\s*\(\s*["\'](?:TODO|test|FIXME|placeholder)["\']',
        re.I),
    (ROJO, 'comentario TODO/FIXME en codigo',
        r'(?://|/\*|<!--)\s*(?:TODO|FIXME|XXX)\b',
        re.I),
    (AMBER, 'try/catch vacio (silencia errores)',
        r'catch\s*(?:\(\s*\w+\s*\))?\s*\{\s*\}',
        re.I),
    (AMBER, 'alert/confirm/prompt en codigo',
        r'\b(?:window\.)?(?:alert|confirm|prompt)\s*\(',
        re.I),
]

# ---------------------------------------------------------------------------
# I. CONTACTO falso
# ---------------------------------------------------------------------------
CONTACTO_FALSO = [
    (ROJO, 'email placeholder tipico',
        r'\b(?:you@example\.com|email@example\.com|test@example\.com|hello@example\.com|info@example\.com|contact@example\.com|your@email\.com|your@email\.xyz|user@example\.com)\b',
        re.I),
    (AMBER, 'direccion generica',
        r'\b(?:123\s+Main\s+St(?:reet)?|456\s+Anywhere|1st\s+Street|Street\s+\d{1,4}|your\s+address|tu\s+direcci[oó]n)\b',
        re.I),
]

# ---------------------------------------------------------------------------
# H. Estructura tier clasico scribe
# ---------------------------------------------------------------------------
SECCION_LITERALES = ['Hero', 'About', 'Skills', 'Projects', 'Contact', 'Services', 'Testimonials', 'Pricing']

# ---------------------------------------------------------------------------
# Comentario de generacion vibe-coded
# ---------------------------------------------------------------------------
VIBE_COMMENTS = [
    (MENOR, 'comentario generado por IA',
        r'<!--\s*(?:generated\s+by\s+claude|built\s+with\s+opencode|vibe-?coded\s+by|built\s+with\s+cursor|generated\s+with\s+ai)\b',
        re.I),
]

# ---------------------------------------------------------------------------
# Buzzwords marketing generico (no slop puro; pide validacion del agente)
# ---------------------------------------------------------------------------
BUZZWORDS = [
    'ai-powered', 'next-generation', 'seamless', 'robust', 'cutting-edge',
    'state-of-the-art', 'world-class', 'best-in-class', 'game-changer',
    'revolutionary', 'disruptive', 'next-gen', 'future-proof',
    'empoderado por ia', 'potenciado por ia', 'de pr[oó]xima generaci[oó]n',
    'sin costuras', 'a prueba de futuro', 'revolucionario',
]

# ---------------------------------------------------------------------------
# Stop words para detectar idioma body vs html lang
# ---------------------------------------------------------------------------
STOPW_ES = [' el ', ' la ', ' los ', ' las ', ' un ', ' una ', ' y ', ' de ',
            ' que ', ' en ', ' es ', ' por ', ' con ', ' para ', ' su ']
STOPW_EN = [' the ', ' and ', ' of ', ' is ', ' in ', ' to ', ' for ', ' with ',
            ' that ', ' it ', ' on ', ' as ', ' this ', ' are ', ' have ']
