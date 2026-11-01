# WALL-A: düşük gecikmeli sohbet ve hafıza araştırması

Tarih: 1 Kasım 2026. Bu belge kaynak ve kod incelemesidir; yeni performans ölçümü yapılmadı ve uygulamanın çalışma davranışı değiştirilmedi.

## Sonuç

Her isteği LLM'e göndermek yerine önce yerel komutlar, güncel durum ve kayıtlı bilgiler kullanılmalı. Serbest sohbet küçük bir metin modeline; sahne hakkında yeni bilgi gerektiren sorular görüntü modeline gitmeli. Hafıza model çağrılarını azaltır, fakat yeni bir soruda modelin hesaplama süresini kendiliğinden çözmez. Akıcı sesli sohbet için ayrıca ses tanıma, ilk yanıt, ses üretimi ve oynatma gecikmeleri azaltılmalı.

## Projede doğrulananlar

- `server/app.py` içindeki `/api/ask`, her soruda görüntü destekli modeli zorunlu tutuyor ve fotoğraf gönderiyor. Ayrı bir metin sohbet yolu yok.
- `cpu_only=True` varsayılanı Ollama isteğine `num_gpu: 0` ekliyor. Proje notlarına göre önceki GPU denemesi Vulkan `device lost` hatası vermiş.
- `stream: False`: kullanıcı cevabın tamamını bekliyor.
- `keep_alive: '2m'`: modelin boşta bellekte tutulması iki dakika ile isteniyor; daha sonraki sorularda yeniden yükleme gerekebilir. Modelin sıcak olması yeni görüntünün işlenmesini ortadan kaldırmaz.
- `num_ctx: 2048`, `num_predict: 160`: bağlam ve çıktı zaten sınırlı. Bunları körlemesine daha da düşürmek kaliteyi etkileyebilir.
- Arayüze yalnızca Ollama `total_duration` değeri dönüyor. Bu, kamera dahil uçtan uca gecikme değil; aşamalar ayrı görünmüyor.
- `server/vision.py`, YuNet + SFace ve SQLite kişi kayıtlarıyla LLM'den bağımsız çalışıyor. Yerel algılama ve hafıza yaklaşımının temeli mevcut.
- Proje notlarında MX450 2 GB VRAM, yaklaşık 16 GB RAM ve 106–136 saniyelik önceki görüntü yanıtları kayıtlı. Bunlar metin sohbeti veya sıcak model için ölçülmüş süreler sayılmaz.

## Önerilen yönlendirme

| İstek | İşleme yolu | Hafıza kullanımı |
| --- | --- | --- |
| “Saat kaç?”, “Kamerayı aç”, “Sus” | Yerel işlev / açık komut kuralları | Gerekmiyorsa model çağrısı yok |
| “Adımı hatırlıyor musun?” | Aktif kullanıcıya ait doğrulanmış kayıt + cevap şablonu | SQLite |
| “Kamerada kayıtlı biri var mı?” | Yeni yüz analizi + kişi kaydı | Güncel gözlem ve eşleşme belirsizliği |
| “Az önce ne konuşuyorduk?” | Son konuşma turları; gerekirse metin modeli | Sınırlı kısa süreli bağlam |
| “Nasılsın?”, “Bana bir fikir ver” | Küçük metin modeli | Yalnızca ilgili tercihler ve yakın konuşma |
| “Masada şu anda ne var?” | Yeni kamera karesi + görüntü modeli | Önceki gözlem güncelmiş gibi sunulmaz |

Yönlendirici ilk sürümde dar kapsamlı komut kurallarıyla çalışabilir; her isteği sınıflandırmak için ayrıca LLM çağırmak gecikme ekler. Olumsuzluk, alıntı ve belirsiz ifadelerde komut uygulanmamalı. “Dur/sus” gibi açık komutlar devam eden üretimi ve ses kuyruğunu kesebilmeli. Serbest model metni doğrudan motor komutu olmamalı.

## Hafıza ve önbellek ayrı tutulmalı

1. **Anlık durum, RAM:** son görüntü zamanı, yüz sonuçları, cihaz ve konuşma durumu. Gözlemler kaynak, zaman ve geçerlilik süresi taşımalı. Kamera bağlantısı kesilince eski gözlem güncel sayılmamalı.
2. **Konuşma bağlamı:** son birkaç tur ve gerektiğinde kısa özet. Bütün geçmişi her isteğe eklemek yerine ilgili bölüm kullanılmalı. Özetleme her cevabın önüne yeni bir model çağrısı koymamalı.
3. **Kalıcı hafıza, SQLite:** kullanıcının açıkça bildirdiği ad, tercihler ve hatırlanmasını istediği bilgiler. Kullanıcı kimliği, bilgi anahtarı, değer, kaynak ve güncelleme zamanı saklanmalı; düzenleme/silme mümkün olmalı. Model tahmini doğrulanmış kişisel bilgi olarak yazılmamalı. Yüzde eşleşen kişi otomatik olarak konuşan kişi sayılmamalı.
4. **Cevap önbelleği:** aynı ve bağlamı değişmemiş isteğe önceki cevap. Anahtar; soru, kullanıcı/oturum, ilgili hafıza sürümü, model/istem sürümü ve varsa görüntü kimliğini içermeli. Yeni kare önceki sahne cevabını geçersiz kılar. İşlem yapan komutlarda eski cevap dönmek yerine işlem çalıştırılmalı.

Benzer anlamlı sorular için *semantic cache* kullanılabiliyor [4]. Ancak “Masada ne var?” aynı cümle olsa da sahne değişmiş olabilir; “ışığı aç” ile “ışığı açma” benzer metinlerdir. Bu nedenle başlangıçta anlam benzerliğiyle cevap tekrarını önermiyorum. Önce açık kurallar ve tam eşleşmeli, bağlama bağlı önbellek. Yeni bir Redis servisi veya vektör veritabanı kurmak başlangıç için gerekli görünmüyor; mevcut SQLite ve RAM yapısı yeterli bir başlangıç.

Hafızadan ilgili bilgiyi alıp yine LLM'e vererek cümle kurdurmak hâlâ model çağrısıdır. Tam hız kazanımı, cevap uygun olduğunda doğrudan şablonla üretilebildiğinde elde edilir. İleride kayıt sayısı büyürse anlamsal arama ayrıca değerlendirilebilir.

## Model ve çalışma ayarları

- **Metin ve görüntüyü ayır:** `qwen3:0.6b` ve `qwen3:1.7b` küçük metin modeli karşılaştırması için aday. Resmî Ollama sayfalarında indirme boyutları yaklaşık 523 MB ve 1,4 GB [5, 6]. Bunlar çalışma RAM/VRAM ihtiyacı değil. Türkçe doğruluğu, konuşma tutarlılığı ve gerçek cihazdaki hızı ölçülmeden seçim yapılmamalı.
- **Düşünme üretimini kapatmayı dene:** destekleyen metin modellerinde `think: false`, kısa günlük sohbet için karşılaştırılabilir [1]. Model/sürüm desteği doğrulanmalı.
- **Ön yükle ve sıcak tut:** Ollama boş istekle ön yükleme ve `keep_alive` destekliyor [2]. Aktif sohbet boyunca sıcak tutma denenebilir; kullanılabilir bellek izlenmeli. Görüntü ve metin modellerini aynı anda sıcak tutmak MX450'nin 2 GB belleğine sığmayabilir; model değişimi de ölçülmeli.
- **GPU hatasını ayrıca araştır:** Ollama NVIDIA ve Vulkan yollarını belgeliyor [3]. Önce hata günlüğünden hangi bağdaştırıcı/backend'in çöktüğü bulunmalı; ardından sürücü, CUDA yolu ve kısmi GPU yükleme kontrollü karşılaştırılmalı. Vulkan hatası tek başına MX450'nin hiç kullanılamayacağını kanıtlamıyor. Destek listesi de bu makinede çalışacağı garantisi değil.
- **Görüntüyü gerektiğinde işle:** sürekli sahne yorumlama yerine istek/olay temelli analiz. Görüntü küçültmeyi nesne tanıma ve küçük yazı okuma için ayrı değerlendir. JPEG dosyasının küçülmesi görsel token sayısının aynı oranda azalacağını göstermez.
- **Yanıtı akıt:** Ollama `stream` destekliyor [1]. Sunucu ve tarayıcı da parçaları iletmeli. Bu, ilk token öncesi hesaplamayı kaldırmaz; metnin tamamını bekleme süresini azaltır.

## Gelecekte sesli konuşma

Akış: mikrofon → konuşma etkinliği algılama (VAD) → konuşmayı yazıya çevirme → yerel yönlendirme/hafıza veya metin modeli → kısa cümle parçaları → ses üretimi → ESP32 ses tamponu/hoparlör.

- Başlangıç adayı `faster-whisper`: CPU `int8` ve VAD desteği var [7]. Türkçe çok dilli modelle denenmeli; resmî depodaki başka donanım benchmark'ları bu bilgisayara taşınmamalı. Kütüphanenin sonuçları iterator olarak vermesi tek başına canlı mikrofon akışı sağlamaz; segmentleme ve uç nokta algılama ayrıca gerekir.
- `sherpa-onnx`, yerel ses tanıma ve akış altyapısı için diğer araştırma adayı [8]. Uygun Türkçe model ve Windows desteği model bazında doğrulanmalı.
- `Piper`, yerel ses üretimi adayı [9]. Türkçe sesin kalite, hız ve model lisansı ayrıca incelenmeli. Sık kullanılan kısa yanıtların sesi önceden üretilebilir.
- Metnin tamamını beklemeden ilk anlamlı cümle seslendirilmeli; tek tek token seslendirmek yerine noktalama/uzunluk eşiğiyle tamponlanmalı.
- Kullanıcı araya girince model üretimi ve ses kuyruğu iptal edilmeli. Gerçek eşzamanlı konuşma için hoparlör sesinin mikrofonu tetiklemesi, yankı giderme ve kesme davranışı test edilmeli. İlk bas-konuş sürümünde oynatma sırasında mikrofonu duraklatmak daha sınırlı bir başlangıçtır.
- Kamera analizinin uzun CPU işi, ses ve yerel komutları kilitlememeli. Ayrı görevler olsa bile aynı CPU/RAM için rekabet edeceğinden kaynak sınırları ve sohbet önceliği ölçülmeli.

## Ölçüm ve uygulama sırası

1. Önce aşama sürelerini kaydet: kamera, ön işleme, model yükleme, ilk görünür token, üretim ve toplam. Ollama `load_duration`, `prompt_eval_duration`, `eval_duration` alanlarını sağlıyor [1]; görsel kodlama bunlardan bağımsız bir alanmış gibi raporlanmamalı. İlk token süresi uygulamada ayrıca ölçülmeli.
2. Görüntü zorunluluğu olmayan metin sohbet yolu ekle; küçük adayları aynı Türkçe sorularla karşılaştır. Soğuk/sıcak, kısa/uzun bağlam ve yüz kontrolü açık/kapalı koşullarını ayır.
3. Yerel komut yönlendiricisi, SQLite tercih hafızası ve açık bilgi sorularına doğrudan cevap ekle.
4. Yanıt akışı, aktif oturumda ön yükleme ve GPU/backend karşılaştırmasını yap.
5. Mikrofon ve hoparlör aşamalarında VAD, metin tanıma, ilk ses, kesme ve oynatma tamponlarını ayrı ölç.

Başlangıç mühendislik hedefleri: metin alındıktan sonra yerel cevapta 100 ms altı; kullanıcı konuşmasını bitirdikten sonra serbest sohbette ilk anlamlı ses için 1–2 saniye. Bunlar ölçülmüş sonuç veya garanti değil. VAD beklemesi, ses tanıma, yönlendirme, ilk model çıktısı, ses üretimi ve ESP32 tamponu bu bütçeye birlikte dahil. “Düşünüyorum” sesi bu hedefte anlamlı cevap sayılmamalı. p50/p95 süreleri, doğruluk, gereksiz model çağrısı oranı ve önbelleğin eski cevap verme hataları birlikte izlenmeli.

Mevcut donanımda küçük metin modeli bu hedefe ulaşamazsa, ölçümlere göre daha güçlü yerel donanım veya isteğe bağlı uzak model değerlendirilir. Bu araştırma bulut bağlantısı eklemez; mevcut yerel çalışma tercihi korunur.

## Ollama kullanan somut robot örnekleri

Kullanıcının devam sorusu üzerine 1 Kasım 2026'da proje README'leri ve geliştirici mimari yazısı ayrıca incelendi. Robotlar yerelde kurulup çalıştırılmadı; aşağıdakiler geliştiricilerin belgelediği davranışlardır.

| Proje | Belgelenen mimari | WALL-A için çıkarım |
| --- | --- | --- |
| [reachy-mini-agent](https://github.com/thc1006/reachy-mini-agent) | Whisper → Ollama Qwen3 → ses/hareket çıktısı. YuNet ve MediaPipe ayrı algılama yapıyor. Görüntü modeli 10 saniyede bir sahne özeti üretiyor. Tekrarlanan sesler diskte önbelleğe alınıyor. | Görsel gözlemi zaman damgasıyla tutmak ve konuşmadan ayırmak; aynı kısa sesleri tekrar üretmemek. |
| [Reachy Claw](https://github.com/suharvest/reachy-claw) | Ayrı konuşma, hareket ve yüz takibi modülleri; VAD → STT → Ollama → cümle ayırıcı → TTS. İhtiyaç üzerine kamera aracı ve konuşmanın kesilmesi destekleniyor. README eski çalışma yolu ile güncel gateway tabanlı yolu ayırıyor. | Ses/algılama bileşenlerini değiştirilebilir kurmak; Türkçe modelleri ayrıca doğrulamak. |
| [Friendly / Argo](https://www.myargoquest.com/blog/how-we-built-friendly-reachy-mini) | Donanım ve asistan ayrı süreçlerde. Yerel Ollama modeli selamlaşmayı cevaplıyor, kapsamlı talepleri buluttaki Claude'a iletiyor. Hafıza SQLite; hatırlama araçları ve cümle bazlı ses üretimi var. | Hızlı karşılık ve kapsamlı cevap yollarını ayırmak; donanım bağlantısının sohbeti kilitlemesini önlemek. |

Sınırlar: reachy-mini-agent GPU ≥8 GB öneriyor. Reachy Claw'ın Jetson Orin NX üzerinde bildirdiği yaklaşık 110 ms yalnızca ASR/TTS aşamalarına ait; LLM dahil süreyi ayrı veriyor. Friendly, M1 Max üzerinde ilk ana model metnini transkripsiyon sonrasından 2,4–5,3 saniye sonra ölçmüş; konuşma bitişini bekleme ve transkripsiyon bunun dışında. Friendly'nin hafıza ve kesme özellikleri yazı tarihinde gerçek robotta henüz denenmemiş. Bu projelerdeki rakamlar MX450 veya Türkçe için doğrulanmış sonuçlar değil.

Bu örneklerden çıkardığım WALL-A önerisi: ESP32 cihaz işlerini yürütür; bilgisayarda hızlı yerel komut/hafıza yolu, metin sohbeti, gerektiğinde görüntü analizi ve ses üretimi ayrı görevler olur. Periyodik pahalı VLM sorgusunu mevcut CPU'da doğrudan kopyalamak yerine istek/olay üzerine çalıştırmak daha uygun bir ilk denemedir.

## Kaynaklar

1. [Ollama Chat API: streaming, düşünme ve süre alanları](https://docs.ollama.com/api/chat)
2. [Ollama FAQ: ön yükleme, keep_alive, CPU/GPU yerleşimi ve eşzamanlılık](https://docs.ollama.com/faq)
3. [Ollama donanım desteği: NVIDIA ve Vulkan](https://docs.ollama.com/gpu)
4. [Redis: LLM cevaplarının anlamsal önbelleği](https://redis.io/docs/latest/develop/ai/redisvl/user_guide/how_to_guides/llmcache/)
5. [Ollama Qwen3 0.6B](https://ollama.com/library/qwen3:0.6b)
6. [Ollama Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b)
7. [SYSTRAN faster-whisper](https://github.com/SYSTRAN/faster-whisper)
8. [sherpa-onnx resmî belgeleri](https://k2-fsa.github.io/sherpa/onnx/index.html)
9. [Open Home Foundation Piper](https://github.com/OHF-Voice/piper1-gpl)
