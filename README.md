# slop-audit

**Detector de AI slop en webs vibe-coded.**

Si alguna vez has generado un portfolio con Claude Code, Cursor, v0 o Lovable
y has publicado sin revisar, probablemente tienes `href="#"` rotos, un enlace
LinkedIn apuntando a `/in/` sin handle, barras de skill con 100% en cosas que
nunca has tocado, o un About que dice "técnico de soporte" mientras el sitio
afirma que dominas React. `slop-audit` encuentra todo eso — y ~80 cosas más —
en un par de segundos, sin dependencias ni APIs externas.

Nace de un caso real. El portfolio de alguien que conozco parecía correcto a
primera vista, pero apenas le pediste clicar en "Demo" te llevaba a `#`. El
LinkedIn era `linkedin.com/in/` (sin handle). Las skills estaban a 95% en
todo. El About decía "soy técnico de soporte informático" pero las barras
reclamaban 100% en React. Thirty seconds de revisión manual habrían salvado
el sitio; no se hizo. Esta skill convierte esos 30 segundos en 1 comando.

---

## Qué hace

Es una skill para agentic coding tools (Claude Code, opencode, Cursor).
La instalas, le pides al agente algo como "revisa mi portfolio recién
generado" y se activa sola. Lanza un scanner determinista en Python (solo
stdlib) que analiza HTML, JSX, TSX y Markdown, clasifica los hallazgos en
tres niveles de severidad y produce un reporte ASCII priorizado. Si hay
suficiente contexto extraído (sección About + lista de skills), el agente
del usuario añade una sección de inferencia narrativa: ¿casa lo que dices
ser con lo que muestras? Sin llamadas a APIs externas, sin keys, sin pip
install de nada.

El score va de 0 a 100, donde **100 es sitio limpio y 0 es slop absoluto**.

---

## Para quién es

- Para quien genera sitios con IA y los publica sin pasarles un humano por
  encima.
- Para quien hace code review de trabajo junior y está cansado de lo mismo.
- Para QA freelance que cobra por auditar y quiere automatizar el 80%.
- Para quien evalúa herramientas vibe-coded (v0 vs Lovable vs Cursor) y
  quiere una métrica objetiva de "¿esto está realmente terminado?".

---

## Instalación

### Claude Code

```bash
# Carpeta de usuario (todos los proyectos)
cp -r slop-audit ~/.claude/skills/

# O dentro de un proyecto concreto
cp -r slop-audit tu-proyecto/.claude/skills/
```

### opencode

```bash
# Linux / macOS
cp -r slop-audit ~/.config/opencode/skills/

# Windows (PowerShell)
Copy-Item -Recurse slop-audit "$env:APPDATA\opencode\skills\"
```

### Cursor y otros

Copia `SKILL.md` donde tu herramienta lee instrucciones del agente. El
scanner también funciona sin skill, directamente desde el CLI:

```bash
python scripts/slop_scan.py tu-portfolio.html
```

---

## Uso

### CLI directo

```bash
# Reporte humano en consola (ASCII pretty, español, emojis 🔴🟡🟢🤔)
python scripts/slop_scan.py mi-portfolio.html

# JSON estructurado para integrar con otros agentes / CI / scripts
python scripts/slop_scan.py mi-portfolio.html --json

# Volcar JSON a archivo
python scripts/slop_scan.py mi-portfolio.html --json -o .slop-report.json

# Auditar una carpeta entera (recorre .html, .jsx, .tsx, .md)
python scripts/slop_scan.py ./mi-sitio/
```

### Vía skill agentic

Pídele al agente cosas como:

- "Revisa mi portfolio recién generado"
- "Audita esta web vibe-coded"
- "Check si mi sitio tiene AI slop"
- "Mi portfolio hecho con Claude/Cursor/v0"

El `SKILL.md` lleva la descripción afinada para que la skill se dispare
exacto en ese contexto y no se activa con code review genérico ni linteo.

---

## Ejemplo de salida

```
╔══════════════════════════════════════════════════════════════════════╗
║  SLOP-AUDIT REPORT                                                 ║
║  Objetivo: mi-portfolio.html                                       ║
║  Generado: 2026-07-20T19:30:00                                     ║
║  Archivos: 1    Slop-Score: 0/100                                  ║
╚══════════════════════════════════════════════════════════════════════╝

RESUMEN
  🔴 Rotos       : 29  (críticos - el usuario lo nota)
  🟡 Sospechosos : 42  (template sin personalizar)
  🟢 Menores     : 2   (accesibilidad/SEO low-hanging fruit)

DETALLE — Rotos  🔴
  ┌─ mi-portfolio.html:20
  │  href="#" placeholder
  │  >> <a href="#">Link</a>
  └
  ┌─ mi-portfolio.html:0
  │  6 barras con pct>=95 (sospechoso)
  │  >> HTML=95%, CSS=98%, JavaScript=97%, React=100%, Vue=96%
  └
  ...

ANÁLISIS DE COHERENCIA NARRATIVA  🤔  (contexto para el agente)
  · Invoque su razonamiento sobre About ↔ Skills (ver contexto abajo).
  · Contexto extraído:
  ── mi-portfolio.html ──
     nombre declarado :
     idioma body       : es
     title             : My Website
     about             : "Soy técnico de soporte informático. Llevo 3 años..."
     skills            : HTML=95%, CSS=98%, JavaScript=97%, React=100%, Vue=96%, ...
     redes             : {'linkedin': 'https://linkedin.com/in/yourname', ...}

PRIORIDAD DE ARREGLO
  1. 🔴 6 barras con pct>=95 (sospechoso)  [mi-portfolio.html]
  2. 🔴 formulario action="#"              [mi-portfolio.html:66]
  3. 🔴 lorem ipsum detectado              [mi-portfolio.html:27]
  ...
```

El agente recibe ese JSON, añade abajo su sección `🤔` con el veredicto
tri-estado (`INCONSISTENTE` / `OK` / `DUDOSO`), y el usuario ve claramente
qué vino de regex y qué vino de razonamiento.

---

## Cómo funciona por dentro

Pipeline de dos fases.

**Fase 1: scanner determinista.** `scripts/slop_scan.py` aplica +80 patrones
clasificados así:

| Nivel | Peso | Ejemplos |
|---|---|---|
| 🔴 Roto | 10 pts | `href="#"`, `mailto:` sin destino, `tel:+1 (555) 123-4567`, lorem ipsum, `form action="#" method=POST`, `src=""` en `<img>`, `og:title` default `Website`, archivos referenciados inexistentes, `console.log("TODO")`, `[Your Name]` placeholder, `you@example.com`. |
| 🟡 Sospechoso | 3 pts | `linkedin.com/in/yourname`, `github.com/yourusername`, skill bars con ≥3 porcentajes ≥95%, ≥5 skills al mismo pct, secuencia mágica 80/85/90/95/100, meta description placeholder, footer `© 2025 Your Name`, `try/catch {}` vacío, idioma `lang="en"` con body en español, "moderna y elegante", "creada con amor", "powered by", "built with ❤". |
| 🟢 Menor | 1 pt | `lang` ausente, `meta description` ausente, favicon `data:,`, buzzwords ("ai-powered", "seamless", "robust"), comentarios `<!-- generated by claude -->`. |

Score = `max(0, 100 - suma(pesos))`.

**Fase 2: inferencia narrativa.** Solo si hay contexto suficiente (`about`
+ `skills` extraídos) **y** ≥2 rojos o ≥4 amber. El agente hace 1-3
inferencias:

- **About ↔ Skills**: ¿casa la narrativa personal con los porcentajes?
- **Identidad coherente**: nombre declarado, LinkedIn real, GitHub público.
- **Hero auténtico vs autogenerado**: scoring 0-10.

Transparencia es regla de oro: lo detectado por regex lleva 🔴/🟡/🟢, lo
inferido por el agente lleva 🤔 y va en sección aparte. El usuario siempre
distingue "esto es slop objetivo" de "esto es inferencia".

---

## Estructura del repositorio

```
slop-audit/
├── SKILL.md                  Frontmatter + instrucciones del agente
├── scripts/
│   ├── slop_scan.py          Scanner determinista (stdlib only)
│   └── rules.py              Reglas editables (~80 patrones)
├── examples/
│   ├── clean_portfolio.html  Site bien hecho: 0 rojos, score 100
│   ├── slop_portfolio.html   Caso real restaurado: 29 rojos, score 0
│   └── edge_*.html           11 casos límite (lorem, linkedin, skills...)
├── tests/
│   └── run_tests.py          Suite sin pytest, stdlib only (28 checks)
└── README.md
```

---

## Testing

```bash
python tests/run_tests.py
```

Sin pytest. Solo stdlib. Verifica:

- **`clean_portfolio.html`**: 0 rojos, ≤3 amber, score ≥90. Es la prueba
  anti-falsos-positivos más importante: un sitio buen hecho no debería
  disparar nada crítico.
- **`slop_portfolio.html`**: ≥8 rojos, ≥10 amber, score ≤45. Detecta los
  cinco síntomas del caso real: `href="#"`, lorem, skill bars mágicas,
  LinkedIn genérico, contexto about="técnico de soporte" + skill React=100%.
- **11 casos `edge_*`**: lorem concentrado, handles reales vs genéricos
  (incluido el boundary de handle de 3 chars), idioma mezclado, skills
  normales vs mágicas, forms rotos vs funcionales, Markdown con
  placeholders, archivo vacío, assets inexistentes, JSX válido sin
  falsos positivos.
- **Dedupe**: la misma regla no se reporta dos veces en la misma línea.

Estado actual: **28 OK, 0 FAIL ✓**

---

## Requisitos

- Python 3.8+
- Cero dependencias externas (sin `pip install`, sin `requirements.txt`)
- Cero llamadas a APIs externas (sin keys, sin tokens, sin telemetría)
- Cero red. Todo corre localmente.

---

## Editar reglas

Las reglas viven en `scripts/rules.py` como constantes Python — fácil de
mantener sin dependencias y portable a Python 3.8+:

```python
# scripts/rules.py
ENLACES = [
    (ROJO, "mi nuevo patrón roto",
     r'\bhref\s*=\s*["\']mi-placeholder["\']', re.I),
    # ...
]
```

Categorías: `ROJO`, `AMBER`, `MENOR`. Pesos: 10 / 3 / 1 (ajustables en
`SCORING` dentro de `slop_scan.py`).

---

## Limitaciones

- **Parser regex, no AST**. En JSX/TSX no detecta imports sin usar, refs
  rotas o hooks mal usados. Detecta slop estructural, no bugs de código.
  No es un linter.
- **Handles cortos de LinkedIn** (`<3 chars`): se marcan 🟡, no 🔴. Un
  handle real corto como `ai` o `je` puede caer aquí y validarse a mano;
  el agente lo descarta si el usuario lo confirma.
- **Detector de idioma** basado en stop-words. Para textos muy cortos
  (<30 palabras) puede fallar.
- **Assets externos**: la validación de `src` inexistentes solo aplica a
  `.html`/`.htm` (en JSX el bundler resuelve `src` en runtime).
- **Cross-references de IDs** (`href="#id"` sin `id`): solo en HTML, no
  en JSX/MD componentes (un componente puede apuntar a un id de otra página).

---

## Roadmap

- [ ] Soporte de Astro `.astro` y Svelte `.svelte`
- [ ] Detector de secciones duplicadas (mismo párrafo en >1 sección)
- [ ] Detector de `alt` idéntico en cards copypasteadas
- [ ] Modo `--ci` (exit code != 0 si score < threshold) para pipelines
- [ ] i18n del reporte (inglés como segunda salida)

---

## Filosofía

- **Determinismo primero.** Si una regex puede detectarlo, no le des al
  agente la oportunidad de alucinar.
- **Transparencia.** El usuario siempre sabe qué vino de regex y qué vino
  de inferencia.
- **Cero lock-in.** Ni dependencias, ni API, ni keys, ni cuenta, ni
  telemetría. Si el proyecto desaparece mañana, el script sigue funcionando.
- **Falsos positivos > falsos negativos.** Un sitio limpio marcado como 🟡
  se verifica en 5 segundos; un slop no detectado se va a producción.

---

## Contribuir

PRs bienvenidos. Antes de mandar uno:

```bash
python tests/run_tests.py
```

Debe dar **28 OK, 0 FAIL**. Si añades un patrón nuevo, añádelo a `rules.py`,
crea un caso `edge_*.html` que lo pruebe y actualiza `tests/run_tests.py`.

---

## Licencia

MIT.
