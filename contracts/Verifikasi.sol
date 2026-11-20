
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;
 
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
 
contract SertifikasiProduk is ERC721 {
 
    // =====================================================
    // 1. ROLE DAN AKSES
    // =====================================================
 
    address public admin;
    address public bpom;
 
    mapping(address => bool) public produsen;
    mapping(address => bool) public distributor;
    mapping(address => bool) public toko;
 
    modifier onlyAdmin() {
        require(msg.sender == admin, "Hanya admin");
        _;
    }
 
    modifier onlyBPOM() {
        require(msg.sender == bpom, "Hanya BPOM");
        _;
    }
 
    modifier onlyProdusen() {
        require(produsen[msg.sender], "Bukan produsen");
        _;
    }
 
    modifier onlyDistributor() {
        require(distributor[msg.sender], "Bukan distributor");
        _;
    }
 
    modifier onlyToko() {
        require(toko[msg.sender], "Bukan toko");
        _;
    }
 
    // =====================================================
    // 2. STATUS DAN STRUKTUR DATA
    // =====================================================
 
    enum StatusBPOM {
        BELUM_DIVERIFIKASI,
        TERVERIFIKASI,
        DITOLAK
    }
 
    enum StatusDistribusi {
        BELUM_DIMULAI,
        MENUNGGU_DISTRIBUTOR,
        MENUNGGU_TOKO,
        SELESAI
    }
 
    struct Produk {
        string namaProduk;
        string nomorBPOM;
        string tanggalProduksi;
        string tanggalKadaluarsa;
        address alamatProdusen;
        StatusBPOM statusBPOM;
        StatusDistribusi statusDistribusi;
        bool terdaftar;
    }
 
    struct Riwayat {
        address aktor;
        string peristiwa;
        string lokasi;
        uint256 timestamp;
    }
 
    mapping(string => Produk) private daftarProduk;
    mapping(string => Riwayat[]) private riwayatProduk;
 
    // [TAMBAHAN] Daftar seluruh Batch ID agar produk bisa ditampilkan di UI
    string[] private daftarBatchId;
 
    mapping(string => uint256) public tokenBatch;
    mapping(uint256 => string) private batchToken;
 
    uint256 private nextTokenId = 1;
 
    // =====================================================
    // 3. EVENT
    // =====================================================
 
    event RoleDiatur(
        string role,
        address akun,
        bool aktif
    );
 
    event BPOMDiatur(address akun);
 
    event ProdukDidaftarkan(
        string batchId,
        string namaProduk,
        address produsen
    );
 
    event StatusBPOMDiubah(
        string batchId,
        StatusBPOM status
    );
 
    event SertifikatDiterbitkan(
        string batchId,
        uint256 tokenId,
        address pemilik
    );
 
    event DistribusiDiperbarui(
        string batchId,
        StatusDistribusi status,
        address aktor
    );
 
    event RiwayatDicatat(
        string batchId,
        address aktor,
        string peristiwa,
        string lokasi,
        uint256 timestamp
    );
 
    // =====================================================
    // 4. CONSTRUCTOR
    // ACCOUNT 1 HANYA MENJADI ADMIN
    // =====================================================
 
    constructor() ERC721("Sertifikat Produk", "BPOM") {
        admin = msg.sender;
    }
 
    // =====================================================
    // 5. PENGATURAN ROLE OLEH ADMIN
    // =====================================================
 
    function setBPOM(address akun) external onlyAdmin {
        require(akun != address(0), "Alamat BPOM tidak valid");
        require(akun != admin, "Admin bukan BPOM");
 
        bpom = akun;
 
        emit BPOMDiatur(akun);
    }
 
    function setProdusen(
        address akun,
        bool aktif
    ) external onlyAdmin {
        require(akun != address(0), "Alamat tidak valid");
        require(akun != admin, "Admin bukan produsen");
 
        produsen[akun] = aktif;
 
        emit RoleDiatur("Produsen", akun, aktif);
    }
 
    function setDistributor(
        address akun,
        bool aktif
    ) external onlyAdmin {
        require(akun != address(0), "Alamat tidak valid");
        require(akun != admin, "Admin bukan distributor");
 
        distributor[akun] = aktif;
 
        emit RoleDiatur("Distributor", akun, aktif);
    }
 
    function setToko(
        address akun,
        bool aktif
    ) external onlyAdmin {
        require(akun != address(0), "Alamat tidak valid");
        require(akun != admin, "Admin bukan toko");
 
        toko[akun] = aktif;
 
        emit RoleDiatur("Toko", akun, aktif);
    }
 
    // =====================================================
    // 6. PRODUSEN MENDAFTARKAN PRODUK
    // HANYA AKUN YANG TERDAFTAR SEBAGAI PRODUSEN
    // =====================================================
 
    function tambahProduk(
        string calldata batchId,
        string calldata namaProduk,
        string calldata tanggalProduksi,
        string calldata tanggalKadaluarsa
    ) external onlyProdusen {
        require(bytes(batchId).length > 0, "Batch ID kosong");
        require(bytes(namaProduk).length > 0, "Nama produk kosong");
        require(
            bytes(tanggalProduksi).length > 0,
            "Tanggal produksi kosong"
        );
        require(
            bytes(tanggalKadaluarsa).length > 0,
            "Tanggal kadaluarsa kosong"
        );
        require(
            !daftarProduk[batchId].terdaftar,
            "Batch sudah terdaftar"
        );
 
        daftarProduk[batchId] = Produk({
            namaProduk: namaProduk,
            nomorBPOM: "",
            tanggalProduksi: tanggalProduksi,
            tanggalKadaluarsa: tanggalKadaluarsa,
            alamatProdusen: msg.sender,
            statusBPOM: StatusBPOM.BELUM_DIVERIFIKASI,
            statusDistribusi: StatusDistribusi.BELUM_DIMULAI,
            terdaftar: true
        });
 
        // [TAMBAHAN] Simpan Batch ID ke dalam daftar
        daftarBatchId.push(batchId);
 
        _catatRiwayat(
            batchId,
            "Batch didaftarkan oleh produsen",
            "Pabrik"
        );
 
        emit ProdukDidaftarkan(
            batchId,
            namaProduk,
            msg.sender
        );
    }
 
    // =====================================================
    // 7. BPOM MEMVERIFIKASI ATAU MENOLAK PRODUK
    // =====================================================
 
    function verifikasiBPOM(
        string calldata batchId,
        bool diterima,
        string calldata nomorBPOM,
        string calldata lokasi
    ) external onlyBPOM {
        Produk storage p = daftarProduk[batchId];
 
        require(p.terdaftar, "Batch tidak ditemukan");
        require(
            p.statusBPOM == StatusBPOM.BELUM_DIVERIFIKASI,
            "Batch sudah diputuskan"
        );
 
        if (diterima) {
            require(
                bytes(nomorBPOM).length > 0,
                "Nomor BPOM wajib diisi"
            );
 
            p.nomorBPOM = nomorBPOM;
            p.statusBPOM = StatusBPOM.TERVERIFIKASI;
            p.statusDistribusi =
                StatusDistribusi.MENUNGGU_DISTRIBUTOR;
 
            _catatRiwayat(
                batchId,
                "Batch terverifikasi BPOM",
                lokasi
            );
 
            _mintSertifikat(batchId, p.alamatProdusen);
        } else {
            p.statusBPOM = StatusBPOM.DITOLAK;
 
            _catatRiwayat(
                batchId,
                "Batch ditolak BPOM",
                lokasi
            );
        }
 
        emit StatusBPOMDiubah(batchId, p.statusBPOM);
    }
 
    // =====================================================
    // 8. MENERBITKAN NFT SERTIFIKAT
    // =====================================================
 
    function _mintSertifikat(
        string memory batchId,
        address pemilik
    ) internal {
        uint256 tokenId = nextTokenId;
        nextTokenId++;
 
        tokenBatch[batchId] = tokenId;
        batchToken[tokenId] = batchId;
 
        _safeMint(pemilik, tokenId);
 
        emit SertifikatDiterbitkan(
            batchId,
            tokenId,
            pemilik
        );
    }
 
    // =====================================================
    // 9. DISTRIBUTOR MENERIMA PRODUK
    // =====================================================
 
    function terimaDistributor(
        string calldata batchId,
        string calldata lokasi
    ) external onlyDistributor {
        Produk storage p = daftarProduk[batchId];
 
        require(p.terdaftar, "Batch tidak ditemukan");
        require(
            p.statusBPOM == StatusBPOM.TERVERIFIKASI,
            "Batch belum terverifikasi"
        );
        require(
            p.statusDistribusi ==
                StatusDistribusi.MENUNGGU_DISTRIBUTOR,
            "Bukan giliran distributor"
        );
 
        p.statusDistribusi = StatusDistribusi.MENUNGGU_TOKO;
 
        _catatRiwayat(
            batchId,
            "Batch diterima distributor",
            lokasi
        );
 
        emit DistribusiDiperbarui(
            batchId,
            p.statusDistribusi,
            msg.sender
        );
    }
 
    // =====================================================
    // 10. TOKO MENERIMA PRODUK
    // =====================================================
 
    function terimaToko(
        string calldata batchId,
        string calldata lokasi
    ) external onlyToko {
        Produk storage p = daftarProduk[batchId];
 
        require(p.terdaftar, "Batch tidak ditemukan");
        require(
            p.statusBPOM == StatusBPOM.TERVERIFIKASI,
            "Batch tidak terverifikasi"
        );
        require(
            p.statusDistribusi == StatusDistribusi.MENUNGGU_TOKO,
            "Distributor belum menerima batch"
        );
 
        p.statusDistribusi = StatusDistribusi.SELESAI;
 
        _catatRiwayat(
            batchId,
            "Batch diterima toko",
            lokasi
        );
 
        emit DistribusiDiperbarui(
            batchId,
            p.statusDistribusi,
            msg.sender
        );
    }
 
    // =====================================================
    // 11. MELIHAT DATA PRODUK
    // =====================================================
 
    // [TAMBAHAN] Jumlah seluruh batch yang terdaftar
    function jumlahBatch() external view returns (uint256) {
        return daftarBatchId.length;
    }
 
    // [TAMBAHAN] Seluruh Batch ID yang terdaftar
    function semuaBatchId() external view returns (string[] memory) {
        return daftarBatchId;
    }
 
    function lihatProduk(
        string calldata batchId
    ) external view returns (Produk memory) {
        require(
            daftarProduk[batchId].terdaftar,
            "Batch tidak ditemukan"
        );
 
        return daftarProduk[batchId];
    }
 
    function lihatJumlahRiwayat(
        string calldata batchId
    ) external view returns (uint256) {
        require(
            daftarProduk[batchId].terdaftar,
            "Batch tidak ditemukan"
        );
 
        return riwayatProduk[batchId].length;
    }
 
    function lihatRiwayat(
        string calldata batchId,
        uint256 indeks
    ) external view returns (Riwayat memory) {
        require(
            daftarProduk[batchId].terdaftar,
            "Batch tidak ditemukan"
        );
        require(
            indeks < riwayatProduk[batchId].length,
            "Indeks tidak valid"
        );
 
        return riwayatProduk[batchId][indeks];
    }
 
    // =====================================================
    // 12. CEK STATUS BPOM DALAM BENTUK TEKS
    // =====================================================
 
    function cekStatusBPOM(
        string calldata batchId
    ) external view returns (string memory) {
        require(
            daftarProduk[batchId].terdaftar,
            "Batch tidak ditemukan"
        );
 
        StatusBPOM status = daftarProduk[batchId].statusBPOM;
 
        if (status == StatusBPOM.BELUM_DIVERIFIKASI) {
            return "BELUM DIVERIFIKASI";
        } else if (status == StatusBPOM.TERVERIFIKASI) {
            return "TERVERIFIKASI";
        } else {
            return "DITOLAK";
        }
    }
 
    // =====================================================
    // 13. CEK STATUS DISTRIBUSI DALAM BENTUK TEKS
    // =====================================================
 
    function cekStatusDistribusi(
        string calldata batchId
    ) external view returns (string memory) {
        require(
            daftarProduk[batchId].terdaftar,
            "Batch tidak ditemukan"
        );
 
        StatusDistribusi status =
            daftarProduk[batchId].statusDistribusi;
 
        if (status == StatusDistribusi.BELUM_DIMULAI) {
            return "BELUM DIMULAI";
        } else if (
            status == StatusDistribusi.MENUNGGU_DISTRIBUTOR
        ) {
            return "MENUNGGU DISTRIBUTOR";
        } else if (
            status == StatusDistribusi.MENUNGGU_TOKO
        ) {
            return "MENUNGGU TOKO";
        } else {
            return "SELESAI";
        }
    }
 
    // =====================================================
    // 14. MENCARI BATCH DARI TOKEN ID
    // =====================================================
 
    function getBatchByToken(
        uint256 tokenId
    ) external view returns (string memory) {
        require(
            tokenId > 0 && tokenId < nextTokenId,
            "NFT tidak ditemukan"
        );
 
        return batchToken[tokenId];
    }
 
    // =====================================================
    // 15. MENCATAT RIWAYAT PRODUK
    // =====================================================
 
    function _catatRiwayat(
        string memory batchId,
        string memory peristiwa,
        string memory lokasi
    ) internal {
        riwayatProduk[batchId].push(
            Riwayat({
                aktor: msg.sender,
                peristiwa: peristiwa,
                lokasi: lokasi,
                timestamp: block.timestamp
            })
        );
 
        emit RiwayatDicatat(
            batchId,
            msg.sender,
            peristiwa,
            lokasi,
            block.timestamp
        );
    }
}
 