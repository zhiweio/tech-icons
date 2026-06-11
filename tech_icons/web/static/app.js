// tech-icons frontend — vanilla JS + Tailwind + daisyUI
// No build step, no framework. Single-file logic.

(() => {
  "use strict";

  // ---- State ----
  const state = {
    query: "",
    vendor: null,
    category: null,
    view: "browse", // 'browse' | 'compare'
    page: 0,
    pageSize: 60,
    items: [],
    total: 0,
    vendors: {},
    concepts: [],
    currentIcon: null,
  };

  // ---- Vendor display config ----
  // Maps internal vendor key → daisyUI badge variant + label
  const VENDOR_STYLE = {
    aws: { badge: "badge-warning", label: "AWS" },
    azure: { badge: "badge-info", label: "Azure" },
    gcp: { badge: "badge-success", label: "GCP" },
    microsoft: { badge: "badge-secondary", label: "Microsoft" },
    cncf: { badge: "badge-primary", label: "CNCF" },
    devicon: { badge: "badge-accent", label: "Devicon" },
    developer: { badge: "badge-neutral", label: "Developer" },
    alibabacloud: { badge: "badge-warning", label: "Alibaba Cloud" },
    digitalocean: { badge: "badge-info", label: "DigitalOcean" },
    elastic: { badge: "badge-accent", label: "Elastic" },
    firebase: { badge: "badge-warning", label: "Firebase" },
    generic: { badge: "badge-ghost", label: "Generic" },
    gis: { badge: "badge-neutral", label: "GIS" },
    ibm: { badge: "badge-primary", label: "IBM" },
    kubernetes: { badge: "badge-info", label: "Kubernetes" },
    oci: { badge: "badge-error", label: "OCI" },
    onprem: { badge: "badge-ghost", label: "On-Prem" },
    openstack: { badge: "badge-error", label: "OpenStack" },
    outscale: { badge: "badge-neutral", label: "Outscale" },
    programming: { badge: "badge-success", label: "Programming" },
    saas: { badge: "badge-accent", label: "SaaS" },
  };

  function vendorBadgeClass(v) {
    return VENDOR_STYLE[v]?.badge || "badge-ghost";
  }

  function vendorLabel(v) {
    return VENDOR_STYLE[v]?.label || v;
  }

  // ---- DOM helpers ----
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ---- Toast ----
  let toastTimer = null;
  function toast(msg) {
    const t = $("#toast");
    $("#toast-msg").textContent = msg;
    t.classList.remove("hidden");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.add("hidden"), 2000);
  }

  // ---- API ----
  async function api(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const ct = res.headers.get("content-type") || "";
    if (ct.includes("application/json")) return res.json();
    return res.text();
  }

  // ---- Rendering ----
  function iconCard(entry) {
    const v = entry.vendor;
    const id = entry.id;
    const name = entry.name || id.split("/").pop();
    const safeId = id.replace(/"/g, "&quot;");
    return `
      <div class="card card-compact bg-base-100 hover:shadow-md cursor-pointer border border-base-300 transition" data-id="${safeId}">
        <div class="card-body items-center text-center !p-3">
          <div class="icon-card-preview">
            <img src="/api/icon/${encodeURI(id)}"
                 alt="${name}"
                 loading="lazy"
                 onerror="this.style.opacity='0.2'" />
          </div>
          <div class="text-xs font-medium line-clamp-2 leading-tight min-h-[2.2em]">${escapeHtml(name)}</div>
          <div class="flex flex-wrap gap-1 justify-center">
            <span class="badge badge-sm ${vendorBadgeClass(v)}">${vendorLabel(v)}</span>
          </div>
        </div>
      </div>
    `;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderGrid(items, append = false) {
    const grid = $("#icon-grid");
    const html = items.map(iconCard).join("");
    if (append) grid.insertAdjacentHTML("beforeend", html);
    else grid.innerHTML = html;

    $("#empty-state").classList.toggle("hidden", items.length > 0 || state.items.length > 0);
    const hasMore = state.items.length < state.total;
    $("#load-more-wrap").classList.toggle("hidden", !hasMore || state.query);
  }

  function renderVendorFilters() {
    const html = ["all"].concat(Object.keys(state.vendors)).map((v) => {
      const isAll = v === "all";
      const active = (isAll && !state.vendor) || state.vendor === v;
      const count = isAll
        ? Object.values(state.vendors).reduce((a, b) => a + b, 0)
        : state.vendors[v];
      const cls = active
        ? "btn-primary"
        : isAll
          ? "btn-ghost"
          : `btn-outline ${vendorBadgeClass(v).replace("badge-", "btn-")}`;
      return `
        <button class="btn btn-xs ${cls}" data-vendor="${isAll ? "" : v}">
          ${isAll ? "All" : vendorLabel(v)} <span class="opacity-60">${count}</span>
        </button>
      `;
    }).join("");
    $("#vendor-filters").innerHTML = html;

    $$("#vendor-filters [data-vendor]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.vendor = btn.dataset.vendor || null;
        renderVendorFilters();
        reloadBrowse();
      });
    });
  }

  function updateResultCount() {
    if (state.query) {
      $("#result-count").textContent = `${state.items.length} match${state.items.length === 1 ? "" : "es"}`;
    } else {
      $("#result-count").textContent = `${state.items.length} of ${state.total}`;
    }
  }

  // ---- Data loaders ----
  async function loadVendors() {
    state.vendors = await api("/api/vendors");
    const total = Object.values(state.vendors).reduce((a, b) => a + b, 0);
    $("#catalog-meta").textContent = `${total} icons`;
    $("#catalog-meta").classList.remove("hidden");
    renderVendorFilters();
  }

  async function loadConcepts() {
    state.concepts = await api("/api/concepts");
    const select = $("#concept-select");
    select.innerHTML =
      `<option value="">— select concept —</option>` +
      state.concepts
        .map(
          (c) =>
            `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)} (${c.vendors.join(", ")})</option>`,
        )
        .join("");
  }

  async function reloadBrowse() {
    state.page = 0;
    state.items = [];
    if (state.query.trim()) {
      const params = new URLSearchParams({ q: state.query.trim(), limit: 100 });
      if (state.vendor) params.set("vendor", state.vendor);
      const results = await api(`/api/search?${params}`);
      state.items = results.map((r) => r.icon_entry);
      state.total = state.items.length;
    } else {
      const params = new URLSearchParams({
        limit: state.pageSize,
        offset: 0,
      });
      if (state.vendor) params.set("vendor", state.vendor);
      const data = await api(`/api/icons?${params}`);
      state.items = data.items;
      state.total = data.total;
    }
    renderGrid(state.items);
    updateResultCount();
  }

  async function loadMore() {
    if (state.query) return; // search returns all in one shot
    state.page += 1;
    const offset = state.page * state.pageSize;
    const params = new URLSearchParams({
      limit: state.pageSize,
      offset: String(offset),
    });
    if (state.vendor) params.set("vendor", state.vendor);
    const data = await api(`/api/icons?${params}`);
    state.items = state.items.concat(data.items);
    renderGrid(data.items, true);
    updateResultCount();
  }

  // ---- Compare view ----
  async function loadConceptComparison(name) {
    if (!name) {
      $("#concept-result").innerHTML = "";
      return;
    }
    try {
      const data = await api(`/api/concepts/${encodeURIComponent(name)}`);
      renderConceptResult(data);
    } catch (e) {
      $("#concept-result").innerHTML = `<div class="alert alert-error">Failed to load: ${escapeHtml(e.message)}</div>`;
    }
  }

  function renderConceptResult(data) {
    const vendors = Object.keys(data.icons).sort();
    if (!vendors.length) {
      $("#concept-result").innerHTML = `<div class="alert">No icons resolved for concept "${escapeHtml(data.name)}".</div>`;
      return;
    }
    const html = `
      <div class="mb-4">
        <h2 class="text-xl font-bold">${escapeHtml(data.name)}</h2>
        <p class="text-sm opacity-70">${vendors.length} vendor(s): ${vendors.map((v) => vendorLabel(v)).join(", ")}</p>
      </div>
      <div class="grid gap-4" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));">
        ${vendors
          .map(
            (v) => `
          <div class="card bg-base-100 border border-base-300">
            <div class="card-body !p-4">
              <h3 class="card-title text-sm">
                <span class="badge ${vendorBadgeClass(v)}">${vendorLabel(v)}</span>
              </h3>
              <div class="space-y-2 mt-2">
                ${data.icons[v]
                  .map(
                    (entry) => `
                  <div class="flex items-center gap-3 p-2 rounded hover:bg-base-200 cursor-pointer" data-id="${escapeHtml(entry.id)}">
                    <div class="w-10 h-10 flex-none flex items-center justify-center">
                      <img src="/api/icon/${encodeURI(entry.id)}" class="w-full h-full" alt="${escapeHtml(entry.name)}" />
                    </div>
                    <div class="text-xs min-w-0">
                      <div class="font-medium truncate">${escapeHtml(entry.name)}</div>
                      <div class="opacity-50 truncate font-mono">${escapeHtml(entry.id)}</div>
                    </div>
                  </div>
                `,
                  )
                  .join("")}
              </div>
            </div>
          </div>
        `,
          )
          .join("")}
      </div>
      ${data.missing?.length ? `<div class="alert alert-warning mt-4 text-xs">Missing icon entries: ${data.missing.map(escapeHtml).join(", ")}</div>` : ""}
    `;
    $("#concept-result").innerHTML = html;
  }

  // ---- Detail modal ----

  // Some vendor SVGs (notably Microsoft Fabric) ship with `width="20" height="20"`
  // but **no `viewBox`**. When inlined and stretched via CSS, the content stays
  // pinned at its intrinsic pixel size in the top-left and looks tiny. Synthesize
  // a viewBox from the width/height attributes so CSS scaling works.
  function ensureSvgViewBox(svgMarkup) {
    const doc = new DOMParser().parseFromString(svgMarkup, "image/svg+xml");
    const svg = doc.documentElement;
    if (!svg || svg.nodeName.toLowerCase() !== "svg") return svgMarkup;
    if (svg.hasAttribute("viewBox")) return svgMarkup;

    const parseLen = (v) => {
      if (!v) return null;
      const n = parseFloat(String(v));
      return Number.isFinite(n) && n > 0 ? n : null;
    };
    const w = parseLen(svg.getAttribute("width"));
    const h = parseLen(svg.getAttribute("height"));
    if (!w || !h) return svgMarkup;

    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    return new XMLSerializer().serializeToString(svg);
  }

  async function openDetail(id) {
    try {
      const entry = await api(`/api/icons/${encodeURI(id)}`);
      state.currentIcon = entry;

      // Check available formats for preview rendering
      const hasSvg = entry.formats && entry.formats.svg;
      const hasPng = entry.formats && entry.formats.png;

      if (hasSvg) {
        const svgRaw = await api(`/api/icon/${encodeURI(id)}?format=raw&image_type=svg`);
        $("#detail-preview").innerHTML = ensureSvgViewBox(svgRaw);
      } else if (hasPng) {
        $("#detail-preview").innerHTML = `<img src="/api/icon/${encodeURI(id)}?image_type=png" class="max-w-full max-h-64 object-contain" alt="${escapeHtml(entry.name)}" />`;
      } else {
        $("#detail-preview").innerHTML = `<div class="text-error">No preview available</div>`;
      }

      $("#detail-name").textContent = entry.name;
      $("#detail-badges").innerHTML = `
        <span class="badge ${vendorBadgeClass(entry.vendor)}">${vendorLabel(entry.vendor)}</span>
        <span class="badge badge-outline">${escapeHtml(entry.category)}</span>
      `;

      $("#meta-id").textContent = entry.id;
      $("#meta-vendor").textContent = vendorLabel(entry.vendor);
      $("#meta-category").textContent = entry.category;
      $("#meta-tags").innerHTML = (entry.tags || [])
        .map((t) => `<span class="badge badge-sm badge-ghost mr-1">${escapeHtml(t)}</span>`)
        .join("");
      $("#meta-aliases").innerHTML = (entry.aliases || [])
        .map((a) => `<span class="badge badge-sm badge-outline mr-1">${escapeHtml(a)}</span>`)
        .join("") || `<span class="opacity-50 text-xs">none</span>`;
      $("#meta-concepts").innerHTML = (entry.related_concepts || [])
        .map((c) => `<a class="badge badge-sm badge-primary mr-1 cursor-pointer" data-concept="${escapeHtml(c)}">${escapeHtml(c)}</a>`)
        .join("") || `<span class="opacity-50 text-xs">none</span>`;
      // Show raw SVG source only when SVG format is available
      if (hasSvg) {
        const svgRaw = await api(`/api/icon/${encodeURI(id)}?format=raw&image_type=svg`);
        $("#meta-svg").textContent = svgRaw;
      } else {
        $("#meta-svg").textContent = `(PNG-only icon — no SVG source available)`;
      }

      // Wire concept badge clicks → switch to compare view
      $$("#meta-concepts [data-concept]").forEach((el) => {
        el.addEventListener("click", () => {
          $("#detail-modal").close();
          switchView("compare");
          $("#concept-select").value = el.dataset.concept;
          loadConceptComparison(el.dataset.concept);
        });
      });

      $("#detail-modal").showModal();
    } catch (e) {
      toast(`Error: ${e.message}`);
    }
  }

  async function copyForCurrent(kind) {
    if (!state.currentIcon) return;
    const id = state.currentIcon.id;
    try {
      let text;
      if (kind === "id") text = id;
      else text = await api(`/api/icon/${encodeURI(id)}?format=${kind}`);
      await navigator.clipboard.writeText(text);
      toast(`Copied: ${kind}`);
    } catch (e) {
      toast(`Copy failed: ${e.message}`);
    }
  }

  // ---- View switching ----
  function switchView(view) {
    state.view = view;
    const isBrowse = view === "browse";
    $("#browse-view").classList.toggle("hidden", !isBrowse);
    $("#compare-view").classList.toggle("hidden", isBrowse);
    $("#tab-browse").classList.toggle("tab-active", isBrowse);
    $("#tab-compare").classList.toggle("tab-active", !isBrowse);
  }

  // ---- Theme ----
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    $("#theme-toggle").checked = theme === "light";
    localStorage.setItem("tech-icons-theme", theme);
  }

  function initTheme() {
    const saved = localStorage.getItem("tech-icons-theme") || "dark";
    applyTheme(saved);
    $("#theme-toggle").addEventListener("change", (e) => {
      applyTheme(e.target.checked ? "light" : "dark");
    });
  }

  // ---- Event wiring ----
  function debounce(fn, wait) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), wait);
    };
  }

  function wireEvents() {
    $("#search-input").addEventListener(
      "input",
      debounce((e) => {
        state.query = e.target.value;
        reloadBrowse();
      }, 300),
    );

    $("#icon-grid").addEventListener("click", (e) => {
      const card = e.target.closest("[data-id]");
      if (card) openDetail(card.dataset.id);
    });

    $("#concept-result").addEventListener("click", (e) => {
      const row = e.target.closest("[data-id]");
      if (row) openDetail(row.dataset.id);
    });

    $("#load-more").addEventListener("click", loadMore);

    $("#tab-browse").addEventListener("click", () => switchView("browse"));
    $("#tab-compare").addEventListener("click", () => switchView("compare"));

    $("#concept-select").addEventListener("change", (e) => {
      loadConceptComparison(e.target.value);
    });

    $$("[data-copy]").forEach((btn) => {
      btn.addEventListener("click", () => copyForCurrent(btn.dataset.copy));
    });
  }

  // ---- Boot ----
  async function boot() {
    initTheme();
    wireEvents();
    try {
      await Promise.all([loadVendors(), loadConcepts()]);
      await reloadBrowse();
    } catch (e) {
      toast(`Failed to load: ${e.message}`);
      console.error(e);
    }
  }

  document.addEventListener("DOMContentLoaded", boot);
})();
