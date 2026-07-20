#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slop-audit scanner determinista. Solo stdlib. Cero dependencias externas.
Uso:
    python slop_scan.py <path>            # archivo o directorio
    python slop_scan.py <path> --json     # salida JSON a stdout
    python slop_scan.py <path> -o report.json   # volcar JSON a archivo
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime

# Forzar stdout en UTF-8 (Windows cp1252 rompe emojis/acentos)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Importar reglas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules as R  # noqa: E402


SCORING = {
    R.ROJO: 10.0,
    R.AMBER: 3.0,
    R.MENOR: 1.0,
}

SEVERITY_ICON = {
    R.ROJO: "🔴",
    R.AMBER: "🟡",
    R.MENOR: "🟢",
}

EXTS_ADMITIDOS = {".html", ".htm", ".jsx", ".tsx", ".tsx", ".js", ".ts", ".jsx", ".md", ".markdown"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def leer_archivo(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (IOError, OSError):
        return ""


def linea_de_offset(texto, offset):
    return texto.count("\n", 0, offset) + 1


def encontrar_ids(texto):
    return set(re.findall(r'\bid\s*=\s*["\']([\w\-]+)["\']', texto, re.I))


def encontrar_elementos_con_atributos(texto, regex):
    """Itera las lineas y devuelve [(linea, match_obj)]."""
    out = []
    for i, line in enumerate(texto.splitlines(), start=1):
        m = regex.search(line)
        if m:
            out.append((i, line.strip(), m))
    return out


def extraer_seccion(texto, nombre_seccion, max_chars=350):
    """Extrae el cuerpo de una seccion cuyo tag/class/id coincide con nombre.
    Acepta variantes español/inglés.
    """
    aliases = {
        "about": ["about", "sobre-mi", "sobre-m\u00ed", "sobremi", "sobre", "perfil",
                  "bio", "perfil-profesional"],
        "hero": ["hero", "portada", "inicio", "intro", "presentation",
                 "presentacion", "presentaci\u00f3n"],
        "skills": ["skills", "habilidades", "competencias", "tech",
                   "tecnologias", "tecnolog\u00edas"],
    }
    nombres = aliases.get(nombre_seccion, [nombre_seccion])
    for nombre in nombres:
        pat = re.compile(
            r'(?is)<(section|div|article|main|header)[^>]*\b(?:id|class|data-section)\s*=\s*["\'][^"\']*'
            + re.escape(nombre) + r'[^"\']*["\'][^>]*>(?P<body>.*?)</\1>',
            re.I)
        m = pat.search(texto)
        if m:
            body = re.sub(r'<[^>]+>', ' ', m.group('body'))
            body = re.sub(r'\s+', ' ', body).strip()
            if body:
                return body[:max_chars]
    return ""


def extraer_skill_bars(texto):
    """Devuelve lista de (label, percent)."""
    out = []
    # Buscar elementos con class o data-* conteniendo skill
    skill_pat = re.compile(
        r'(?is)<(?P<tag>\w+)\b[^>]*\b(?:class|data-skill|data-name|data-label)\s*=\s*'
        r'["\'][^"\']*\b(?:skill|habilidad|competencia)\b[^"\']*["\'][^>]*>',
        re.I)
    for m in skill_pat.finditer(texto):
        start = m.start()
        # buscar el primer cierre del mismo tag (no anidado, suficiente para skills)
        end_pat = re.compile(r'</' + m.group('tag') + r'\s*>', re.I)
        end_match = end_pat.search(texto, m.end())
        if not end_match:
            continue
        bloque = texto[start:end_match.end()]
        # label: data-name o data-label o texto interno
        label = ""
        nm = re.search(r'data-(?:name|label)\s*=\s*["\']([^"\']+)["\']', bloque, re.I)
        if nm:
            label = nm.group(1).strip()
        if not label:
            # texto interno, quitando tags hijos
            inner = re.sub(r'(?is)^<' + m.group('tag') + r'[^>]*>', '', bloque)
            inner = re.sub(r'(?is)</' + m.group('tag') + r'\s*>$', '', inner)
            inner = re.sub(r'<[^>]+>', ' ', inner)
            inner = re.sub(r'\s+', ' ', inner).strip()
            label = inner[:40].strip()
        # pct: width inline / data-level / aria-valuenow / texto "95%"
        pct = None
        wm = R.SKILL_WIDTH_INLINE.search(bloque)
        if wm:
            pct = int(wm.group(1))
        if pct is None:
            dm = R.SKILL_DATA_LEVEL.search(bloque)
            if dm:
                pct = int(dm.group(1))
        if pct is None:
            am = R.ARIA_VALUENOW.search(bloque)
            if am:
                pct = int(am.group(1))
        if pct is None:
            # texto "92%" en contenido
            pm = re.search(r'(9[0-9]|1[0-9]{2})\s*%', bloque)
            if pm:
                pct = int(pm.group(1))
        if pct is not None and 0 <= pct <= 100 and label:
            label = re.sub(r'\s+', ' ', label).strip()
            out.append((label, pct))
    # Fallback Markdown
    if not out:
        md_pat = re.compile(r'(?m)^\s*[-*]\s*(.+?)\s*[:\-]\s*(\d{1,3})\s*%')
        for m in md_pat.finditer(texto):
            label = m.group(1).strip()
            pct = int(m.group(2))
            if 0 <= pct <= 100:
                out.append((label, pct))
    return out


def extraer_title(texto):
    m = re.search(r'(?is)<title[^>]*>(.*?)</title>', texto)
    if m:
        return re.sub(r'\s+', ' ', m.group(1)).strip()[:120]
    return ""


def detectar_idioma(texto):
    """Devuelve 'es', 'en', u 'otro' segun conteo de stop-words."""
    sample = " " + re.sub(r'<[^>]+>', ' ', texto.lower()) + " "
    n_es = sum(sample.count(w) for w in R.STOPW_ES)
    n_en = sum(sample.count(w) for w in R.STOPW_EN)
    if n_es > n_en * 1.5:
        return 'es'
    if n_en > n_es * 1.5:
        return 'en'
    return 'otro'


def extraer_nombre_declarado(texto):
    """Intenta sacar el nombre real de la persona (json-ld, <title>, about)."""
    m = re.search(r'(?s)"name"\s*:\s*"([^"]+)"', texto)
    if m and not re.search(r'your name|john doe|jane doe', m.group(1), re.I):
        return m.group(1).strip()
    title = extraer_title(texto)
    if title:
        # intentar separar
        partes = re.split(r'\s*[\|\-—··]\s*', title)
        for p in partes:
            p = p.strip()
            if 2 < len(p) < 60 and not re.search(r'portfolio|web|site|valer',
                                                  p, re.I) and ' ' in p:
                return p
    return ""


def extraer_redes_declaradas(texto):
    """Devuelve dict {red: url} para pasar al agente."""
    out = {}
    for red, pat in [
        ('linkedin', re.compile(r'https?://(?:[a-z]+\.)?linkedin\.com/in/[\w.\-]+', re.I)),
        ('github', re.compile(r'https?://github\.com/[\w.\-]+', re.I)),
        ('twitter', re.compile(r'https?://(?:twitter|x)\.com/[\w]+', re.I)),
    ]:
        m = pat.search(texto)
        if m:
            out[red] = m.group(0)
    return out


# ---------------------------------------------------------------------------
# Scanners por categoria
# ---------------------------------------------------------------------------

def escanear_patrones(texto, reglas):
    """Aplica lista de patrones. Devuelve [{linea, desc, cat, snippet}].
    Dedupe por (linea, descripcion) para evitar reportes repetidos.
    """
    hallazgos = []
    vistos = set()
    lineas = texto.splitlines()
    for cat, desc, pat, flags in reglas:
        regex = re.compile(pat, flags or 0)
        for m in regex.finditer(texto):
            offset = m.start()
            ln = linea_de_offset(texto, offset)
            key = (ln, desc)
            if key in vistos:
                continue
            vistos.add(key)
            snippet = ""
            if 0 <= ln - 1 < len(lineas):
                snippet = lineas[ln - 1].strip()[:80]
            hallazgos.append({
                "linea": ln,
                "categoria": cat,
                "descripcion": desc,
                "snippet": snippet,
            })
    return hallazgos


def escanear_skill_bars(texto):
    """Detecta barras de skill sospechosas (porcentajes magicos)."""
    out = []
    skills = extraer_skill_bars(texto)
    if not skills:
        return out
    # Magico: 5 o mas skills con la misma pct
    pcts = [pct for _, pct in skills]
    if pcts:
        from collections import Counter
        cnt = Counter(pcts)
        for pct, n in cnt.items():
            if n >= 5 and pct >= 80:
                out.append({
                    "linea": 0,
                    "categoria": R.ROJO,
                    "descripcion": f"{n} barras de skill todas a {pct}% (inventado)",
                    "snippet": ", ".join([lbl for lbl, p in skills if p == pct][:5]),
                })
        # Porcentajes >= 95 repetidos
        altas = [p for p in pcts if p >= 95]
        if len(altas) >= 3:
            out.append({
                "linea": 0,
                "categoria": R.ROJO,
                "descripcion": f"{len(altas)} barras con pct>=95 (sospechoso)",
                "snippet": ", ".join([f"{lbl}={pct}%" for lbl, pct in skills if pct >= 95][:5]),
            })
        # 100%
        cien = [p for p in pcts if p == 100]
        if cien:
            out.append({
                "linea": 0,
                "categoria": R.AMBER,
                "descripcion": f"{len(cien)} barras con 100% (presuncion)",
                "snippet": ", ".join([lbl for lbl, p in skills if p == 100]),
            })
        # Secuencia 80/85/90/95/100
        if sorted(set(pcts)) == [80, 85, 90, 95, 100] and len(pcts) >= 5:
            out.append({
                "linea": 0,
                "categoria": R.AMBER,
                "descripcion": "secuencia magica 80/85/90/95/100",
                "snippet": ", ".join([f"{lbl}" for lbl, _ in skills]),
            })
    # Skill sin label
    for label, pct in skills:
        if not label.strip():
            out.append({
                "linea": 0,
                "categoria": R.AMBER,
                "descripcion": f"barra de skill sin label {pct}%",
                "snippet": label,
            })
    return out


def escanear_links_internos(texto, extension):
    """Marca href="#id" si el id no existe.
    Solo aplica a documentos HTML completos (.html/.htm). En JSX/MDX el
    componente puede referenciar un id de otra pagina y seria falso positivo.
    """
    out = []
    if extension.lower() not in (".html", ".htm"):
        return out
    ids = encontrar_ids(texto)
    for m in re.finditer(r'\bhref\s*=\s*["\']#([\w\-]+)["\']', texto, re.I):
        if m.group(1) not in ids:
            ln = linea_de_offset(texto, m.start())
            out.append({
                "linea": ln,
                "categoria": R.ROJO,
                "descripcion": f"href='#{m.group(1)}' pero no existe id='{m.group(1)}'",
                "snippet": m.group(0)[:80],
            })
    return out


def escanear_assets_inexistentes(texto, base_dir, extension):
    """Marca img/link href que referencian archivos locales no existentes.
    Solo aplica a .html/.htm (en JSX/Vite el bundler resuelve src runtime).
    """
    out = []
    if extension.lower() not in (".html", ".htm"):
        return out
    for tag, attr in [('<img', 'src'),
                     ('<link', 'href'),
                     ('<script', 'src')]:
        pat = re.compile(
            r'<\s*' + tag[1:] + r'\b[^>]*\b' + attr + r'\s*=\s*["\']([^"\']+)["\']',
            re.I)
        for line_num, line in enumerate(texto.splitlines(), start=1):
            m = pat.search(line)
            if not m:
                continue
            url = m.group(1).strip()
            if url.startswith(('http://', 'https://', 'data:', 'mailto:', 'tel:', '#')):
                continue
            if not url:
                continue
            # ruta relativa
            ruta = os.path.normpath(os.path.join(base_dir, url.split('?')[0]))
            if not os.path.exists(ruta):
                out.append({
                    "linea": line_num,
                    "categoria": R.ROJO,
                    "descripcion": f"{attr}='{url}' archivo no existe",
                    "snippet": line.strip()[:80],
                })
    return out


def escanear_idioma_vs_lang(texto):
    out = []
    idioma_body = detectar_idioma(texto)
    m = re.search(r'<html[^>]*\blang\s*=\s*["\']([a-zA-Z\-]+)["\']', texto, re.I)
    if m:
        lang_declarado = m.group(1).lower().split('-')[0]
        if idioma_body == 'es' and lang_declarado == 'en':
            out.append({
                "linea": 1,
                "categoria": R.AMBER,
                "descripcion": f"html lang='{lang_declarado}' pero cuerpo en espanol",
                "snippet": m.group(0)[:80],
            })
        elif idioma_body == 'en' and lang_declarado == 'es':
            out.append({
                "linea": 1,
                "categoria": R.AMBER,
                "descripcion": f"html lang='{lang_declarado}' pero cuerpo en ingles",
                "snippet": m.group(0)[:80],
            })
    return out


def escanear_click_here(texto):
    """Marca <a> con texto generico tipo 'Click here' 'aqui' 'Link'."""
    out = []
    pat = re.compile(
        r'(?is)<a[^>]*>(?P<texto>[^<]+)</a>')
    for m in pat.finditer(texto):
        txt = re.sub(r'\s+', ' ', m.group('texto')).strip().lower()
        if txt in ('click here', 'here', 'link', 'link here', 'click here to visit',
                   'aqui', 'aqui el link', 'click', 'ver mas', 'ver m\u00e1s',
                   'aqu\u00ed', 'aqu\u00ed el link'):
            ln = linea_de_offset(texto, m.start())
            out.append({
                "linea": ln,
                "categoria": R.AMBER,
                "descripcion": f"enlace con texto generico '{m.group('texto').strip()}'",
                "snippet": m.group(0)[:80],
            })
    return out


def escanear_h2_literales(texto):
    """Marca h2 cuyo texto es literalmente 'About' 'Skills' etc (sin contexto)."""
    out = []
    pat = re.compile(r'(?is)<h[12][^>]*>(?P<texto>.*?)</h[12]>')
    for m in pat.finditer(texto):
        txt = re.sub(r'<[^>]+>', ' ', m.group('texto'))
        txt = re.sub(r'\s+', ' ', txt).strip()
        if txt in R.SECCION_LITERALES:
            ln = linea_de_offset(texto, m.start())
            out.append({
                "linea": ln,
                "categoria": R.AMBER,
                "descripcion": f"titulo seccion literal sin contexto: '{txt}'",
                "snippet": m.group(0)[:80],
            })
    return out


def escanear_footer_default(texto):
    out = []
    patrones = [
        # © 2025 Your Name  /  © 2025 Tu nombre
        re.compile(r'(?is)©\s*\d{4}\s+(?:your\s+name|tu\s+nombre)\b', re.I),
        # © {year} template literal no sustituido
        re.compile(r'(?is)©\s*\$\{[^}]*year[^}]*\}', re.I),
        # © 2025  All rights reserved.  sin autor despues del anyo
        re.compile(r'(?is)©\s*\d{4}\s*\.?\s*all\s+rights\s+reserved\s*\.\s*(?:</p>|<br|$)', re.I),
        # © año vacio y nada despues
        re.compile(r'(?is)©\s*\d{4}\s*(?:</|<br\s*/?>\s*$|\s*$)', re.I),
    ]
    for pat in patrones:
        for m in pat.finditer(texto):
            ln = linea_de_offset(texto, m.start())
            # Evitar doble match: si ya esta en lista, saltar
            if any(h["linea"] == ln for h in out):
                continue
            out.append({
                "linea": ln,
                "categoria": R.AMBER,
                "descripcion": "footer default sin reemplazo",
                "snippet": m.group(0).strip()[:80],
            })
    return out


def escanear_buzzwords(texto):
    out = []
    sample = texto.lower()
    for bw in R.BUZZWORDS:
        n = sample.count(bw)
        if n:
            out.append({
                "linea": 0,
                "categoria": R.MENOR,
                "descripcion": f"buzzword: '{bw}' x{n}",
                "snippet": "",
            })
    return out


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def escanear_archivo(path, base_dir):
    texto = leer_archivo(path)
    if not texto.strip():
        return [], None
    hallazgos = []

    todas_reglas = (
        R.ENLACES
        + R.TEXTO_PLACEHOLDER
        + R.CONTENIDO_GENERICO
        + R.META_PLACEHOLDER
        + R.IMAGENES
        + R.FORMS_JSX
        + R.CONTACTO_FALSO
        + R.VIBE_COMMENTS
    )
    hallazgos += escanear_patrones(texto, todas_reglas)
    hallazgos += escanear_skill_bars(texto)
    ext = os.path.splitext(path)[1].lower()
    hallazgos += escanear_links_internos(texto, ext)
    hallazgos += escanear_assets_inexistentes(texto, os.path.dirname(path), ext)
    hallazgos += escanear_idioma_vs_lang(texto)
    hallazgos += escanear_click_here(texto)
    hallazgos += escanear_h2_literales(texto)
    hallazgos += escanear_footer_default(texto)
    hallazgos += escanear_buzzwords(texto)

    # Contexto para el agente (cuadra de inferencia narrativa)
    contexto = {
        "archivo": path,
        "title": extraer_title(texto),
        "about": extraer_seccion(texto, "about", 350),
        "hero": extraer_seccion(texto, "hero", 350),
        "skills": [{"label": lbl, "pct": pct}
                   for lbl, pct in extraer_skill_bars(texto)[:10]],
        "idioma_body": detectar_idioma(texto),
        "nombre_declarado": extraer_nombre_declarado(texto),
        "redes": extraer_redes_declaradas(texto),
    }
    return hallazgos, contexto


def consolidar(hallazgos_por_archivo, contexto_por_archivo):
    """Consolida hallazgos de todos los archivos."""
    todos = []
    for archivo, hallazgos in hallazgos_por_archivo.items():
        for h in hallazgos:
            todos.append({
                "archivo": archivo,
                "linea": h.get("linea", 0),
                "categoria": h["categoria"],
                "descripcion": h["descripcion"],
                "snippet": h.get("snippet", ""),
            })
    return todos


def calcular_score(hallazgos):
    """Score 0-100, 100 = limpio."""
    peso = sum(SCORING.get(h["categoria"], 0) for h in hallazgos)
    # 1 rojo (-10), aplicar suavizado
    score = max(0, 100 - int(round(peso)))
    return score


# ---------------------------------------------------------------------------
# Reporte (humano, ASCII pretty)
# ---------------------------------------------------------------------------

def render_reporte(todos, contextos, base_path=None):
    rojos = [h for h in todos if h["categoria"] == R.ROJO]
    amber = [h for h in todos if h["categoria"] == R.AMBER]
    menores = [h for h in todos if h["categoria"] == R.MENOR]
    score = calcular_score(todos)
    n_archivos = len(contextos)
    fecha = datetime.now().isoformat(timespec='seconds')

    out = []
    ancho = 70
    def pad(s, ancho=ancho):
        # pad considers display width approx using len
        return s + " " * max(0, ancho - len(s) - 1) + "║"
    out.append("╔" + "═" * ancho + "╗")
    out.append(pad("║  SLOP-AUDIT REPORT"))
    out.append(pad(f"║  Objetivo: {base_path or ''}"))
    out.append(pad(f"║  Generado: {fecha}"))
    out.append(pad(f"║  Archivos: {n_archivos}    Slop-Score: {score}/100"))
    out.append("╚" + "═" * ancho + "╝")
    out.append("")

    out.append("RESUMEN")
    out.append(f"  🔴 Rotos       : {len(rojos)}  (críticos - el usuario lo nota)")
    out.append(f"  🟡 Sospechosos : {len(amber)}  (template sin personalizar)")
    out.append(f"  🟢 Menores     : {len(menores)}  (accesibilidad/SEO low-hanging fruit)")
    out.append("")

    def render_grupo(titulo, icon, items):
        if not items:
            return
        out.append("")
        out.append(f"{titulo}  {icon}")
        for h in items:
            arc = h["archivo"]
            if base_path and arc.startswith(base_path):
                arc = arc[len(base_path):].lstrip("\\/")
            out.append(f"  ┌─ {arc}:{h['linea']}")
            out.append(f"  │  {h['descripcion']}")
            if h.get("snippet"):
                out.append(f"  │  >> {h['snippet']}")
            out.append("  └")

    render_grupo("DETALLE — Rotos", "🔴", rojos)
    render_grupo("DETALLE — Sospechosos", "🟡", amber)
    render_grupo("DETALLE — Menores", "🟢", menores)

    # Contexto para inferencia narrativa
    out.append("")
    out.append("ANÁLISIS DE COHERENCIA NARRATIVA  🤔  (contexto para el agente)")
    hay_about = any(c.get("about") for c in contextos.values())
    hay_skills = any(c.get("skills") for c in contextos.values())
    trigger_inferencia = len(rojos) + (len(amber) // 2) >= 2
    if not (hay_about and hay_skills):
        out.append("  · No se encontró sección About con skills suficiente — se omite inferencia.")
        out.append("  · Contexto extraído:")
    else:
        if trigger_inferencia:
            out.append("  · Invoque su razonamiento sobre About ↔ Skills (ver contexto abajo).")
        else:
            out.append("  · Pocos hallazgos críticos — inferencia opcional.")
        out.append("  · Contexto extraído:")
    for arc, ctx in contextos.items():
        if not ctx:
            continue
        arc_c = arc
        if base_path and arc_c.startswith(base_path):
            arc_c = arc_c[len(base_path):].lstrip("\\/")
        out.append(f"  ── {arc_c} ──")
        out.append(f"     nombre declarado : {ctx.get('nombre_declarado','(no detectado)')}")
        out.append(f"     idioma body       : {ctx.get('idioma_body')}")
        out.append(f"     title             : {ctx.get('title','')}")
        if ctx.get("about"):
            out.append(f"     about             : \"{ctx['about'][:200]}\"")
        if ctx.get("skills"):
            skills_str = ", ".join(f"{s['label']}={s['pct']}%"
                                   for s in ctx["skills"])
            out.append(f"     skills            : {skills_str}")
        if ctx.get("redes"):
            out.append(f"     redes             : {ctx['redes']}")

    # Prioridad
    out.append("")
    out.append("PRIORIDAD DE ARREGLO")
    prioridad = sorted(rojos, key=lambda h: h["descripcion"])[:8]
    for i, h in enumerate(prioridad, 1):
        out.append(f"  {i}. 🔴 {h['descripcion']}  [{h['archivo']}:{h['linea']}]")
    misc = sorted(amber, key=lambda h: h["descripcion"])[:5]
    for j, h in enumerate(misc, len(prioridad) + 1):
        out.append(f"  {j}. 🟡 {h['descripcion']}  [{h['archivo']}]")

    out.append("")
    out.append("──────────────────────────────────────────────────────────────")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def listar_archivos_admitidos(path):
    paths = []
    if os.path.isfile(path):
        if os.path.splitext(path)[1].lower().replace('.tsx', '.jsx') in EXTS_ADMITIDOS \
                or os.path.splitext(path)[1].lower() in EXTS_ADMITIDOS:
            paths.append(path)
        return paths
    for root, dirs, files in os.walk(path):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in EXTS_ADMITIDOS:
                paths.append(os.path.join(root, f))
    return paths


def main(args):
    if not args.path:
        print("Uso: python slop_scan.py <path> [--json] [-o file.json]")
        return 2
    path = os.path.abspath(args.path)
    if not os.path.exists(path):
        print(f"Error: no existe {path}")
        return 2
    archivos = listar_archivos_admitidos(path)
    if not archivos:
        print(f"No se encontraron archivos admisibles en {path}")
        return 1

    hallazgos_arc = {}
    contextos = {}
    base_dir = path if os.path.isdir(path) else os.path.dirname(path)

    for arc in sorted(archivos):
        h, ctx = escanear_archivo(arc, base_dir)
        hallazgos_arc[arc] = h
        contextos[arc] = ctx

    todos = consolidar(hallazgos_arc, contextos)

    if args.json:
        payload = {
            "objetivo": path,
            "fecha": datetime.now().isoformat(timespec='seconds'),
            "archivos": [a for a in archivos],
            "score": calcular_score(todos),
            "hallazgos": todos,
            "contexto": contextos,
        }
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            print(f"Reporte JSON guardado en {args.output}")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(render_reporte(todos, contextos, base_path=base_dir))
    return 0


def main_cli():
    parser = argparse.ArgumentParser(description="slop-audit scanner")
    parser.add_argument("path", nargs="?", help="Archivo o carpeta a auditar")
    parser.add_argument("--json", action="store_true", help="Salida JSON a stdout")
    parser.add_argument("-o", "--output", help="Volcar JSON a archivo")
    args = parser.parse_args()
    sys.exit(main(args))


if __name__ == "__main__":
    main_cli()
