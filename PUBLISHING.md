# Publikasi CVGO ke PyPI

Panduan ini digunakan agar pengguna nantinya dapat memasang CVGO dengan:

```bash
pip install cvgo
```

## 1. Periksa nama proyek

Buka halaman berikut:

```text
https://pypi.org/project/cvgo/
```

Halaman 404 biasanya berarti belum ada rilis publik dengan nama tersebut.
Namun, kepastian terakhir tetap ditentukan PyPI saat upload pertama karena
sebuah nama dapat ditahan atau terlalu mirip dengan proyek lain.

## 2. Buat akun

Buat dua akun terpisah:

- TestPyPI: https://test.pypi.org/account/register/
- PyPI: https://pypi.org/account/register/

Aktifkan 2FA dan buat API token. Jangan memasukkan token ke source code,
repository Git, README, atau file yang dibagikan.

## 3. Siapkan environment

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 4. Jalankan pengujian

```bash
python -m unittest discover -s tests -v
python -m compileall -q src examples tests
```

Lakukan juga pengujian manual dengan webcam, Arduino, dan satu chat Telegram
khusus pengujian pada environment yang memakai MediaPipe 0.10.21 sebelum rilis.
Pastikan token Telegram hanya disimpan sebagai environment variable dan tidak
ikut masuk ke source, contoh, log, atau distribution.

Siapkan dan uji model Tasks API sebelum rilis:

```bash
python -c "import cvgo as go; go.download_model('object_detection')"
python -c "import cvgo as go; go.download_model('gesture_recognizer')"
```

Model tidak dimasukkan ke wheel. `ObjectDetector` dan `GestureRecognizer`
mengunduh model resmi MediaPipe satu kali, lalu menggunakannya dari cache.

## 5. Build distribution

Pastikan folder `dist` dari percobaan lama sudah tidak digunakan, kemudian:

```bash
python -m build
python -m twine check dist/*
```

Hasil normalnya terdiri dari:

```text
dist/cvgo-0.1.1.tar.gz
dist/cvgo-0.1.1-py3-none-any.whl
```

## 6. Uji di TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

Username untuk token:

```text
__token__
```

Password adalah API token TestPyPI lengkap yang diawali `pypi-`.

Uji instalasinya di virtual environment baru. Dependency tetap diambil dari
PyPI utama karena TestPyPI tidak selalu mempunyai semua dependency:

```bash
pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  cvgo
```

Lalu uji:

```bash
python -c "import cvgo; print(cvgo.__version__)"
```

## 7. Upload ke PyPI

Jika TestPyPI berhasil:

```bash
python -m twine upload dist/*
```

Setelah rilis tampil, uji lagi di virtual environment baru:

```bash
pip install cvgo
python -c "import cvgo; print(cvgo.__version__)"
```

## 8. Rilis berikutnya

File dengan nomor versi yang sama tidak dapat diunggah ulang. Jika ada revisi,
ubah versi di `pyproject.toml`, misalnya:

```toml
version = "0.1.1"
```

Lalu build ulang dan upload file versi baru.

## Versi inti CVGO

CVGO mengunci stack inti yang telah diuji:

```toml
numpy==1.26.4
opencv-contrib-python==4.11.0.86
mediapipe==0.10.21
```

Penguncian versi ini menjaga API `mp.solutions`, model, modul `cv2`, dan hasil
pengujian agar konsisten antara komputer pengembang dan komputer peserta.
Gunakan virtual environment khusus agar exact pin tidak berbenturan dengan
proyek lain yang membutuhkan OpenCV atau NumPy versi berbeda.
