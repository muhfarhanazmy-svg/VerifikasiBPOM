# Sample Hardhat Project

This project demonstrates a basic Hardhat use case. It comes with a sample contract, a test for that contract, and a Hardhat Ignition module that deploys that contract.

Try running some of the following tasks:

```shell
npx hardhat help
npx hardhat test
REPORT_GAS=true npx hardhat test
npx hardhat node
npx hardhat ignition deploy ./ignition/modules/Lock.js
```
# VerifikasiBPOM
# Verifikasi BPOM Berbasis Blockchain

Aplikasi verifikasi produk BPOM menggunakan smart contract `SertifikasiProduk` (Hardhat), antarmuka Streamlit, dan integrasi Web3.py.

## Prasyarat

- Node.js (disarankan versi LTS) dan npm
- Python 3.10 atau lebih baru

## Cara Menjalankan

### 1. Instal dependensi

```bash
npm install
pip install streamlit web3
```

### 2. Compile smart contract

```bash
npx hardhat compile
```

### 3. Jalankan node Hardhat

Buka terminal baru dan biarkan tetap berjalan:

```bash
npx hardhat node
```

### 4. Deploy smart contract

Di terminal lain:

```bash
npx hardhat run scripts/deploy.js --network localhost
```

Alamat contract tersimpan di `deployment.json` dan dibaca otomatis oleh aplikasi.

> Di Windows, pesan `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)` setelah deploy berhasil adalah bug Node.js saat proses keluar dan dapat diabaikan.

### 5. Jalankan aplikasi

Pastikan `app.py` berada di folder project Hardhat, lalu:

```bash
streamlit run app.py
```

Buka `http://localhost:8501` di browser.

### 6. Atur role (sekali setelah deploy)

| Akun | Role | Cara |
|------|------|------|
| Akun #0 | Admin | Otomatis (akun yang melakukan deploy) |
| Akun #1 | BPOM | Halaman **Pengaturan Akun**, tab **Atur BPOM** |
| Akun #2 | Produsen | Halaman **Pengaturan Akun**, tab **Kelola Produsen** |

Pilih akun aktif lewat dropdown **Akun aktif** di sidebar. Alamat akun dapat disalin dari terminal `hardhat node` atau dari bagian **Daftar akun Hardhat** di halaman Pengaturan Akun.

## Alur Penggunaan

1. **Admin (Akun #0):** atur akun BPOM dan Produsen.
2. **Produsen (Akun #2):** daftarkan produk di halaman **Tambah Produk**.
3. **BPOM (Akun #1):** setujui atau tolak produk di halaman **Verifikasi BPOM**.
4. **Semua pengguna:** lihat hasil di **Dashboard**, **Daftar Produk**, atau **Detail Produk**.

## Catatan

- Setiap kali `npx hardhat node` dihentikan dan dijalankan ulang, seluruh data blockchain hilang. Deploy ulang contract dan atur ulang role.
- Transaksi ditandatangani oleh akun Hardhat lokal melalui Web3.py, bukan MetaMask.

## Pemecahan Masalah

| Pesan error | Solusi |
|-------------|--------|
| `Tidak bisa terhubung ke http://127.0.0.1:8545` | Jalankan `npx hardhat node`. |
| `File ABI tidak ditemukan` | Jalankan `npx hardhat compile`. |
| `ABI belum memiliki fungsi semuaBatchId()` | Gunakan `SertifikasiProduk.sol` versi terbaru, lalu compile dan deploy ulang. |
| `Tidak ada contract di alamat ...` | Node di-restart. Deploy ulang contract. |
| `Akses ditolak` | Ganti akun aktif di sidebar sesuai role yang dibutuhkan. |