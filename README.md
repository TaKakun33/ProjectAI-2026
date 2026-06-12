# 🧠 CogniPace AI

> **Asisten Manajemen Beban Kognitif Mahasiswa**  
> Aplikasi web berbasis AI yang membantu mahasiswa memprediksi beban studi, memvisualisasikan tumpukan deadline, menyusun jadwal prioritas otomatis, dan berdiskusi langsung mengenai beban tugas melalui Chatbot Akademik interaktif.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red?logo=streamlit)
![Ollama](https://img.shields.io/badge/Ollama-Supported-green)

---

## 📖 Tentang Aplikasi

CogniPace AI adalah prototype aplikasi web yang dirancang untuk membantu mahasiswa mengelola beban kognitif akademik mereka. Dengan mengunggah file CSV berisi data tugas, aplikasi ini akan:

1. **Memvisualisasikan** distribusi deadline dalam bentuk kalender heatmap interaktif.
2. **Menganalisis** skor beban kognitif dan memecah tugas terberat (Micro-Stepping) menggunakan Local LLM.
3. **Menyusun** jadwal prioritas pengerjaan tugas secara otomatis.
4. **Berdiskusi** secara interaktif mengenai jadwal dan tips belajar melalui **Chatbot Asisten Akademik**.

---

## ✨ Fitur Utama

### 📅 Kalender Interaktif & Tabel Prioritas
- Heatmap 5 level warna untuk memantau kepadatan deadline.
- Tabel prioritas otomatis yang mengurutkan tugas berdasarkan urgensi (kritis, mendesak, atau aman).

### 🤖 Analisis & Pemecahan Tugas (AI)
- **Skor Beban Kognitif:** Prediksi tingkat stres studi (skala 1–10).
- **Micro-Stepping:** AI secara otomatis mendeteksi tugas terberat dan memecahnya menjadi 3 langkah kecil yang konkret untuk dikerjakan.
- **Tips Manajemen Waktu:** Rekomendasi teknik belajar yang disesuaikan.

### 💬 Chatbot Asisten Akademik
- Fitur chat interaktif yang memungkinkan mahasiswa bertanya seputar jadwal (contoh: *"Tugas apa yang harus dikerjakan besok?"*).
- Menjawab berdasarkan "sumber kebenaran" dari data jadwal yang Anda unggah, sehingga meminimalkan risiko halusinasi AI.

---
 
## 🌿 Struktur Branch
 
Repositori ini memiliki **dua versi aplikasi** dalam branch yang berbeda, disesuaikan dengan kebutuhan dan kondisi jaringan:
 
```
ProjectAI-2026/
├── main          ← Branch ini (README & gambaran umum proyek)
├── ollama        ← Versi OFFLINE — AI lokal via Ollama
└── streamlit     ← Versi ONLINE  — AI cloud via Groq API
```
 
---
 
## 🔀 Pilih Versi yang Sesuai
 
| | Branch `ollama` | Branch `streamlit` |
|---|---|---|
| **Koneksi** | ✅ Bisa offline | 🌐 Butuh internet |
| **AI Engine** | Ollama (lokal) | Groq API (cloud) |
| **Model** | llama3.1:8b / phi3 / mistral | llama-3.1-8b-instant (gratis) |
| **Kecepatan AI** | Tergantung hardware | ⚡ Sangat cepat |
| **Setup** | Lebih panjang (install Ollama) | Lebih cepat (cukup API key) |
| **Biaya** | Gratis sepenuhnya | Gratis (Groq free tier) |
| **Cocok untuk** | Privasi tinggi, tanpa internet | Demo cepat, laptop low-spec |
 
---

## 📦 Branch `ollama` — Versi Offline
 
Gunakan branch ini jika kamu ingin menjalankan AI **100% lokal** tanpa mengirim data ke server manapun. <br>
➡️ Lihat **[README branch ollama](https://github.com/TaKakun33/ProjectAI-2026/blob/Ollama/README.md)** untuk panduan instalasi lengkap.

## 🌐 Akses Prototipe (Live Demo)

Anda dapat mencoba aplikasi CogniPace AI secara langsung melalui web tanpa perlu melakukan instalasi di komputer Anda:
> **🔗 [Klik di sini untuk membuka CogniPace AI](https://cognipace.streamlit.app)**
