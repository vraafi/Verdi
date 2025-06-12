# Instruksi Upload ke GitHub dan Deployment

## Langkah 1: Membuat Repository di GitHub

1. **Login ke GitHub**
   - Buka https://github.com
   - Login dengan akun GitHub Anda (atau buat akun baru jika belum punya)

2. **Buat Repository Baru**
   - Klik tombol "+" di pojok kanan atas
   - Pilih "New repository"
   - Nama repository: `portfolio-website` (atau nama lain yang Anda inginkan)
   - Deskripsi: "Website portofolio pribadi dengan desain modern"
   - Pilih "Public" (agar bisa menggunakan GitHub Pages gratis)
   - **JANGAN** centang "Add a README file" (karena kita sudah punya)
   - Klik "Create repository"

## Langkah 2: Upload Website ke GitHub

Setelah repository dibuat, GitHub akan menampilkan halaman dengan instruksi. Ikuti langkah berikut:

1. **Copy URL Repository**
   - Copy URL yang ditampilkan (contoh: `https://github.com/username/portfolio-website.git`)

2. **Jalankan Perintah Git**
   Buka terminal/command prompt di folder `portfolio-website` dan jalankan:
   
   ```bash
   git remote add origin https://github.com/USERNAME/REPOSITORY-NAME.git
   git branch -M main
   git push -u origin main
   ```
   
   **Ganti `USERNAME` dan `REPOSITORY-NAME` dengan informasi repository Anda!**

3. **Masukkan Kredensial GitHub**
   - Jika diminta username dan password, masukkan kredensial GitHub Anda
   - Untuk password, gunakan Personal Access Token (bukan password biasa)

## Langkah 3: Mengaktifkan GitHub Pages

1. **Buka Settings Repository**
   - Di halaman repository GitHub, klik tab "Settings"
   - Scroll ke bawah hingga menemukan section "Pages"

2. **Konfigurasi GitHub Pages**
   - Di section "Source", pilih "Deploy from a branch"
   - Branch: pilih "main" (atau "master")
   - Folder: pilih "/ (root)"
   - Klik "Save"

3. **Tunggu Deployment**
   - GitHub akan memproses deployment (biasanya 1-5 menit)
   - Setelah selesai, akan muncul URL website Anda
   - URL biasanya: `https://username.github.io/repository-name/`

## Langkah 4: Akses Website Anda

Setelah deployment selesai, website Anda akan dapat diakses melalui URL GitHub Pages. Contoh:
- `https://username.github.io/portfolio-website/`

## Tips Tambahan

### Mengupdate Website
Jika Anda ingin mengubah website di masa depan:
1. Edit file di komputer lokal
2. Jalankan perintah:
   ```bash
   git add .
   git commit -m "Update website"
   git push
   ```
3. GitHub Pages akan otomatis update dalam beberapa menit

### Custom Domain (Opsional)
Jika Anda memiliki domain sendiri:
1. Di Settings > Pages, masukkan domain Anda di "Custom domain"
2. Konfigurasi DNS domain Anda untuk mengarah ke GitHub Pages

### Troubleshooting
- **Error 404**: Pastikan file `index.html` ada di root folder
- **Website tidak update**: Tunggu beberapa menit, atau coba hard refresh (Ctrl+F5)
- **Error push**: Pastikan URL repository benar dan Anda punya akses

## Keamanan
- Jangan pernah commit file yang berisi informasi sensitif (password, API keys, dll.)
- Gunakan Personal Access Token untuk autentikasi, bukan password

---

**Selamat! Website portofolio Anda sekarang sudah online dan dapat diakses oleh siapa saja di internet secara gratis!**

