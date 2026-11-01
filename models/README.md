# Yerel yüz modelleri

Kurulum: `.\.venv\Scripts\python.exe tools/setup_vision.py`

- YuNet 2023mar: yüz kutusu ve beş yüz referans noktası, MIT lisansı.
- SFace 2021dec: hizalanmış yüzün 128 boyutlu temsilini üretir, Apache 2.0 lisansı.

Kaynak: [OpenCV Zoo](https://github.com/opencv/opencv_zoo). İndirme betiği yayımlanan Git-LFS SHA-256 değerlerini doğrular ve lisans dosyalarını indirir. Model dosyaları Git dışında tutulur. Modeller çalışma sırasında internet kullanmaz. OpenCV 4.11 ile 2023mar YuNet modeli kullanılır; 2026may modeli OpenCV 5.x için farklı dinamik giriş davranışına sahiptir.
