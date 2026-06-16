const fmtTWD = (n) =>
  n == null ? "—" : `NT$${Math.round(n).toLocaleString("en-US")}`;

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    const err = new Error(body?.detail?.message || r.statusText);
    err.detail = body?.detail;
    throw err;
  }
  return r.json();
}

async function loadHealth() {
  try {
    const h = await fetchJSON("/api/health");
    document.getElementById("health-strip").textContent =
      `${h.records.toLocaleString()} postings indexed · sources: ${h.sources.join(", ")}`;
  } catch (e) {
    document.getElementById("health-strip").textContent = "API unreachable.";
  }
}

async function populateRoles() {
  const { roles } = await fetchJSON("/api/roles");
  for (const id of ["role-select", "underpaid-role"]) {
    const sel = document.getElementById(id);
    sel.innerHTML = "";
    for (const r of roles) {
      const opt = document.createElement("option");
      opt.value = r.title;
      opt.textContent = `${r.title} (${r.postings})`;
      sel.appendChild(opt);
    }
  }
}

function percentileTable(data) {
  const cells = ["p10", "p25", "p50", "p75", "p90"]
    .map((p) => `<div class="cell"><span class="label">${p.toUpperCase()}</span>
       <span class="value">${fmtTWD(data[p])}</span></div>`)
    .join("");
  return `<div class="percentile-row">${cells}</div>
    <p class="hint" style="margin-top:1rem">Sample size: ${data.sample_size} postings</p>`;
}

document.getElementById("benchmark-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  const params = new URLSearchParams();
  for (const [k, v] of fd.entries()) if (v) params.append(k, v);
  const out = document.getElementById("benchmark-result");
  out.innerHTML = "Loading…";
  try {
    const data = await fetchJSON(`/api/benchmark?${params}`);
    out.innerHTML = percentileTable(data);
  } catch (err) {
    out.innerHTML = `<p class="error">${err.message}</p>`;
  }
});

document.getElementById("underpaid-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  const params = new URLSearchParams();
  for (const [k, v] of fd.entries()) if (v) params.append(k, v);
  const out = document.getElementById("underpaid-result");
  out.innerHTML = "Loading…";
  try {
    const data = await fetchJSON(`/api/me/underpaid?${params}`);
    const sign = data.gap_pct >= 0 ? "+" : "";
    out.innerHTML = `
      <p><span class="verdict ${data.verdict}">${data.verdict.replace("_", " ")}</span>
      You earn ${sign}${data.gap_pct}% vs. the market median (${fmtTWD(data.market_median_monthly_twd)}).</p>
      ${percentileTable(data.benchmark)}`;
  } catch (err) {
    out.innerHTML = `<p class="error">${err.message}</p>`;
  }
});

async function loadSkills() {
  const out = document.getElementById("skills-result");
  try {
    const { skills } = await fetchJSON("/api/skills/trending?top=15");
    const rows = skills
      .map(
        (s) => `<tr><td>${s.skill}</td><td>${s.postings.toLocaleString()}</td>
          <td>${fmtTWD(s.median_pay_twd)}</td></tr>`,
      )
      .join("");
    out.innerHTML = `<table><thead><tr><th>Skill</th><th>Postings</th><th>Median monthly</th></tr></thead><tbody>${rows}</tbody></table>`;
  } catch (e) {
    out.innerHTML = `<p class="error">Could not load skills.</p>`;
  }
}

(async () => {
  await loadHealth();
  await populateRoles();
  await loadSkills();
})();
