from pathlib import Path
import os
import io
import base64
import uvicorn
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

ROOT_DIR     = Path(__file__).resolve().parent
REPORTS_DIR  = ROOT_DIR / "sample_reports"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def extract_text(path: str) -> str:
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()

def ask_groq(pdf_text: str, report_name: str, question: str) -> str:
    if not GROQ_API_KEY:
        return "GROQ_API_KEY not found in .env file."
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""You are an expert medical assistant with deep knowledge of nutrition, lifestyle medicine, and clinical lab interpretation.

A patient has shared their medical report. Your job is to:

STEP 1 - Extract key findings from the report:
- Read all lab values, vitals, and test results
- Note which values are HIGH, LOW, or ABNORMAL and by how much
- Note the patient name, age, and gender if available

STEP 2 - Answer the question using BOTH the report data AND your own medical knowledge:
- Always reference the actual numbers from the report (e.g. Your Triglycerides are 210 mg/dL which is High)
- Then apply your medical expertise to give a specific, personalized recommendation based on those values
- For example: if Triglycerides are high, explain what that means for oily food, which specific oils to avoid, which are safer, and why
- If a value is normal, reassure the patient but still give sound general advice
- Be specific, practical, and actionable - not generic

RULES:
- Never diagnose a disease
- Always ground your recommendation in the patient actual numbers
- Use simple language the patient can understand
- Do not just summarize the report - synthesize it with real medical knowledge to answer the question
- Raise the temperature of your answer: be confident, direct and helpful

--- REPORT: {report_name} ---
{pdf_text[:6000]}
--- END OF REPORT ---

Patient Question: {question}

Give a clear, personalized answer based on the report values and your medical knowledge:"""
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.5,
    )
    return resp.choices[0].message.content.strip()

@app.get("/", response_class=HTMLResponse)
async def index():
    sample_reports = []
    if REPORTS_DIR.exists():
        sample_reports = sorted([p.name for p in REPORTS_DIR.glob("*.pdf")])
    reports_json = str(sample_reports).replace("'", '"')
    return HTMLResponse(content=HTML_PAGE.replace("__REPORTS__", reports_json))

@app.get("/reports")
async def list_reports():
    if not REPORTS_DIR.exists():
        return JSONResponse([])
    return JSONResponse(sorted([p.name for p in REPORTS_DIR.glob("*.pdf")]))

@app.post("/load-sample")
async def load_sample(name: str = Form(...)):
    path = REPORTS_DIR / name
    if not path.exists():
        return JSONResponse({"error": f"{name} not found"}, status_code=404)
    text = extract_text(str(path))
    if not text:
        return JSONResponse({"error": "Could not extract text. May be a scanned PDF."}, status_code=400)
    return JSONResponse({"name": name, "text": text, "chars": len(text)})

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = ""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    text = text.strip()
    if not text:
        return JSONResponse({"error": "Could not extract text. May be a scanned PDF."}, status_code=400)
    b64 = base64.b64encode(content).decode()
    return JSONResponse({"name": file.filename, "text": text, "chars": len(text), "b64": b64})

@app.post("/chat")
async def chat(
    question: str = Form(...),
    pdf_text: str = Form(...),
    report_name: str = Form(...),
):
    try:
        answer = ask_groq(pdf_text, report_name, question)
        return JSONResponse({"answer": answer})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>MediChat</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0f0f0f;
  --surface:#1a1a1a;
  --surface2:#222;
  --border:rgba(255,255,255,0.08);
  --border2:rgba(255,255,255,0.14);
  --text:#ececec;
  --text2:#999;
  --text3:#555;
  --accent:#3ecf8e;
  --accent-dim:rgba(62,207,142,0.12);
  --accent-border:rgba(62,207,142,0.3);
  --user-bg:#1e2d24;
  --user-border:rgba(62,207,142,0.2);
  --danger:#e05c6b;
  --font:'DM Sans',sans-serif;
  --mono:'DM Mono',monospace;
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--font);font-size:15px;line-height:1.6}
.app{display:flex;height:100vh;overflow:hidden}

/* ── Sidebar ── */
.sidebar{width:260px;flex-shrink:0;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden}
.sidebar-header{padding:18px 16px 12px;border-bottom:1px solid var(--border)}
.sidebar-logo{display:flex;align-items:center;gap:9px;margin-bottom:14px}
.logo-icon{width:30px;height:30px;background:var(--accent-dim);border:1px solid var(--accent-border);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px}
.logo-text{font-size:15px;font-weight:500;color:var(--text)}
.new-chat-btn{width:100%;padding:9px 12px;background:var(--accent);color:#0a1a12;border:none;border-radius:8px;font-family:var(--font);font-size:13px;font-weight:500;cursor:pointer;transition:background 0.15s;text-align:left;display:flex;align-items:center;gap:7px}
.new-chat-btn:hover{background:#4de09e}
.sidebar-section{padding:12px 16px 6px;font-size:10px;font-weight:500;letter-spacing:1px;text-transform:uppercase;color:var(--text3)}
.report-list{flex:1;overflow-y:auto;padding:0 8px 8px}
.report-list::-webkit-scrollbar{width:3px}
.report-list::-webkit-scrollbar-thumb{background:var(--border2)}
.report-item{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:7px;cursor:pointer;transition:background 0.12s;font-size:13px;color:var(--text2);border:1px solid transparent}
.report-item:hover{background:var(--surface2);color:var(--text)}
.report-item.active{background:var(--accent-dim);border-color:var(--accent-border);color:var(--accent)}
.report-item .pdf-icon{font-size:12px;flex-shrink:0;opacity:0.6}
.report-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* ── Main chat ── */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative}

/* ── Top bar ── */
.topbar{padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px;flex-shrink:0;background:var(--bg)}
.topbar-report{font-size:13px;color:var(--text2);display:flex;align-items:center;gap:7px}
.topbar-report .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex-shrink:0}
.topbar-name{color:var(--text);font-weight:500}

/* ── Messages ── */
.messages{flex:1;overflow-y:auto;padding:24px 0;display:flex;flex-direction:column;gap:6px}
.messages::-webkit-scrollbar{width:4px}
.messages::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

.msg-row{display:flex;padding:4px 20px;animation:fadeup 0.2s ease}
@keyframes fadeup{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.msg-row.user{justify-content:flex-end}
.msg-row.ai{justify-content:flex-start}

.bubble{max-width:72%;padding:12px 16px;border-radius:16px;font-size:14px;line-height:1.65}
.msg-row.user .bubble{background:var(--user-bg);border:1px solid var(--user-border);border-radius:16px 4px 16px 16px;color:var(--text)}
.msg-row.ai .bubble{background:var(--surface);border:1px solid var(--border);border-radius:4px 16px 16px 16px;color:var(--text);white-space:pre-wrap}

/* PDF attachment bubble */
.pdf-bubble{display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface2);border:1px solid var(--border2);border-radius:10px;max-width:260px;cursor:default}
.pdf-bubble-icon{width:34px;height:34px;background:rgba(224,92,107,0.12);border:1px solid rgba(224,92,107,0.25);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0}
.pdf-bubble-info .pdf-bname{font-size:13px;font-weight:500;color:var(--text);max-width:170px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pdf-bubble-info .pdf-bsub{font-size:11px;color:var(--text3);margin-top:1px}

/* Typing indicator */
.typing{display:flex;gap:5px;align-items:center;padding:4px 2px}
.typing span{width:6px;height:6px;border-radius:50%;background:var(--text3);animation:blink 1.2s infinite}
.typing span:nth-child(2){animation-delay:.2s}
.typing span:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,60%,100%{opacity:0.3}30%{opacity:1}}

/* Empty state */
.empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;color:var(--text3);padding:40px;text-align:center}
.empty-icon{font-size:40px;opacity:0.25}
.empty h2{font-size:18px;font-weight:500;color:var(--text2)}
.empty p{font-size:13px;max-width:280px;line-height:1.6}
.empty-pills{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:8px}
.pill{padding:7px 14px;background:var(--surface);border:1px solid var(--border2);color:var(--text2);border-radius:20px;font-size:12px;cursor:pointer;transition:all 0.15s}
.pill:hover{border-color:var(--accent-border);color:var(--accent);background:var(--accent-dim)}

/* ── Input bar ── */
.input-area{padding:14px 20px 18px;flex-shrink:0;background:var(--bg)}
.input-box{display:flex;align-items:flex-end;gap:8px;background:var(--surface);border:1px solid var(--border2);border-radius:14px;padding:8px 8px 8px 14px;transition:border-color 0.15s}
.input-box:focus-within{border-color:var(--accent-border)}
.attach-btn{width:34px;height:34px;flex-shrink:0;background:var(--surface2);border:1px solid var(--border);border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--text2);transition:all 0.15s;font-size:18px;line-height:1}
.attach-btn:hover{background:var(--accent-dim);border-color:var(--accent-border);color:var(--accent)}
#file-input{display:none}
textarea{flex:1;background:transparent;border:none;outline:none;color:var(--text);font-family:var(--font);font-size:14px;resize:none;min-height:34px;max-height:140px;line-height:1.6;padding:4px 0;overflow-y:auto}
textarea::placeholder{color:var(--text3)}
.send-btn{width:34px;height:34px;flex-shrink:0;background:var(--accent);border:none;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background 0.15s,transform 0.1s;color:#0a1a12}
.send-btn:hover{background:#4de09e}
.send-btn:active{transform:scale(0.93)}
.send-btn:disabled{background:var(--surface2);color:var(--text3);cursor:not-allowed;transform:none}
.send-btn svg{width:15px;height:15px}

/* Pending PDF bar */
.pending-bar{margin:0 20px 8px;padding:8px 12px;background:var(--surface2);border:1px solid var(--border2);border-radius:9px;display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text2)}
.pending-bar .pname{color:var(--text);font-weight:500;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pending-bar .remove{cursor:pointer;color:var(--text3);font-size:16px;line-height:1;flex-shrink:0;transition:color 0.12s}
.pending-bar .remove:hover{color:var(--danger)}
.pending-bar{display:none}
.pending-bar.visible{display:flex}

/* Chat history items */
.sidebar-body{flex:1;overflow-y:auto;display:flex;flex-direction:column}
.sidebar-body::-webkit-scrollbar{width:3px}
.sidebar-body::-webkit-scrollbar-thumb{background:var(--border2)}
.history-item{display:flex;align-items:center;gap:8px;padding:8px 10px;margin:0 8px;border-radius:7px;cursor:pointer;transition:background 0.12s;font-size:13px;color:var(--text2);border:1px solid transparent;position:relative}
.history-item:hover{background:var(--surface2);color:var(--text)}
.history-item.active{background:var(--accent-dim);border-color:var(--accent-border);color:var(--accent)}
.history-item .h-icon{font-size:12px;flex-shrink:0;opacity:0.5}
.history-item .h-title{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px}
.history-item .h-del{display:none;position:absolute;right:8px;top:50%;transform:translateY(-50%);color:var(--text3);font-size:14px;line-height:1;padding:2px 4px;border-radius:4px;transition:color 0.1s,background 0.1s}
.history-item:hover .h-del{display:block}
.history-item .h-del:hover{color:var(--danger);background:rgba(224,92,107,0.1)}
.history-date{padding:10px 18px 4px;font-size:10px;font-weight:500;letter-spacing:0.8px;text-transform:uppercase;color:var(--text3)}
.sidebar-divider{height:1px;background:var(--border);margin:8px 16px}

/* Toast */
.toast{position:fixed;bottom:90px;left:50%;transform:translateX(-50%);background:var(--danger);color:#fff;padding:9px 18px;border-radius:8px;font-size:13px;opacity:0;pointer-events:none;transition:opacity 0.2s;z-index:99}
.toast.show{opacity:1}
</style>
</head>
<body>
<div class="app">

  <!-- Sidebar -->
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <div class="logo-icon">🩺</div>
        <span class="logo-text">MediChat</span>
      </div>
      <button class="new-chat-btn" onclick="newChat()">
        <span>＋</span> New Chat
      </button>
    </div>
    <div class="sidebar-body">
      <div class="sidebar-section" style="padding-top:14px">Recent Chats</div>
      <div id="history-list"><div style="padding:8px 18px;font-size:12px;color:var(--text3)">No previous chats yet.</div></div>
      <div class="sidebar-divider"></div>
      <div class="sidebar-section">Sample Reports</div>
      <div class="report-list" id="report-list">
        <div style="padding:10px;font-size:12px;color:var(--text3)">Loading...</div>
      </div>
    </div>
  </div>

  <!-- Main -->
  <div class="main">
    <div class="topbar">
      <div class="topbar-report" id="topbar-info">
        <span style="font-size:13px;color:var(--text3)">No report loaded — upload a PDF or pick one from the sidebar</span>
      </div>
    </div>

    <div class="messages" id="messages">
      <div class="empty" id="empty-state">
        <div class="empty-icon">💬</div>
        <h2>Ask about your medical report</h2>
        <p>Upload a PDF or select a sample report from the sidebar, then ask anything.</p>
        <div class="empty-pills">
          <div class="pill" onclick="usePill(this)">What are the abnormal values?</div>
          <div class="pill" onclick="usePill(this)">Summarize this report</div>
          <div class="pill" onclick="usePill(this)">Patient name and age?</div>
          <div class="pill" onclick="usePill(this)">Which vitals need attention?</div>
          <div class="pill" onclick="usePill(this)">Any critical findings?</div>
          <div class="pill" onclick="usePill(this)">Diet recommendations?</div>
        </div>
      </div>
    </div>

    <!-- Pending PDF bar -->
    <div class="pending-bar" id="pending-bar">
      <span>📄</span>
      <span class="pname" id="pending-name"></span>
      <span class="remove" onclick="removePending()" title="Remove">×</span>
    </div>

    <!-- Input -->
    <div class="input-area">
      <div class="input-box">
        <button class="attach-btn" onclick="document.getElementById('file-input').click()" title="Upload PDF">＋</button>
        <input type="file" id="file-input" accept=".pdf" onchange="handleFileSelect(this)"/>
        <textarea id="q-input" placeholder="Ask anything about this report…" rows="1"
          onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
        <button class="send-btn" id="send-btn" onclick="sendMessage()" title="Send">
          <svg viewBox="0 0 16 16" fill="currentColor"><path d="M1 8l13-6-5 6 5 6-13-6z"/></svg>
        </button>
      </div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ── State ────────────────────────────────────────────────────────────────────
let reportText   = "";
let reportName   = "";
let pendingFile  = null;
let currentChatId = null;
// messages stored as [{role, text, isPDF, pdfChars}]
let currentMessages = [];

const messagesEl    = document.getElementById("messages");
const emptyState    = document.getElementById("empty-state");
const topbarInfo    = document.getElementById("topbar-info");
const sendBtn       = document.getElementById("send-btn");
const qInput        = document.getElementById("q-input");
const pendingBar    = document.getElementById("pending-bar");
const pendingNameEl = document.getElementById("pending-name");

// ── Chat history (localStorage) ───────────────────────────────────────────────
function getHistory() {
  try { return JSON.parse(localStorage.getItem("medichat_history") || "[]"); }
  catch { return []; }
}
function saveHistory(h) {
  localStorage.setItem("medichat_history", JSON.stringify(h));
}
function saveCurrentChat() {
  if (!currentMessages.length) return;
  const h = getHistory();
  const firstUserMsg = currentMessages.find(m => m.role === "user" && !m.isPDF);
  const title = firstUserMsg ? firstUserMsg.text.slice(0, 48) : (reportName || "Untitled chat");
  const existing = h.findIndex(c => c.id === currentChatId);
  const entry = {
    id: currentChatId,
    title,
    reportName,
    reportText,
    messages: currentMessages,
    ts: Date.now(),
  };
  if (existing >= 0) h[existing] = entry;
  else h.unshift(entry);
  // keep max 40 chats
  saveHistory(h.slice(0, 40));
  renderHistory();
}
function deleteChat(id, e) {
  e.stopPropagation();
  const h = getHistory().filter(c => c.id !== id);
  saveHistory(h);
  renderHistory();
  if (currentChatId === id) startFreshChat();
}
function renderHistory() {
  const h = getHistory();
  const el = document.getElementById("history-list");
  if (!h.length) {
    el.innerHTML = '<div style="padding:8px 18px;font-size:12px;color:var(--text3)">No previous chats yet.</div>';
    return;
  }
  // Group by date
  const today = new Date(); today.setHours(0,0,0,0);
  const yesterday = new Date(today); yesterday.setDate(today.getDate()-1);
  const groups = {};
  h.forEach(c => {
    const d = new Date(c.ts); d.setHours(0,0,0,0);
    let label = d >= today ? "Today" : d >= yesterday ? "Yesterday" : d.toLocaleDateString("en-IN",{day:"numeric",month:"short"});
    if (!groups[label]) groups[label] = [];
    groups[label].push(c);
  });
  el.innerHTML = Object.entries(groups).map(([label, chats]) =>
    `<div class="history-date">${label}</div>` +
    chats.map(c => `
      <div class="history-item${c.id === currentChatId ? " active" : ""}" onclick="loadChat('${c.id}')">
        <span class="h-icon">💬</span>
        <span class="h-title" title="${escHtml(c.title)}">${escHtml(c.title)}</span>
        <span class="h-del" onclick="deleteChat('${c.id}', event)" title="Delete">×</span>
      </div>`).join("")
  ).join("");
}
function loadChat(id) {
  // Save current chat first
  saveCurrentChat();
  const h = getHistory();
  const chat = h.find(c => c.id === id);
  if (!chat) return;
  currentChatId   = chat.id;
  reportText      = chat.reportText || "";
  reportName      = chat.reportName || "";
  currentMessages = chat.messages  || [];
  // Re-render messages
  messagesEl.innerHTML = "";
  if (!currentMessages.length) {
    messagesEl.appendChild(emptyState);
    emptyState.style.display = "";
  } else {
    emptyState.style.display = "none";
    currentMessages.forEach(m => {
      if (m.isPDF) renderPDFBubble(m.text, m.pdfChars);
      else if (m.role === "user") renderUserBubble(m.text);
      else renderAIBubble(m.text);
    });
  }
  if (reportName) setTopbar(reportName, reportText.length);
  else topbarInfo.innerHTML = `<span style="font-size:13px;color:var(--text3)">No report loaded</span>`;
  document.querySelectorAll(".report-item,.history-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".history-item").forEach(el => {
    if (el.querySelector(".h-title") && el.onclick) {
      const oid = el.getAttribute("onclick");
    }
  });
  renderHistory(); // re-render to update active state
  scrollBottom();
  qInput.focus();
}
function startFreshChat() {
  saveCurrentChat();
  currentChatId   = "chat_" + Date.now();
  currentMessages = [];
  reportText = ""; reportName = "";
  pendingFile = null;
  pendingBar.classList.remove("visible");
  messagesEl.innerHTML = "";
  messagesEl.appendChild(emptyState);
  emptyState.style.display = "";
  topbarInfo.innerHTML = `<span style="font-size:13px;color:var(--text3)">No report loaded — upload a PDF or pick one from the sidebar</span>`;
  document.querySelectorAll(".report-item,.history-item").forEach(el => el.classList.remove("active"));
  renderHistory();
  qInput.value = "";
  autoResize(qInput);
}

// ── Load sample reports into sidebar ──────────────────────────────────────────
async function loadSidebar() {
  const list = document.getElementById("report-list");
  try {
    const res  = await fetch("/reports");
    const data = await res.json();
    if (!data.length) {
      list.innerHTML = '<div style="padding:10px;font-size:12px;color:var(--text3)">No reports found in sample_reports/</div>';
      return;
    }
    list.innerHTML = data.map(r =>
      `<div class="report-item" onclick="loadSample('${r}')" title="${r}">
        <span class="pdf-icon">📄</span>
        <span class="report-name">${r}</span>
      </div>`
    ).join("");
  } catch(e) {
    list.innerHTML = '<div style="padding:10px;font-size:12px;color:var(--text3)">Could not load reports.</div>';
  }
}

// ── Load a sample report from sidebar ────────────────────────────────────────
async function loadSample(name) {
  saveCurrentChat();
  // start a new chat context for this report
  currentChatId   = "chat_" + Date.now();
  currentMessages = [];
  messagesEl.innerHTML = "";
  messagesEl.appendChild(emptyState);
  emptyState.style.display = "";

  document.querySelectorAll(".report-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".history-item").forEach(el => el.classList.remove("active"));
  const clicked = [...document.querySelectorAll(".report-item")].find(el => el.querySelector(".report-name").textContent === name);
  if (clicked) clicked.classList.add("active");

  const fd = new FormData();
  fd.append("name", name);
  try {
    const res  = await fetch("/load-sample", { method:"POST", body:fd });
    const data = await res.json();
    if (data.error) { showToast(data.error); return; }
    reportText = data.text;
    reportName = data.name;
    setTopbar(name, data.chars);
    addSystemMsg(`📄 Report loaded: <strong>${name}</strong> (${data.chars.toLocaleString()} chars extracted)`);
  } catch(e) {
    showToast("Failed to load report: " + e.message);
  }
}

// ── Handle file picker ────────────────────────────────────────────────────────
function handleFileSelect(input) {
  const file = input.files[0];
  if (!file) return;
  pendingFile = file;
  pendingNameEl.textContent = file.name;
  pendingBar.classList.add("visible");
  input.value = "";
}

function removePending() {
  pendingFile = null;
  pendingBar.classList.remove("visible");
}

// ── Upload pending PDF then send message ──────────────────────────────────────
async function uploadAndSet() {
  if (!pendingFile) return;
  const fd = new FormData();
  fd.append("file", pendingFile);
  const res  = await fetch("/upload", { method:"POST", body:fd });
  const data = await res.json();
  if (data.error) throw new Error(data.error);

  // Show PDF bubble in chat
  addPDFBubble(pendingFile.name, data.chars);
  reportText = data.text;
  reportName = data.name;
  setTopbar(data.name, data.chars);
  document.querySelectorAll(".report-item").forEach(el => el.classList.remove("active"));
  removePending();
}

// ── Send message ──────────────────────────────────────────────────────────────
async function sendMessage() {
  const q = qInput.value.trim();
  if (!q && !pendingFile) return;

  sendBtn.disabled = true;
  qInput.disabled  = true;
  hideEmpty();

  // Upload PDF first if pending
  if (pendingFile) {
    try {
      await uploadAndSet();
    } catch(e) {
      showToast("Upload failed: " + e.message);
      sendBtn.disabled = false;
      qInput.disabled  = false;
      return;
    }
  }

  if (!q) {
    sendBtn.disabled = false;
    qInput.disabled  = false;
    return;
  }

  if (!reportText) {
    addUserBubble(q);
    qInput.value = "";
    autoResize(qInput);
    addAIBubble("Please upload a PDF or select a report from the sidebar first.");
    sendBtn.disabled = false;
    qInput.disabled  = false;
    return;
  }

  addUserBubble(q);
  qInput.value = "";
  autoResize(qInput);

  const typingId = addTyping();

  const fd = new FormData();
  fd.append("question",    q);
  fd.append("pdf_text",    reportText);
  fd.append("report_name", reportName);

  try {
    const res  = await fetch("/chat", { method:"POST", body:fd });
    const data = await res.json();
    removeTyping(typingId);
    if (data.error) addAIBubble("Error: " + data.error);
    else addAIBubble(data.answer);
  } catch(e) {
    removeTyping(typingId);
    addAIBubble("Network error: " + e.message);
  }

  sendBtn.disabled = false;
  qInput.disabled  = false;
  qInput.focus();
}

// ── DOM helpers ───────────────────────────────────────────────────────────────
// ── Render helpers (no state mutation) ───────────────────────────────────────
function renderUserBubble(text) {
  const row = document.createElement("div");
  row.className = "msg-row user";
  row.innerHTML = `<div class="bubble">${escHtml(text)}</div>`;
  messagesEl.appendChild(row);
  scrollBottom();
}
function renderAIBubble(text) {
  const row = document.createElement("div");
  row.className = "msg-row ai";
  row.innerHTML = `<div class="bubble">${escHtml(text)}</div>`;
  messagesEl.appendChild(row);
  scrollBottom();
}
function renderPDFBubble(name, chars) {
  const row = document.createElement("div");
  row.className = "msg-row user";
  row.innerHTML = `
    <div class="pdf-bubble">
      <div class="pdf-bubble-icon">📄</div>
      <div class="pdf-bubble-info">
        <div class="pdf-bname">${escHtml(name)}</div>
        <div class="pdf-bsub">${(chars||0).toLocaleString()} chars extracted</div>
      </div>
    </div>`;
  messagesEl.appendChild(row);
  scrollBottom();
}
// ── State-mutating wrappers ───────────────────────────────────────────────────
function addUserBubble(text) {
  currentMessages.push({role:"user", text});
  renderUserBubble(text);
}
function addAIBubble(text) {
  currentMessages.push({role:"ai", text});
  renderAIBubble(text);
  saveCurrentChat();
}
function addSystemMsg(html) {
  const row = document.createElement("div");
  row.className = "msg-row ai";
  row.innerHTML = `<div class="bubble" style="font-size:13px;color:var(--text2)">${html}</div>`;
  messagesEl.appendChild(row);
  hideEmpty();
  scrollBottom();
}
function addPDFBubble(name, chars) {
  currentMessages.push({role:"user", isPDF:true, text:name, pdfChars:chars});
  renderPDFBubble(name, chars);
  saveCurrentChat();
}

let typingCounter = 0;
function addTyping() {
  const id  = "typing-" + (++typingCounter);
  const row = document.createElement("div");
  row.className = "msg-row ai";
  row.id = id;
  row.innerHTML = `<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
  messagesEl.appendChild(row);
  scrollBottom();
  return id;
}
function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function setTopbar(name, chars) {
  topbarInfo.innerHTML = `<div class="dot"></div><span class="topbar-name">${escHtml(name)}</span><span style="color:var(--text3);font-size:12px;margin-left:4px">(${chars.toLocaleString()} chars)</span>`;
}

function hideEmpty() {
  if (emptyState) emptyState.style.display = "none";
}

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3500);
}

function newChat() { startFreshChat(); }

function usePill(el) {
  qInput.value = el.textContent;
  autoResize(qInput);
  qInput.focus();
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}

// init
currentChatId = "chat_" + Date.now();
renderHistory();
loadSidebar();
</script>
</body>
</html>"""

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7860)
