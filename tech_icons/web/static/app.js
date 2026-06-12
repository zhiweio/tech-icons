// tech-icons frontend — Cosmic Volcano theme
// Vanilla JS, no framework. Single-file logic.

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
  const VENDOR_LABELS = {
    aws: "AWS",
    azure: "Azure",
    gcp: "GCP",
    microsoft: "Microsoft",
    cncf: "CNCF",
    devicon: "Devicon",
    developer: "Developer",
    alibabacloud: "Alibaba Cloud",
    digitalocean: "DigitalOcean",
    elastic: "Elastic",
    firebase: "Firebase",
    generic: "Generic",
    gis: "GIS",
    ibm: "IBM",
    kubernetes: "Kubernetes",
    oci: "OCI",
    onprem: "On-Prem",
    openstack: "OpenStack",
    outscale: "Outscale",
    programming: "Programming",
    saas: "SaaS",
  };

  const VENDOR_CMP_CLASSES = {
    aws: "vendor-aws",
    azure: "vendor-azure",
    gcp: "vendor-gcp",
    microsoft: "vendor-microsoft",
    cncf: "vendor-cncf",
    devicon: "vendor-devicon",
    developer: "vendor-developer",
    alibabacloud: "vendor-alibabacloud",
    digitalocean: "vendor-digitalocean",
    elastic: "vendor-elastic",
    firebase: "vendor-firebase",
    generic: "vendor-generic",
    gis: "vendor-gis",
    ibm: "vendor-ibm",
    kubernetes: "vendor-kubernetes",
    oci: "vendor-oci",
    onprem: "vendor-onprem",
    openstack: "vendor-openstack",
    outscale: "vendor-outscale",
    programming: "vendor-programming",
    saas: "vendor-saas",
  };

  function vendorClass(v) {
    return VENDOR_CMP_CLASSES[v] || "vendor-generic";
  }

  function vendorLabel(v) {
    return VENDOR_LABELS[v] || v;
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
    toastTimer = setTimeout(() => t.classList.add("hidden"), 2200);
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
  let cardIndex = 0;

  function iconCard(entry, index) {
    const v = entry.vendor;
    const id = entry.id;
    const name = entry.name || id.split("/").pop();
    const safeId = id.replace(/"/g, "&quot;");
    const i = index != null ? index : cardIndex++;
    return `
      <div class="icon-card animate-in" data-id="${safeId}" style="--i: ${i}">
        <div class="icon-card-preview">
          <img src="/api/icon/${encodeURI(id)}"
               alt="${escapeHtml(name)}"
               loading="lazy"
               onerror="this.style.opacity='0.15'" />
        </div>
        <span class="icon-card-name">${escapeHtml(name)}</span>
        <span class="icon-card-vendor ${vendorClass(v)}">${vendorLabel(v)}</span>
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
    if (append) {
      const html = items.map((entry, idx) => iconCard(entry, cardIndex + idx)).join("");
      cardIndex += items.length;
      grid.insertAdjacentHTML("beforeend", html);
    } else {
      cardIndex = 0;
      const html = items.map((entry, idx) => iconCard(entry, idx)).join("");
      grid.innerHTML = html;
    }

    $("#empty-state").classList.toggle("hidden", items.length > 0 || state.items.length > 0);
    const hasMore = state.items.length < state.total;
    $("#load-more-wrap").classList.toggle("hidden", !hasMore || state.query);
  }

  function renderVendorFilters() {
    const vendorKeys = Object.keys(state.vendors);
    const total = vendorKeys.reduce((a, k) => a + state.vendors[k], 0);

    const html = [
      `<button class="filter-chip${!state.vendor ? " active" : ""}" data-vendor="">
        All <span class="count">${total}</span>
      </button>`,
    ]
      .concat(
        vendorKeys.map((v) => {
          const active = state.vendor === v;
          return `
        <button class="filter-chip${active ? " active" : ""}" data-vendor="${v}">
          ${vendorLabel(v)} <span class="count">${state.vendors[v]}</span>
        </button>
      `;
        }),
      )
      .join("");

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
    const vendorCount = Object.keys(state.vendors).length;
    // Update footer stats
    const fi = $("#footer-icon-count");
    const fv = $("#footer-vendor-count");
    if (fi) fi.textContent = `${total.toLocaleString()} icons`;
    if (fv) fv.textContent = `${vendorCount} vendors`;
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
      $("#concept-result").innerHTML = `<div class="empty-state" style="padding:40px">Failed to load: ${escapeHtml(e.message)}</div>`;
    }
  }

  function renderConceptResult(data) {
    const vendors = Object.keys(data.icons).sort();
    if (!vendors.length) {
      $("#concept-result").innerHTML = `<div class="empty-state" style="padding:40px">No icons resolved for concept "${escapeHtml(data.name)}".</div>`;
      return;
    }
    const html = `
      <div style="grid-column: 1 / -1; margin-bottom: 8px;">
        <h2 class="compare-concept-title">${escapeHtml(data.name)}</h2>
        <p class="compare-concept-meta">${vendors.length} vendor(s): ${vendors.map((v) => vendorLabel(v)).join(", ")}</p>
      </div>
      ${vendors
        .map(
          (v) => `
        <div class="compare-card">
          <div class="compare-card-header">
            <span class="compare-vendor-badge ${vendorClass(v)}">${vendorLabel(v)}</span>
          </div>
          ${data.icons[v]
            .map(
              (entry) => `
            <div class="compare-icon-row" data-id="${escapeHtml(entry.id)}">
              <div class="compare-icon-thumb">
                <img src="/api/icon/${encodeURI(entry.id)}" alt="${escapeHtml(entry.name)}" loading="lazy" />
              </div>
              <div class="compare-icon-info">
                <div class="ci-name">${escapeHtml(entry.name)}</div>
                <div class="ci-id">${escapeHtml(entry.id)}</div>
              </div>
            </div>
          `,
            )
            .join("")}
        </div>
      `,
        )
        .join("")}
      ${data.missing?.length ? `<div style="grid-column:1/-1;padding:12px;border-radius:8px;background:rgba(245,158,11,0.06);border:1px solid rgba(245,158,11,0.15);margin-top:8px;font-size:0.78rem;color:var(--text-secondary);">Missing icon entries: ${data.missing.map(escapeHtml).join(", ")}</div>` : ""}
    `;
    $("#concept-result").innerHTML = html;
  }

  // ---- Detail modal ----

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
        $("#detail-preview").innerHTML = `<img src="/api/icon/${encodeURI(id)}?image_type=png" style="max-width:100%;max-height:100%;object-fit:contain;" alt="${escapeHtml(entry.name)}" />`;
      } else {
        $("#detail-preview").innerHTML = `<span style="color:var(--accent-orange);font-size:0.82rem;">No preview</span>`;
      }

      $("#detail-name").textContent = entry.name;
      $("#detail-badges").innerHTML = `
        <span class="modal-badge ${vendorClass(entry.vendor)}">${vendorLabel(entry.vendor)}</span>
        <span class="modal-badge" style="background:var(--bg-surface);color:var(--text-secondary);">${escapeHtml(entry.category)}</span>
      `;

      $("#meta-id").textContent = entry.id;
      $("#meta-vendor").textContent = vendorLabel(entry.vendor);
      $("#meta-category").textContent = entry.category;
      $("#meta-tags").innerHTML = (entry.tags || [])
        .map((t) => `<span class="meta-chip">${escapeHtml(t)}</span>`)
        .join("");
      $("#meta-aliases").innerHTML = (entry.aliases || [])
        .map((a) => `<span class="meta-chip">${escapeHtml(a)}</span>`)
        .join("") || `<span style="font-size:0.78rem;color:var(--text-muted);">none</span>`;
      $("#meta-concepts").innerHTML = (entry.related_concepts || [])
        .map((c) => `<span class="meta-chip meta-chip-link" data-concept="${escapeHtml(c)}">${escapeHtml(c)}</span>`)
        .join("") || `<span style="font-size:0.78rem;color:var(--text-muted);">none</span>`;

      // SVG source
      if (hasSvg) {
        const svgRaw = await api(`/api/icon/${encodeURI(id)}?format=raw&image_type=svg`);
        $("#meta-svg").textContent = svgRaw;
      } else {
        $("#meta-svg").textContent = `(PNG-only icon — no SVG source available)`;
      }
      // Reset source toggle
      const srcToggle = $("#svg-source-toggle");
      const srcContent = $("#svg-source-content");
      srcToggle.textContent = "▶ View SVG source";
      srcContent.classList.remove("open");

      // Wire concept badge clicks → switch to compare view
      $$("#meta-concepts .meta-chip-link").forEach((el) => {
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
    $("#filter-bar").classList.toggle("hidden", !isBrowse);
    $("#tab-browse").classList.toggle("active", isBrowse);
    $("#tab-compare").classList.toggle("active", !isBrowse);
  }

  // ---- Theme ----
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("tech-icons-theme", theme);
  }

  function initTheme() {
    const saved = localStorage.getItem("tech-icons-theme") || "dark";
    applyTheme(saved);
    $("#theme-toggle").addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      applyTheme(current === "light" ? "dark" : "light");
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
    // Search
    $("#search-input").addEventListener(
      "input",
      debounce((e) => {
        state.query = e.target.value;
        reloadBrowse();
      }, 300),
    );

    // Icon card clicks (grid)
    $("#icon-grid").addEventListener("click", (e) => {
      const card = e.target.closest("[data-id]");
      if (card) openDetail(card.dataset.id);
    });

    // Compare result row clicks
    $("#concept-result").addEventListener("click", (e) => {
      const row = e.target.closest("[data-id]");
      if (row) openDetail(row.dataset.id);
    });

    // Load more
    $("#load-more").addEventListener("click", loadMore);

    // Nav tabs
    $("#tab-browse").addEventListener("click", () => switchView("browse"));
    $("#tab-compare").addEventListener("click", () => switchView("compare"));

    // Concept selector
    $("#concept-select").addEventListener("change", (e) => {
      loadConceptComparison(e.target.value);
    });

    // Copy buttons
    $$("[data-copy]").forEach((btn) => {
      btn.addEventListener("click", () => copyForCurrent(btn.dataset.copy));
    });

    // Modal close button
    $(".modal-close").addEventListener("click", () => {
      $("#detail-modal").close();
    });

    // Modal backdrop click to close
    $("#detail-modal").addEventListener("click", (e) => {
      if (e.target === $("#detail-modal")) {
        $("#detail-modal").close();
      }
    });

    // SVG source toggle
    $("#svg-source-toggle").addEventListener("click", () => {
      const content = $("#svg-source-content");
      const toggle = $("#svg-source-toggle");
      const isOpen = content.classList.toggle("open");
      toggle.textContent = isOpen ? "▼ Hide SVG source" : "▶ View SVG source";
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
