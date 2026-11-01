# WALL-A kamera firmware'i

ESP32-S3 N16R8 için Arduino/PlatformIO uygulaması. Kamera JPEG görüntüsü sunar; SD kartı, harici modülleri ve motorları kullanmaz.

Cihaz testi başarılı: derlendi, karta yüklendi, OV2640 (PID 0x26) algılandı ve 640×480 JPEG alındı. İlk 5 GHz ağ denemesi başarısız olduktan sonra kullanıcı 2,4 GHz ağını yazdı. Son yüklemede kart station modunda **192.168.100.83** adresine bağlandı. Gerçek `/status`, `/capture` ve Python panelinin `/api/capture` istekleri başarılı; JPEG bellekte çözüldü. IP DHCP ile değişebilir.

## Wi-Fi ayarı

`include/wifi_config.h` dosyasına 2,4 GHz ağının adını ve şifresini yaz:

```cpp
#define WALL_A_WIFI_SSID "WiFi_adin"
#define WALL_A_WIFI_PASSWORD "WiFi_sifren"
```

Dosya Git dışında tutulur. Yeni kurulumda `wifi_config.example.h` dosyasını `wifi_config.h` adıyla kopyala. Tırnak veya ters eğik çizgi içeren değerlerde C++ metin kaçışlarını kullan: `\"` ve `\\`. Şifre firmware ikilisine de gömülür; özel ayar dosyasını veya derlenmiş firmware'i paylaşma.

Kart 25 saniye boyunca bu ağa bağlanmayı dener. Bilgiler boşsa veya bağlantı kurulamazsa şu yedek ağı açar:

- Ağ: **WALL-A-CAM**
- Şifre: **walla2026**
- Kart adresi: **192.168.4.1**

Normal ağ bağlantısında kartın IP'si modemden alınır ve seri terminalde `NETWORK_READY mode=station ip=...` satırında görünür. Bilgisayar ile kart aynı yerel ağda olmalıdır; istemci izolasyonu olan misafir ağları bağlantıyı engelleyebilir.

## Derleme ve yükleme

Proje kökünde PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-firmware.txt
.\.venv\Scripts\python.exe tools/firmware.py build
.\.venv\Scripts\python.exe tools/firmware.py upload --port COM5
.\.venv\Scripts\python.exe tools/firmware.py monitor --port COM5
```

USB-UART soketini kullan. Seri monitörü kapatmak için Ctrl+C. Yükleme sırasında başka bir program COM5'i açık tutmamalı. Derleyici ve çerçeve `.tools/pio-core`, derleme çıktıları `firmware/.pio` altında tutulur.

`esp32-s3-devkitc-1` derleme tabanı kullanılır; bu seçim kartın fiziksel olarak Espressif DevKitC olduğu iddiası değildir. 16 MB quad flash, octal PSRAM ve USB-UART üzerinden log için ayarlar ayrıca geçersiz kılınmıştır.

## Kamera pin profili ve doğrulama

Profil Espressif'in `BOARD_ESP32S3_GOOUUU` düzenidir. Fotoğraflardaki kamera işaretli GPIO grubu ile uyumlu olduğu için seçildi; kesin üretici adı bilinmiyor. Sensör sorgusu ve ilk gerçek JPEG alınması, profilin bu kartta çalıştığını doğruladı.

| Hat | GPIO |
|---|---|
| SCCB SDA / SCL | 4 / 5 |
| XCLK | 15 |
| VSYNC / HREF / PCLK | 6 / 7 / 13 |
| D0–D7 | 11, 9, 8, 10, 12, 18, 17, 16 |
| PWDN / RESET | -1 / -1; harici kontrol kullanılmaz |

Kaynak: [Espressif kamera pin tanımları](https://github.com/espressif/esp32-camera/blob/master/examples/camera_example/main/camera_pinout.h). Aynı dosyadaki WROOM profilinin PWDN=38 seçeneği bu firmware'de kullanılmaz. SD kart başlatılmaz.

## Uç noktalar

- `/`: Basit fotoğraf alma sayfası.
- `/status`: Kamera durumu, sensör PID, flash/PSRAM kapasitesi ve ağ adresi.
- `/capture`: Yeni 640×480 JPEG. Kamera çalışmıyorsa HTTP 503 döner.

Kamera başlatılamasa da ağ ve durum servisi açılır. Seri çıktıda `CAMERA_READY` tek başına yeterli değildir; `FIRST_FRAME` ve son `NETWORK_READY ... camera_ready=true` satırları da kontrol edilmeli.

Python panelinde kartın IP'sini girip **Fotoğraf çek** kullan. Önizleme başarılı olduktan sonra **Bu görüntüye sor** ile yerel Ollama'ya gönder.

## Orijinal yazılım

İlk yüklemeden önce 16 MB flash yedeği `backups/` altında tamamlanmalı ve SHA-256 kaydı alınmalı. Yedek dosyaları özel bilgiler içerebilir; paylaşılmaz ve Git dışında tutulur. Yedek alınması/firmware'in çalışması ile ilgili gerçek sonuçlar `docs/donanim.md` ve `plan.md` içinde kaydedilir.
