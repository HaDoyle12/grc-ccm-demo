"""Renderer: build a single self-contained site/index.html from the register.

No external JS/CSS, no CDN: the page is one file, so it can be published to
GitHub Pages, attached to a ticket, or archived as audit evidence as-is.
Every value is HTML-escaped in the browser (esc()) before it is rendered.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "collectors"))
from _common import AS_OF, DATA  # noqa: E402

ROOT = Path(__file__).parent
DATASETS = ["controls", "evidence", "findings", "risks", "policies", "training", "changes", "access_reviews", "repo_security"]

CSS = """
*{box-sizing:border-box}body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0;background:#f6f8fa;color:#1b1f23}
header{background:#0a2540;color:#fff;padding:16px 28px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
header h1{margin:0;font-size:19px}header span{opacity:.7;font-size:12px}
.banner{background:#fff8c5;color:#6b4f00;font-size:12px;padding:6px 28px;border-bottom:1px solid #eac54f}
.tabs{background:#0a2540;padding:6px 20px 0;display:flex;flex-wrap:wrap;gap:3px;border-bottom:3px solid #0969da}
.tabbtn{background:transparent;color:#aebfd4;border:none;border-radius:6px 6px 0 0;padding:9px 14px;cursor:pointer;font-size:13px;font-weight:500}
.tabbtn:hover{background:#13325a;color:#fff}.tabbtn.active{background:#f6f8fa;color:#0a2540;font-weight:700}
.tabbtn:focus-visible,.mode button:focus-visible{outline:2px solid #58a6ff;outline-offset:2px}
.mode{display:flex;gap:0;border:1px solid #3d5a80;border-radius:8px;overflow:hidden}
.mode button{background:transparent;color:#cfd9e6;border:none;padding:6px 12px;font-size:12px;cursor:pointer}
.mode button.on{background:#0969da;color:#fff;font-weight:600}
.panel{display:none;padding:18px 28px 50px}.panel.active{display:block}
h2{font-size:19px;margin:2px 0 4px;color:#0a2540}h3{font-size:14px;margin:18px 0 8px;color:#24292f}
.lastupd{font-size:11px;color:#6b7785;background:#eef1f4;display:inline-block;padding:3px 10px;border-radius:12px;margin:2px 0 12px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0 14px}
.card{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:12px 18px;min-width:130px}
.card .n{font-size:25px;font-weight:700}.card .l{font-size:11px;color:#57606a;text-transform:uppercase}.card .cs{font-size:11px;color:#8b949e;margin-top:2px}
table{border-collapse:collapse;width:100%;font-size:12px;background:#fff;margin:6px 0}
th,td{border:1px solid #eaecef;padding:5px 9px;text-align:left;vertical-align:top}
th{background:#f6f8fa;position:sticky;top:0;cursor:pointer}tr:hover{background:#fafbfc}
input,select{padding:6px 10px;margin:8px 8px 8px 0;border:1px solid #d0d7de;border-radius:6px;font-size:12px}input{width:280px}
.pill{padding:1px 8px;border-radius:10px;font-size:10.5px;white-space:nowrap}
.ok{background:#dafbe1;color:#1a7f37}.warn{background:#fff8c5;color:#9a6700}.bad{background:#ffebe9;color:#cf222e}.muted{background:#eef1f4;color:#57606a}.std{background:#ddf4ff;color:#0550ae}
a{color:#0969da;text-decoration:none}a:hover{text-decoration:underline}
.note{font-size:12px;color:#57606a;margin:8px 0}
.how{font-size:12px;color:#1b1f23;background:#fff;border-left:3px solid #0969da;padding:8px 12px;margin:8px 0;border-radius:0 6px 6px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.panelbox{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:14px;margin:8px 0}
.hbars{display:flex;flex-direction:column;gap:5px}.hbar{display:flex;align-items:center;gap:8px;font-size:11.5px}
.hl{width:170px;text-align:right;color:#57606a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ht{flex:1;max-width:300px;background:#eef1f4;border-radius:4px;height:14px;overflow:hidden}.hf{display:block;height:14px}.hv{width:44px;font-weight:600}
.heat td{text-align:center;font-weight:600}.c{text-align:center}
pre{background:#0d1117;color:#e6edf3;padding:12px;border-radius:8px;font-size:11.5px;overflow:auto;line-height:1.45}
.legend{font-size:11px;color:#57606a}.legend span{margin-right:12px}
"""

JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
let MODE = 'strict';
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $ = id => document.getElementById(id);
const pill = (t, cls) => `<span class="pill ${cls}">${esc(t)}</span>`;
const statusCls = s => ({'Effective':'ok','Needs attention':'warn','Not effective':'bad','Exception':'bad','Open':'warn','In remediation':'std','Closed':'muted','Current':'ok','Overdue':'bad','Due < 60 days':'warn','Critical':'bad','High':'warn','Moderate':'std','Low':'muted','Major NC':'bad','Minor NC':'warn','OFI':'std'}[s] || 'muted');
const st = c => MODE === 'strict' ? c.strict_status : c.audit_status;
const yes = v => v === true ? pill('✓','ok') : v === false ? pill('✗','bad') : pill('?','muted');
const link = (u, t) => u ? `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t);
const pct = (a, b) => b ? Math.round(1000 * a / b) / 10 : 0;

function card(n, l, cs, color) { return `<div class="card"><div class="n" style="color:${color||'#0a2540'}">${esc(n)}</div><div class="l">${esc(l)}</div>${cs?`<div class="cs">${esc(cs)}</div>`:''}</div>`; }
function hbars(items) { return '<div class="hbars">' + items.map(([l, v, max, col]) => `<div class="hbar"><div class="hl" title="${esc(l)}">${esc(l)}</div><div class="ht"><span class="hf" style="width:${max?100*v/max:0}%;background:${col}"></span></div><div class="hv">${esc(v)}${max===100?'%':''}</div></div>`).join('') + '</div>'; }
function donut(parts, label) {
  const tot = parts.reduce((a, p) => a + p[1], 0) || 1; let acc = 0; const R = 42, C = 2 * Math.PI * R;
  const segs = parts.map(([n, v, col]) => { const len = C * v / tot; const s = `<circle r="${R}" cx="55" cy="55" fill="none" stroke="${col}" stroke-width="16" stroke-dasharray="${len} ${C-len}" stroke-dashoffset="${-acc}" transform="rotate(-90 55 55)"><title>${esc(n)}: ${v}</title></circle>`; acc += len; return s; }).join('');
  return `<svg width="110" height="110" role="img" aria-label="${esc(label)}">${segs}<text x="55" y="60" text-anchor="middle" font-size="16" font-weight="700" fill="#0a2540">${pct(parts[0][1], tot)}%</text></svg>`;
}
function trend(h) {
  const W = 520, H = 140, P = 28, max = Math.max(...h.map(x => x.controls));
  const x = i => P + i * (W - 2 * P) / Math.max(h.length - 1, 1), y = v => H - P - (H - 2 * P) * v / max;
  const line = (k, col) => `<polyline fill="none" stroke="${col}" stroke-width="2.5" points="${h.map((p, i) => `${x(i)},${y(p[k])}`).join(' ')}"/>`;
  return `<svg width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="Effective controls trend">${line('audit_effective','#0969da')}${line('strict_effective','#1a7f37')}
    <text x="${P}" y="${H-6}" font-size="10" fill="#57606a">${esc(h[0].week)}</text><text x="${W-P}" y="${H-6}" font-size="10" text-anchor="end" fill="#57606a">${esc(h[h.length-1].week)}</text></svg>
    <div class="legend"><span style="color:#0969da">■ Audit view effective</span><span style="color:#1a7f37">■ Strict view effective</span></div>`;
}
function table(id, cols, rows) {
  const head = cols.map((c, i) => `<th data-i="${i}">${esc(c[0])}</th>`).join('');
  const body = rows.map(r => '<tr>' + cols.map(c => `<td${c[2]?` class="${c[2]}"`:''}>${c[1](r)}</td>`).join('') + '</tr>').join('');
  return `<table id="${id}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function overview() {
  const c = D.controls, eff = c.filter(x => st(x) === 'Effective').length, of = D.findings.filter(f => f.status !== 'Closed');
  const ev = D.evidence, tr = D.training, chg = D.changes;
  const trainPct = pct(tr.reduce((a, t) => a + t.completed, 0), tr.reduce((a, t) => a + t.population, 0));
  const doms = [...new Set(c.map(x => x.domain))].map(d => { const s = c.filter(x => x.domain === d); return [d, pct(s.filter(x => st(x) === 'Effective').length, s.length), 100]; }).sort((a, b) => a[1] - b[1]);
  const col = v => v >= 85 ? '#2da44e' : v >= 60 ? '#d4a72c' : '#cf222e';
  const sts = MODE === 'strict' ? [['Effective','#2da44e'],['Needs attention','#d4a72c'],['Not effective','#cf222e']] : [['Effective','#2da44e'],['Exception','#cf222e']];
  $('p-overview').innerHTML = `<h2>Continuous Control Monitoring — Overview</h2><div class="lastupd">Data as of ${esc(D.as_of)} · ${MODE==='strict'?'Strict internal view':'Audit-threshold view'}</div>
  <div class="cards">${card(c.length,'ISO 27001 controls','Annex A, 2022')}${card(pct(eff,c.length)+'%','Effective',eff+' of '+c.length, col(pct(eff,c.length)))}
  ${card(pct(c.filter(x=>x.automation==='Automated').length,c.length)+'%','Automated evidence','pulled by collectors')}${card(of.length,'Open findings',of.filter(f=>f.overdue).length+' overdue','#cf222e')}
  ${card(ev.filter(e=>e.stale).length,'Stale evidence','> 90 days old','#9a6700')}${card(pct(chg.filter(x=>x.within_sla).length,chg.length)+'%','Change review SLA','48h, from timelines')}${card(trainPct+'%','Training complete','all cohorts')}</div>
  <div class="how"><b>Strict vs audit view.</b> The strict view applies our internal bar (evidence &lt; 90 days, no open finding, ≥ 2 artefacts), so it shows more red than an auditor would. Use the toggle (top right) to show the audit-threshold view to stakeholders.</div>
  <div class="grid2"><div class="panelbox"><h3>Control status</h3>${donut(sts.map(([s,col])=>[s,c.filter(x=>st(x)===s).length,col]),'status')}
  <div class="legend">${sts.map(([s,col])=>`<span style="color:${col}">■ ${esc(s)} ${c.filter(x=>st(x)===s).length}</span>`).join('')}</div></div>
  <div class="panelbox"><h3>12-week trend</h3>${trend(D.history)}</div></div>
  <div class="panelbox"><h3>Effective % by domain (weakest first)</h3>${hbars(doms.map(([d,v])=>[d,v,100,col(v)]))}</div>`;
}

function controls() {
  const c = D.controls, themes = [...new Set(c.map(x => x.theme))], doms = [...new Set(c.map(x => x.domain))].sort();
  const sts = MODE === 'strict' ? ['Effective','Needs attention','Not effective'] : ['Effective','Exception'];
  const heat = '<table class="heat"><thead><tr><th>Domain</th>' + sts.map(s => `<th>${esc(s)}</th>`).join('') + '<th>Total</th></tr></thead><tbody>' +
    doms.map(d => { const s = c.filter(x => x.domain === d); return `<tr><td style="text-align:left">${esc(d)}</td>` + sts.map(k => { const n = s.filter(x => st(x) === k).length; return `<td class="${n ? statusCls(k) : ''}">${n || ''}</td>`; }).join('') + `<td>${s.length}</td></tr>`; }).join('') + '</tbody></table>';
  $('p-controls').innerHTML = `<h2>ISO Controls</h2><div class="lastupd">ISO/IEC 27001:2022 Annex A · source: GRC platform assessments + evidence collectors</div>
  <div class="grid2"><div class="panelbox"><h3>Domain × status</h3>${heat}</div><div class="panelbox"><h3>By theme</h3>${hbars(themes.map(t => { const s = c.filter(x => x.theme === t); return [t + ' (' + s.length + ')', pct(s.filter(x => st(x) === 'Effective').length, s.length), 100, '#0969da']; }))}
  <div class="how">Each row links back to its system of record. The register stores the link and status — never a copy of the evidence.</div></div></div>
  <input id="q" placeholder="Filter controls… (e.g. 8.8, IAM, Manual)" aria-label="Filter controls"><select id="fs" aria-label="Status filter"><option value="">All statuses</option>${sts.map(s=>`<option>${esc(s)}</option>`).join('')}</select>
  <div id="ctab"></div>`;
  const draw = () => {
    const q = $('q').value.toLowerCase(), fs = $('fs').value;
    const rows = c.filter(x => (!fs || st(x) === fs) && (!q || Object.values(x).join(' ').toLowerCase().includes(q)));
    $('ctab').innerHTML = `<div class="note">${rows.length} of ${c.length} controls</div>` + table('ct', [
      ['Control', r => link(r.grc_link, r.control_id)], ['Title', r => esc(r.title)], ['Domain', r => esc(r.domain)], ['Owner', r => esc(r.owner_team)],
      ['Automation', r => pill(r.automation, r.automation === 'Automated' ? 'ok' : r.automation === 'Manual' ? 'muted' : 'std')], ['Evidence from', r => esc(r.evidence_system)],
      ['Last tested', r => esc(r.last_tested)], ['Evidence', r => esc(r.evidence_count), 'c'], ['Open findings', r => r.open_findings ? pill(r.open_findings, 'warn') : '', 'c'],
      ['Status', r => pill(st(r), statusCls(st(r)))]], rows);
  };
  $('q').oninput = draw; $('fs').onchange = draw; draw();
}

function simple(id, title, sub, how, cards, cols, rows) {
  $(id).innerHTML = `<h2>${esc(title)}</h2><div class="lastupd">${esc(sub)}</div><div class="cards">${cards}</div>${how ? `<div class="how">${how}</div>` : ''}` + table(id + 't', cols, rows);
}

function render() {
  overview(); controls();
  const f = D.findings, open = f.filter(x => x.status !== 'Closed');
  simple('p-findings', 'Findings & Nonconformities', 'source: GitHub Project board (issue per finding)', 'Remediation windows: Major NC 30 days · Minor NC 90 days · OFI 180 days. Overdue is computed from the open date, not a manually set label.',
    card(open.length, 'Open') + card(open.filter(x => x.overdue).length, 'Overdue', '', '#cf222e') + card(open.filter(x => x.classification === 'Major NC').length, 'Major NC', '', '#cf222e') + card(f.filter(x => x.source === 'Continuous monitoring').length, 'Found by monitoring', 'not by an auditor', '#1a7f37'),
    [['ID', r => link(r.link, r.id)], ['Finding', r => esc(r.title)], ['Control', r => esc(r.control_id)], ['Class', r => pill(r.classification, statusCls(r.classification))], ['Source', r => esc(r.source)], ['Opened', r => esc(r.opened)], ['Due', r => esc(r.due) + (r.overdue ? ' ' + pill('overdue', 'bad') : '')], ['Owner', r => esc(r.owner_team)], ['Status', r => pill(r.status, statusCls(r.status))]], f);
  const rs = D.repo_security;
  simple('p-repos', 'Repository Security', 'source: GitHub REST API via gh api (this tab can run LIVE)', 'Unknown (?) means the token could not read the setting. Unknown is never counted as a pass.',
    card(rs.length, 'Repos in scope') + card(pct(rs.filter(r => r.branch_protection === true).length, rs.length) + '%', 'Branch protection') + card(pct(rs.filter(r => r.secret_scanning === true).length, rs.length) + '%', 'Secret scanning') + card(rs.reduce((a, r) => a + r.open_critical_vulns, 0), 'Open critical vulns', '', '#cf222e'),
    [['Repo', r => esc(r.repo)], ['Tier', r => pill(r.tier, statusCls(r.tier))], ['Branch protection', r => yes(r.branch_protection), 'c'], ['Req. reviews', r => esc(r.required_reviews), 'c'], ['Secret scanning', r => yes(r.secret_scanning), 'c'], ['Push protection', r => yes(r.push_protection), 'c'], ['Dependabot', r => yes(r.dependabot_alerts), 'c'], ['Code scanning', r => yes(r.code_scanning), 'c'], ['Critical vulns', r => r.open_critical_vulns ? pill(r.open_critical_vulns + (r.oldest_critical_days > 30 ? ' · ' + r.oldest_critical_days + 'd' : ''), r.oldest_critical_days > 30 ? 'bad' : 'warn') : '', 'c'], ['Signed releases', r => yes(r.signed_releases), 'c'], ['Last push', r => esc(r.last_push)]], rs);
  const ar = D.access_reviews;
  simple('p-access', 'Access Reviews', 'source: identity provider groups + review campaign decisions', '',
    card(ar.filter(a => a.complete).length + '/' + ar.length, 'Campaigns complete') + card(ar.reduce((a, r) => a + r.revoked, 0), 'Access revoked', 'this cycle'),
    [['Application', r => esc(r.application)], ['Users in scope', r => esc(r.users_in_scope), 'c'], ['Reviewed', r => esc(r.reviewed), 'c'], ['Revoked', r => esc(r.revoked), 'c'], ['Last campaign', r => esc(r.last_campaign)], ['Complete', r => yes(r.complete), 'c']], ar);
  const tr = D.training;
  simple('p-training', 'Security Awareness Training', 'source: HRIS roster joined to LMS completions on employee ID', 'People in the roster with no LMS record are shown as <b>no record</b> rather than dropped — that is the population an auditor samples.',
    tr.map(t => card(t.pct + '%', t.cohort, t.completed + ' of ' + t.population, t.pct >= 95 ? '#1a7f37' : '#9a6700')).join(''),
    [['Cohort', r => esc(r.cohort)], ['Population', r => esc(r.population), 'c'], ['Completed', r => esc(r.completed), 'c'], ['Overdue', r => esc(r.overdue), 'c'], ['No record', r => esc(r.no_record), 'c'], ['Completion', r => hbars([['', r.pct, 100, r.pct >= 95 ? '#2da44e' : '#d4a72c']])]], tr);
  const ch = D.changes;
  simple('p-changes', 'Change Management', 'source: emergency-change issues · SLA computed from issue timeline events', 'Review SLA is 48 hours from deploy to second-person review. The clock comes from timeline events, so a mis-configured bot label cannot change the number.',
    card(ch.length, 'Emergency changes', 'last 90 days') + card(pct(ch.filter(c => c.within_sla).length, ch.length) + '%', 'Reviewed within SLA') + card(ch.filter(c => !c.approved_by_second_person).length, 'Missing 2nd approver', '', '#cf222e'),
    [['Change', r => esc(r.id)], ['Opened', r => esc(r.opened)], ['Service', r => esc(r.service)], ['Review hours', r => esc(r.review_hours), 'c'], ['Within SLA', r => yes(r.within_sla), 'c'], ['2nd approver', r => yes(r.approved_by_second_person), 'c']], ch.slice().sort((a, b) => b.review_hours - a.review_hours));
  const po = D.policies;
  simple('p-policies', 'Policies & Standards', 'source: policy repo — last merged PR labelled annual-review', '',
    card(po.filter(p => p.status === 'Current').length, 'Current', '', '#1a7f37') + card(po.filter(p => p.status === 'Due < 60 days').length, 'Due < 60 days', '', '#9a6700') + card(po.filter(p => p.status === 'Overdue').length, 'Overdue', '', '#cf222e'),
    [['Policy', r => esc(r.policy)], ['Last review', r => esc(r.last_review)], ['Age (days)', r => esc(r.age_days), 'c'], ['Owner', r => esc(r.owner_team)], ['Status', r => pill(r.status, statusCls(r.status))]], po.slice().sort((a, b) => b.age_days - a.age_days));
  const rk = D.risks, order = {Critical: 0, High: 1, Moderate: 2, Low: 3};
  simple('p-risks', 'Risk Register', 'source: GitHub issues labelled "Risk Register"', '',
    ['Critical', 'High', 'Moderate', 'Low'].map(s => card(rk.filter(r => r.severity === s).length, s)).join(''),
    [['ID', r => esc(r.id)], ['Risk', r => esc(r.title)], ['Severity', r => pill(r.severity, statusCls(r.severity))], ['Treatment', r => esc(r.treatment)], ['Owner', r => esc(r.owner_team)], ['Last worked', r => esc(r.last_worked)]], rk.slice().sort((a, b) => order[a.severity] - order[b.severity]));
  const ev = D.evidence;
  simple('p-evidence', 'Evidence Inventory', 'source: evidence store (Microsoft Graph, metadata only) + GitHub Releases from Actions', 'Evidence produced by GitHub Actions is published as a release asset with a SHA-256 and a build-provenance attestation, so an auditor can verify it with <code>gh attestation verify</code>.',
    card(ev.length, 'Artefacts') + card(ev.filter(e => e.store === 'GitHub Actions').length, 'Machine-generated', 'by Actions') + card(ev.filter(e => e.stale).length, 'Stale > 90d', '', '#9a6700'),
    [['ID', r => esc(r.evidence_id)], ['Artefact', r => link(r.link, r.name)], ['Store', r => esc(r.store)], ['Control', r => esc(r.control_id)], ['Collected', r => esc(r.collected)], ['Age', r => r.stale ? pill(r.age_days + 'd', 'warn') : esc(r.age_days + 'd'), 'c'], ['SHA-256', r => `<code>${esc(r.sha256)}</code>`]], ev);
  const fr = Object.entries(D.freshness);
  $('p-pipeline').innerHTML = `<h2>Data Pipeline & Freshness</h2><div class="lastupd">How the numbers on this page are produced</div>
  <pre>${esc(D.diagram)}</pre>` + table('frt', [['Dataset', r => esc(r[0])], ['System of record', r => esc(r[1].source)], ['Mode', r => pill(r[1].mode, r[1].mode === 'live' ? 'ok' : 'std')], ['Rows', r => esc(r[1].rows), 'c'], ['Last success', r => esc((r[1].last_success || '').replace('T', ' '))], ['Status', r => pill(r[1].status, r[1].status === 'ok' ? 'ok' : 'bad')]], fr) +
  `<div class="how">Full write-up of every process: <a href="https://github.com/HaDoyle12/grc-ccm-demo/blob/main/docs/06-pipeline-processes.md">docs/06-pipeline-processes.md</a> · data connections: <a href="https://github.com/HaDoyle12/grc-ccm-demo/blob/main/docs/01-data-connections.md">docs/01</a> · audit evidence recipes: <a href="https://github.com/HaDoyle12/grc-ccm-demo/blob/main/docs/05-audit-evidence-examples.md">docs/05</a></div>`;
}

document.querySelectorAll('.tabbtn').forEach(b => b.onclick = () => {
  document.querySelectorAll('.tabbtn').forEach(x => { x.classList.toggle('active', x === b); x.setAttribute('aria-selected', x === b); });
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === b.dataset.p));
  history.replaceState(null, '', '#' + b.dataset.p.slice(2));
});
document.querySelectorAll('.mode button').forEach(b => b.onclick = () => {
  MODE = b.dataset.m; document.querySelectorAll('.mode button').forEach(x => { x.classList.toggle('on', x === b); x.setAttribute('aria-pressed', x === b); }); render();
});
render();
const start = document.querySelector(`.tabbtn[data-p="p-${location.hash.slice(1)}"]`); if (start) start.click();
"""

TABS = [("overview", "Overview"), ("controls", "ISO Controls"), ("findings", "Findings"), ("repos", "Repo Security"),
        ("access", "Access Reviews"), ("training", "Training"), ("changes", "Change Mgmt"), ("policies", "Policies"),
        ("risks", "Risk Register"), ("evidence", "Evidence"), ("pipeline", "Data Pipeline")]

DIAGRAM = """ systems of record (one collector each)
 GRC platform ─ GitHub API ─ GitHub Project ─ Issues ─ Policy repo ─ HRIS+LMS ─ IdP ─ Evidence store
      │             │             │            │           │            │        │         │
  controls   repo_security    findings     risks/changes  policies   training  access   evidence
      └─────────────┴─────────────┴────────────┴───────────┴────────────┴────────┴─────────┘
                                     │  data/<dataset>.json  (+ _freshness.json)
                              build_register.py ──► data/register.db  +  exports/*.csv
                                     │
                                gen_html.py ──► site/index.html (this page)
                                     │
                     GitHub Actions ──► check_freshness.py ──► GitHub Pages
                                     └──► weekly snapshot Release (audit trail)"""


def main():
    data = {n: json.loads((DATA / f"{n}.json").read_text())["rows"] for n in DATASETS}
    data["history"] = json.loads((DATA / "history.json").read_text())
    data["freshness"] = json.loads((DATA / "_freshness.json").read_text())
    data["as_of"] = AS_OF.isoformat()
    data["diagram"] = DIAGRAM
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    tabs = "".join(f'<button class="tabbtn{" active" if i == 0 else ""}" role="tab" aria-selected="{str(i == 0).lower()}" data-p="p-{k}">{t}</button>' for i, (k, t) in enumerate(TABS))
    panels = "".join(f'<section class="panel{" active" if i == 0 else ""}" id="p-{k}" role="tabpanel"></section>' for i, (k, _) in enumerate(TABS))
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Northwind Cloud — ISO Control Command Center (demo)</title><style>{CSS}</style></head><body>
<header><div><h1>Northwind Cloud — ISO Control Command Center</h1><span>Continuous control monitoring · GitHub CLI + Actions · demo</span></div>
<div class="mode" role="group" aria-label="View"><button data-m="strict" class="on" aria-pressed="true">Strict internal</button><button data-m="audit" aria-pressed="false">Audit threshold</button></div></header>
<div class="banner">⚠️ Demo: Northwind Cloud is fictional and every number on this page is synthetic sample data. Repo Security can run live against this demo repository only.</div>
<nav class="tabs" role="tablist">{tabs}</nav>{panels}
<script id="data" type="application/json">{payload}</script><script>{JS}</script></body></html>"""
    out = ROOT / "site" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"dashboard written: {out.relative_to(ROOT)} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
