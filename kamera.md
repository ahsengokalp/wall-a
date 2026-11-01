# Robotun kamera ve görsel zekâ hedefleri

Bu belge, masaüstü robotunun kamerayla kazanmasını istediğimiz yetenekleri tanımlar. Buradaki maddeler hedeflerdir; henüz uygulanmış özellikler değildir. Genel geliştirme sırası için `plan.md` kullanılacak.

## 1. İnsan varlığını ve etkileşim niyetini anlama

- Kameranın karşısında insan olup olmadığını algılamak.
- Birinin masaya geldiğini, yaklaştığını veya uzaklaştığını fark etmek.
- Kişinin robota yönelmesi gibi görsel ipuçlarından etkileşim başlatmak isteyebileceğini tahmin etmek.
- İleride mikrofon eklendiğinde görsel ipuçlarını sesle birleştirerek robotla konuşulup konuşulmadığını değerlendirmek.
- OLED eklendiğinde gözlerini kişiye doğru yönlendirmek veya karşılama ifadesi göstermek.
- Motorlar eklendiğinde başını kişiye çevirmek.

**Örnek:** Kullanıcı masaya oturduğunda robot onu fark eder ve uygun bir karşılama tepkisi verir. Görsel ipuçları, kişinin niyetini kesin bildiği şeklinde yorumlanmaz.

## 2. Kullanıcıyı ve tanıştırılan arkadaşları tanıma

- Kullanıcının yüzünü tanıtma işlemiyle kaydetmek ve sonraki karşılaşmalarda tanımak.
- Kullanıcının tanıştırdığı arkadaşları adlarıyla ilişkilendirmek ve tekrar geldiklerinde tanımak.
- Aynı anda görünen birden fazla kişiyi ayrı ayrı takip edebilmek.
- Tanıma yeterince güvenilir değilse kişiyi “bilinmeyen” olarak değerlendirmek; isim uydurmamak.
- Yanlış eşleşmeleri düzeltmek, kayıtlı kişileri listelemek ve silmek için Python arayüzünde kontroller sunmak.
- Kişi kaydını açık bir tanıştırma işlemiyle yapmak; yüz kayıtlarını varsayılan olarak bilgisayarda yerel saklamak.

**Örnek:** Kullanıcı “Bu benim arkadaşım Ayşe” diyerek veya arayüzden kayıt başlatarak kişiyi tanıtır. Robot sonraki karşılaşmada yeterli güvenle eşleşirse Ayşe'yi adıyla karşılayabilir.

## 3. Hareketleri ve el işaretlerini anlama

- El sallamayı algılayıp selam vermek.
- Açık avuç gibi önceden belirlenmiş bir dur işaretini algılamak.
- Parmağın işaret ettiği yönü ve mümkün olduğunda hedef nesneyi tahmin etmek.
- Sesli komut gerektirmeyen, küçük ve açık bir hareket sözlüğü oluşturmak.
- Tek bir belirsiz kare yerine kısa süreli gözlemlerle hareketi doğrulamak; aynı hareketin sürekli tekrar tetiklenmesini önlemek.

**Örnek:** Kullanıcı el salladığında robot selam verir. Hareket sistemi eklendiğinde dur işareti robotun hareketini durdurmak için kullanılabilir; ayrıca arayüzde bağımsız bir durdurma kontrolü bulunur.

## 4. Duruş ve ergonomi farkındalığı

- Kullanıcı isterse çalışma sırasında duruşunu belirli aralıklarla değerlendirmek.
- Ekrana veya kameraya olağandan fazla yaklaşmayı ve uzun süre korunmuş olumsuz duruş örüntülerini fark etmeye çalışmak.
- Kamera konumu ve kullanıcının normal oturuşu için başlangıç ayarı yapmak; yalnızca yüz yakınlığını kesin mesafe ölçümü saymamak.
- Tek bir görüntüye dayanarak uyarmak yerine belirli süre devam eden durumları değerlendirmek.
- Hoparlör eklendiğinde sesli hatırlatma, öncesinde Python arayüzünde bildirim sunmak.
- İzlemeyi açma/kapatma, hatırlatma sıklığı ve bildirimleri erteleme ayarları sağlamak.
- Bu özelliği tıbbi değerlendirme yerine günlük duruş farkındalığı ve hatırlatma amacıyla kullanmak.

**Örnek:** Kullanıcı uzun süre öne eğilmiş halde kaldığında robot, ayarlanan sıklığı aşmadan oturuşunu değiştirmesini hatırlatır.

## 5. Çevreyi anlama ve ileride hareketi destekleme

- Masadaki nesneleri ve genel sahneyi tanımlamak; kullanıcının görüntüyle ilgili sorularını cevaplamak.
- İleride engelleri, masa kenarlarını, kapıları ve geçiş alanlarını algılamayı denemek.
- Baş hareketi ile masada/zeminde yer değiştirmeyi ayrı geliştirme adımları olarak ele almak.
- Fiziksel hareket eklenirken uygun mesafe, kenar algılama ve hareket geri bildirimi sensörlerini ayrıca planlamak.
- Serbest metin üreten görsel modelin yorumunu tek başına güvenli navigasyon veya motor komutu kaynağı olarak kullanmamak.

**Örnek:** İlk sürüm “Masamda ne görüyorsun?” sorusunu cevaplar. İleride hareketli sürüm, doğrulanmış sensör verileri ve hareket sınırlarıyla engellere tepki verir.

## Uygulama yaklaşımı

- **ESP32-S3:** Kamera görüntüsünü alır ve Wi-Fi üzerinden bilgisayara iletir.
- **Python sunucusu ve kontrol arayüzü:** Kamera önizlemesi, tek fotoğraf alma, özellikleri açma/kapatma, kişi tanıtma ve sonuçları gösterme işlevlerini sağlar.
- **Yerel Ollama ve görüntü destekleyen model:** Sahne hakkında soru cevaplama ve genel görsel yorumlama için kullanılır. İlk sürümde model eğitimi hedeflenmez.
- **Göreve özel görüntü işleme bileşenleri:** İnsan/yüz algılama, yüz eşleştirme, el işareti, vücut duruşu ve takip için uygun araçlar ayrıca seçilir. Her kamera karesi büyük görsel modele gönderilmez.
- **Zaman içinde değerlendirme:** Kişi, hareket ve duruş sonuçları mümkün olduğunda birkaç gözlem üzerinden doğrulanır; belirsizlik arayüzde belirtilir.
- **Veri yönetimi:** Sürekli video kaydı varsayılan olmayacak. Fotoğraf ve kişi kayıtlarının saklanması/silinmesi arayüzden açıkça yönetilecek.

## Geliştirme sırası

1. Kamera bağlantısını doğrula ve Python arayüzünde gerçek görüntüyü göster.
2. Ollama ile tek fotoğrafa soru sorma özelliğini tamamla.
3. İnsan/yüz algılama ve basit takip ekle.
4. Kullanıcı ve arkadaş tanıtma/tanıma akışını ekle.
5. El sallama ve açık avuç gibi sınırlı el işaretlerini ekle.
6. İsteğe bağlı duruş takibi ve hatırlatmaları ekle.
7. OLED, mikrofon ve hoparlör aşamaları tamamlandıkça görsel yetenekleri karakter tepkileriyle birleştir.
8. Motorlar ve ek sensörler alındığında baş yönlendirme, ardından ihtiyaç varsa yer değiştirme üzerinde çalış.

Modeller, başarı eşikleri ve çalışma hızları; bilgisayarın donanımı, kameranın görüş açısı, ışık koşulları ve gerçek denemeler sonucunda belirlenecek.
