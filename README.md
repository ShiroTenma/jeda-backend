# JEDA Backend

**JEDA (Digital Wellness & Behavioral Interception System)** — backend FastAPI untuk prototipe akademik pemantauan perilaku penggunaan perangkat dan intervensi digital.

Backend menerima ringkasan perilaku dan sampel visual dari [JEDA Android](https://github.com/ShiroTenma/jeda-android), melakukan penilaian melalui FDS (*behavioral scoring*) dan RRS (*risk aggregation*), serta menyediakan endpoint pesan intervensi kognitif.

> **Status:** Prototipe dalam pengembangan. Belum dirancang atau divalidasi untuk penggunaan produksi maupun sebagai alat diagnosis kesehatan.

## Daftar Isi

- [Arsitektur](#arsitektur)
- [Fitur](#fitur)
- [Teknologi](#teknologi)
- [Persyaratan](#persyaratan)
- [Instalasi dan Konfigurasi](#instalasi-dan-konfigurasi)
- [Menjalankan Backend](#menjalankan-backend)
- [Koneksi dengan Android](#koneksi-dengan-android)
- [API](#api)
- [Struktur Proyek](#struktur-proyek)
- [Pengujian](#pengujian)
- [Keamanan dan Privasi](#keamanan-dan-privasi)

## Arsitektur

```text
JEDA Android
   |  ringkasan perilaku / frame / permintaan pesan
   v
Tailscale (jaringan privat)
   |
   v
FastAPI
   ├── /api/analyze-behavior  → FDS
   ├── /api/analyze-frame     → visual classifier + RRS
   └── /api/cognitive-message → layanan pesan kognitif
```

Repository Android: [ShiroTenma/jeda-android](https://github.com/ShiroTenma/jeda-android).

## Fitur

- **Behavioral analysis:** Evaluasi snapshot perilaku menggunakan FDS.
- **Visual analysis:** Penerimaan frame dan pemrosesan melalui layanan klasifikasi visual.
- **Risk aggregation:** Penggabungan hasil analisis visual dan konteks sesi melalui RRS.
- **Cognitive message:** Endpoint untuk menghasilkan pesan intervensi berdasarkan konteks permintaan.
- **Token-based access:** Header `X-Backend-Token` untuk endpoint analisis.
- **Health check:** Endpoint publik untuk menguji ketersediaan backend.
- **Automated tests:** Pengujian untuk API, skema, FDS, RRS, analisis visual, dan pesan kognitif.

> Implementasi di repository ini merupakan prototipe. Keberadaan modul tidak berarti model, skor, atau intervensinya sudah tervalidasi secara klinis.

## Teknologi

| Komponen | Teknologi |
| --- | --- |
| Bahasa | Python 3.11+ |
| Web API | FastAPI |
| ASGI server | Uvicorn |
| Validasi data | Pydantic |
| Pengolahan citra dan inference | Pillow, NumPy, ONNX, ONNX Runtime |
| Dependency management | uv |
| Pengujian | pytest, HTTPX |
| Koneksi antarperangkat | Tailscale (disarankan) |

## Persyaratan

- Python 3.11 atau lebih baru.
- [uv](https://docs.astral.sh/uv/).
- Tailscale pada laptop/server dan perangkat Android untuk pengujian melalui jaringan privat.

## Instalasi dan Konfigurasi

```bash
git clone https://github.com/ShiroTenma/jeda-backend.git
cd jeda-backend
uv sync --group dev
```

Salin template konfigurasi:

```bash
cp .env.example .env
```

Pada Windows PowerShell, gunakan `Copy-Item .env.example .env`.

Buat token acak:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Atur `BACKEND_TOKEN` di `.env` menggunakan hasil tersebut. Jangan mengunggah file `.env` atau token ke Git.

**Penting:** Konfigurasi dibaca melalui environment variables di `app/config.py`. File `.env` tidak dibaca otomatis oleh aplikasi; jalankan Uvicorn dengan `--env-file .env` atau ekspor variabelnya ke environment.

Beberapa nilai FDS dapat dikonfigurasi melalui variabel berawalan `FDS_`. Default aktual didefinisikan di `app/config.py`. Komentar konfigurasi lama di `.env.example` mungkin tidak sepenuhnya sesuai dengan implementasi terbaru.

## Menjalankan Backend

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env --reload
```

Gunakan `--reload` hanya untuk development.

Endpoint health lokal:

```text
http://127.0.0.1:8000/health
```

Respons saat ini dari `app/main.py`:

```json
{
  "status": "ok",
  "service": "jeda-backend",
  "version": "0.3.0"
}
```

Dokumentasi API interaktif FastAPI tersedia secara default di `http://127.0.0.1:8000/docs`.

## Koneksi dengan Android

1. Jalankan Tailscale pada kedua perangkat dan sambungkan ke tailnet yang sama.
2. Pastikan backend berjalan dan dapat diakses dari perangkat Android.
3. Gunakan hostname MagicDNS `jeda-backend` jika sudah dikonfigurasi, atau gunakan IP Tailscale server.
4. Atur host, port, dan token yang sama melalui konfigurasi koneksi pada aplikasi Android.
5. Uji endpoint health terlebih dahulu sebelum menguji endpoint analisis.

Alamat `0.0.0.0` digunakan sebagai bind address server, **bukan** alamat yang dimasukkan ke perangkat Android.

## API

| Method | Endpoint | Fungsi | Autentikasi |
| --- | --- | --- | --- |
| GET | `/health` | Status layanan | Tidak |
| POST | `/api/analyze-behavior` | Analisis snapshot perilaku (FDS) | Token |
| POST | `/api/analyze-frame` | Analisis frame dan agregasi risiko (RRS) | Token |
| POST | `/api/cognitive-message` | Pesan intervensi kognitif | Token |

Endpoint yang dilindungi menggunakan header `X-Backend-Token`. Untuk payload dan respons yang akurat, lihat skema di `app/schemas/` atau dokumentasi OpenAPI saat server berjalan.

## Model Visual dan Atribusi

JEDA menggunakan **model klasifikasi visual pihak ketiga** untuk prototipe analisis frame. Pengembang JEDA **tidak mengklaim telah melatih model tersebut maupun membuat dataset pelatihannya**.

### Artefak model

Hasil inspeksi file ONNX lokal:

| File | Input / output | Keterangan |
| --- | --- | --- |
| `nsfw_classifier_5class_quantized.onnx` | `pixel_values` → `logits` (5 kelas) | Quantized Vision Transformer, model utama |
| `nsfw_model_quantized.onnx` | `pixel_values` → `logits` (2 kelas) | Quantized Vision Transformer, fallback |
| `baseline_classifier.onnx` | `input` → `probabilities` (2 kelas) | Model baseline sederhana berlabel `jeda-baseline`, fallback terakhir |

Preprocessing dan interpretasi skor diimplementasikan dalam `app/services/visual.py`. Pada model lima kelas, kode mengasumsikan urutan **drawings, hentai, neutral, porn, sexy** dan menghitung risiko sebagai jumlah probabilitas `hentai + porn + sexy`. Interpretasi ini merupakan keputusan implementasi JEDA.

### Sumber model dan atribusi

Model lima kelas yang digunakan JEDA berasal dari model pihak ketiga **[LukeJacob2023/nsfw-image-detector](https://huggingface.co/LukeJacob2023/nsfw-image-detector)** di Hugging Face, sebagaimana dikonfirmasi oleh pengembang JEDA. Pemilik/penerbit model asal adalah **LukeJacob2023**, dan halaman Hugging Face mencantumkan **lisensi Apache-2.0** untuk repositori model tersebut.

File `nsfw_classifier_5class_quantized.onnx` adalah artefak ONNX terkuantisasi yang digunakan aplikasi. **Asal model dasarnya diketahui, tetapi jalur pengunduhan spesifik, versi/revisi model, dan siapa yang melakukan konversi/kuantisasi belum terdokumentasi**. Repositori [onnx-community/nsfw-image-detector-ONNX](https://huggingface.co/onnx-community/nsfw-image-detector-ONNX) merupakan referensi konversi ONNX yang relevan, tetapi belum terkonfirmasi sebagai lokasi pengunduhan artefak JEDA.

Model card pihak ketiga menyebut penggunaan dataset kustom untuk pelatihan. **Tim JEDA tidak membuat dataset tersebut, tidak melakukan pelatihan model dasar, dan tidak mengklaim hasil evaluasi model aslinya sebagai hasil evaluasi JEDA.** Detail sumber dataset dan izin penggunaannya perlu dirujuk ke dokumentasi pemilik model.

Asal pasti file dua kelas `nsfw_model_quantized.onnx` **masih belum teridentifikasi**; jangan mengasumsikan file tersebut memiliki sumber atau lisensi yang identik hanya karena arsitekturnya serupa.

### Batasan

- Output klasifikasi merupakan estimasi statistik dan dapat menghasilkan false positive atau false negative.
- Hasil evaluasi model dari pihak ketiga tidak otomatis berlaku pada data dan perangkat JEDA.
- Risiko yang dihitung JEDA dari probabilitas klasifikasi tidak boleh dianggap ukuran klinis atau validasi perilaku.
- Sebelum mendistribusikan model atau mempublikasikan klaim performa, verifikasi provenance, lisensi, dan evaluasi pada data yang relevan.

## Struktur Proyek

```text
jeda-backend/
├── app/
│   ├── api/
│   │   ├── behavior.py
│   │   ├── cognitive.py
│   │   ├── deps.py
│   │   └── visual.py
│   ├── schemas/
│   ├── services/
│   │   ├── cognitive.py
│   │   ├── fds.py
│   │   ├── rrs.py
│   │   └── visual.py
│   ├── config.py
│   └── main.py
├── tests/
├── .env.example
└── pyproject.toml
```

## Pengujian

Jalankan seluruh pengujian:

```bash
uv run --group dev pytest -v
```

Pengujian endpoint health saja:

```bash
uv run --group dev pytest tests/test_health.py -v
```

Hasil tes tidak diklaim di sini; jalankan perintah tersebut pada environment Anda untuk memverifikasi kondisi terkini.

## Keamanan dan Privasi

JEDA merupakan prototipe akademik dan masih memerlukan penguatan sebelum dapat dipakai secara publik.

- Gunakan token yang kuat dan aktifkan autentikasi sebelum membuka akses jaringan.
- Batasi akses backend pada tailnet privat atau jaringan tepercaya; binding ke `0.0.0.0` memperluas interface yang menerima koneksi.
- Perlakukan screenshot atau frame sebagai data sensitif. Periksa mekanisme pemrosesan dan retensi sebelum menggunakan data nyata.
- Nilai FDS/RRS bersifat eksperimental, bukan diagnosis medis.
- Hindari menyimpan atau mencatat kredensial, foto pribadi, dan payload sensitif secara tidak perlu.

## Repository Terkait

[JEDA Android](https://github.com/ShiroTenma/jeda-android) — aplikasi Kotlin dan Jetpack Compose yang menyediakan monitoring, visual sampling, serta UI intervensi.
