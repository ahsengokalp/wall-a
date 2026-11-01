# WALL-A · Kamera asistanı

Python kontrol paneli ve yerel Ollama üzerinden görüntüye soru sorma. ESP32 kamera firmware kaynağı `firmware/` altında hazırlandı; fiziksel karttaki doğrulama durumu `docs/donanim.md` içinde izlenir. Kart bağlanmadan da dosyadan fotoğraf yüklenebilir.

## Windows'ta çalıştırma

Proje için `.venv` ortamı kullanılır. Proje klasöründeki `start.bat` dosyasını aç ve tarayıcıda **http://127.0.0.1:8000** adresine git. Terminali açık tut; kapatmak için Ctrl+C kullan.

Yeni ortam kurulumu gerekiyorsa PowerShell'de:

```powershell
cd C:\dev\wall-a
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8000
```

Tam olarak test edilen sürümleri kurmak için `requirements.txt` yerine test paketlerini de içeren `requirements-lock.txt` kullanılabilir.

Ollama uygulamasını aç. İlk görüntü modeli için:

```powershell
ollama pull qwen3-vl:2b-instruct
```

Model indirmesi yaklaşık 1,9 GB internet ve disk alanı gerektirir. [Resmî model sayfası](https://ollama.com/library/qwen3-vl:2b-instruct). Bu bilgisayarda model indirildi. İlk GPU denemesi Vulkan `device lost` hatası verdiğinden panelde **CPU ile çalıştır** varsayılan açıktır. Bu seçenek yalnızca bu uygulamanın sorgusuna `num_gpu: 0` ekler; Ollama'nın genel ayarını değiştirmez. CPU'da ilk yanıt yavaş olabilir; GPU denemesi için kutu kaldırılabilir.

1. Panelde model listesini yenile ve görüntü modelini seç.
2. JPEG, PNG veya WebP fotoğrafı yükle (en fazla 8 MB).
3. Sorunu yaz ve **Bu görüntüye sor** düğmesine bas.
4. ESP32 hazır olduğunda kartın yerel IP adresini gir ve **Fotoğraf çek** veya **Yeni çek ve sor** kullan.

## Kamera sözleşmesi

Beklenen cihaz uç noktası `GET http://KART_IP/capture`: başarılı yanıtta HTTP 200 ve gerçek JPEG/PNG/WebP görüntüsü döndürür. Şu an bu uç noktayı sağlayan firmware karta yüklenmedi. IP girmek mevcut kart yazılımına bu özelliği kazandırmaz. Yerel IPv4 adresleri ve HTTP port 80/8080 desteklenir.

## Yerel çalışma ve görüntüler

Sunucu yalnızca bilgisayarın loopback adresinde dinler. Ollama'ya `127.0.0.1:11434` üzerinden erişir; bulut modelleri seçime dahil edilmez. Son sekiz görüntü RAM'de tutulur, diske yazılmaz; sunucu kapanınca silinir. Ollama'ya gönderilmeden önce görüntü en fazla 1280×1280 olarak yeniden kodlanır. Panel sohbet geçmişi veya yüz tanıma henüz içermez.

## Kontroller

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/check_local.py --model qwen3-vl:2b-instruct
```

Son komut geçici bir HTTP sunucusu açar, RAM'de hazırladığı kırmızı kare/mavi daire görselini gerçek Ollama'ya gönderir ve sunucuyu kapatır. Bu, ESP32 kamera testi değildir. Test görseli diske kaydedilmez.

İlk doğrulama: proje ortamında **20 test geçti**, JavaScript sözdizimi kontrolü geçti ve gerçek yerel model kırmızı kare/mavi daireyi doğru tanımladı. İlk CPU sorgusu yaklaşık **136 saniye** sürdü. Daha sonra gerçek ESP32 kamerasından 640×480 JPEG hem doğrudan hem panelin `/api/capture` isteğiyle alınıp bellekte çözüldü. Son kart IP'si **192.168.100.83**; panelde bu IP'yi girip **Fotoğraf çek** kullan. Test görüntüleri diske kaydedilmedi. Otomatik testlerin geçici sunucuları kapatılır; normal kullanımda yukarıdaki terminal komutuyla kendi sunucunu açık tut.

Donanım hedefleri `kamera.md`, aşamalar `plan.md`, doğrulanması gereken pinler `docs/donanim.md` dosyasındadır.

## ESP32 kamera yazılımı

Kamera uygulamasının kaynakları, Wi-Fi ayarı ve PowerShell komutları [firmware/README.md](firmware/README.md) dosyasındadır. Wi-Fi bilgilerini yalnızca `firmware/include/wifi_config.h` içine yaz; bu dosya Git dışında tutulur. Kamera firmware'inin karta yüklenme ve donanım test durumu `docs/donanim.md` içinde izlenir.
