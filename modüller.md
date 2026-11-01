# Kart ve modül envanteri

Bu belge, projede kullanılan parçaları ve doğrulama durumlarını kaydeder. Fotoğrafta görülen bilgiler, araçla okunan bilgiler ve henüz doğrulanmayan özellikler ayrı belirtilmiştir.

## 1. Ana kart — Kameralı ESP32-S3 N16R8

### Araçla doğrulanan özellikler

COM5 üzerinden esptool ile okundu. Flash belleğe yazılmadı; tanılama sırasında RAM'de geçici stub çalıştırıldı ve kart yeniden başlatıldı.

| Özellik | Bilgi |
|---|---|
| İşlemci | ESP32-S3, QFN56 |
| Silikon revizyonu | v0.2 |
| İşlemci hızı | 240 MHz |
| Çekirdekler | Çift ana çekirdek ve düşük güç çekirdeği |
| PSRAM | 8 MB gömülü PSRAM; araç çıktısı: `AP_3v3` |
| Flash bellek | 16 MB |
| Flash veri hattı | Quad, 4 veri hattı |
| Flash beslemesi | eFuse bilgisinde 3,3 V |
| Kristal | 40 MHz |
| Kablosuz özellikler | Araç çıktısında Wi-Fi ve Bluetooth 5 LE |
| USB-UART dönüştürücü | Windows aygıt adı: USB-Enhanced-SERIAL CH343 |
| Seri port | Son doğrulamada COM5; yeniden bağlandığında değişebilir |

### Ön yüz fotoğrafında görülenler

- Metal modül üzerinde `ESP32-S3-N16R8` işareti bulunuyor.
- Kamera takılı; şerit kablo kartın kamera soketine bağlı.
- Kamera şeridinde `TY-OV26` ve `40-V1.0` olarak okunan işaretler var. Bunlar sensörün kesin modelini veya GPIO eşlemesini tek başına doğrulamıyor.
- Üst bölümde PCB anten alanı bulunuyor.
- İki USB Type-C soketi var.
- `EN/RST` ve `BOOT` düğmeleri var.
- `ON`, `TX`, `RX`, `IO2` işaretli göstergeler ve `48` işaretinin yanında bir LED bileşeni görülüyor. LED türü ve kesin elektriksel bağlantıları şemadan doğrulanacak.
- Kenar bağlantı deliklerine pin header lehimlenmemiş görünüyor.

Ön yüz fotoğrafında anten yukarıda, USB soketleri aşağıdayken üstten alta okunan bağlantı etiketleri:

| Sol sıra | Sağ sıra |
|---|---|
| 3V3 | TX |
| EN | RX |
| 4 | 1 |
| 5 | 2 |
| 6 | 42 |
| 7 | 41 |
| 15 | 40 |
| 16 | 39 |
| 17 | 38 |
| 18 | 37 |
| 8 | 36 |
| 3 | 35 |
| 46 | 0 |
| 9 | 45 |
| 10 | 48 |
| 11 | 47 |
| 12 | 21 |
| 13 | 20 |
| 14 | 19 |
| 5V | GND |

Bu tablo kart üzerindeki etiketlerin kaydıdır; listelenen GPIO'ların boş veya harici kullanıma uygun olduğunu göstermez. Kamera, bellek, SD kart ve USB bağlantıları bazı pinleri kullanabilir. Etiketlerin yanındaki Camera/SD Card/PSRAM işaretlerinden kesin pin haritası çıkarılmadı.

### Arka yüz fotoğrafında doğrulananlar

- Üst bölümde microSD kart yuvası bulunuyor. Kart takılı olduğu veya yuvanın yazılımla çalıştığı doğrulanmadı.
- İki USB soketinin işlevleri PCB üzerinde açıkça yazıyor:
  - `USB-UART`: Fotoğrafta kablonun takılı olduğu soket. CH343/COM5 bağlantısı ve esptool tanılama bu bağlantıyla doğrulandı.
  - `USB-OTG`: Diğer soket. Doğrudan USB işlevleri henüz denenmedi.
- PCB üzerinde `Camera`, `SD Card` ve `PSRAM` açıklamaları ile işaretler bulunuyor.
- Bu fotoğrafta üretici adı veya kartın kesin ürün/revizyon kodu okunmuyor.

**Yön notu:** USB-UART/USB-OTG ayrımında soketin sağda veya solda olmasına değil, PCB üzerindeki yazıya bakılacak. Kartın önünden ve arkasından bakıldığında yönler ters görünür.

### Henüz doğrulanmayan bilgiler

- Geliştirme kartının üreticisi, kesin ürün adı ve kart revizyonu.
- microSD yuvasının GPIO bağlantıları ve kullanılacak arayüz modu.
- Kart üzerindeki LED'lerin türleri ve GPIO bağlantıları.
- Kartın regülatör özellikleri ve harici yükler için kullanılabilir besleme akımı.

**Çalışma testiyle doğrulanan kamera profili:** Espressif'in `BOARD_ESP32S3_GOOUUU` pin düzeni, sensör sorgusu ve ilk 640×480 JPEG alma testinde çalıştı. Bu, kartın üretici kimliğinin kesinleştiği anlamına gelmez. İlk yüklemeden önce mevcut firmware'in tam 16 MB yedeği alındı.

| Kamera hattı | Çalışan GPIO |
|---|---|
| SCCB SDA / SCL | 4 / 5 |
| XCLK | 15 |
| VSYNC / HREF / PCLK | 6 / 7 / 13 |
| D0–D7 | 11, 9, 8, 10, 12, 18, 17, 16 |
| PWDN / RESET | -1 / -1; harici kontrol yok |

Kaynak: [Espressif kamera pin tanımları](https://github.com/espressif/esp32-camera/blob/master/examples/camera_example/main/camera_pinout.h), `BOARD_ESP32S3_GOOUUU`. Firmware ve derleme ayarları `firmware/` altında. Sensör modeli OV2640 olarak doğrulandı; PID `0x0026`. SD kart ve diğer modüller bu testte kullanılmadı.

## 2. Takılı kamera

| Özellik | Durum |
|---|---|
| Adet | 1 |
| Fiziksel bağlantı | Şerit kabloyla ana kartın kamera soketine takılı |
| Sensör modeli | OV2640; sürücü üzerinden PID 0x0026 okundu |
| Görüntü alma testi | Seri açılış ve Wi-Fi testleri başarılı; 640×480 JPEG, doğrudan ağ örneği 13.311 bayt; Python panel API'si de gerçek cihazdan fotoğraf aldı |
| Son ağ durumu | 2,4 GHz ağında station modu, IP 192.168.100.83; DHCP ile değişebilir |
| Projedeki görev | Çevre görüntüsü alma; görüntüyü bilgisayardaki modele iletme |

Panelde başarılı biçimde yorumlanan klavye fotoğrafı bilgisayardan yüklenmiştir; ESP32 kamerasından alınmış değildir.

## 3. I²C OLED ekran

- Mevcut, ana karta henüz bağlanmadı.
- Ön yüz fotoğrafında soldan sağa pinler: `GND`, `VDD`, `SCK`, `SDA`.
- Arka yüz PCB işareti fotoğrafta `GM009605v4.8` olarak okunuyor; kesin sürücü/çözünürlük bilgisi olarak kabul edilmedi.
- Bağlantı deliklerinde lehimli header görünmüyor.
- Sürücü modeli, çözünürlük ve besleme uyumluluğu henüz doğrulanmadı.
- Kamera bağlantıları belirlendikten sonra uygun I²C GPIO'ları seçilecek. Önceki GPIO 8/9 önerisi kesin bağlantı planı değildir.
- Görev: Karakterin gözleri, ifadeleri ve çalışma durumu.

## 4. INMP441 mikrofonlar

- Kullanıcının bildirdiği adet: 2.
- Henüz bağlanmadı veya test edilmedi; modül fotoğrafları incelenmedi.
- İlk olarak tek mikrofonla kayıt doğrulanacak; ikinci mikrofon daha sonra eklenecek.
- I²S pinleri kamera ve diğer donanımlarla çakışmayacak şekilde seçilecek.

## 5. MAX98357A ses amplifikatörü

- Kullanıcının bildirdiği adet: 1.
- Henüz bağlanmadı veya test edilmedi; modül fotoğrafı incelenmedi.
- Görev: Üretilen sesi hoparlöre aktarmak.
- Hoparlör henüz yok. Hoparlör seçimi, besleme ve bağlantılar ses aşamasında kesinleştirilecek.
- Hoparlör çıkışlarından hiçbiri GND'ye bağlanmayacak.

## 6. TP4056 şarj modülü

- Kullanıcıda mevcut; henüz bağlanmadı veya test edilmedi.
- Koruma devresi içeren sürüm olup olmadığı fotoğraf/ürün bilgisiyle doğrulanacak.
- İlk aşamalar USB beslemeyle yapılacak. Pil, regülasyon ve güç paylaşımı daha sonra planlanacak; TP4056 tek başına bunların tamamını sağlamış kabul edilmeyecek.

## 7. Eksik ve sonraya bırakılan parçalar

| Parça | Durum |
|---|---|
| Hoparlör | Henüz yok; ses aşamasında alınacak |
| Servo/motor ve mekanik parçalar | Hareket aşamasında seçilecek |
| Motor beslemesi | Hareket sistemiyle birlikte planlanacak |
| Mesafe/masa kenarı sensörleri | Hareket hedeflerine göre daha sonra değerlendirilecek |
| Batarya ve taşınabilir güç sistemi | Sonraya bırakıldı |

Genel geliştirme sırası `plan.md`, görsel zekâ hedefleri `kamera.md`, tanılama notları `docs/donanim.md` dosyalarında bulunur.
