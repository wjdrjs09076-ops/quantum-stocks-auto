const LATEST_URL = "./data/latest.json";
const HISTORY_URL = "./data/history.csv";

const TICKER_NAMES = {
  QSI: "Quantum-Si",
  QBTS: "D-Wave Quantum",
  RGTI: "Rigetti Computing",
  IONQ: "IonQ",
  QTUM: "Defiance Quantum ETF (QTUM)"
};

function fmtPrice(x) {
  if (x === null || x === undefined || Number.isNaN(Number(x))) return "-";
  return Number(x).toFixed(2);
}

async function loadLatest() {
  const res = await fetch(LATEST_URL, { cache: "no-store" });
  if (!res.ok) throw new Error("latest.json을 불러오지 못했습니다.");
  return res.json();
}

async function loadHistoryCsv() {
  const res = await fetch(HISTORY_URL, { cache: "no-store" });
  if (!res.ok) return null; // 처음엔 없을 수 있음
  return res.text();
}

function parseCsv(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return [];
  const header = lines[0].split(",");
  return lines.slice(1).map(line => {
    const cols = line.split(",");
    const obj = {};
    header.forEach((h, i) => (obj[h] = cols[i]));
    return obj;
  });
}

function renderLatest(data) {
  document.getElementById("updatedAt").textContent = data.generated_at_utc ?? "-";

  const tbody = document.querySelector("#priceTable tbody");
  tbody.innerHTML = "";

  const rows = data.rows ?? [];
  for (const r of rows) {
    const tr = document.createElement("tr");

    const tdTicker = document.createElement("td");
    tdTicker.textContent = r.ticker;

    const tdName = document.createElement("td");
    tdName.textContent = TICKER_NAMES[r.ticker] ?? "-";

    const tdPrice = document.createElement("td");
    tdPrice.textContent = fmtPrice(r.price_usd);

    const tdTime = document.createElement("td");
    tdTime.textContent = r.price_time_utc ?? "-";

    tr.append(tdTicker, tdName, tdPrice, tdTime);
    tbody.appendChild(tr);
  }
}

function renderHistory(records, limit = 80) {
  const tbody = document.querySelector("#historyTable tbody");
  tbody.innerHTML = "";

  const sliced = records.slice(-limit).reverse();
  for (const row of sliced) {
    const tr = document.createElement("tr");
    const cols = ["timestamp_utc", "QSI", "QBTS", "RGTI", "IONQ", "QTUM"];
    for (const c of cols) {
      const td = document.createElement("td");
      td.textContent = c === "timestamp_utc" ? (row[c] ?? "-") : fmtPrice(row[c]);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
}

async function refreshAll() {
  const latest = await loadLatest();
  renderLatest(latest);

  const histText = await loadHistoryCsv();
  if (histText) {
    const records = parseCsv(histText);
    renderHistory(records);
  }
}

document.getElementById("refreshBtn").addEventListener("click", () => {
  refreshAll().catch(err => alert(err.message));
});

// 페이지에서도 5분마다 갱신(백엔드가 갱신됐다는 전제)
refreshAll().catch(console.error);
setInterval(() => refreshAll().catch(console.error), 5 * 60 * 1000);
