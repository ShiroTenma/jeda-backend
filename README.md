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
