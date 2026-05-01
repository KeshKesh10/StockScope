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

function showModal(message, title = "Error") {
  const modal = document.getElementById("error-modal");
  const titleElement = document.getElementById("error-title");
  const errorMessage = document.getElementById("error-message");
  if (!modal || !errorMessage) return;
  if (titleElement) titleElement.textContent = title;
  errorMessage.textContent = message;
  modal.hidden = false;
  modal.classList.remove("hidden");
}

function hideModal() {
  const modal = document.getElementById("error-modal");
  if (!modal) return;
  modal.hidden = true;
  modal.classList.add("hidden");
}

function setupGlobalModal() {
  const modal = document.getElementById("error-modal");
  const closeBtn = document.getElementById("close-error-modal");
  if (!modal || !closeBtn) return;

  closeBtn.addEventListener("click", hideModal);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      hideModal();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      hideModal();
    }
  });
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

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const ticker = document.getElementById("ticker").value.trim();
    if (!ticker) {
      showModal("Enter a ticker symbol first.");
      return;
    }

    try {
      const data = await postJson("/api/stock", { ticker });
      sessionStorage.setItem("stockscope:lastStockResult", JSON.stringify(data));
      window.location.href = `/stock/${encodeURIComponent(data.ticker)}`;
    } catch (error) {
      const message = error.message || "Stock request failed.";
      const isRateLimited = /alpha vantage|too many requests|rate limit/i.test(message);
      showModal(message, isRateLimited ? "Rate Limit Reached" : "Ticker Not Found");
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
  const tableBody = document.getElementById("favorites-body");
  if (!tableBody) return;

  const form = document.getElementById("industry-form");
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const industry = document.getElementById("industry-filter").value.trim();
      loadFavorites(industry).catch((error) => showModal(error.message));
    });
  }

  loadFavorites().catch((error) => showModal(error.message));
}

function setupDetailPage() {
  const panel = document.getElementById("detail-panel");
  if (!panel) return;

  const ticker = panel.getAttribute("data-ticker");

  function renderDetailData(data) {
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
  }

  const cached = sessionStorage.getItem("stockscope:lastStockResult");
  if (cached) {
    try {
      const parsed = JSON.parse(cached);
      if (String(parsed.ticker || "").toUpperCase() === String(ticker || "").toUpperCase()) {
        renderDetailData(parsed);
        return;
      }
    } catch {
      // Ignore malformed cache and fetch from API.
    }
  }

  postJson("/api/stock", { ticker })
    .then((data) => {
      sessionStorage.setItem("stockscope:lastStockResult", JSON.stringify(data));
      renderDetailData(data);
    })
    .catch((error) => {
      const message = error.message || "Stock request failed.";
      const isRateLimited = /alpha vantage|too many requests|rate limit/i.test(message);
      showModal(message, isRateLimited ? "Rate Limit Reached" : "Ticker Not Found");
    });
}

function setupControlledSignupPage() {
  const form = document.getElementById("controlled-signup-form");
  if (!form) return;

  const state = {
    fields: {
      name: "",
      email: "",
      phone: "",
      category: "",
    },
    fieldErrors: {
      name: "",
      email: "",
      phone: "",
      category: "",
    },
    saveStatus: "READY",
  };

  const listElement = document.getElementById("signup-list");
  const saveStatusElement = document.getElementById("save-status");
  const submitButton = document.getElementById("signup-submit");
  const filterSelect = document.getElementById("category-filter");
  const applyFilterBtn = document.getElementById("apply-category-filter");

  function validateField(name, value) {
    if (name === "name") {
      return value.trim() ? "" : "Name Required";
    }
    if (name === "email") {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim()) ? "" : "Invalid Email";
    }
    if (name === "phone") {
      const digits = value.replace(/\D/g, "");
      return digits.length === 10 ? "" : "10-digit Phone Required";
    }
    if (name === "category") {
      return value ? "" : "Category Required";
    }
    return "";
  }

  function validate() {
    const nextErrors = {
      name: validateField("name", state.fields.name),
      email: validateField("email", state.fields.email),
      phone: validateField("phone", state.fields.phone),
      category: validateField("category", state.fields.category),
    };
    state.fieldErrors = nextErrors;
    return Object.values(nextErrors).every((error) => !error);
  }

  function renderErrors() {
    document.getElementById("error-name").textContent = state.fieldErrors.name;
    document.getElementById("error-email").textContent = state.fieldErrors.email;
    document.getElementById("error-phone").textContent = state.fieldErrors.phone;
    document.getElementById("error-category").textContent = state.fieldErrors.category;
  }

  function renderState() {
    if (saveStatusElement) saveStatusElement.textContent = state.saveStatus;
    submitButton.disabled = !validate() || state.saveStatus === "SAVING";
    renderErrors();
  }

  function renderList(items) {
    if (!listElement) return;
    listElement.innerHTML = "";
    if (!items.length) {
      listElement.innerHTML = "<li>No signups found.</li>";
      return;
    }
    for (const item of items) {
      const li = document.createElement("li");
      li.textContent = `${item.name} | ${item.email} | ${item.phone} | ${item.category}`;
      listElement.appendChild(li);
    }
  }

  async function loadSignups(category = "") {
    const query = category ? `?category=${encodeURIComponent(category)}` : "";
    const response = await fetch(`/api/signups${query}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to load signups");
    }
    renderList(payload);
  }

  for (const fieldName of Object.keys(state.fields)) {
    const element = document.getElementById(`signup-${fieldName}`);
    if (!element) continue;
    element.addEventListener("input", (event) => {
      state.fields[fieldName] = event.target.value;
      state.fieldErrors[fieldName] = validateField(fieldName, state.fields[fieldName]);
      renderState();
    });
    element.addEventListener("change", (event) => {
      state.fields[fieldName] = event.target.value;
      state.fieldErrors[fieldName] = validateField(fieldName, state.fields[fieldName]);
      renderState();
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validate()) {
      renderState();
      return;
    }

    state.saveStatus = "SAVING";
    renderState();

    try {
      const response = await fetch("/api/signups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state.fields),
      });
      const payload = await response.json();
      if (!response.ok) {
        if (payload.fieldErrors) {
          state.fieldErrors = {
            ...state.fieldErrors,
            ...payload.fieldErrors,
          };
        }
        throw new Error(payload.error || "Save failed");
      }

      state.saveStatus = "SUCCESS";
      state.fields = {
        name: "",
        email: "",
        phone: "",
        category: "",
      };

      document.getElementById("signup-name").value = "";
      document.getElementById("signup-email").value = "";
      document.getElementById("signup-phone").value = "";
      document.getElementById("signup-category").value = "";

      await loadSignups(filterSelect ? filterSelect.value : "");
    } catch (error) {
      state.saveStatus = "ERROR";
      showModal(error.message || "Could not save signup");
    }

    renderState();
  });

  if (applyFilterBtn) {
    applyFilterBtn.addEventListener("click", () => {
      loadSignups(filterSelect ? filterSelect.value : "").catch((error) => showModal(error.message));
    });
  }

  loadSignups().catch((error) => showModal(error.message));
  renderState();
}

setupGlobalModal();
setupIndexPage();
setupFavoritesPage();
setupDetailPage();
setupControlledSignupPage();
