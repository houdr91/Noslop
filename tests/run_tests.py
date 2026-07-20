#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test suite for noslop.
No pytest. Standard library only. Usage:
    python tests/run_tests.py
"""

import os
import sys
import json
import subprocess
from collections import Counter

# Asegurar rutas
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "slop_scan.py")
EXAMPLES = os.path.join(ROOT, "examples")

ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"


def escanear(nombre_archivo):
    """Corre el scanner sobre examples/<nombre_archivo> y devuelve el JSON."""
    path = os.path.join(EXAMPLES, nombre_archivo)
    r = subprocess.run(
        [sys.executable, SCRIPT, path, "--json"],
        capture_output=True, text=True, env=ENV, encoding="utf-8"
    )
    if r.returncode != 0:
        raise RuntimeError(f"Scanner fallo con {nombre_archivo}: {r.stderr}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        print(r.stdout[:500])
        raise


def contar(hallazgos):
    c = Counter(h["categoria"] for h in hallazgos)
    return c.get("broken", 0), c.get("fishy", 0), c.get("minor", 0)


resultados = []
failuras = []


def check(nombre, condicion, detalle=""):
    if condicion:
        resultados.append(f"  [OK] {nombre}")
        return True
    failuras.append(f"  [FAIL] {nombre}  {detalle}")
    return False


def test_clean_portfolio():
    j = escanear("clean_portfolio.html")
    r, a, m = contar(j["hallazgos"])
    check("clean_portfolio: 0 rojos", r == 0, f"obtuvo {r}")
    check("clean_portfolio: <= 3 amber", a <= 3, f"obtuvo {a}")
    check("clean_portfolio: score >= 90", j["score"] >= 90, f"score={j['score']}")


def test_slop_portfolio():
    j = escanear("slop_portfolio.html")
    r, a, m = contar(j["hallazgos"])
    check("slop_portfolio: >= 8 rojos", r >= 8, f"obtuvo {r}")
    check("slop_portfolio: >= 10 amber", a >= 10, f"obtuvo {a}")
    check("slop_portfolio: score <= 45", j["score"] <= 45, f"score={j['score']}")
    # Detalles clave del caso real
    descs = {h["descripcion"] for h in j["hallazgos"]}
    check("slop_portfolio: detecta href='#'",
          any('href="#" placeholder' in d for d in descs))
    check("slop_portfolio: detecta linkedin generico",
          any('linkedin handle' in d for d in descs))
    check("slop_portfolio: detecta skill bars sospechosas",
          any('barras' in d for d in descs))
    check("slop_portfolio: detecta lorem",
          any('lorem' in d for d in descs))
    # Extraer contexto para la inferencia narrativa
    ctx_key = next(iter(j["contexto"].keys()))
    ctx = j["contexto"][ctx_key]
    check("slop_portfolio: contexto tiene about",
          "t\u00e9cnico" in ctx.get("about", "").lower())
    check("slop_portfolio: contexto tiene skills con React=100%",
          any(s["label"] == "React" and s["pct"] == 100 for s in ctx.get("skills", [])))


def test_edge_just_lorem():
    j = escanear("edge_just_lorem.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_just_lorem: >= 2 rojos (lorem)", r >= 2, f"obtuvo {r}")


def test_edge_linkedin():
    j = escanear("edge_linkedin_real_vs_generico.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_linkedin: 0 rojos (no hay handle placeholder roto)", r == 0,
          f"obtuvo {r}")
    check("edge_linkedin: >= 1 amber (yourname generico o ai corto)", a >= 1,
          f"obtuvo {a}")
    # El handle real largo no debe aparecer en hallazgos
    descs = " ".join(h.get("snippet", "") for h in j["hallazgos"])
    check("edge_linkedin: handle real no se reporta",
          "martagomezzeledon" not in descs)


def test_edge_mixed_languages():
    j = escanear("edge_mixed_languages.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_mixed_languages: >= 1 amber (lang mismatch)", a >= 1,
          f"obtuvo {a}")


def test_edge_skill_normal():
    j = escanear("edge_skill_normal.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_skill_normal: 0 rojos", r == 0, f"obtuvo {r}")
    check("edge_skill_normal: 0 amber por skill bars", a == 0, f"obtuvo {a}")


def test_edge_skills_95x5():
    j = escanear("edge_skills_95x5.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_skills_95x5: >= 1 rojo (mismo pct en 5+ skills)", r >= 1,
          f"obtuvo {r}")


def test_edge_form_roto():
    j = escanear("edge_form_roto.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_form_roto: detecta form action='#'", r >= 1, f"obtuvo {r}")


def test_edge_form_bueno():
    j = escanear("edge_form_bueno.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_form_bueno: 0 rojos por el form", r == 0, f"obtuvo {r}")


def test_edge_markdown_blog():
    j = escanear("edge_markdown_blog.md")
    r, a, m = contar(j["hallazgos"])
    check("edge_markdown_blog: >= 3 rojos (corchetes + TODO/FIXME)",
          r >= 3, f"obtuvo {r}")


def test_edge_empty():
    j = escanear("edge_empty.html")
    # Debe ejecutarse sin error, no requiere hallazgos
    check("edge_empty: score defined", "score" in j)


def test_edge_assets_missing():
    j = escanear("edge_assets_missing.html")
    r, a, m = contar(j["hallazgos"])
    check("edge_assets_missing: >= 2 rojos (profile + non-existent)", r >= 2,
          f"obtuvo {r}")


def test_edge_jsx_real():
    j = escanear("edge_jsx_real.jsx")
    r, a, m = contar(j["hallazgos"])
    check("edge_jsx_real: 0 rojos (sin falsos positivos en JSX valido)",
          r == 0, f"obtuvo {r}")


def test_dedupe():
    """La misma regla no debe reportarse dos veces en la misma linea."""
    j = escanear("slop_portfolio.html")
    vistos = set()
    dups = 0
    for h in j["hallazgos"]:
        key = (h["linea"], h["descripcion"])
        if key in vistos:
            dups += 1
        vistos.add(key)
    check("dedupe: no hay duplicados por (linea, descripcion)", dups == 0,
          f"hay {dups} duplicados")


def test_help():
    r = subprocess.run([sys.executable, SCRIPT],
                      capture_output=True, text=True, env=ENV, encoding="utf-8")
    # Esperamos codigo != 0 porque falta path
    check("cli: sin args devuelve usage", r.returncode != 0)


def main():
    print("════════════════════════════════════════════════════════════════")
    print("  noslop — test suite")
    print("════════════════════════════════════════════════════════════════")
    tests = [
        test_clean_portfolio,
        test_slop_portfolio,
        test_edge_just_lorem,
        test_edge_linkedin,
        test_edge_mixed_languages,
        test_edge_skill_normal,
        test_edge_skills_95x5,
        test_edge_form_roto,
        test_edge_form_bueno,
        test_edge_markdown_blog,
        test_edge_empty,
        test_edge_assets_missing,
        test_edge_jsx_real,
        test_dedupe,
        test_help,
    ]
    for t in tests:
        print(f"\n[{t.__name__}]")
        try:
            t()
        except Exception as e:
            failuras.append(f"  [FAIL] {t.__name__}  excepcion: {e}")

    print("\n════════════════════════════════════════════════════════════════")
    for r in resultados:
        print(r)
    if failuras:
        print("\nFAILURAS:")
        for f in failuras:
            print(f)
        print(f"\n  TOTAL: {len(resultados)} OK, {len(failuras)} FAIL")
        return 1
    print(f"\n  TOTAL: {len(resultados)} OK, 0 FAIL  ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
