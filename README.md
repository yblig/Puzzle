# 🧩 Dunia Puzzle

Satu aplikasi, **33 game puzzle** asah otak — berbahasa Indonesia, tampilan modern, bisa diinstal di HP dan dimainkan **offline**.

Tanpa framework dan tanpa build: cukup buka `index.html` lewat web server.

## ⭐ Unggulan: Tebak Kata

Tebak kata huruf demi huruf. Setiap tebakan salah memunculkan **potongan tubuh** (kepala → badan → tangan → kaki). Enam kali salah, orangnya tergantung!

- **1.260+ kata** dalam **24 kategori**: Hewan, Buah, Sayuran, Makanan Nusantara, Minuman, Negara, Kota Indonesia, Profesi, Benda di Rumah, Alat Sekolah, Olahraga, Alat Musik, Anggota Tubuh, Alam, Cuaca & Langit, Transportasi, Pakaian, Warna, Bunga & Tumbuhan, Antariksa, Teknologi, Perasaan & Sifat, Tempat, Budaya Indonesia, Tokoh & Dongeng
- Pilih kategori atau 🎲 Acak, tombol 💡 Petunjuk, streak 🔥, dan kata tidak gampang berulang

Daftar kata ada di [`js/data/words.js`](js/data/words.js). Untuk menambah kata, tinggal tambahkan ke array kategorinya.

## 🎮 Daftar Game

| Kategori | Game |
|---|---|
| 🔤 Kata | Tebak Kata (hangman), Acak Kata, Kata 5 Huruf, Cari Kata, Tebak Emoji, Kuis Pintar, Tebak Bendera |
| 🧩 Logika | Sudoku, Puzzle Geser, Lampu Padam, Sapu Ranjau, Nonogram, Matahari & Bulan (Biner), Ratu Catur, Menara Hanoi, Urutkan Bola, Banjir Warna, Solitaire Pasak, Dorong Peti (Sokoban, 10 level), Tebak Kode |
| 🔢 Angka | 2048, Tebak Angka, Matematika Kilat, Pola Angka, Kotak Ajaib |
| 🧠 Memori | Memori Kartu, Ingat Urutan, Ingat Angka, Warna Kata, Cari Warna Beda |
| ♟️ Strategi | Tic Tac Toe, Empat Sebaris, Reversi (melawan komputer, 3 tingkat kesulitan) |

Fitur umum: tingkat kesulitan, rekor terbaik & jumlah menang tersimpan di perangkat, efek suara (bisa dimatikan), confetti, petunjuk cara main di setiap game, kontrol sentuh/swipe & keyboard.

## ▶️ Menjalankan

```bash
python3 -m http.server 8000
# buka http://localhost:8000
```

Atau aktifkan **GitHub Pages** (Settings → Pages → branch ini, folder root) supaya bisa dibuka dari HP. Di Chrome Android, pilih menu ⋮ → *Tambahkan ke layar utama* agar terpasang seperti aplikasi.

## 📁 Struktur

```
index.html              halaman utama
css/style.css           tema & tampilan
js/app.js               inti: router, modal, suara, confetti, API game
js/data/words.js        bank kata
js/data/quiz.js         soal kuis, teka-teki emoji, bendera
js/games/*.js           game per kategori (word, logic, number, memory, strategy)
sw.js, manifest.webmanifest, assets/   PWA (offline & instal)
```
