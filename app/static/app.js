async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function showModal(message) {
  const modal = document.getElementById("error-modal");
  const errorMessage = document.getElementById("error-message");
  if (!modal || !errorMessage) return;
  errorMessage.textContent = message;
  modal.classList.remove("hidden");
}

function hideModal() {
  const modal = document.getElementById("error-modal");
  if (!modal) return;
  modal.classList.add("hidden");
}

function formatNumber(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }
  return `${Number(value).toFixed(2)}${suffix}`;
}

function renderMetrics(data, prefix = "metric") {
  const growth = document.getElementById(`${prefix}-growth`);
  const pe = document.getElementById(`${prefix}-pe`);
  const gop = document.getElementById(`${prefix}-gop`);

  if (growth) growth.textContent = formatNumber(data.growth_rate, "%");
  if (pe) pe.textContent = formatNumber(data.pe_ratio);
  if (gop) gop.textContent = formatNumber(data.growth_over_pe);
}

function setupIndexPage() {
  const form = document.getElementById("home-search-form");
  if (!form) return;

  const closeBtn = document.getElementById("close-error-modal");

  if (closeBtn) closeBtn.addEventListener("click", hideModal);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const ticker = document.getElementById("ticker").value.trim();
    if (!ticker) {
      showModal("Enter a ticker symbol first.");
      return;
    }

    try {
      const data = await postJson("/api/stock", { ticker });
      window.location.href = `/stock/${encodeURIComponent(data.ticker)}`;
    } catch (error) {
      showModal(error.message || "Ticker not found.");
    }
  });
}

async function loadFavorites(industry = "") {
  const tableBody = document.getElementById("favorites-body");
  if (!tableBody) return;

  const query = industry ? `?industry=${encodeURIComponent(industry)}` : "";
  const response = await fetch(`/api/favorites${query}`);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Failed to load favorites");
  }

  tableBody.innerHTML = "";

  if (!data.length) {
    tableBody.innerHTML = `<tr><td colspan="6">No favorites found.</td></tr>`;
    return;
  }

  for (const item of data) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.ticker}</td>
      <td>${item.industry || "N/A"}</td>
      <td>${formatNumber(item.growth_rate, "%")}</td>
      <td>${formatNumber(item.pe_ratio)}</td>
      <td>${formatNumber(item.growth_over_pe)}</td>
      <td><button data-del="${item.ticker}">Remove</button></td>
    `;
    tableBody.appendChild(row);
  }

  tableBody.querySelectorAll("button[data-del]").forEach((button) => {
    button.addEventListener("click", async () => {
      const ticker = button.getAttribute("data-del");
      await fetch(`/api/favorites/${ticker}`, { method: "DELETE" });
      loadFavorites(industry);
    });
  });
}

function setupFavoritesPage() {
  const form = document.getElementById("industry-form");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const industry = document.getElementById("industry-filter").value.trim();
    loadFavorites(industry).catch((error) => showModal(error.message));
  });

  loadFavorites().catch((error) => showModal(error.message));
}

function setupDetailPage() {
  const panel = document.getElementById("detail-panel");
  if (!panel) return;

  const ticker = panel.getAttribute("data-ticker");
  const closeBtn = document.getElementById("close-error-modal");
  if (closeBtn) closeBtn.addEventListener("click", hideModal);

  postJson("/api/stock", { ticker })
    .then((data) => {
      const title = document.getElementById("result-title");
      if (title) title.textContent = `${data.name || "Unknown"} (${data.ticker})`;

      const industry = document.getElementById("result-industry");
      if (industry) industry.textContent = `Industry: ${data.industry || "N/A"}`;

      renderMetrics(data, "detail");

      const gopPass = document.getElementById("detail-gop-pass");
      if (gopPass) {
        gopPass.textContent = data.growth_over_pe_pass === null
          ? "N/A"
          : data.growth_over_pe_pass
          ? "PASS (> 1.00)"
          : "FAIL";
      }

      document.getElementById("detail-target").textContent = formatNumber(data.analyst_target_price);
      document.getElementById("detail-high").textContent = formatNumber(data.week_52_high);
      document.getElementById("detail-earnings").textContent = data.latest_quarter || "N/A";
      document.getElementById("detail-desc").textContent = data.description || "No description available.";

      const favoriteBtn = document.getElementById("detail-favorite-btn");
      if (favoriteBtn) {
        favoriteBtn.addEventListener("click", async () => {
          try {
            await postJson("/api/favorites", data);
            favoriteBtn.textContent = "Favorited";
            favoriteBtn.disabled = true;
          } catch (error) {
            showModal(error.message || "Could not save favorite");
          }
        });
      }
    })
    .catch((error) => showModal(error.message));
}

setupIndexPage();
setupFavoritesPage();
setupDetailPage();
