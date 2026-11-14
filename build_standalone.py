"""Build a self-contained dashboard HTML: page markup + a small runtime that
provides the same dash.* API the page code uses, with the cleaned data inlined."""
import json, re, sys
page = open('dash/index.html').read()
d3 = open('/opt/npm-tools/node_modules/d3/dist/d3.min.js').read()
csv = open('out/cleaned.csv').read()
tests = json.load(open('out/stat_tests.json'))['rows']
scripts = re.findall(r'<script>(.*?)</script>', page, re.S)
body = re.sub(r'<script>.*?</script>', '', page, flags=re.S).replace('<meta name="dash-one-writer">', '')
runtime = r'''
const RAW = {customers: d3.csvParse(CSVTEXT, (o) => { for (const k in o) if (o[k] === '') o[k] = null; return o; }), stat_tests: TESTS};
const calcs = {}, draws = {}, onDatas = [];
const defaults = {gender:'', season:'', category:'', age_group:'', subscribed:''};
let params = {...defaults}, cache = {};
const cs = getComputedStyle(document.documentElement);
window.dash = {
  colors: ['var(--series-1)', 'var(--series-2)'],
  params: () => params,
  calc: (id, spec) => { calcs[id] = spec; },
  data: (id) => {
    if (RAW[id]) return {status: 'ok', data: RAW[id]};
    if (calcs[id]) { if (!(id in cache)) cache[id] = calcs[id].fn(...calcs[id].inputs.map((i) => dash.data(i).data)); return {status: 'ok', data: cache[id]}; }
    return {status: 'missing', data: []};
  },
  onData: (fn) => { onDatas.push(fn); fn(); },
  draw: (name, fn) => { draws[name] = fn; },
  setParams: (p) => { params = {...params, ...p}; rerun(); },
  resetParams: () => { params = {...defaults}; rerun(); },
};
function rerun() {
  cache = {};
  onDatas.forEach((f) => f());
  for (const [n, fn] of Object.entries(draws)) document.querySelectorAll(`[data-draw="${n}"]`).forEach((el) => { try { fn(el); } catch (e) { console.error(n, e); } });
}
let lastW = 0;
window.addEventListener('resize', () => { const w = window.innerWidth; if (Math.abs(w - lastW) > 20) { lastW = w; rerun(); } });
'''
html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Customer Shopping Behavior Dashboard</title>
<style>
:root {{ --color-fg:#1f1e1d; --color-fg-muted:#6b6a68; --color-bg:#ffffff; --color-panel:#faf9f7; --color-border-line:#e6e3de;
  --color-ok:#2f7d4f; --color-warn:#c27c0e; --color-bad:#b3261e; --series-1:#2a6fb0; --series-2:#c56b2c;
  --font-anthropic-sans: system-ui, -apple-system, "Segoe UI", Roboto, Inter, sans-serif; --font-anthropic-serif: Georgia, "Times New Roman", serif;
  --cds-font-size-title:30px; --cds-font-size-heading:19px; --cds-font-size-body:14px; --cds-font-size-caption:12px; --cds-font-weight-medium:600;
  --cds-gap-xs:4px; --cds-gap-sm:6px; --cds-gap-md:14px; --cds-gap-lg:20px; --cds-gap-xl:32px; --cds-pad-md:10px; --cds-pad-lg:18px; --cds-radius:10px;
  --cds-text-secondary:#5f5e5b; --cds-chart-grid:#e3e0da; --cds-surface-popover:#ffffff; --cds-border:#d9d5ce; --cds-shadow-popover:0 4px 14px rgba(0,0,0,.12); }}
@media (prefers-color-scheme: dark) {{ :root {{ --color-fg:#ecebe8; --color-fg-muted:#a3a19c; --color-bg:#1c1b1a; --color-panel:#252422; --color-border-line:#3a3936;
  --series-1:#5b9be0; --cds-text-secondary:#b4b2ad; --cds-chart-grid:#3a3936; --cds-surface-popover:#2c2b29; --cds-border:#45433f; color-scheme: dark; }} }}
html, body {{ background: var(--color-bg); margin: 0; }}
#dash-root {{ max-width: 1280px; margin: 0 auto; padding: 24px clamp(14px, 3vw, 32px) 48px; }}
.dash-select {{ font: inherit; font-size: 13px; padding: 5px 8px; border-radius: 8px; border: 1px solid var(--color-border-line); background-color: var(--color-bg); color: var(--color-fg); min-width: 110px; }}
</style>
<script>{d3}</script>
<script>const CSVTEXT = {json.dumps(csv)}; const TESTS = {json.dumps(tests)};</script>
<script>{runtime}</script>
</head><body><div id="dash-root">{body}</div>
''' + ''.join(f'<script>{s}</script>\n' for s in scripts) + '<script>rerun();</script>\n</body></html>\n'
open(sys.argv[1], 'w').write(html)
print(len(html))
