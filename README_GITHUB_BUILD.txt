JAPARIS ID PHOTO PRO — BUILD WINDOWS EXE TANPA INSTALL PYTHON DI PC PENGGUNA

PENTING
Paket ini menyiapkan proses build .exe melalui komputer Windows milik GitHub Actions.
Python hanya dipasang di komputer build cloud, bukan di PC tempat aplikasi dipakai.

CARA MENDAPATKAN EXE
1. Buat akun gratis di https://github.com jika belum punya.
2. Buat repository baru bernama japaris-id-photo-pro. Pilih Public atau Private.
3. Upload seluruh isi folder paket ini ke repository, termasuk folder .github.
4. Buka tab Actions pada repository.
5. Pilih workflow "Build JAPARIS ID PHOTO PRO for Windows".
6. Klik tombol "Run workflow" lalu konfirmasi "Run workflow".
7. Tunggu sampai proses selesai dengan tanda hijau.
8. Buka hasil run tersebut, cari bagian Artifacts, lalu download
   JAPARIS-ID-PHOTO-PRO-Windows-MVP.
9. Ekstrak ZIP hasil download dan jalankan JAPARIS_ID_PHOTO_PRO.exe.

CATATAN MVP
- Target: Windows 10/11 64-bit.
- Pada penggunaan pertama, rembg mungkin mengunduh model U2Net dari internet.
  Jadi build MVP ini belum sepenuhnya offline pada pemakaian pertama.
- Setelah model tersedia, background removal dilakukan lokal.
- Smart Resolution masih menggunakan Lanczos interpolation, bukan AI super-resolution.
- Aturan resolusi: sisi terpanjang di bawah 2000 px dinaikkan proporsional menjadi 2000 px;
  jika 2000 px atau lebih, resolusi dipertahankan.
- Jangan gunakan foto pelanggan penting sebagai satu-satunya salinan; simpan file sumber.
- MVP belum memiliki brush refine, batch editing, crop ukuran pas foto, atau print layout.

Jika workflow gagal, buka log langkah yang merah dan kirim screenshot/log error.
