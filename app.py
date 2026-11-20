import html
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
 
import streamlit as st
from web3 import Web3
 
# =====================================================================
# 1. KONFIGURASI
# =====================================================================
 
RPC_URL = "http://127.0.0.1:8545"   # node Hardhat lokal
CHAIN_ID = 31337
ZERO = "0x0000000000000000000000000000000000000000"
 
BASE_DIR = Path(__file__).resolve().parent
FOLDER_PROYEK = [BASE_DIR, BASE_DIR.parent]  # app.py boleh di root proyek atau subfolder
 
# ABI dari hasil compile Hardhat
FILE_ABI = "artifacts/contracts/SertifikasiProduk.sol/SertifikasiProduk.json"
 
# Kemungkinan lokasi file deployment (alamat diambil otomatis dari file pertama yang ada).
# Bisa juga diset lewat environment variable CONTRACT_ADDRESS.
FILE_DEPLOY = [
    "deployments/localhost.json",
    "deployments/hardhat.json",
    "deployed-address.json",
    "deployment.json",
    "ignition/deployments/chain-31337/deployed_addresses.json",
]
 
# Urutan enum pada smart contract
STATUS_BPOM = [
    ("Belum Diverifikasi", "warn"),
    ("Terverifikasi", "ok"),
    ("Ditolak", "err"),
]
STATUS_DISTRIBUSI = ["Belum Dimulai", "Menunggu Distributor", "Menunggu Toko", "Selesai"]
 
# =====================================================================
# 2. TEMA (LIGHT / DARK)
# =====================================================================
 
CSS = """
.stApp{background:var(--bg);color:var(--teks)}
.block-container{padding-top:2.2rem;max-width:1200px}
#MainMenu,footer{visibility:hidden}
[data-testid="stHeader"]{background:transparent}
[data-testid="stHeader"] button{color:var(--teks)}
[data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--garis)}
 
.stApp p,.stApp label,.stApp li,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-baseweb="tab"] p{color:var(--teks)}
.stApp [data-testid="stCaptionContainer"] p{color:var(--redup)}
 
/* input */
.stApp input,.stApp textarea{color:var(--teks)!important;-webkit-text-fill-color:var(--teks)}
.stApp ::placeholder{color:var(--redup)!important;-webkit-text-fill-color:var(--redup)!important}
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],
.stApp [data-baseweb="textarea"],.stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="select"] > div > div,.stApp [data-baseweb="select"] input,
.stApp input[type="text"],.stApp input[type="number"],.stApp input:not([type]),
.stApp textarea{background-color:var(--input)!important}
.stApp [data-baseweb="input"],.stApp [data-baseweb="textarea"],
.stApp [data-baseweb="select"] > div{border-color:var(--garis)!important}
.stApp [data-baseweb="select"] *{color:var(--teks)}
[data-baseweb="popover"] ul,[data-baseweb="popover"] li,[data-baseweb="menu"],
[data-baseweb="calendar"]{background:var(--kartu)!important;color:var(--teks)!important}
[data-baseweb="popover"] li:hover{background:var(--garis)!important}
[data-baseweb="calendar"] *{color:var(--teks)}
 
/* tombol */
.stApp button[data-testid^="stBaseButton-primary"]{
  background:var(--aksen);border:none;color:var(--aksen-teks);font-weight:600}
.stApp button[data-testid^="stBaseButton-primary"] p{color:var(--aksen-teks)}
.stApp button[data-testid^="stBaseButton-secondary"]{
  background:var(--kartu);border:1px solid var(--garis);color:var(--teks)}
.stApp button[data-testid^="stBaseButton-secondary"] p{color:var(--teks)}
 
/* form, tab, expander */
[data-testid="stForm"],[data-testid="stExpander"]{
  background:var(--kartu);border:1px solid var(--garis);border-radius:12px}
[data-baseweb="tab-highlight"]{background:var(--aksen)!important}
[data-baseweb="tab-border"]{background:var(--garis)!important}
 
/* komponen kustom */
.brand{font-size:1.2rem;font-weight:700;color:var(--aksen)}
.brand-sub{color:var(--redup);font-size:.8rem;margin-bottom:1rem}
.judul{font-size:1.7rem;font-weight:700;margin:0}
.sub{color:var(--redup);margin:.15rem 0 1.3rem}
.kartu{background:var(--kartu);border:1px solid var(--garis);border-radius:12px;
  padding:1rem 1.2rem;margin-bottom:.9rem}
.kartu-judul{font-weight:600;margin-bottom:.7rem}
.angka-label{color:var(--redup);font-size:.78rem;text-transform:uppercase;letter-spacing:.05em}
.angka-nilai{font-size:2.1rem;font-weight:700;line-height:1.2;margin-top:.2rem}
.kv{display:grid;grid-template-columns:minmax(130px,30%) 1fr;gap:.55rem 1rem;font-size:.92rem}
.kv-k{color:var(--redup)}
.kv-v{word-break:break-all}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85rem}
.badge{display:inline-block;padding:.12rem .65rem;border-radius:999px;font-size:.78rem;font-weight:600;
  white-space:nowrap}
.badge.ok{color:var(--ok);background:color-mix(in srgb,var(--ok) 15%,transparent)}
.badge.err{color:var(--err);background:color-mix(in srgb,var(--err) 15%,transparent)}
.badge.warn{color:var(--warn);background:color-mix(in srgb,var(--warn) 15%,transparent)}
.badge.info{color:var(--aksen);background:color-mix(in srgb,var(--aksen) 15%,transparent)}
.badge.muted{color:var(--redup);background:color-mix(in srgb,var(--redup) 15%,transparent)}
.notif{border-radius:10px;padding:.75rem 1rem;margin-bottom:.9rem;font-size:.93rem;
  border:1px solid var(--garis);border-left-width:4px}
.notif.ok{border-left-color:var(--ok)}
.notif.err{border-left-color:var(--err)}
.notif.warn{border-left-color:var(--warn)}
.notif.info{border-left-color:var(--aksen)}
.tbl-wrap{overflow-x:auto;border:1px solid var(--garis);border-radius:12px;
  background:var(--kartu);margin-bottom:.6rem}
table.tbl{width:100%;border-collapse:collapse;font-size:.92rem}
table.tbl th{text-align:left;padding:.7rem 1rem;color:var(--redup);font-size:.74rem;
  text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--garis)}
table.tbl td{padding:.7rem 1rem;border-bottom:1px solid var(--garis)}
table.tbl tr:last-child td{border-bottom:none}
"""
 
 
def pasang_tema(gelap):
    """Suntikkan CSS sesuai mode terang / gelap."""
    if gelap:
        warna = dict(bg="#0B1220", panel="#0F1A2E", kartu="#16213A", garis="#27344F",
                     teks="#E6EDF7", redup="#93A1B8", aksen="#2DD4BF", aksen_teks="#04201C",
                     input="#0F172A", ok="#4ADE80", err="#F87171", warn="#FBBF24")
    else:
        warna = dict(bg="#F4F7F9", panel="#FFFFFF", kartu="#FFFFFF", garis="#DDE5EA",
                     teks="#14212B", redup="#5B6B78", aksen="#0F766E", aksen_teks="#FFFFFF",
                     input="#FFFFFF", ok="#15803D", err="#B91C1C", warn="#B45309")
    variabel = ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in warna.items())
    st.markdown(f"<style>:root{{{variabel}}}{CSS}</style>", unsafe_allow_html=True)
 
 
# =====================================================================
# 3. KOMPONEN TAMPILAN
# =====================================================================
 
class Html(str):
    """Penanda bahwa teks sudah berupa HTML aman (tidak di-escape lagi)."""
 
 
def e(teks):
    return html.escape(str(teks))
 
 
def badge(teks, jenis="muted"):
    return Html(f'<span class="badge {jenis}">{e(teks)}</span>')
 
 
def mono(teks):
    return Html(f'<span class="mono">{e(teks)}</span>')
 
 
def kv(baris):
    isi = "".join(
        f'<div class="kv-k">{e(k)}</div><div class="kv-v">{v if isinstance(v, Html) else e(v)}</div>'
        for k, v in baris
    )
    return f'<div class="kv">{isi}</div>'
 
 
def kartu(judul_kartu, baris):
    st.markdown(
        f'<div class="kartu"><div class="kartu-judul">{e(judul_kartu)}</div>{kv(baris)}</div>',
        unsafe_allow_html=True,
    )
 
 
def kartu_angka(kolom, label, nilai, warna="var(--aksen)"):
    kolom.markdown(
        f'<div class="kartu" style="border-left:4px solid {warna}">'
        f'<div class="angka-label">{e(label)}</div><div class="angka-nilai">{e(nilai)}</div></div>',
        unsafe_allow_html=True,
    )
 
 
def notif(jenis, teks):
    st.markdown(f'<div class="notif {jenis}">{e(teks)}</div>', unsafe_allow_html=True)
 
 
def tabel(header, baris):
    kepala = "".join(f"<th>{e(h)}</th>" for h in header)
    isi = "".join(
        "<tr>" + "".join(f"<td>{v if isinstance(v, Html) else e(v)}</td>" for v in b) + "</tr>"
        for b in baris
    )
    st.markdown(
        f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{kepala}</tr></thead>'
        f"<tbody>{isi}</tbody></table></div>",
        unsafe_allow_html=True,
    )
 
 
def judul(teks, sub=""):
    """Judul halaman + tampilkan hasil transaksi terakhir (jika ada)."""
    st.markdown(f'<div class="judul">{e(teks)}</div><div class="sub">{e(sub)}</div>', unsafe_allow_html=True)
    hasil = st.session_state.pop("hasil_tx", None)
    if hasil:
        notif("ok", hasil["pesan"])
        kartu("Detail Transaksi", [
            ("Status", badge("Berhasil", "ok")),
            ("Transaction Hash", mono(hasil["hash"])),
            ("Nomor Blok", hasil["blok"]),
            ("Gas Terpakai", hasil["gas"]),
        ])
 
 
# =====================================================================
# 4. KONEKSI BLOCKCHAIN
# =====================================================================
 
ALAMAT_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
 
 
ABAIKAN = {"node_modules", ".venv", "venv", ".git", "build-info", "cache", "__pycache__"}
 
 
def cari_file(relatif):
    # 1) coba path standar
    for folder in FOLDER_PROYEK:
        path = folder / relatif
        if path.exists():
            return path
    # 2) cadangan: cari berdasarkan nama file di dalam folder proyek
    nama = Path(relatif).name
    for folder in FOLDER_PROYEK:
        for akar, subfolder, berkas in os.walk(folder):
            subfolder[:] = [s for s in subfolder if s not in ABAIKAN]
            if nama in berkas:
                path = Path(akar) / nama
                if "artifacts" in relatif and "artifacts" not in path.parts:
                    continue
                return path
    return None
 
 
def cari_alamat_di_json(data):
    """Cari alamat contract di dalam JSON (format deployment bisa berbeda-beda)."""
    ditemukan = []
 
    def telusuri(node, kunci=""):
        if isinstance(node, dict):
            for k, v in node.items():
                telusuri(v, str(k))
        elif isinstance(node, list):
            for v in node:
                telusuri(v, kunci)
        elif isinstance(node, str) and ALAMAT_RE.match(node):
            ditemukan.append((kunci, node))
 
    telusuri(data)
    for kunci, alamat in ditemukan:
        if "sertifikasi" in kunci.lower():
            return alamat
    return ditemukan[0][1] if ditemukan else None
 
 
def ambil_alamat_contract():
    dari_env = os.environ.get("CONTRACT_ADDRESS")
    if dari_env:
        return dari_env
    for relatif in FILE_DEPLOY:
        path = cari_file(relatif)
        if path:
            try:
                alamat = cari_alamat_di_json(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
            if alamat:
                return alamat
    raise FileNotFoundError(
        "Alamat contract tidak ditemukan. Deploy contract dulu atau isi FILE_DEPLOY "
        "di bagian konfigurasi app.py."
    )
 
 
def sambung():
    """Hubungkan ke Hardhat dan siapkan objek contract."""
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        raise ConnectionError(f"Tidak bisa terhubung ke {RPC_URL}. Jalankan: npx hardhat node")
    if w3.eth.chain_id != CHAIN_ID:
        raise ConnectionError(f"Chain ID {w3.eth.chain_id} tidak sesuai (seharusnya {CHAIN_ID}).")
 
    path_abi = cari_file(FILE_ABI)
    if not path_abi:
        raise FileNotFoundError(f"File ABI tidak ditemukan ({FILE_ABI}). Jalankan: npx hardhat compile")
    abi = json.loads(path_abi.read_text(encoding="utf-8"))["abi"]
 
    nama_fungsi = {x.get("name") for x in abi}
    if "semuaBatchId" not in nama_fungsi:
        raise ValueError(
            "ABI belum memiliki fungsi semuaBatchId(). Tambahkan getter pada smart contract, "
            "lalu compile dan deploy ulang."
        )
 
    alamat = Web3.to_checksum_address(ambil_alamat_contract())
    if w3.eth.get_code(alamat) == b"":
        raise ValueError(f"Tidak ada contract di alamat {alamat}. Deploy ulang contract ke node Hardhat.")
    return w3, w3.eth.contract(address=alamat, abi=abi)
 
 
# =====================================================================
# 5. FUNGSI BANTU SMART CONTRACT
# =====================================================================
 
def cek_role(c, akun):
    if akun == c.functions.admin().call():
        return "Admin"
    if akun == c.functions.bpom().call():
        return "BPOM"
    if c.functions.produsen(akun).call():
        return "Produsen"
    return "Pengguna"
 
 
def ambil_semua_produk(c):
    """Baca seluruh produk dari smart contract."""
    hasil = []
    for batch in c.functions.semuaBatchId().call():
        p = c.functions.lihatProduk(batch).call()
        p = list(p.values()) if isinstance(p, dict) else list(p)
        hasil.append({
            "batch": batch, "nama": p[0], "nomor_bpom": p[1], "produksi": p[2],
            "kadaluarsa": p[3], "produsen": p[4], "status": int(p[5]), "distribusi": int(p[6]),
        })
    return hasil
 
 
def badge_status(kode):
    teks, jenis = STATUS_BPOM[kode]
    return badge(teks, jenis)
 
 
def pesan_error(err):
    teks = str(err)
    cocok = re.search(r"reverted[^A-Za-z0-9]*(?:with reason string[^A-Za-z0-9]*)?([^'\"\)\],]+)", teks)
    return cocok.group(1).strip() if cocok else teks[:300]
 
 
def kirim_transaksi(w3, fungsi, akun, pesan_sukses):
    """Kirim transaksi memakai akun Hardhat (sudah unlocked di node), lalu tampilkan hasilnya."""
    try:
        with st.spinner("Transaksi pending, menunggu konfirmasi blok..."):
            tx_hash = fungsi.transact({"from": akun})
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    except Exception as err:  # noqa: BLE001
        notif("err", f"Transaksi gagal: {pesan_error(err)}")
        return
    if receipt.status != 1:
        notif("err", "Transaksi gagal (reverted oleh smart contract).")
        return
    st.session_state["hasil_tx"] = {
        "pesan": pesan_sukses, "hash": w3.to_hex(tx_hash),
        "blok": receipt.blockNumber, "gas": receipt.gasUsed,
    }
    st.rerun()  # muat ulang agar semua data terbaru
 
 
def tampil_detail(c, p):
    """Kartu detail produk (dipakai di beberapa halaman)."""
    token_id = c.functions.tokenBatch(p["batch"]).call()
    if token_id > 0:
        nft = [("Sertifikat NFT", badge("Diterbitkan", "ok")),
               ("Token ID", f"#{token_id}"),
               ("Pemilik NFT", mono(c.functions.ownerOf(token_id).call()))]
    else:
        nft = [("Sertifikat NFT", badge("Belum diterbitkan", "muted"))]
    kartu(f"Detail Produk: {p['batch']}", [
        ("Batch ID", p["batch"]),
        ("Nama Produk", p["nama"]),
        ("Nomor BPOM", p["nomor_bpom"] or "-"),
        ("Produsen", mono(p["produsen"])),
        ("Tanggal Produksi", p["produksi"]),
        ("Tanggal Kedaluwarsa", p["kadaluarsa"]),
        ("Status BPOM", badge_status(p["status"])),
        ("Status Distribusi", STATUS_DISTRIBUSI[p["distribusi"]]),
    ] + nft)
 
 
def akses_ditolak(role_dibutuhkan):
    notif("err", f"Akses ditolak. Halaman ini hanya dapat digunakan oleh akun {role_dibutuhkan}.")
 
 
# =====================================================================
# 6. HALAMAN
# =====================================================================
 
def halaman_dashboard(w3, c, akun, role):
    judul("Dashboard", "Ringkasan sertifikasi produk, seluruh data dibaca dari smart contract")
    data = ambil_semua_produk(c)
    kolom = st.columns(4)
    kartu_angka(kolom[0], "Total Produk", len(data))
    kartu_angka(kolom[1], "Terverifikasi", sum(d["status"] == 1 for d in data), "var(--ok)")
    kartu_angka(kolom[2], "Ditolak", sum(d["status"] == 2 for d in data), "var(--err)")
    kartu_angka(kolom[3], "Belum Diverifikasi", sum(d["status"] == 0 for d in data), "var(--warn)")
 
    kiri, kanan = st.columns(2)
    with kiri:
        kartu("Koneksi Blockchain", [
            ("Status", badge("Terhubung", "ok")),
            ("Jaringan", f"Hardhat Local (Chain ID {w3.eth.chain_id})"),
            ("RPC", mono(RPC_URL)),
            ("Blok Terakhir", w3.eth.block_number),
        ])
    with kanan:
        kartu("Smart Contract", [
            ("Nama", c.functions.name().call()),
            ("Alamat", mono(c.address)),
            ("Admin", mono(c.functions.admin().call())),
            ("BPOM", mono(c.functions.bpom().call())),
        ])
 
 
def halaman_daftar(w3, c, akun, role):
    judul("Daftar Produk", "Produk yang tercatat di blockchain")
    data = ambil_semua_produk(c)
    if not data:
        notif("info", "Belum ada produk terdaftar.")
        return
 
    cari = st.text_input("Cari produk", placeholder="Ketik Batch ID atau nama produk").strip().lower()
    hasil = [d for d in data if cari in d["batch"].lower() or cari in d["nama"].lower()]
 
    if not hasil:
        notif("warn", "Produk tidak ditemukan.")
        return
    tabel(
        ["Batch ID", "Nama Produk", "Nomor BPOM", "Tgl Produksi", "Tgl Kedaluwarsa", "Status"],
        [[d["batch"], d["nama"], d["nomor_bpom"] or "-", d["produksi"], d["kadaluarsa"],
          badge_status(d["status"])] for d in hasil],
    )
    st.caption(f"Menampilkan {len(hasil)} dari {len(data)} produk")
 
    pilih = st.selectbox("Pilih produk untuk melihat detail", [d["batch"] for d in hasil])
    tampil_detail(c, next(d for d in hasil if d["batch"] == pilih))
 
 
def halaman_tambah(w3, c, akun, role):
    judul("Tambah Produk", "Pendaftaran batch produk baru oleh Produsen")
    if role != "Produsen":
        akses_ditolak("Produsen")
        return
 
    with st.form("form_tambah"):
        batch = st.text_input("Batch ID", placeholder="Contoh: BATCH-001")
        nama = st.text_input("Nama Produk", placeholder="Contoh: Sirup Batuk Herbal")
        k1, k2 = st.columns(2)
        produksi = k1.date_input("Tanggal Produksi", value=date.today())
        kadaluarsa = k2.date_input("Tanggal Kedaluwarsa", value=date.today() + timedelta(days=365))
        kirim = st.form_submit_button("Daftarkan Produk", type="primary")
 
    if not kirim:
        return
 
    batch, nama = batch.strip(), nama.strip()
    if not batch or not nama:
        notif("err", "Batch ID dan nama produk wajib diisi.")
    elif len(batch) > 50 or len(nama) > 100:
        notif("err", "Batch ID maksimal 50 karakter dan nama produk maksimal 100 karakter.")
    elif kadaluarsa <= produksi:
        notif("err", "Tanggal kedaluwarsa harus setelah tanggal produksi.")
    elif batch in c.functions.semuaBatchId().call():
        notif("err", f"Batch ID '{batch}' sudah terdaftar.")
    else:
        kirim_transaksi(
            w3,
            c.functions.tambahProduk(batch, nama, produksi.isoformat(), kadaluarsa.isoformat()),
            akun,
            f"Produk '{nama}' (batch {batch}) berhasil didaftarkan.",
        )
 
 
def halaman_verifikasi(w3, c, akun, role):
    judul("Verifikasi BPOM", "Setujui atau tolak produk yang menunggu verifikasi")
    if role != "BPOM":
        akses_ditolak("BPOM")
        return
 
    menunggu = [d for d in ambil_semua_produk(c) if d["status"] == 0]
    if not menunggu:
        notif("info", "Tidak ada produk yang menunggu verifikasi.")
        return
 
    pilih = st.selectbox("Pilih Batch ID", [d["batch"] for d in menunggu])
    tampil_detail(c, next(d for d in menunggu if d["batch"] == pilih))
 
    st.markdown("#### Keputusan Verifikasi")
    nomor = st.text_input("Nomor BPOM", placeholder="Contoh: MD 123456789012 (wajib jika disetujui)").strip()
    lokasi = st.text_input("Lokasi Verifikasi", placeholder="Contoh: Jakarta").strip()
    k1, k2, _ = st.columns([1, 1, 3])
    setuju = k1.button("Setujui", type="primary")
    tolak = k2.button("Tolak")
 
    if not (setuju or tolak):
        return
    if not lokasi:
        notif("err", "Lokasi verifikasi wajib diisi.")
    elif setuju and not nomor:
        notif("err", "Nomor BPOM wajib diisi untuk menyetujui produk.")
    elif setuju:
        kirim_transaksi(
            w3, c.functions.verifikasiBPOM(pilih, True, nomor, lokasi), akun,
            f"Batch {pilih} disetujui. Sertifikat NFT telah diterbitkan untuk produsen.",
        )
    else:
        kirim_transaksi(
            w3, c.functions.verifikasiBPOM(pilih, False, "", lokasi), akun,
            f"Batch {pilih} ditolak. Status produk: Ditolak.",
        )
 
 
def halaman_detail(w3, c, akun, role):
    judul("Detail Produk", "Informasi lengkap produk berdasarkan Batch ID")
    data = ambil_semua_produk(c)
    if not data:
        notif("info", "Belum ada produk terdaftar.")
        return
    pilih = st.selectbox("Batch ID", [d["batch"] for d in data])
    st.button("Muat Ulang Data")  # klik tombol = Streamlit membaca ulang dari blockchain
    tampil_detail(c, next(d for d in data if d["batch"] == pilih))
 
 
def halaman_pengaturan(w3, c, akun, role):
    judul("Pengaturan Akun", "Manajemen role oleh Admin")
    if role != "Admin":
        akses_ditolak("Admin")
        return
 
    admin = c.functions.admin().call()
    bpom = c.functions.bpom().call()
    kartu("Role Saat Ini", [
        ("Admin", mono(admin)),
        ("BPOM Terdaftar", mono(bpom) if bpom != ZERO else "Belum diatur"),
    ])
 
    tab_bpom, tab_produsen, tab_cek = st.tabs(["Atur BPOM", "Kelola Produsen", "Cek Role"])
 
    with tab_bpom:
        with st.form("form_bpom"):
            alamat = st.text_input("Alamat akun BPOM", placeholder="0x...").strip()
            kirim = st.form_submit_button("Simpan Akun BPOM", type="primary")
        if kirim:
            if not Web3.is_address(alamat):
                notif("err", "Format alamat wallet tidak valid.")
            elif Web3.to_checksum_address(alamat) == admin:
                notif("err", "Akun Admin tidak boleh dijadikan BPOM.")
            else:
                alamat = Web3.to_checksum_address(alamat)
                kirim_transaksi(w3, c.functions.setBPOM(alamat), akun, f"Akun BPOM diatur ke {alamat}.")
 
    with tab_produsen:
        with st.form("form_produsen"):
            alamat = st.text_input("Alamat akun Produsen", placeholder="0x...").strip()
            aksi = st.radio("Aksi", ["Aktifkan", "Nonaktifkan"], horizontal=True)
            kirim = st.form_submit_button("Simpan Role Produsen", type="primary")
        if kirim:
            if not Web3.is_address(alamat):
                notif("err", "Format alamat wallet tidak valid.")
            elif Web3.to_checksum_address(alamat) == admin:
                notif("err", "Akun Admin tidak boleh dijadikan Produsen.")
            else:
                alamat = Web3.to_checksum_address(alamat)
                aktif = aksi == "Aktifkan"
                kirim_transaksi(
                    w3, c.functions.setProdusen(alamat, aktif), akun,
                    f"Role Produsen untuk {alamat} berhasil {'diaktifkan' if aktif else 'dinonaktifkan'}.",
                )
 
    with tab_cek:
        alamat = st.text_input("Alamat yang ingin dicek", placeholder="0x...", key="cek_alamat").strip()
        if alamat:
            if not Web3.is_address(alamat):
                notif("err", "Format alamat wallet tidak valid.")
            else:
                alamat = Web3.to_checksum_address(alamat)
                kartu("Status Role", [
                    ("Alamat", mono(alamat)),
                    ("Admin", badge("Ya", "ok") if alamat == admin else badge("Bukan", "muted")),
                    ("BPOM", badge("Ya", "ok") if alamat == bpom else badge("Bukan", "muted")),
                    ("Produsen", badge("Aktif", "ok") if c.functions.produsen(alamat).call()
                     else badge("Tidak aktif", "muted")),
                ])
 
    with st.expander("Daftar akun Hardhat (untuk menyalin alamat)"):
        akun_semua = w3.eth.accounts
        tabel(["#", "Alamat", "Role"],
              [[i, mono(a), cek_role(c, a)] for i, a in enumerate(akun_semua)])
 
 
HALAMAN = {
    "Dashboard": halaman_dashboard,
    "Daftar Produk": halaman_daftar,
    "Tambah Produk": halaman_tambah,
    "Verifikasi BPOM": halaman_verifikasi,
    "Detail Produk": halaman_detail,
    "Pengaturan Akun": halaman_pengaturan,
}
 
# =====================================================================
# 7. PROGRAM UTAMA
# =====================================================================
 
 
def main():
    st.set_page_config(page_title="Verifikasi BPOM", page_icon="✅", layout="wide")
 
    with st.sidebar:
        st.markdown(
            '<div class="brand">Verifikasi BPOM</div>'
            '<div class="brand-sub">Sertifikasi produk berbasis blockchain</div>',
            unsafe_allow_html=True,
        )
        menu = st.radio("Menu", list(HALAMAN), label_visibility="collapsed")
        gelap = st.toggle("Mode Gelap", value=False)
 
    pasang_tema(gelap)
 
    try:
        w3, c = sambung()
    except Exception as err:  # noqa: BLE001
        judul("Verifikasi BPOM")
        notif("err", f"Koneksi blockchain gagal: {err}")
        st.stop()
 
    akun_list = w3.eth.accounts
    if not akun_list:
        judul("Verifikasi BPOM")
        notif("err", "Node tidak memiliki akun. Pastikan menjalankan: npx hardhat node")
        st.stop()
 
    with st.sidebar:
        st.divider()
        akun = st.selectbox(
            "Akun aktif",
            akun_list,
            format_func=lambda a: f"Akun #{akun_list.index(a)}  {a[:6]}...{a[-4:]}",
        )
        role = cek_role(c, akun)
        jenis_role = {"Admin": "info", "BPOM": "info", "Produsen": "ok"}.get(role, "muted")
        saldo = float(w3.from_wei(w3.eth.get_balance(akun), "ether"))
        kartu("Wallet", [
            ("Alamat", mono(f"{akun[:8]}...{akun[-6:]}")),
            ("Saldo", f"{saldo:,.4f} ETH"),
            ("Role", badge(role, jenis_role)),
            ("Jaringan", badge("Terhubung", "ok")),
        ])
        st.caption("Transaksi ditandatangani oleh akun Hardhat lokal melalui Web3.py.")
 
    HALAMAN[menu](w3, c, akun, role)
 
 
main()
