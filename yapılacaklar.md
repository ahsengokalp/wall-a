# Yapılacaklar

## Öncelik: görsel algılama ve kişi kayıtları

- [ ] LLM'den bağımsız hafif yüz algılama ekle; yüz kutuları ve işlem süresini panelde göster.
- [ ] Kullanıcı isteğiyle arayüzden ad + fotoğraf üzerinden kişi kaydı oluştur.
- [ ] Kayıtlı kişileri listele ve sil; belirsiz eşleşmeleri “Bilinmeyen” göster.
- [ ] Kamera karelerini kayıtlı kişilerle karşılaştır; kayıtlı fotoğraflar yerine yerel yüz temsilleri sakla.
- [ ] Önce tek kareyi, ardından kullanıcı başlatınca aralıklı kamera kontrolünü doğrula.

## LLM / VLM yanıt hızını iyileştirme

1 Kasım 2026 kaynak ve kod incelemesi: [Hızlı asistan, hafıza ve sesli sohbet araştırması](docs/hizli-asistan.md). Önerilen sıra: aşama ölçümleri → ayrı küçük metin modeli → yerel komut/hafıza yönlendirmesi → yanıt akışı → sesli konuşma. Araştırma yeni bir hız ölçümü veya uygulanmış performans değişikliği değildir.

- [ ] Görüntüsüz metin sohbet yolu ekle; küçük metin modellerinin Türkçe kalite ve ilk token sürelerini karşılaştır.
- [ ] Saat/durum/cihaz komutlarını ve açık hafıza sorgularını LLM çağırmadan yanıtlayan yerel yönlendirici ekle.
- [ ] Kullanıcı tercihleri için düzenlenebilir/silinebilir SQLite hafızası ve sınırlı yakın konuşma bağlamı ekle.
- [ ] Tam eşleşmeli cevap önbelleğini kullanıcı, bağlam, görüntü ve hafıza sürümüne bağla; değişen sahneye eski cevap verme.
- [ ] Sesli aşamada konuşma bitişinden ilk anlamlı sese gecikmeyi ve kullanıcı araya girdiğinde üretim/oynatma iptalini ölç.

Mevcut durum: MX450 2 GB VRAM ve yaklaşık 16 GB RAM; Ollama 0.40.11, Qwen3-VL 2B Instruct. Otomatik GPU denemesi Vulkan `device lost` hatası verdi; CPU modu kullanılıyor. Gözlenen ilk cevaplar yaklaşık 106,5–136,4 saniye; gerçek kamera karesinde kullanıcı ekran görüntüsünde 134,2 saniye görüldü. Bu süreler akıcı sohbet için fazla uzun.

- [ ] Toplam gecikmeyi ayrı ölç: kamera aktarımı, görüntü ön işleme, model yükleme, görsel kodlama, ilk yanıt ve metin üretimi.
- [ ] Soğuk başlangıç ile model bellekteyken yapılan sorguları karşılaştır.
- [ ] GPU/Vulkan hatasını incele; uygun sürücü/backend ve bellek ayarlarını kontrollü dene.
- [ ] Daha küçük/hızlı görüntü modellerini aynı görsellerle kalite ve gecikme açısından karşılaştır.
- [ ] Görüntü çözünürlüğü ve JPEG kalitesini düşürmenin tanıma başarısına etkisini ölç.
- [ ] Çıkış uzunluğu, bağlam ve CPU iş parçacığı ayarlarını ölçerek düzenle.
- [ ] Modelin bellekte kalma süresini değerlendir; RAM/VRAM kullanımını takip et.
- [ ] Yanıt akışını (streaming) arayüze ekle; bunun ilk düşünme/görsel kodlama süresini ortadan kaldırmadığını dikkate al.
- [ ] Yüz, el hareketi ve duruş gibi sık çalışan görevleri küçük görev modelleriyle yürüt; her kareyi VLM'e gönderme.

Belirli bir hızlanma oranı garanti edilmez. Başarı, aynı donanımda aynı örneklerle gerçek süre ve cevap kalitesi ölçülerek değerlendirilecek. Şimdiki çalışmanın ana hedefi yüz algılama ve kullanıcının kişi kayıtları; LLM performans ayarları sonraki iş olarak kaydedildi.

## Sonraki aşamalar

- [ ] Kayıtlı kişi başına birden fazla örnek fotoğraf ve yanlış eşleşme düzeltme akışı.
- [ ] El sallama / açık avuç algılama.
- [ ] İsteğe bağlı duruş takibi.
- [ ] Mikrofon → OLED → hoparlör → hareket sırası (`plan.md`).
