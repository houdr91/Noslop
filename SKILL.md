---
name: slop-audit
description: Audita portfolios y sites generados con IA (vibe-coded: Claude Code, Cursor, opencode, v0, Lovable, Bolt) en busca de "AI slop": enlaces href="#" no rellenados, LinkedIn/GitHub genéricos, barras de skill con porcentajes inventados, lorem ipsum, placeholders textuales, meta-tags sin rellenar, contenido genérico scribe-tier, formularios sin action y contradicciones narrativas entre la sección About y las skills mostradas. Úsala SOLO cuando el usuario pida algo tipo "revisa mi portfolio recién generado", "audita esta web vibe-coded", "check si mi sitio tiene AI slop", "mi portfolio hecho con Claude/Cursor/v0/Lovable", o presente uno o varios archivos `.html` / `.jsx` / `.tsx` / `.md` de un sitio personal o portfolio que sospeche fue generado con IA. NO la actives para revisión general de código, refactor, bugs funcionales, performance, accesibilidad pura o linteo de proyectos serios.
---

# slop-audit — Detector de "AI slop" en webs vibe-coded

Nace de un caso real: un portfolio generado con IA que tenía `href="#"` sin rellenar, un enlace de LinkedIn genérico, barras de skill con porcentajes inventados y contradicciones entre el About ("técnico de soporte") y las skills mostradas (95% en React).

## Cómo usar esta skill

Cuando el usuario te pida auditar un portfolio o web (y la skill se dispare), sigue SIEMPRE este pipeline de 2 fases:

### Fase 1 — Escaneo determinista (script de Python)

1. Identifica qué archivos auditar (los `.html`, `.jsx`, `.tsx`, `.js`, `.ts`, `.md`, `.markdown` que el usuario haya mencionado o que estén en el directorio que pidió).
2. Ejecuta el script con:

   ```
   python <ruta_a_esta_skill>/scripts/slop_scan.py <archivo_o_carpeta> --json -o .slop-report.json
   ```

   - El script usa SOLO la stdlib de Python (3.8+). No requiere `pip install` de nada.
   - No hace ninguna llamada a APIs externas. Todo el análisis determinista ocurre localmente.
   - La salida JSON contiene: hallazgos priorizados (🔴/🟡/🟢), contexto extraído y el score.

3. Lee el JSON generado y entra a la Fase 2.

### Fase 2 — Análisis de coherencia narrativa (tu razonamiento)

El script NO puede detectar contradicciones semánticas. Ese es TRABAJO TUYO. Solo PROCÉDE a esta fase si en el JSON hay contexto suficiente (campo `about` no vacío AND campo `skills` no vacío).

**Cuando lo invoques, haz uno o varios de estos chequeos con el contexto extraído:**

- **About ↔ Skills**: compara el primer párrafo del `about` con la lista de `skills` (label + pct). ¿La narrativa personal cuadra con los porcentajes? Ejemplo de contradicción: "soy técnico de soporte" + "React 95%". Devuelve `INCONSISTENTE` / `OK` / `DUDOSO` + 1 línea de justificación citando el excerpt.
- **Identidad coherente**: compara `nombre_declarado` con `redes` declaradas. ¿Una persona con 10 skills a 95% no tiene GitHub? ¿El LinkedIn es genérico? Devuelve veredicto.
- **Hero auténtico**: ¿el `hero` suena autogenerado o auténtico? Frases tipo "moderna y elegante", "creada con amor", "boceto de la aplicación" son fingerprints de slop. Veredicto 0-10.

No hagas más inferencias que esas. La regla de oro es **no invocar tu razonamiento si hay menos de 2 hallazgos rojos o menos de 4 amber** — en ese caso el sitio está limpio y no vale la pena gastar tokens.

### Fase 3 — Reporte final

Renderiza el reporte en el formato exacto que entrega el script (ASCII pretty, tabla rojos/amber/menores) y AÑADE al final una sección titulada:

```
ANÁLISIS DE COHERENCIA NARRATIVA  🤔
  › Hallazgo 1: <tu juicio>
    Evidencia: <excerpt citado> ⟷ <titulo skill bar 95%>
    Veredicto: INCONSISTENTE / OK / DUDOSO

  › Hallazgo 2: ...
```

Si decidiste no invocar la inferencia porque el sitio estaba limpio, escribe:
```
ANÁLISIS DE COHERENCIA NARRATIVA  🤔
  · Sitio sin hallazgos críticos. No se invoca inferencia narrativa.
```

## Formato del reporte

El script ya entrega el reporte formateado. Tu única tarea es añadir la sección narrativa arriba. NO cambies el resto del reporte.

El score es 0-100, donde **100 = sitio limpio** y **0 = slop absoluto**.

## Reglas de comportamiento

- **Sé transparente**: lo detectado por regex LLEVA icono 🔴/🟡/🟢 y línea. Lo inferido por ti LLEVA icono 🤔 y la sección separada — el usuario debe distinguir "esto es slop objetivo" vs "esto es inferencia".
- **Tri-estado**: nunca digas "roto" en una inferencia — usa `INCONSISTENTE` / `OK` / `DUDOSO`.
- **No alucines**: si el script no extrajo `about`, no inventes un about. Si no hay skills, no inventes skills.
- **No edites archivos del usuario** durante el scan. Solo lee y reporta. Si el usuario pide arreglar algo, pídele confirmación explícita primero.
- **Idioma del reporte**: español por defecto. Sólo cambia a inglés si el usuario te pidió el audit en inglés.

## Limitaciones conocidas

- El scanner puede dar falsos positivos en handles cortos de LinkedIn (`linkedin.com/in/ai`) — los marca como 🟡 (sospechoso), no como 🔴. Si el usuario te dice "ese handle es real", descarta el hallazgo.
- En JSX/TSX el parser es regex, no un AST: no detecta imports sin usar ni refs rotas (la skill novalida código, valida slop).
- El detector de idioma body vs `lang` declarado usa stop-words; para textos muy cortos puede fallar.
- Los porcentajes de skill `< 80` nunca se marcan como mágicos — sólo se marcan acumulaciones sospechosas (≥5 barras con mismo pct, o ≥3 barras ≥95%, o secuencia mágica 80-100).

## Estructura de la skill

```
slop-audit/
├── SKILL.md                 # este archivo
├── scripts/
│   ├── slop_scan.py         # scanner determinista (classmethods stdlib)
│   └── rules.py             # reglas editables por el usuario
├── examples/
│   ├── clean_portfolio.html # caso limpio (0 rojos esperados)
│   ├── slop_portfolio.html  # caso real de slop
│   └── edge_*.html          # casos edge para afinar
├── tests/
│   └── run_tests.py         # suite sin pytest, stdlib only
└── README.md
```
