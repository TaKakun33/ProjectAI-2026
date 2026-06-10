# 🧠 CogniPace AI

> **Asisten Manajemen Beban Kognitif Mahasiswa**  
> Aplikasi web berbasis AI yang membantu mahasiswa memprediksi beban studi, memvisualisasikan tumpukan deadline lewat kalender interaktif, dan menyusun jadwal prioritas pengerjaan tugas secara otomatis.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)
![Ollama](https://img.shields.io/badge/Ollama-phi3-green)

---

## 📖 Tentang Aplikasi

CogniPace AI adalah prototype aplikasi web yang dirancang untuk membantu mahasiswa mengelola beban kognitif akademik mereka. Dengan mengunggah file CSV berisi data tugas, aplikasi ini akan:

1. **Memvisualisasikan** distribusi deadline dalam bentuk kalender heatmap interaktif
2. **Memprediksi** skor beban kognitif menggunakan Local LLM (Ollama + phi3)
3. **Menyusun** jadwal prioritas pengerjaan tugas secara otomatis berdasarkan kedekatan deadline dan tumpukan tugas
4. **Merekomendasikan** actionable plan harian agar semua tugas selesai tepat waktu

---

## ✨ Fitur Utama

### 📅 Kalender Interaktif
- Navigasi bebas ke bulan manapun menggunakan tombol **Prev / Next**
- **Klik tanggal** untuk melihat detail lengkap tugas yang jatuh tempo pada hari tersebut (nama tugas, mata kuliah, status)
- Heatmap 5 level warna berdasarkan kepadatan deadline
- Highlight khusus untuk hari ini

| Warna | Keterangan |
|-------|-----------|
| ⬜ Abu-abu | Tidak ada tugas |
| 🟨 Kuning | 1 tugas |
| 🟧 Oranye | 2 tugas |
| 🟥 Merah muda | 3 tugas |
| 🔴 Merah tua | 4 tugas |
| 🚨 Merah pekat | 5+ tugas (Zona Kritis) |

### 📋 Tabel Prioritas Otomatis
- Tugas diurutkan berdasarkan **skor prioritas** (deadline terdekat + tumpukan terbanyak = prioritas tertinggi)
- Label urgensi berwarna: 🔴 Kritis → 🟠 Mendesak → 🟡 Perhatikan → 🟢 Aman
- Dibuat dari Pandas **tetap berfungsi meski Ollama offline**

### 🤖 Analisis AI (Ollama phi3)
- Prediksi skor beban kognitif (skala 1–10)
- Jadwal harian terstruktur (tabel JSON dari AI)
- Ringkasan analisis dan tips manajemen waktu

### 📂 CSV Dinamis
Aplikasi mengenali **berbagai format kolom** secara otomatis tidak harus menggunakan nama kolom tertentu.

---

## 🔧 Prasyarat

Pastikan semua komponen berikut sudah terpasang di komputer kamu sebelum instalasi:

### 1. Python 3.10 atau lebih baru
```bash
python --version
# Output: Python 3.10.x atau lebih baru
```
Download: https://www.python.org/downloads/

### 2. Ollama
Ollama adalah runtime untuk menjalankan Large Language Model secara lokal.

- **Windows / macOS**: Download installer dari https://ollama.com/download
- **Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. Model phi3 (diunduh via Ollama)
Setelah Ollama terpasang, unduh model phi3 (~2.3 GB):
```bash
ollama pull phi3
```

### 4. Git (opsional, untuk clone repo)
Download: https://git-scm.com/downloads

---

## 🚀 Instalasi

### Langkah 1: Clone atau Download Repositori

**Menggunakan Git:**
```bash
git clone https://github.com/TaKakun33/ProjectAI-2026.git
cd ProjectAI-2026
```

**Atau download ZIP** dari tombol hijau "Code" → "Download ZIP", lalu ekstrak.

---

### Langkah 2: Buat Virtual Environment (Direkomendasikan)

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

---

### Langkah 3: Install Dependensi Python

```bash
pip install ollama streamlit pandas
```

Paket yang akan diinstall:

| Paket | Versi Minimum | Fungsi |
|-------|--------------|--------|
| `streamlit` | 1.35.0 | Framework UI web |
| `pandas` | 2.0.0 | Pengolahan data CSV |
| `ollama` | 0.2.0 | Koneksi ke Ollama local LLM |

---

### Langkah 4: Jalankan Server Ollama

Buka **terminal/command prompt baru** (terpisah dari terminal aplikasi), lalu jalankan:

```bash
ollama serve
```

Biarkan terminal ini tetap terbuka selama menggunakan aplikasi.

> **Catatan:** Di beberapa sistem, Ollama otomatis berjalan di background setelah instalasi. Jika perintah `ollama serve` menampilkan error "address already in use", berarti Ollama sudah berjalan dan kamu bisa langsung ke langkah berikutnya.

---

### Langkah 5: Jalankan Aplikasi

Kembali ke terminal pertama (yang sudah diaktifkan virtual environment), lalu jalankan:

```bash
streamlit run app.py
```

Aplikasi akan otomatis terbuka di browser pada alamat:
```
http://localhost:8501
```
