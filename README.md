# MG4 Home Assistant Bridge

MG4 arabasındaki uygulamanın verilerini Home Assistant’ta cihaz ve sensör olarak gösterir.

Uygulama arabada çalışır; bu paket sadece **Home Assistant** tarafıdır.

---

## Ne işe yarar?

- Şarj %, menzil, kilometre, dış sıcaklık  
- Lastik basınçları  
- Şarj durumu / güç / kalan süre (şarjdayken)  
- Konum  

Veriyi araba Wi‑Fi üzerinden HA’ya **kendisi gönderir**. HA arabayı aramaz.

---

## Kurulum (HACS)

1. Bu repoyu HACS’e **Custom repository** olarak ekle (Integration).
2. **MG4 Home Assistant Bridge** indir.
3. Home Assistant’ı yeniden başlat.
4. **Entegrasyon ekle** → MG4 Home Assistant Bridge.
5. İsim ve **öneki** yaz (arabadaki önek ile aynı olmalı).

---

## Elle kurulum

`custom_components/mg4_bridge` klasörünü şuraya kopyala:

`config/custom_components/mg4_bridge/`

Sonra HA’yı yeniden başlat ve entegrasyonu ekle.

---

## Arabayla eşleştirme

1. Arabada uygulamaya HA adresini ve token’ı kaydet.
2. Önek iki tarafta da aynı olsun.
3. Wi‑Fi varken uygulama otomatik veri yollar.

Token: HA → profil → **Güvenlik** → Long-lived access tokens.

---

## Sorun olursa

- Önek uyuşmuyorsa sensörler güncellenmez.
- HA adresi dışarıdan açılmıyorsa araba ev dışı Wi‑Fi’den yazamaz.
- Entegrasyon yoksa uygulama yine de basit sensör yazabilir; cihaz + kalıcılık için bu paket gerekir.

Android uygulama: [merthankaraman/mg-home-assistant](https://github.com/merthankaraman/mg-home-assistant)
