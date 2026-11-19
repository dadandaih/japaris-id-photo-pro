import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import threading
import queue
from PIL import Image, ImageTk, ImageOps
from pathlib import Path

APP_TITLE = 'JAPARIS ID PHOTO PRO — MVP'
MIN_LONG_EDGE = 2000

class JaparisApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry('1100x720')
        self.root.minsize(900, 600)
        self.root.configure(bg='#171a21')
        self.original = None
        self.working = None
        self.preview_ref = None
        self.bg_color = '#ffffff'
        self.cutout_ready = False
        self.bg_queue = queue.Queue()
        self.bg_busy = False
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self.root, bg='#222733', padx=18, pady=14)
        top.pack(fill='x')
        tk.Label(top, text='JAPARIS ID PHOTO PRO', fg='white', bg='#222733', font=('Segoe UI', 18, 'bold')).pack(side='left')
        tk.Label(top, text='MVP • Local photo workflow', fg='#aeb8c8', bg='#222733', font=('Segoe UI', 9)).pack(side='right')

        body = tk.Frame(self.root, bg='#171a21', padx=14, pady=14)
        body.pack(fill='both', expand=True)
        side = tk.Frame(body, bg='#222733', width=250, padx=14, pady=14)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        tk.Label(side, text='TOOLS', fg='#9eabc0', bg='#222733', font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(0, 10))
        self._btn(side, 'Buka Foto', self.open_photo)
        self.bg_button = self._btn(side, 'AI Hapus Background', self.remove_background)
        self._btn(side, 'Pilih Warna Background', self.choose_bg)
        self._btn(side, 'Terapkan Background Solid', self.apply_background)
        self._btn(side, 'Smart Resolution Check', self.smart_resolution)
        self._btn(side, 'Simpan Hasil', self.save_result, accent=True)
        tk.Label(side, text='ATURAN RESOLUSI', fg='#9eabc0', bg='#222733', font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(22, 7))
        tk.Label(side, text='Sisi terpanjang < 2000 px: diperbesar ke 2000 px.\n\nSisi terpanjang ≥ 2000 px: dipertahankan.\n\nRasio aspek selalu dijaga.', justify='left', wraplength=215, fg='#d7deea', bg='#222733', font=('Segoe UI', 9)).pack(anchor='w')
        self.status = tk.StringVar(value='Buka foto untuk memulai.')
        tk.Label(side, textvariable=self.status, fg='#70d6a5', bg='#222733', wraplength=215, justify='left', font=('Segoe UI', 9)).pack(side='bottom', anchor='w', pady=(12, 0))

        right = tk.Frame(body, bg='#171a21')
        right.pack(side='left', fill='both', expand=True, padx=(14, 0))
        self.canvas = tk.Label(right, text='Preview foto akan tampil di sini', fg='#8994a7', bg='#101319', font=('Segoe UI', 14), compound='center')
        self.canvas.pack(fill='both', expand=True)
        self.info = tk.StringVar(value='Belum ada foto')
        tk.Label(right, textvariable=self.info, fg='#b9c3d2', bg='#171a21', anchor='w', font=('Segoe UI', 9)).pack(fill='x', pady=(10, 0))
        tk.Label(self.root, text='Catatan: versi MVP ini memakai resize Lanczos untuk memenuhi minimum pixel, bukan AI super-resolution. AI upscaling dan penyempurnaan mask akan ditambahkan pada tahap berikutnya.', fg='#d6b36a', bg='#171a21', font=('Segoe UI', 9), pady=8).pack(fill='x')

    def _btn(self, parent, text, command, accent=False):
        bg = '#236b55' if accent else '#303949'
        button = tk.Button(parent, text=text, command=command, bg=bg, fg='white', activebackground='#3b4960', activeforeground='white', relief='flat', bd=0, padx=10, pady=10, anchor='w', font=('Segoe UI', 10, 'bold' if accent else 'normal'))
        button.pack(fill='x', pady=4)
        return button

    def open_photo(self):
        if self.bg_busy:
            messagebox.showinfo('Sedang memproses', 'Tunggu proses AI selesai sebelum membuka foto lain.')
            return
        path = filedialog.askopenfilename(filetypes=[('Image files', '*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff')])
        if not path: return
        try:
            self.original = ImageOps.exif_transpose(Image.open(path)).convert('RGBA')
            self.working = self.original.copy()
            self.cutout_ready = False
            self._refresh()
            self.status.set('Foto dimuat. File sumber tidak diubah.')
        except Exception as e:
            messagebox.showerror('Gagal membuka foto', str(e))

    def _refresh(self):
        if self.working is None: return
        preview = self.working.copy()
        preview.thumbnail((760, 590), Image.Resampling.LANCZOS)
        self.preview_ref = ImageTk.PhotoImage(preview)
        self.canvas.configure(image=self.preview_ref, text='')
        w, h = self.working.size
        ow, oh = self.original.size
        self.info.set(f'Foto sumber: {ow} × {oh} px    |    Preview kerja: {w} × {h} px    |    Background: {self.bg_color}')

    def remove_background(self):
        if self.working is None:
            messagebox.showinfo('Info', 'Buka foto terlebih dahulu.')
            return
        if self.bg_busy:
            return

        # Jalankan model AI di thread terpisah agar jendela tidak Not Responding.
        # Pada pemakaian pertama, rembg dapat mengunduh model U2NET (sekitar 170 MB).
        image_for_worker = self.working.copy()
        self.bg_busy = True
        self.bg_button.configure(state='disabled', text='Memproses AI...')
        self.status.set('AI sedang menyiapkan model dan memotong background. Pemakaian pertama dapat mengunduh model; jendela tetap bisa digunakan.')

        def worker():
            try:
                from rembg import remove, new_session
                session = new_session('u2net')
                result = remove(image_for_worker, session=session).convert('RGBA')
                self.bg_queue.put(('success', result))
            except Exception as exc:
                self.bg_queue.put(('error', str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(200, self._check_background_result)

    def _check_background_result(self):
        try:
            kind, payload = self.bg_queue.get_nowait()
        except queue.Empty:
            if self.bg_busy:
                self.root.after(200, self._check_background_result)
            return

        self.bg_busy = False
        self.bg_button.configure(state='normal', text='AI Hapus Background')
        if kind == 'success':
            self.working = payload
            self.cutout_ready = True
            self._refresh()
            self.status.set('Background berhasil dipisahkan. Periksa tepi rambut dan bahu.')
            messagebox.showinfo('Selesai', 'Background berhasil dipisahkan. Periksa hasil rambut dan tepi bahu.')
        else:
            self.status.set('AI background removal gagal. Foto asli tetap aman.')
            messagebox.showerror('AI cutout gagal', payload + '\n\nJika ini pemakaian pertama, pastikan internet aktif agar model U2NET dapat diunduh. Setelah model tersimpan, pemrosesan berikutnya dapat dilakukan lokal.')

    def choose_bg(self):
        color = colorchooser.askcolor(color=self.bg_color, title='Pilih warna background')
        if color and color[1]:
            self.bg_color = color[1]
            self.status.set(f'Warna dipilih: {self.bg_color}')
            self._refresh()

    def apply_background(self):
        if self.working is None:
            messagebox.showinfo('Info', 'Buka foto terlebih dahulu.'); return
        if not self.cutout_ready and self.working.getchannel('A').getextrema() == (255, 255):
            messagebox.showwarning('Belum ada mask', 'Jalankan AI Hapus Background terlebih dahulu agar warna solid tidak menutupi foto.')
            return
        bg = Image.new('RGBA', self.working.size, self.bg_color)
        bg.alpha_composite(self.working)
        self.working = bg
        self._refresh()
        self.status.set('Background solid diterapkan.')

    def smart_resolution(self):
        if self.working is None:
            messagebox.showinfo('Info', 'Buka foto terlebih dahulu.'); return
        w, h = self.working.size
        long_edge = max(w, h)
        if long_edge >= MIN_LONG_EDGE:
            self.status.set(f'Resolusi dipertahankan: {w} × {h} px (sudah ≥ 2000 px).')
            messagebox.showinfo('Smart Resolution', f'Foto tidak diubah.\nResolusi: {w} × {h} px')
            return
        scale = MIN_LONG_EDGE / long_edge
        new_size = (round(w * scale), round(h * scale))
        self.working = self.working.resize(new_size, Image.Resampling.LANCZOS)
        self._refresh()
        self.status.set(f'Diperbesar secara proporsional menjadi {new_size[0]} × {new_size[1]} px.')
        messagebox.showinfo('Smart Resolution', f'Foto diperbesar dengan Lanczos (bukan AI super-resolution).\n{w} × {h} → {new_size[0]} × {new_size[1]} px')

    def save_result(self):
        if self.working is None:
            messagebox.showinfo('Info', 'Belum ada foto untuk disimpan.'); return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg *.jpeg')], initialfile='japaris_hasil.png')
        if not path: return
        try:
            out = self.working
            if Path(path).suffix.lower() in ('.jpg', '.jpeg'):
                if out.mode == 'RGBA':
                    bg = Image.new('RGB', out.size, 'white'); bg.paste(out, mask=out.getchannel('A')); out = bg
                else: out = out.convert('RGB')
                out.save(path, quality=95, subsampling=0, dpi=(300, 300))
            else:
                out.save(path, dpi=(300, 300))
            self.status.set(f'Hasil disimpan: {path}')
            messagebox.showinfo('Berhasil', 'Hasil foto berhasil disimpan. File sumber tetap aman.')
        except Exception as e:
            messagebox.showerror('Gagal menyimpan', str(e))

if __name__ == '__main__':
    root = tk.Tk()
    app = JaparisApp(root)
    root.mainloop()
