# Donanım doğrulama notları

## Bilinenler

- Fotoğraftaki modül işareti: ESP32-S3-N16R8.
- Kart üzerinde kamera, iki USB-C bağlantısı, EN/RST ve BOOT düğmeleri bulunuyor.
- Arka yüz fotoğrafıyla microSD yuvası ve USB soketlerinin `USB-UART` / `USB-OTG` etiketleri doğrulandı. Kullanıcının kablosu USB-UART soketinde. Kamera sensörü ve GPIO haritası bu fotoğraftan kesinleşmedi.
- Windows bağlantısı: CH343 USB-UART, önceki okumada COM5.
- esptool ile COM5 üzerinden ESP32-S3 revizyon v0.2, 240 MHz, 8 MB gömülü PSRAM doğrulandı.
- esptool flash-id ile 16 MB flash, quad veri hattı ve 3,3 V flash beslemesi doğrulandı. Flash belleğe yazılmadı; tanılama için RAM'de geçici stub çalıştırıldı ve kart yeniden başlatıldı.
- Bilgisayar: NVIDIA GeForce MX450, 2048 MiB VRAM; yaklaşık 16 GB sistem RAM'i.
- Yerel Ollama sürümü ilk kontrolde 0.40.11; ilk kontrolde model listesi boştu.
- `qwen3-vl:2b-instruct` yerel olarak indirildi. İlk otomatik GPU denemesi görüntü kodlama sırasında `ggml_vulkan: device lost on Vulkan0` hatası verdi. CPU modu bu nedenle panelde varsayılan seçildi; yalnızca uygulama sorgularına `num_gpu: 0` ekler.
- CPU modundaki uçtan uca denemede model kırmızı kareyi ve mavi daireyi doğru tanımladı. Ollama süresi 133,6 saniye; toplam sorgu süresi 136,4 saniye ölçüldü. Bu tek soğuk başlangıç ölçümüdür; sonraki sorguların aynı sürede tamamlanacağını garanti etmez.

## Kamera firmware'inden önce gerekenler

N16R8 işareti flash/PSRAM seçeneğini belirtir; kart üreticisini veya kamera kablolamasını belirlemez. Kartın arka yüz fotoğrafı, üretici şeması veya satın alma bağlantısıyla şu bilgiler doğrulanmalı:

- Kamera sensörünün modeli.
- D0–D7, XCLK, PCLK, VSYNC, HREF, SCCB SDA/SCL, varsa PWDN ve RESET pinleri.
- Flash/PSRAM tipi ve kartın derleme ayarları.
- Kart üstündeki LED ve USB bağlantılarının pinleri.

İlk sensör denemesi için Espressif'in `BOARD_ESP32S3_GOOUUU` profili seçildi; fotoğraflardaki kamera işaretli GPIO grubuyla eşleşiyor. Tam üretici kimliği hâlâ bilinmiyor. Kaynak ve çalışan pinler `modüller.md` ve `firmware/README.md` içinde kayıtlı. Mevcut firmware'in tam yedeğinden sonra yapılan sensör sorgusu ve ilk JPEG testi başarılı oldu. Harici modül pinleri bu pin haritasına göre seçilecek.

Kartın ön/arka yüz ayrıntıları, bağlantı etiketleri ve diğer parçaların envanteri proje kökündeki `modüller.md` dosyasına kaydedildi.

## Orijinal firmware yedeği

- Tam okuma esptool 5.6.0 ile COM5 üzerinden tamamlandı; offset 0, uzunluk 16.777.216 bayt.
- Dosya: `backups/esp32-original-2026-11-01.bin`.
- SHA-256: `d73b6dd5a15e469a30629798664fb6e9e5c0ee30ef2679d75858d97a72b6fb15`.
- Boyut ve özet `backups/esp32-original-2026-11-01.json` içinde de kayıtlı. Bu özet sonraki dosya değişikliklerini kontrol etmek içindir; bağımsız ikinci flash okuması yapılmadı.
- Yedek alma işlemi başarılı tamamlandı ve yükleme öncesinde dosyanın SHA-256 özeti tekrar doğrulandı.

## Kamera firmware'i — ilk cihaz testi

- PlatformIO 6.2.0 / espressif32 6.12.0 / Arduino 2.0.17 ile derleme başarılı.
- COM5 üzerinden yükleme başarılı; esptool 4.9.0 yazılan flash bloklarının özetlerini doğruladı.
- GOOUUU pin profili gerçek sensör sorgusu ve JPEG alma ile bu kartta çalıştı. Kesin üretici adı hâlâ bilinmiyor.
- Sensör PID: `0x0026`; kurulu kamera sürücüsündeki `OV2640_PID` ile eşleşir.
- İlk görüntü: 640×480 JPEG, 10.563 bayt. Seri çıktı: `FIRST_FRAME 640x480 10563 bytes`.
- Flash: 16.777.216 bayt. PSRAM başlatıldı; Arduino toplam kullanılabilir PSRAM raporu 8.386.279 bayt.
- Kullanıcının girdiği ağ Windows taramasında 5 GHz / kanal 36 olarak görüldü. ESP32-S3'ün desteklediği 2,4 GHz bandında aynı ağ bu taramada görülmedi. Bu bulgu, modemde başka bir 2,4 GHz ağının olmadığı anlamına gelmez.
- Kartın station bağlantısı 25 saniyede kurulamadı. Yedek erişim noktası açıldı: `WALL-A-CAM`, IP `192.168.4.1`, `camera_ready=true`.
- İlk tanılama kaydı `.tools/board-status.json` altında tutuluyor. Ağ üzerinden fotoğraf ve panel bağlantısı henüz test edilmedi.

## 2,4 GHz ayarı sonrası başarılı ağ testi

- Kullanıcı Wi-Fi ayar dosyasını 2,4 GHz ağına güncelledi; firmware yeniden derlendi ve COM5 üzerinden başarıyla yüklendi. Yazılan verinin özeti esptool tarafından doğrulandı.
- Kart `mode=station ip=192.168.100.83 camera_ready=true` bildirdi. `.tools/board-status.json` son açılışı içeriyor.
- `/status`: HTTP 200, kamera hazır, hata 0, OV2640 PID 38 (0x26).
- `/capture`: HTTP 200; 640×480 JPEG, 13.311 bayt. Pillow ile bellekte tam çözüldü; dosyaya görüntü kaydedilmedi.
- Açık Python sunucusunda `/api/capture`: HTTP 200; aynı fiziksel karttan 640×480 fotoğraf alınıp panel formatında döndürüldü ve çözüldü.
- Bu, gerçek cihazdan panel API'sine kadar doğrulamadır. Kullanıcının tarayıcıda yeni kareyi görmesi ve gerçek kamera karesine Ollama sorgusu sonraki adımlardır.
- IP adresi DHCP ile atanır; değişirse seri terminal veya modem üzerinden güncel adres okunmalı.
