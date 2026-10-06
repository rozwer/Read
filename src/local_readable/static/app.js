const $ = (selector) => document.querySelector(selector);
const form = $("#upload-form");
const fileInput = $("#pdf-file");
const dropZone = $("#drop-zone");
const modelSelect = $("#model");
const jobsRoot = $("#jobs");
let pollTimer;

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function loadStatus() {
  const status = await request("/api/status");
  const models = status.ollama.models || [];
  $("#ollama-status").textContent = status.ollama.available ? "稼働中" : "停止中";
  $("#ollama-status").className = status.ollama.available ? "ok" : "";
  modelSelect.innerHTML = models.length
    ? models.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("")
    : '<option value="">Ollamaモデルがありません</option>';
  $("#submit-button").disabled = !models.length;
}

function addTerm(source = "", target = "") {
  const row = document.createElement("div");
  row.className = "term-row";
  row.innerHTML = `<input class="term-source" type="text" placeholder="Spatial token" value="${escapeHtml(source)}"><input class="term-target" type="text" placeholder="空間トークン" value="${escapeHtml(target)}"><button type="button" aria-label="用語を削除">×</button>`;
  row.querySelector("button").addEventListener("click", () => { row.remove(); updateTermCount(); });
  $("#terms").append(row);
  updateTermCount();
}

function updateTermCount() {
  $("#term-count").textContent = `${document.querySelectorAll(".term-row").length}語`;
}

function glossary() {
  return [...document.querySelectorAll(".term-row")].map((row) => ({
    source: row.querySelector(".term-source").value.trim(),
    target: row.querySelector(".term-target").value.trim(),
  })).filter((item) => item.source && item.target);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files[0]) return;
  $("#submit-button").disabled = true;
  $("#form-message").textContent = "PDFを端末内へ取り込んでいます…";
  const data = new FormData();
  data.append("file", fileInput.files[0]);
  data.append("model", modelSelect.value);
  data.append("glossary", JSON.stringify(glossary()));
  try {
    await request("/api/jobs", { method: "POST", body: data });
    form.reset();
    $("#terms").innerHTML = "";
    updateTermCount();
    $("#form-message").textContent = "翻訳を開始しました。";
    await loadJobs();
  } catch (error) {
    $("#form-message").textContent = error.message;
  } finally {
    $("#submit-button").disabled = false;
  }
});

for (const type of ["dragenter", "dragover"]) dropZone.addEventListener(type, (event) => { event.preventDefault(); dropZone.classList.add("dragging"); });
for (const type of ["dragleave", "drop"]) dropZone.addEventListener(type, (event) => { event.preventDefault(); dropZone.classList.remove("dragging"); });
dropZone.addEventListener("drop", (event) => { if (event.dataTransfer.files[0]) fileInput.files = event.dataTransfer.files; });

async function loadJobs() {
  const jobs = await request("/api/jobs");
  jobsRoot.innerHTML = jobs.length ? jobs.map(jobHtml).join("") : '<p class="empty">まだ翻訳はありません。</p>';
  document.querySelectorAll("[data-read]").forEach((button) => button.addEventListener("click", () => openReader(jobs.find((job) => job.id === button.dataset.read))));
  clearTimeout(pollTimer);
  if (jobs.some((job) => ["queued", "running"].includes(job.state))) pollTimer = setTimeout(loadJobs, 2500);
}

function jobHtml(job) {
  const qa = job.page_count_matches === true ? `ページ一致 ${job.source_pages}/${job.translated_pages}` : job.message;
  const actions = job.state === "completed" ? `<button data-read="${job.id}">見開きで読む</button><a href="${job.translated_url}">訳文PDF</a><a href="${job.bilingual_url}">対訳PDF</a>` : "";
  const error = job.error ? `<p title="${escapeHtml(job.error)}">${escapeHtml(job.error.slice(0, 120))}</p>` : `<p>${escapeHtml(qa)}</p>`;
  return `<article class="job"><div><h3>${escapeHtml(job.filename)}</h3>${error}</div><div><span class="badge ${job.state}">${stateLabel(job.state)}</span></div><div class="job-actions">${actions}</div></article>`;
}

function openReader(job) {
  $("#reader-title").textContent = job.filename;
  $("#source-frame").src = `${job.source_url}#view=FitH`;
  $("#translated-frame").src = `${job.translated_url}#view=FitH`;
  $("#reader").classList.remove("hidden");
  $("#reader").scrollIntoView({ behavior: "smooth" });
}

function stateLabel(state) { return ({ queued: "待機中", running: "翻訳中", completed: "完了", failed: "失敗" })[state] || state; }
function escapeHtml(value = "") { const node = document.createElement("div"); node.textContent = value; return node.innerHTML; }

$("#add-term").addEventListener("click", () => addTerm());
$("#refresh").addEventListener("click", loadJobs);
$("#close-reader").addEventListener("click", () => $("#reader").classList.add("hidden"));
Promise.all([loadStatus(), loadJobs()]).catch((error) => { $("#form-message").textContent = error.message; });

