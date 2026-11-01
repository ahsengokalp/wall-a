# Masaüstü robot asistanı geliştirme planı

## Hedef ve çalışma biçimi

Önce kamerayla çevresini gören, bilgisayardaki Ollama üzerinden soruları cevaplayan bir asistan oluşturacağız. Python tabanlı kontrol arayüzü başlangıçtan itibaren kullanılacak. Ardından sırasıyla mikrofon, OLED, hoparlör ve hareket eklenecek.

Hızlı ilerlemek için her aşamada önce çalışan en küçük sürümü tamamlayacağız. Bir aşamanın temel işlevi çalışınca sonraki aşamaya geçeceğiz. İlk sürüm için model eğitilmeyecek; hazır görüntü destekli bir model kullanılacak.

## Mevcut durum

- Fotoğrafta ESP32-S3-N16R8 işaretli, kameralı ve iki USB-C girişli geliştirme kartı var. Bellek kapasitesi yazılımla doğrulanacak.
- Windows, CH343 USB-UART dönüştürücüsünü COM5 olarak algıladı. esptool ile ESP32-S3 revizyon v0.2, 8 MB gömülü PSRAM ve 16 MB quad flash doğrulandı. Flash belleğe yazılmadı; port numarası değişebilir.
- Kartın tam üretici/modeli ve şeması henüz kesinleşmedi. OV2640 sensörü ve Espressif GOOUUU kamera pin profili çalışma testiyle doğrulandı.
- Bilgisayarda Ollama 0.40.11, MX450 2 GB VRAM ve yaklaşık 16 GB sistem RAM'i mevcut. `qwen3-vl:2b-instruct` indirildi. İlk GPU sorgusu Vulkan device-lost hatası verdi; panelde CPU modu varsayılan seçildi.
- Python uygulaması `.venv` ortamında kuruldu, esptool `.tools` klasörüne kuruldu. ESP32 derleme araçları henüz kurulmadı.
- Kontrol paneli, fotoğraf yükleme, yerel görüntü modeli seçimi, soru sorma ve `/capture` kamera istemcisi uygulandı. Gerçek kart kamerasından henüz görüntü alınmadı.
- Proje sanal ortamında 20 otomatik test geçti; JavaScript sözdizimi kontrolü geçti. Gerçek HTTP sunucusu üzerinden yerel model denemesinde kırmızı kare/mavi daire doğru tanımlandı. İlk CPU sorgusu yaklaşık 136 saniye sürdü. Tarayıcıda görsel kontrol yapılmadı.
- Kullanıcının tarayıcı ekran görüntüsünde dosyadan yüklenen gerçek klavye fotoğrafı doğru yorumlandı; gösterilen süre 106,5 saniyeydi. Bu, ESP32 kamera görüntüsü testi değildir.
- Kamera firmware'i derlendi ve COM5 üzerinden yüklendi; esptool yazılan veriyi doğruladı. OV2640 sensörü (PID 0x26), PSRAM ve ilk 640×480 JPEG (10.563 bayt) seri açılış çıktısıyla doğrulandı.
- Girilen Wi-Fi ağı Windows taramasında 5 GHz/kanal 36 olarak görüldü. Kart ağa bağlanamayınca `WALL-A-CAM` erişim noktasını 192.168.4.1 adresinde açtı; `camera_ready=true`. 2,4 GHz ağ bilgileriyle yeniden yükleme veya bilgisayarın yedek ağa bağlanması gerekiyor. Ağ üzerinden JPEG ve Python paneli bağlantısı henüz doğrulanmadı.
- Son durum: Kullanıcı 2,4 GHz ağ bilgilerini güncelledi; yeniden derleme/yükleme başarılı. Kart station modunda **192.168.100.83** adresine bağlandı. `/status`, doğrudan `/capture` ve açık Python panelinin `/api/capture` isteği gerçek cihazla başarılı. JPEG 640×480 olarak Pillow ile bellekte açıldı; doğrudan örnek 13.311 bayt. Önceki 5 GHz bağlantı sorunu aşıldı. IP modem tarafından değiştirilebilir.
- Harici modül bağlantısı yapılmadı. Fotoğraflarda kart ve OLED bağlantı header'ları lehimlenmemiş görünüyor.
- Mevcut parçalar: 2× INMP441, I²C OLED, MAX98357A, TP4056. Hoparlör henüz yok.

## İlk sürümün mimarisi

```text
Python kontrol arayüzü (bilgisayarda)
  ├─ ESP32 bağlantısı ve kamera önizlemesi
  ├─ Fotoğraf çekme ve soru yazma
  └─ Bağlantı durumu, cevaplar ve hata mesajları
             │
       Python sunucusu
         ├─ Wi-Fi üzerinden ESP32 kamera → JPEG fotoğraf
         └─ Yerel Ollama API → görüntü + soru → Türkçe cevap
```

- Hızlı başlangıç için Python/FastAPI sunucusu ve aynı sunucunun sunduğu sade bir tarayıcı arayüzü kullanılacak. Ayrı bir masaüstü paketleme işi ilk sürüme dahil edilmeyecek.
- ESP32, kamera ve donanım kontrolünü yapacak; büyük model bilgisayarda çalışacak.
- İlk sürüm tek fotoğraf üzerinden soru cevaplayacak. Sürekli video analizi sonraya bırakılacak.
- Kamera önizlemesi ile yapay zekâ analizi ayrı işlemler olacak; her önizleme karesi modele gönderilmeyecek.
- Ollama'ya sunucu erişecek; Ollama'yı doğrudan yerel ağa açmak gerekmeyecek.
- Cihaz başlangıçta yerel ağda kullanılacak. İnternete açma bu planın ilk sürümüne dahil değil.
- Yerel model kullanıldığında görüntü işleme bilgisayarda gerçekleşecek. Bilgisayarın ve Ollama'nın açık olması gerekecek.

## Aşama 1 — Kart ve kameranın ilk çalıştırılması

- [ ] Kartın arka yüzü ve varsa ürün bağlantısından tam modeli/şemayı belirle.
- [x] Kamera sensörünü ve pin eşlemesini çalışma testiyle doğrula: OV2640, GOOUUU profili. Sensör sorgusu ve ilk JPEG başarılı; pinler `modüller.md` içinde kayıtlı. Kesin kart üreticisi hâlâ bilinmiyor.
- [x] ESP32 çipini, flash belleği ve PSRAM'i araçla doğrula.
- [x] Firmware yüklemeden önce mevcut yazılımın tam 16 MB yedeğini al: `backups/esp32-original-2026-11-01.bin`. Boyut ve SHA-256, yanındaki JSON dosyasında kayıtlı.
- [x] Gerekli ESP32 derleme/yükleme araçlarını kur ve kart ayarlarını kaydet: PlatformIO 6.2.0, espressif32 6.12.0, Arduino 2.0.17, 16 MB QIO flash ve OPI PSRAM.
- [x] Wi-Fi bağlantısı, durum bilgisi ve JPEG fotoğraf alma işlevlerini içeren ilk firmware'i hazırla ve karta yükle. Ağ üzerinden uç noktaların doğrulaması hâlâ bekliyor.
- [x] Python sunucusunu ve ilk kontrol ekranını oluştur: cihaz adresi, bağlantı kontrolü, fotoğraf çekme, son fotoğraf ve hata görünümü. Kamera istemcisi otomatik testlerle doğrulandı; gerçek cihaz bağlantısı aşağıdaki adımda doğrulanacak.
- [x] Firmware'i yükle ve gerçek karttan fotoğrafı panelin kamera API'sine getir. JPEG içeriği gerçek cihazla doğrulandı.
- [ ] Kullanıcı tarayıcıda 192.168.100.83 adresiyle “Fotoğraf çek” düğmesine basıp görüntüyü gözle kontrol etsin.

**Tamamlanma ölçütü:** Arayüzde “Fotoğraf çek” düğmesine basınca karttan yeni bir görüntü gelir ve gösterilir. Bağlantı kesilirse anlaşılır bir hata görünür.

## Aşama 2 — Ollama ile gören asistan

- [x] Bilgisayarın GPU/VRAM/RAM bilgilerini, Ollama sürümünü ve kurulu modelleri kontrol et.
- [x] İlk deneme için görüntü destekleyen yerel model seç ve kur: Qwen3-VL 2B Instruct, yaklaşık 1,9 GB. Donanımdaki yanıt başarısı ve hız ayrıca doğrulanacak.
- [x] Bilgisayarda hazırlanan test görseliyle Ollama görüntü girişini doğrula. Gerçek HTTP → görüntü yükleme → Ollama → Türkçe cevap akışı CPU modunda çalıştı. Gerçek kamera fotoğrafı ayrıca denenecek.
- [x] Arayüze soru alanı ve “Çek ve sor” işlemi ekle.
- [ ] Yeni kamera fotoğrafını soruyla birlikte Ollama'ya gönder ve Türkçe cevabı göster.
- [x] İşlem sürerken durum göster; bağlantı, model ve zaman aşımı hatalarını yönet.
- [x] Tekrar kullanılacak fotoğrafın zamanını göster; yeni çekim ile önceki görüntüye soruyu ayırt et.

**Tamamlanma ölçütü:** Kullanıcı “Masada ne görüyorsun?” yazar; karttan yeni fotoğraf alınır ve yerel modelin cevabı aynı arayüzde görünür.

**Sınır:** Model nesneler, sayılar, küçük yazılar ve konumlar hakkında yanılabilir. Fiziksel hareket kontrolü yalnızca serbest model yanıtına bağlanmayacak.

## Aşama 3 — Mikrofon

- [ ] Kamera ile çakışmayan I²S pinlerini belirle.
- [ ] Önce tek INMP441 ile kısa ses kaydı al ve bilgisayarda dinleyerek doğrula.
- [ ] Konuşmayı yazıya çevirme servisini Python sunucusuna ekle.
- [ ] Arayüze bas-konuş kontrolü ekle; sesi metne, metni mevcut asistan akışına bağla.
- [ ] İkinci mikrofonu ancak tek mikrofon çalıştıktan sonra ekle. İki mikrofonun kendiliğinden gürültü engelleme veya yön bulma sağlamadığını dikkate al.

**Tamamlanma ölçütü:** Kullanıcının sesli sorusu metne çevrilir ve asistan cevap verir.

## Aşama 4 — OLED ve karakter ifadeleri

- [ ] OLED sürücüsünü, çözünürlüğünü ve besleme uyumluluğunu doğrula.
- [ ] Kamera/mikrofon ile çakışmayan I²C pinlerini seç; önceki GPIO 8/9 önerisini şema olmadan kesin kabul etme.
- [ ] Bekleme, görüntü alma, dinleme, düşünme ve hata durumlarına uygun göz animasyonlarını oluştur.
- [ ] Python sunucusundan gelen durumları ekrana yansıt.

**Tamamlanma ölçütü:** Ekrandaki karakter, asistanın gerçek çalışma durumunu yansıtır.

## Aşama 5 — Hoparlör ve sesli cevap

- [ ] Hoparlör seçimini MAX98357A besleme ve güç koşullarıyla birlikte yap.
- [ ] Bilgisayarda Türkçe metinden sese dönüşümü doğrula.
- [ ] Kamera/mikrofon pinlerini gözeterek MAX98357A bağlantısını kur ve sesi ESP32 üzerinden oynat.
- [ ] Konuşma sırasında mikrofonun kendi sesini yeniden tetiklemesini başlangıçta dinlemeyi duraklatarak önle.

**Tamamlanma ölçütü:** Asistanın metin cevabı hoparlörden duyulur.

## Aşama 6 — Hareket ve gövde

- [ ] Gövde, ağırlık ve hareket hedefini belirle; önce başın sağa/sola dönmesini hedefle.
- [ ] Buna uygun servo, mekanik parçalar ve ayrı motor beslemesini seç.
- [ ] Arayüze manuel hareket kontrolü ve durdurma düğmesi ekle.
- [ ] Yazılımsal açı/hız sınırları koy ve güvenli başlangıç konumunu belirle.
- [ ] Daha sonra nesne tespiti/takip sistemiyle kamerayı hedefe yönlendirmeyi dene. Hızlı takip için her kareyi sohbet modeline göndermeyi temel yöntem olarak kullanma.

**Tamamlanma ölçütü:** Robot arayüzden sınırlandırılmış hareket komutlarını uygular; iletişim kesilince yeni hareket komutları üretmez.

## Güç ve bağlantı ilkeleri

- İlk aşamalarda USB besleme kullanılacak; bağlantılar güç kesikken yapılacak.
- GPIO'lar 3,3 V seviyesinde kullanılacak; motor veya hoparlör doğrudan GPIO'ya bağlanmayacak.
- Kamera, PSRAM, USB ve açılış işlevleri tarafından kullanılan pinler şema üzerinden kontrol edilecek.
- MAX98357A hoparlör çıkışlarından hiçbiri GND'ye bağlanmayacak.
- Pil ve taşınabilir kullanım sonraya bırakılacak. TP4056 tek başına ESP32 için gerilim düzenleme ve güç paylaşımı çözümü sayılmayacak.

## Planlanan proje düzeni

```text
firmware/        ESP32 kamera ve sonraki donanım işlevleri
server/          Python/FastAPI, cihaz bağlantısı ve Ollama entegrasyonu
server/static/   Tarayıcı kontrol arayüzü
docs/            Doğrulanmış pinler, kurulum ve donanım notları
plan.md          Aşamalar ve ilerleme
```

## Sıradaki somut işler

1. Panelde ESP32 IP alanına 192.168.100.83 yazıp “Fotoğraf çek” ile kamera açısını ve görüntüyü gözle kontrol et.
2. ESP32 görüntüsünü “Bu görüntüye sor” veya “Yeni çek ve sor” ile Ollama'ya sor.
3. Sonrasında yaklaşık 106–136 saniyelik ilk CPU yanıtlarını hızlandırmayı değerlendir.

Her aşama tamamlandıkça bu dosyadaki ilgili kutular işaretlenecek; doğrulanan donanım ve model bilgileri plana eklenecek.
