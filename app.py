"""
CogniPace AI v4 — Arsitektur Hybrid yang Andal
================================================
Strategi:
  - PYTHON  → kalender, tabel prioritas, jadwal harian (100% deterministik, selalu berhasil)
  - AI (opsional) → skor beban kognitif, ringkasan analisis, tips manajemen waktu, pemecahan tugas
  AI hanya diminta teks pendek via tag sederhana — tidak ada JSON kompleks.
  Kalender & jadwal tetap muncul meski AI offline / gagal.
"""

import re
import json
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date, timedelta

try:
    import ollama
    OLLAMA_TERSEDIA = True
except ImportError:
    OLLAMA_TERSEDIA = False


# ═══════════════════════════════════════════════
# KONFIGURASI
# ═══════════════════════════════════════════════
st.set_page_config(page_title="CogniPace AI", page_icon="🧠", layout="wide")

# Daftar model yang direkomendasikan
MODEL_OPTIONS = [
    "llama3.1:8b",   # Terbaik untuk instruksi
    "phi3",          # Paling ringan
]

# ═══════════════════════════════════════════════
# BAGIAN 1: DETEKSI KOLOM & PARSING DATA
# ═══════════════════════════════════════════════

ALIAS_KOLOM = {
    "nama tugas":    "tugas", "nama tugas (simulasi)": "tugas",
    "tugas":         "tugas", "assignment": "tugas", "task": "tugas",
    "kerjaan":       "tugas", "pekerjaan":  "tugas", "kegiatan": "tugas",
    "mata kuliah":   "matkul","matkul":     "matkul","subject":  "matkul",
    "course":        "matkul","pelajaran":  "matkul","mapel":    "matkul",
    "kelas":         "matkul",
    "deadline":      "deadline","due date":  "deadline","due_date": "deadline",
    "batas waktu":   "deadline","tanggal akhir":"deadline",
    "tanggal deadline":"deadline","tgl deadline":"deadline",
    "jatuh tempo":   "deadline","akhir":     "deadline",
    "prioritas":     "prioritas","priority":  "prioritas",
    "estimasi waktu":"estimasi","estimasi":  "estimasi","durasi":  "estimasi",
    "estimated time":"estimasi","time":      "estimasi",
    "status":        "status",  "kondisi":   "status","state":   "status",
    "tanggal diberikan":"tgl_mulai","tanggal mulai":"tgl_mulai",
    "mulai":         "tgl_mulai","start":    "tgl_mulai",
}

BULAN_ID = {
    "januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,
    "juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12,
    "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"agu":8,"agt":8,
    "sep":9,"okt":10,"nov":11,"des":12,
    "january":1,"february":2,"march":3,"may":5,"june":6,"july":7,
    "august":8,"october":10,"december":12,
}

def deteksi_kolom(df: pd.DataFrame) -> dict:
    mapping = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in ALIAS_KOLOM:
            internal = ALIAS_KOLOM[key]
            if internal not in mapping:
                mapping[internal] = col
    return mapping

def parse_tgl(s: str, tahun_default: int = None) -> date | None:
    if tahun_default is None: tahun_default = date.today().year
    s = str(s).strip()
    parts = s.replace(",", " ").split()
    for i, p in enumerate(parts):
        bln = BULAN_ID.get(p.lower())
        if bln:
            others = [x for j, x in enumerate(parts) if j != i]
            for o in others:
                try:
                    hr = int(o)
                    thn = tahun_default
                    for o2 in others:
                        try:
                            yy = int(o2)
                            if 2020 <= yy <= 2035:
                                thn = yy; break
                        except: pass
                    return date(thn, bln, hr)
                except: pass
    try:
        r = pd.to_datetime(s, format="mixed", dayfirst=True, errors="raise")
        if r.year >= 2020: return r.date()
    except: pass
    iso_match = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if iso_match:
        try: return date.fromisoformat(iso_match.group(1))
        except: pass
    return None

def parse_jam(s) -> int:
    if pd.isna(s): return 2
    nums = re.findall(r'\d+', str(s))
    return int(nums[0]) if nums else 2

BOBOT_PRI = {"tinggi": 0, "high": 0, "kritis": 0, "sedang": 1, "medium": 1, "normal": 1, "rendah": 2, "low": 2, "ringan": 2}

def proses_df(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    today = date.today()
    df = df.copy()
    if "deadline" in mapping:
        df["_deadline"] = df[mapping["deadline"]].apply(parse_tgl)
    else:
        df["_deadline"] = None

    df["_hari_tersisa"] = df["_deadline"].apply(lambda d: (d - today).days if d else 9999)
    df["_jam"] = df[mapping["estimasi"]].apply(parse_jam) if "estimasi" in mapping else 2

    if "prioritas" in mapping:
        df["_bobot_pri"] = df[mapping["prioritas"]].apply(lambda x: BOBOT_PRI.get(str(x).lower().strip(), 1))
        df["_prioritas"] = df[mapping["prioritas"]].apply(lambda x: str(x).strip())
    else:
        df["_bobot_pri"] = 1; df["_prioritas"] = "Sedang"

    df["_skor"] = df["_hari_tersisa"] + df["_bobot_pri"] * 2
    df["_tugas"]  = df[mapping["tugas"]].apply(str)  if "tugas"  in mapping else "Tugas"
    df["_matkul"] = df[mapping["matkul"]].apply(str) if "matkul" in mapping else "—"

    if "status" in mapping:
        selesai_kata = {"selesai","done","complete","completed","finished","sudah"}
        df["_selesai"] = df[mapping["status"]].apply(lambda x: str(x).lower().strip() in selesai_kata)
    else:
        df["_selesai"] = False

    return df


# ═══════════════════════════════════════════════
# BAGIAN 2: PYTHON → KALENDER, TABEL, JADWAL
# ═══════════════════════════════════════════════

def bangun_beban(df: pd.DataFrame) -> dict:
    beban = {}
    for _, r in df.iterrows():
        if r["_deadline"] is None: continue
        key = str(r["_deadline"])
        if key not in beban: beban[key] = {"jumlah": 0, "tugas": []}
        beban[key]["jumlah"] += 1
        beban[key]["tugas"].append({
            "tugas":       r["_tugas"], "matkul":      r["_matkul"],
            "deadline":    key, "prioritas":   r["_prioritas"],
            "estimasi_jam":r["_jam"], "status":      "Selesai" if r["_selesai"] else "Belum Selesai",
        })
    return beban

def bangun_tabel_prioritas(df: pd.DataFrame) -> pd.DataFrame:
    df_aktif = df[~df["_selesai"] & (df["_deadline"].notna())].copy()
    if df_aktif.empty: return pd.DataFrame()
    df_aktif = df_aktif.sort_values("_skor").reset_index(drop=True)
    df_aktif.index += 1

    def urgensi(hari):
        if hari < 0:     return "🔴 Terlambat"
        elif hari <= 2:  return "🔴 Kritis"
        elif hari <= 5:  return "🟠 Mendesak"
        elif hari <= 10: return "🟡 Perhatikan"
        else:            return "🟢 Aman"

    kolom = {}
    if "_tugas"  in df_aktif.columns: kolom["_tugas"]  = "Nama Tugas"
    if "_matkul" in df_aktif.columns: kolom["_matkul"] = "Mata Kuliah"

    df_out = pd.DataFrame()
    for k, v in kolom.items(): df_out[v] = df_aktif[k].values
    df_out["Deadline"]      = df_aktif["_deadline"].apply(lambda d: d.strftime("%d %b %Y") if d else "—").values
    df_out["Hari Tersisa"]  = df_aktif["_hari_tersisa"].apply(lambda h: h if h != 9999 else "?").values
    df_out["Prioritas"]     = df_aktif["_prioritas"].values
    df_out["Estimasi"]      = df_aktif["_jam"].apply(lambda j: f"{j} jam").values
    df_out["Urgensi"]       = df_aktif["_hari_tersisa"].apply(urgensi).values
    df_out.index = range(1, len(df_out) + 1)
    return df_out

def bangun_jadwal_harian(df: pd.DataFrame) -> pd.DataFrame:
    df_aktif = df[~df["_selesai"] & (df["_deadline"].notna())].sort_values("_skor").copy()
    if df_aktif.empty: return pd.DataFrame()

    today = date.today()
    jadwal = []
    hari = today

    for _, r in df_aktif.iterrows():
        dl = r["_deadline"]
        jam = r["_jam"]
        hari_tersisa = r["_hari_tersisa"]

        if hari_tersisa < 0:
            catatan = "⚠️ Deadline sudah terlewat! Selesaikan sesegera mungkin."
            tgl_kerjakan = today
        elif hari_tersisa == 0:
            catatan = "🚨 Deadline HARI INI! Prioritaskan sekarang."
            tgl_kerjakan = today
        elif hari_tersisa <= 2:
            catatan = f"🔴 Deadline {dl.strftime('%d %b')} — kerjakan sekarang!"
            tgl_kerjakan = hari
        else:
            catatan = f"Selesaikan sebelum {dl.strftime('%d %b %Y')}"
            tgl_kerjakan = hari
            hari += timedelta(days=1)

        jadwal.append({
            "Tanggal Kerjakan": tgl_kerjakan.strftime("%d %b %Y (%a)"),
            "Nama Tugas":       r["_tugas"], "Mata Kuliah":      r["_matkul"],
            "Prioritas":        r["_prioritas"], "Estimasi":         f"{jam} jam",
            "Deadline":         dl.strftime("%d %b %Y"), "Catatan":          catatan,
        })
    return pd.DataFrame(jadwal)


# ═══════════════════════════════════════════════
# BAGIAN 3: AI — HANYA UNTUK ANALISIS TEKS
# ═══════════════════════════════════════════════

def panggil_ai_analisis(csv_str: str, kolom_info: str, model: str) -> str:
    """ AI menganalisis teks dengan tambahan pemecahan tugas (fokus) via tag XML. """
    hari_ini = date.today().strftime("%d %B %Y")

    prompt = f"""Kamu adalah AI Asisten Akademik. Hari ini {hari_ini}.

Data tugas mahasiswa:
{csv_str}

Kolom data: {kolom_info}

Berikan analisis singkat dalam Bahasa Indonesia. Jawab HANYA dengan format berikut, tidak ada teks lain:

<skor>[angka 1-10, di mana 10=sangat berat]</skor>

<ringkasan>[2-3 kalimat analisis kondisi beban mahasiswa berdasarkan data di atas]</ringkasan>

<fokus>
Tugas paling berat/menantang dari data di atas adalah [Nama Tugas]. Mulailah mengerjakannya dengan 3 langkah kecil ini:
1. [Langkah pertama]
2. [Langkah kedua]
3. [Langkah ketiga]
</fokus>

<tips>
1. [tip konkret pertama]
2. [tip konkret kedua]
3. [tip konkret ketiga]
</tips>"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.4},   # Sedikit dinaikkan agar pemecahan tugas lebih bervariasi
    )
    return response["message"]["content"]


def parse_ai_teks(teks: str) -> dict:
    """Parse tag XML sederhana dari respons AI."""
    def ekstrak(tag):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", teks, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    skor_str = ekstrak("skor")
    try:
        skor = max(1, min(10, int(float(re.sub(r"[^\d.]", "", skor_str)))))
    except:
        skor = None

    return {
        "skor":      skor,
        "ringkasan": ekstrak("ringkasan"),
        "fokus":     ekstrak("fokus"),
        "tips":      ekstrak("tips"),
    }


# ═══════════════════════════════════════════════
# BAGIAN 4: KALENDER HTML+JS INTERAKTIF
# ═══════════════════════════════════════════════

def render_kalender(beban_json: str, tahun_awal: int, bulan_awal: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:transparent;padding:6px 10px}}
.cal-nav{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
.cal-nav button{{background:#4a90d9;color:#fff;border:none;border-radius:8px;padding:8px 20px;
  font-size:.95rem;cursor:pointer;transition:background .2s;font-weight:600}}
.cal-nav button:hover{{background:#2c6fad}}
.month-lbl{{font-size:1.35rem;font-weight:800;color:#1a1a2e}}
.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}}
.hdr{{text-align:center;font-size:.68rem;font-weight:700;color:#999;padding:5px 0;
  letter-spacing:.05em;text-transform:uppercase}}
.cell{{border-radius:10px;min-height:78px;padding:7px 6px;border:2px solid transparent;
  transition:transform .15s,box-shadow .15s;font-size:.7rem}}
.cell.click{{cursor:pointer}}
.cell.click:hover{{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.18);
  border-color:#4a90d9!important;z-index:2}}
.cell.empty{{background:transparent}}
.cell.c0{{background:#f4f5f7;color:#bbb}}
.cell.c1{{background:#e8f4fd;border-color:#b3d9f5}}
.cell.c2{{background:#fff3cd;border-color:#ffc107}}
.cell.c3{{background:#ffe0b2;border-color:#ff9800}}
.cell.c4{{background:#ffccbc;border-color:#ff5722}}
.cell.c5{{background:#e53935;border-color:#b71c1c;color:#fff}}
.cell.today{{outline:3px solid #1976d2;outline-offset:-2px}}
.cell.today .dn{{color:#1976d2;font-weight:900}}
.dn{{font-size:.9rem;font-weight:700;margin-bottom:4px;display:flex;
  justify-content:space-between;align-items:center}}
.badge{{background:rgba(0,0,0,.12);border-radius:20px;padding:1px 7px;
  font-size:.6rem;font-weight:800}}
.c5 .badge{{background:rgba(255,255,255,.25)}}
.chip{{display:block;background:rgba(0,0,0,.07);border-radius:5px;padding:2px 5px;
  margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.62rem}}
.c5 .chip{{background:rgba(255,255,255,.2);color:#fff}}
.chip.pt{{border-left:3px solid #e53935}}
.chip.ps{{border-left:3px solid #ff9800}}
.chip.pr{{border-left:3px solid #4caf50}}
.legend{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;
  margin-top:14px;font-size:.7rem;color:#666}}
.leg{{display:flex;align-items:center;gap:5px}}
.lb{{width:14px;height:14px;border-radius:4px;border:1px solid rgba(0,0,0,.1);flex-shrink:0}}
/* Modal */
.overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);
  z-index:1000;align-items:center;justify-content:center;padding:16px}}
.overlay.on{{display:flex}}
.modal{{background:#fff;border-radius:18px;padding:26px;max-width:500px;width:100%;
  max-height:82vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,.3);
  animation:up .22s ease}}
@keyframes up{{from{{transform:translateY(24px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
.m-date{{font-size:1.05rem;font-weight:800;color:#1a1a2e;margin-bottom:3px}}
.m-sub{{font-size:.78rem;color:#888;margin-bottom:16px}}
.tcard{{background:#f8f9fa;border-radius:11px;padding:13px 14px;margin-bottom:10px}}
.tc-name{{font-weight:700;font-size:.92rem;color:#1a1a2e;margin-bottom:6px}}
.tc-row{{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.76rem;color:#555}}
.tc-row span{{display:flex;align-items:center;gap:4px}}
.pbadge{{display:inline-block;padding:2px 10px;border-radius:20px;
  font-size:.66rem;font-weight:700;margin-top:7px}}
.pt{{background:#fde8e8;color:#c62828}}
.ps{{background:#fff3e0;color:#e65100}}
.pr{{background:#e8f5e9;color:#2e7d32}}
.sdone{{background:#e8f5e9;color:#2e7d32;font-size:.66rem;font-weight:700;
  padding:2px 10px;border-radius:20px;display:inline-block;margin-top:7px;margin-left:6px}}
.stodo{{background:#fff3e0;color:#e65100;font-size:.66rem;font-weight:700;
  padding:2px 10px;border-radius:20px;display:inline-block;margin-top:7px;margin-left:6px}}
.btn-close{{width:100%;margin-top:16px;padding:11px;background:#f0f2f5;border:none;
  border-radius:9px;font-size:.88rem;cursor:pointer;color:#333;font-weight:600;transition:background .2s}}
.btn-close:hover{{background:#e2e5ea}}
</style></head>
<body>
<div class="cal-nav">
  <button onclick="nav(-1)">&#8592; Prev</button>
  <span class="month-lbl" id="lbl"></span>
  <button onclick="nav(1)">Next &#8594;</button>
</div>
<div class="cal-grid" id="grid"></div>
<div class="legend">
  <div class="leg"><div class="lb" style="background:#f4f5f7"></div>Bebas</div>
  <div class="leg"><div class="lb" style="background:#e8f4fd;border-color:#b3d9f5"></div>1</div>
  <div class="leg"><div class="lb" style="background:#fff3cd;border-color:#ffc107"></div>2</div>
  <div class="leg"><div class="lb" style="background:#ffe0b2;border-color:#ff9800"></div>3</div>
  <div class="leg"><div class="lb" style="background:#ffccbc;border-color:#ff5722"></div>4</div>
  <div class="leg"><div class="lb" style="background:#e53935"></div>5+ 🚨</div>
  <div class="leg"><div class="lb" style="outline:3px solid #1976d2;background:#fff"></div>Hari ini</div>
</div>
<div class="overlay" id="ov" onclick="closeM(event)">
  <div class="modal">
    <div class="m-date" id="md"></div>
    <div class="m-sub"  id="ms"></div>
    <div id="mb"></div>
    <button class="btn-close" onclick="closeML()">✕ Tutup</button>
  </div>
</div>
<script>
const D={beban_json};
let Y={tahun_awal},M={bulan_awal};
const BLN=["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
const HPN=["Minggu","Senin","Selasa","Rabu","Kamis","Jumat","Sabtu"];
const BS=["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
function pad(n){{return String(n).padStart(2,"0")}}
function key(y,m,d){{return y+"-"+pad(m)+"-"+pad(d)}}
function render(){{
  document.getElementById("lbl").textContent=BLN[M]+" "+Y;
  const g=document.getElementById("grid");g.innerHTML="";
  ["Sen","Sel","Rab","Kam","Jum","Sab","Min"].forEach(h=>{{
    const e=document.createElement("div");e.className="hdr";e.textContent=h;g.appendChild(e);
  }});
  const today=new Date();
  const fd=new Date(Y,M,1);
  const td=new Date(Y,M+1,0).getDate();
  const off=(fd.getDay()+6)%7;
  for(let i=0;i<off;i++){{const e=document.createElement("div");e.className="cell empty";g.appendChild(e);}}
  for(let d=1;d<=td;d++){{
    const k=key(Y,M+1,d);
    const info=D[k];const n=info?info.jumlah:0;
    let cls=n===0?"c0":n===1?"c1":n===2?"c2":n===3?"c3":n===4?"c4":"c5";
    const isTd=(d===today.getDate()&&M===today.getMonth()&&Y===today.getFullYear());
    const cell=document.createElement("div");
    cell.className="cell "+cls+(isTd?" today":"")+(n>0?" click":"");
    let badge=n>0?`<span class="badge">${{n}}</span>`:"";
    let chips="";
    if(info){{
      info.tugas.slice(0,2).forEach(t=>{{
        const nm=t.tugas.length>16?t.tugas.slice(0,16)+"…":t.tugas;
        const pc=(t.prioritas||"").toLowerCase().startsWith("t")?"pt":
                 (t.prioritas||"").toLowerCase().startsWith("r")?"pr":"ps";
        chips+=`<span class="chip ${{pc}}">📌 ${{nm}}</span>`;
      }});
      if(info.tugas.length>2)chips+=`<span class="chip">+${{info.tugas.length-2}} lagi…</span>`;
    }}
    cell.innerHTML=`<div class="dn"><span>${{d}}</span>${{badge}}</div>${{chips}}`;
    if(n>0)cell.addEventListener("click",()=>openM(k,info,d));
    g.appendChild(cell);
  }}
}}
function nav(dir){{M+=dir;if(M<0){{M=11;Y--;}}if(M>11){{M=0;Y++;}}render();}}
function openM(k,info,d){{
  const pts=k.split("-");const dt=new Date(+pts[0],+pts[1]-1,+pts[2]);
  document.getElementById("md").textContent=HPN[dt.getDay()]+", "+d+" "+BS[dt.getMonth()]+" "+dt.getFullYear();
  document.getElementById("ms").textContent=info.jumlah+" tugas deadline hari ini";
  let html="";
  info.tugas.forEach((t,i)=>{{
    const pc=(t.prioritas||"").toLowerCase().startsWith("t")?"pt":
             (t.prioritas||"").toLowerCase().startsWith("r")?"pr":"ps";
    const done=(t.status||"").toLowerCase().includes("selesai")||(t.status||"").toLowerCase().includes("done");
    html+=`<div class="tcard">
      <div class="tc-name">${{i+1}}. ${{t.tugas}}</div>
      <div class="tc-row">
        ${{t.matkul&&t.matkul!=="—"?`<span>📚 ${{t.matkul}}</span>`:""}}
        <span>📅 ${{t.deadline}}</span>
        <span>⏱️ ${{t.estimasi_jam}} jam</span>
      </div>
      <span class="pbadge ${{pc}}">🎯 ${{t.prioritas||"Sedang"}}</span>
      <span class="${{done?"sdone":"stodo"}}">${{done?"✅ Selesai":"⏳ Belum Selesai"}}</span>
    </div>`;
  }});
  document.getElementById("mb").innerHTML=html;
  document.getElementById("ov").classList.add("on");
}}
function closeM(e){{if(e.target===document.getElementById("ov"))closeML();}}
function closeML(){{document.getElementById("ov").classList.remove("on");}}
document.addEventListener("keydown",e=>{{if(e.key==="Escape")closeML();}});
render();
</script>
</body></html>"""


# ═══════════════════════════════════════════════
# TAMPILAN UTAMA
# ═══════════════════════════════════════════════

# ── Sidebar: pilih model ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pengaturan AI")
    model_pilihan = st.selectbox(
        "Model Ollama",
        options=MODEL_OPTIONS,
        index=0,
        help="llama3.1:8b paling bagus. phi3 paling ringan tapi sering gagal JSON.",
    )
    st.caption(
        """**Rekomendasi:**
- `llama3.1:8b` — terbaik, ~5GB
- `phi3` — ringan, ~2.3GB (kadang tidak konsisten)
```"""
    )
    st.divider()
    st.caption("🧠 CogniPace AI v4\nStreamlit + Pandas + Ollama")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🧠 CogniPace AI")
st.markdown(
    "**Asisten Manajemen Beban Kognitif Mahasiswa**  \n"
    "Upload CSV tugas → Python generate kalender & jadwal → AI berikan analisis & tips"
)
st.divider()

# ── Upload ────────────────────────────────────────────────────────────────────
st.subheader("📂 Upload Data Tugas")
st.caption(
    "Format CSV bebas — minimal kolom **nama tugas** dan **deadline**. "
    "Kolom lain (prioritas, estimasi waktu, matkul, status) opsional."
)
uploaded_file = st.file_uploader("Pilih file .csv", type=["csv"])

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)

    st.subheader("👀 Preview Data")
    st.dataframe(df_raw, use_container_width=True)

    # Deteksi kolom
    mapping = deteksi_kolom(df_raw)
    kolom_display = " · ".join([f"**{k}** → `{v}`" for k, v in mapping.items()])
    if mapping:
        st.info(f"🔍 Kolom terdeteksi: {kolom_display}")
    else:
        st.warning("⚠️ Tidak ada kolom standar yang dikenali. Pastikan ada kolom deadline.")

    if "deadline" not in mapping:
        st.error("❌ Kolom **deadline** tidak ditemukan. Periksa nama kolom di CSV.")
        st.stop()

    df_proc = proses_df(df_raw, mapping)
    total_valid   = df_proc["_deadline"].notna().sum()
    total_aktif   = (~df_proc["_selesai"] & df_proc["_deadline"].notna()).sum()

    st.info(f"📊 {len(df_raw)} baris · {total_valid} dengan deadline valid · {total_aktif} belum selesai")
    st.divider()

    # ── Tombol ───────────────────────────────────────────────────────────────
    if st.button("🔍 Buat Kalender & Analisis AI", type="primary", use_container_width=True):

        # ── PROSES DATA (Python, selalu berhasil) ────────────────────────────
        beban_dict  = bangun_beban(df_proc)
        df_prio     = bangun_tabel_prioritas(df_proc)
        df_jadwal   = bangun_jadwal_harian(df_proc)

        # ── PANGGIL AI (opsional, hanya untuk teks) ──────────────────────────
        ai_hasil = {"skor": None, "ringkasan": "", "fokus": "", "tips": ""}
        ai_error = None

        if not OLLAMA_TERSEDIA:
            ai_error = "Library `ollama` tidak ditemukan. `pip install ollama`"
        else:
            with st.spinner(f"🤖 AI ({model_pilihan}) menganalisis... (~10-20 detik)"):
                try:
                    kolom_info = ", ".join([f'"{c}"' for c in df_raw.columns])
                    respons_ai = panggil_ai_analisis(
                        df_raw.to_csv(index=False), kolom_info, model_pilihan
                    )
                    ai_hasil = parse_ai_teks(respons_ai)
                    # Simpan raw untuk debug
                    st.session_state["ai_raw"] = respons_ai
                except Exception as e:
                    ai_error = str(e)
                    st.session_state["ai_raw"] = ""

        st.success("✅ Kalender & jadwal siap!")

        # ════════════════════════════════════════
        # OUTPUT
        # ════════════════════════════════════════

        # ── Metrik ───────────────────────────────────────────────────────────
        total_padat = sum(1 for v in beban_dict.values() if v["jumlah"] >= 3)
        c1, c2, c3 = st.columns(3)
        with c1:
            skor = ai_hasil.get("skor")
            if skor:
                delta = "⚠️ Berat" if skor >= 7 else ("🟡 Sedang" if skor >= 4 else "🟢 Ringan")
                st.metric("🎯 Skor Beban (AI)", f"{skor} / 10", delta)
            else:
                st.metric("🎯 Skor Beban (AI)", "N/A", "AI offline" if ai_error else "—")
        with c2:
            st.metric("📋 Tugas Aktif", f"{total_aktif} tugas")
        with c3:
            st.metric("🔴 Hari Padat (3+ DL)", f"{total_padat} hari")

        # AI error notice (kecil, tidak blokir output)
        if ai_error:
            st.warning(
                f"⚠️ AI tidak tersedia ({ai_error[:80]}...). "
                "Kalender & jadwal tetap ditampilkan dari data CSV."
            )

        st.divider()

        # ── Kalender ─────────────────────────────────────────────────────────
        st.subheader("📅 Kalender Beban Tugas")
        st.caption(
            "Navigasi dengan **← Prev / Next →** · "
            "**Klik tanggal berwarna** → detail tugas, prioritas & estimasi"
        )

        if beban_dict:
            tgl0    = min(beban_dict.keys())
            thn_awal = int(tgl0[:4])
            bln_awal = int(tgl0[5:7]) - 1
        else:
            thn_awal = date.today().year
            bln_awal = date.today().month - 1

        beban_js = json.dumps(beban_dict, ensure_ascii=False)
        components.html(render_kalender(beban_js, thn_awal, bln_awal), height=540, scrolling=False)

        st.divider()

        # ── Tabel prioritas ───────────────────────────────────────────────────
        st.subheader("📋 Tabel Prioritas Pengerjaan Tugas")
        st.caption("Urutan: deadline terdekat + prioritas tertinggi → kerjakan dari baris paling atas")

        if not df_prio.empty:
            def warnai(row):
                u = row.get("Urgensi","")
                if "Terlambat" in u or "Kritis" in u: return ["background-color:#ffe0e0"]*len(row)
                elif "Mendesak" in u:                 return ["background-color:#fff3e0"]*len(row)
                elif "Perhatikan" in u:               return ["background-color:#fffde7"]*len(row)
                else:                                 return ["background-color:#f1f8e9"]*len(row)
            st.dataframe(
                df_prio.style.apply(warnai, axis=1),
                use_container_width=True,
                height=min(60 + len(df_prio)*38, 400),
            )
        else:
            st.success("🎉 Semua tugas sudah selesai!")

        st.divider()

        # ── Jadwal harian ─────────────────────────────────────────────────────
        st.subheader("🗓️ Rekomendasi Jadwal Harian")
        st.caption("Jadwal otomatis dari algoritma Python — 1 tugas per hari, diurutkan dari yang paling mendesak")

        if not df_jadwal.empty:
            def warnai_jadwal(row):
                c = row.get("Catatan","")
                if "Deadline HARI INI" in c or "terlewat" in c:
                    return ["background-color:#ffe0e0"]*len(row)
                elif "🔴" in c:
                    return ["background-color:#fff3e0"]*len(row)
                else:
                    return [""]*len(row)
            st.dataframe(
                df_jadwal.style.apply(warnai_jadwal, axis=1),
                use_container_width=True,
                hide_index=True,
                height=min(60 + len(df_jadwal)*38, 460),
            )
        else:
            st.info("Tidak ada tugas aktif yang perlu dijadwalkan.")

        st.divider()

        # ── Analisis & Tips AI ────────────────────────────────────────────────
        st.subheader("💡 Analisis & Tips dari AI")

        ringkasan = ai_hasil.get("ringkasan","")
        fokus     = ai_hasil.get("fokus", "") # PERUBAHAN 3: Ambil nilai fokus
        tips      = ai_hasil.get("tips","")

        if ringkasan:
            st.info(f"📊 **Analisis Kondisi:** {ringkasan}")

        # Menampilkan Pemecahan Tugas (Micro-Stepping) dalam kotak sukses
        if fokus:
            st.success(f"🎯 **Pemecahan Tugas Terberat (Micro-Stepping):**\n\n{fokus}")

        if tips:
            st.markdown("**💡 Tips Manajemen Waktu:**")
            st.markdown(tips)

        if not ringkasan and not tips and not fokus:
            if ai_error:
                st.info(
                    "💡 AI tidak tersedia. Gunakan kalender dan tabel prioritas di atas "
                    "sebagai panduan pengerjaan tugas."
                )
            else:
                st.info("AI tidak memberikan analisis untuk data ini.")

        # Debug expander
        if st.session_state.get("ai_raw"):
            with st.expander("🛠️ Respons mentah AI (debug)"):
                st.text(st.session_state["ai_raw"])

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🧠 CogniPace AI v4 · Python-first + Ollama optional · Streamlit + Pandas")
