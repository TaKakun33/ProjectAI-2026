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
- Heatmap 5 level warna untuk memantau kepadatan deadline[cite: 6].
- Tabel prioritas otomatis yang mengurutkan tugas berdasarkan urgensi (kritis, mendesak, atau aman).

### 🤖 Analisis & Pemecahan Tugas (AI)
- **Skor Beban Kognitif:** Prediksi tingkat stres studi (skala 1–10).
- **Micro-Stepping:** AI secara otomatis mendeteksi tugas terberat dan memecahnya menjadi 3 langkah kecil yang konkret untuk dikerjakan.
- **Tips Manajemen Waktu:** Rekomendasi teknik belajar yang disesuaikan.

### 💬 Chatbot Asisten Akademik
- Fitur chat interaktif yang memungkinkan mahasiswa bertanya seputar jadwal (contoh: *"Tugas apa yang harus dikerjakan besok?"*).
- Menjawab berdasarkan "sumber kebenaran" dari data jadwal yang Anda unggah, sehingga meminimalkan risiko halusinasi AI.

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

### 3. Model AI (diunduh via Ollama)
Anda dapat memilih antara model llama3.1:8b (untuk akurasi tinggi) atau phi3 (untuk perangkat yang lebih ringan). Unduh model yang diinginkan di terminal:
```bash
# Untuk akurasi tinggi
ollama pull llama3.1:8b

# Untuk perangkat ringan
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

ollama pull phi3
