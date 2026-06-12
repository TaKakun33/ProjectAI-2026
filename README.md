# 🧠 CogniPace AI

> **Asisten Manajemen Beban Kognitif Mahasiswa**  
> Aplikasi web berbasis AI yang membantu mahasiswa memprediksi beban studi, memvisualisasikan tumpukan deadline, menyusun jadwal prioritas otomatis, dan berdiskusi langsung mengenai beban tugas melalui Chatbot Akademik interaktif.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)
![Ollama](https://img.shields.io/badge/Ollama-Supported-green)

**🌐 Akses Prototipe (Live Demo)**
**[Klik di sini untuk membuka CogniPace AI](https://cognipace.streamlit.app)**

---

TUJUAN PRODUK
=============

Mahasiswa sering mengalami *overload* informasi dan kesulitan dalam mengatur prioritas tugas secara terstruktur. CogniPace mencoba menjembatani masalah tersebut dengan alur:

1. Pengguna mengunggah file .csv data tugas.
2. Sistem menghitung skor urgensi secara matematis (deterministik).
3. Visualisasi data melalui kalender heatmap dan tabel jadwal harian.
4. AI menganalisis beban studi, memberikan tips *micro-stepping*, dan menyediakan *chatbot* untuk konsultasi jadwal secara *real-time*.

---

FITUR UTAMA
===========

- **Kalender Heatmap Interaktif**: Visualisasi kepadatan deadline dengan 5 level warna.
- **Tabel Prioritas Otomatis**: Pengurutan tugas berdasarkan deadline dan bobot prioritas.
- **Analisis AI (Groq API)**: Prediksi skor beban studi (1-10), ringkasan kondisi, dan tips manajemen waktu.
- **Micro-Stepping**: Fitur AI untuk memecah tugas terberat menjadi 3 langkah konkret.
- **Chatbot Asisten Akademik**: Konsultasi jadwal berbasis konteks data (meminimalisir halusinasi AI).
- **CSV Dinamis**: Mengenali berbagai format kolom tugas secara otomatis.

---

TECH STACK
==========

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| Framework | Streamlit | UI Web & Deployment Cloud |
| Processing | Pandas | Manipulasi CSV, Kalender, Logika Penjadwalan |
| AI Engine | Groq API | Inference model Llama 3 (Cloud Based) |
| Bahasa | Python | Bahasa utama logika sistem |
| Deployment | Streamlit Cloud | Hosting aplikasi secara online |

---

ARSITEKTUR & STRUKTUR BRANCH
============================

CogniPace menggunakan *Hybrid Architecture*. Proses kritis tetap dilakukan oleh kode Python, sementara proses kreatif diserahkan ke AI.

**Versi Aplikasi:**
- `streamlit`: Versi Online (Groq API).
- `ollama`: Versi Offline (AI Lokal).

**Diagram Alur:**
1. Input CSV -> 2. Deteksi Kolom & Parsing (Pandas) -> 3. Perhitungan Skor & Kalender (Deterministik) -> 4. Panggilan API ke Groq/Ollama (AI) -> 5. Output di Dashboard.

---

ALASAN PEMILIHAN TEKNOLOGI
==========================

1. **Python & Pandas**
   Menjamin akurasi 100% untuk data tanggal dan perhitungan sisa hari. Logika ini bersifat faktual, sehingga tidak boleh diserahkan ke AI agar tidak terjadi kesalahan perhitungan.

2. **Streamlit**
   Pilihan terbaik untuk mengubah skrip data science menjadi aplikasi web fungsional yang cepat dan profesional.

3. **Groq API**
   Memungkinkan AI berjalan di *Cloud*, sehingga aplikasi tetap cepat diakses tanpa membebani RAM/GPU laptop pengguna. Respons model sangat cepat dibandingkan API lainnya.

---

CARA MENJALANKAN LOKAL
===============================
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
### 3. Model AI (diunduh via Ollama)
Anda dapat memilih antara model llama3.1:8b (untuk akurasi tinggi) atau phi3 (untuk perangkat yang lebih ringan). Unduh model yang diinginkan di terminal:
```bash
# Untuk perangkat ringan
ollama pull phi3

# Untuk akurasi tinggi
ollama pull llama3.1:8b
```

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


BATASAN PROTOTYPE
=================

- Format input terbatas pada file .csv.
- Akurasi analisis AI bergantung pada kualitas data tugas yang diunggah.
- Jadwal adalah rekomendasi, tetap memerlukan penyesuaian manual oleh pengguna.
- Versi Online membutuhkan koneksi internet untuk fitur AI (Chatbot & Analisis).

---

ROADMAP PENGEMBANGAN
====================

- Integrasi API kalender (Google Calendar).
- Penambahan fitur autentikasi pengguna.
- Pelacakan progres penyelesaian tugas (riwayat belajar).
- Optimasi model AI yang lebih ringan/spesifik untuk komoditas data tertentu.

---
*Dibuat oleh Tim CogniPace AI - 2026*
