# 🧠 CogniPace AI

> **Asisten Manajemen Beban Kognitif Mahasiswa**  
> Aplikasi web berbasis AI yang membantu mahasiswa memprediksi beban studi, memvisualisasikan tumpukan deadline lewat kalender interaktif, dan menyusun jadwal prioritas pengerjaan tugas secara otomatis.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)
![Ollama](https://img.shields.io/badge/Ollama-phi3-green)

---

Branch ini adalah versi **online** dari CogniPace AI yang menggunakan **Groq API** sebagai AI engine. Tidak perlu install Ollama atau mendownload model AI — cukup daftarkan API key gratis dan langsung jalan.
 
> 🔀 Mencari versi offline? Lihat branch [`ollama`](https://github.com/TaKakun33/ProjectAI-2026/tree/Ollama)
 
---


## 📖 Tentang Aplikasi

CogniPace AI adalah prototype aplikasi web yang dirancang untuk membantu mahasiswa mengelola beban kognitif akademik mereka. Dengan mengunggah file CSV berisi data tugas, aplikasi ini akan:

1. **Memvisualisasikan** distribusi deadline dalam bentuk kalender heatmap interaktif
2. **Memprediksi** skor beban kognitif menggunakan Online LLM (Groq)
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
- Dibuat dari Pandas 

### 🤖 Analisis AI 
- Prediksi skor beban kognitif (skala 1–10)
- Jadwal harian terstruktur (tabel JSON dari AI)
- Ringkasan analisis dan tips manajemen waktu
- Fleksibel Pilih model llama-3.3-70b-versatile (pintar), llama-3.1-8b-instant (instant) atau gemma2-9b-it (alternative)  langsung dari aplikasi.

### 📂 CSV Dinamis
Aplikasi mengenali **berbagai format kolom** secara otomatis tidak harus menggunakan nama kolom tertentu.

---

## 🌐 Akses Prototipe (Live Demo)

Anda dapat mencoba aplikasi CogniPace AI secara langsung melalui web tanpa perlu melakukan instalasi di komputer Anda:

> **🔗 [Klik di sini untuk membuka CogniPace AI](https://cognipace.streamlit.app)**
