import os
import json
import time
import requests
from io import BytesIO
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from groq import Groq

# Şifreleri koddan değil, GitHub'ın gizli kasasından çekiyoruz!
api_keys_env = os.environ.get("GROQ_API_KEYS", "")
GROQ_KEYS = [k.strip() for k in api_keys_env.split(",")] if api_keys_env else []

print("[*] Bulut Ajanı Başlatılıyor... Groq Modelleri Test Ediliyor...")
try:
    client = Groq(api_key=GROQ_KEYS[0])
    ACTIVE_MODEL = "llama-3.1-8b-instant" # Metin ve çoklu dil için en ideal Llama modeli
except Exception:
    ACTIVE_MODEL = "llama3-70b-8192"

def get_ai_multilingual_content(product_name, specs, key_index):
    """3 dilde (EN, TR, RU) Thermo Fisher standartlarında içerik üretir."""
    client = Groq(api_key=GROQ_KEYS[key_index % len(GROQ_KEYS)])
    
    prompt = f"""
    Sen global bir kimya firması olan Chemdor için çalışan uzman bir farmakolog ve endüstriyel kimyagersin. 
    Ürün: {product_name}
    Özellik: {specs}
    
    Görevin bu ürün için Thermo Fisher standartlarında kusursuz bir JSON üretmektir.
    Lütfen bana SADECE geçerli bir JSON formatında şu bilgileri dön:
    {{
        "tr": {{
            "properties": "Fiziksel ve kimyasal özellikleri (yoğunluk, kaynama noktası, CAS vb.)",
            "usage": "Farmakolojik ve endüstriyel kullanım alanları, reaksiyon mekanizmaları hakkında en az 150-200 kelimelik akademik açıklama.",
            "safety": "Saklama ve güvenlik koşulları."
        }},
        "en": {{
            "properties": "Physical and chemical properties...",
            "usage": "Academic explanation of pharmacological and industrial usage (min 150-200 words)...",
            "safety": "Safety and storage conditions."
        }},
        "ru": {{
            "properties": "Физико-химические свойства...",
            "usage": "Академическое объяснение фармакологического и промышленного применения...",
            "safety": "Условия хранения и безопасности."
        }},
        "tags": ["seo_tag1", "seo_tag2", "seo_tag3"]
    }}
    Başka hiçbir metin yazma, sadece JSON.
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=ACTIVE_MODEL,
            temperature=0.4
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"[-] AI Hatası ({product_name})")
        return {"tr": {"usage": "Veri hazırlık aşamasında."}, "en": {"usage": "Data in preparation."}, "ru": {"usage": "Данные в стадии подготовки."}, "tags": []}

def create_chemdor_image_with_logo(code, name, img_path):
    """Chemdor web sitesinden logoyu çeker ve şişe üzerine entegre eder."""
    img = Image.new('RGB', (600, 600), color=(245, 247, 250))
    d = ImageDraw.Draw(img)
    
    # Şişe Çizimi
    d.rectangle([200, 150, 400, 500], fill=(255, 255, 255), outline=(200, 200, 200), width=4)
    d.rectangle([270, 100, 330, 150], fill=(50, 50, 50))
    
    # Etiket Arka Planı
    d.rectangle([200, 220, 400, 450], fill=(240, 240, 240), outline=(200, 200, 200), width=1)
    
    # Canlı logoyu çek ve yapıştır
    try:
        response = requests.get("https://www.chemdor.com/images/logo.jpg", timeout=5)
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        logo = logo.resize((150, int(150 * logo.height / logo.width)))
        img.paste(logo, (225, 230), logo)
    except Exception:
        # Logo çekilemezse metin yaz
        d.text((250, 250), "CHEMDOR", fill="black")

    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
        font_small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    short_name = name[:20] + ".." if len(name) > 20 else name
    d.text((210, 320), short_name, fill=(30, 30, 30), font=font_large)
    d.text((210, 360), f"Ref: {code}", fill=(100, 100, 100), font=font_small)
    d.text((210, 400), "Research Grade", fill=(180, 40, 40), font=font_small)
    
    img.save(img_path)

def main():
    if not GROQ_KEYS:
        print("[-] HATA: GROQ_API_KEYS bulunamadı. Lütfen GitHub Secrets ayarlarını yapın.")
        return

    os.makedirs("static/images/products", exist_ok=True)
    df = pd.read_excel("Progen_Analitik_Fiyat_Listesi_2026_V2.xlsx", sheet_name="Türkçe Katalog", header=3)
    
    products_list = []
    key_index = 0
    count = 0
    
    for idx, row in df.iterrows():
        code = str(row.iloc[1])
        if pd.isna(row.iloc[1]) or not code.startswith("CHI"):
            continue
            
        name = str(row.iloc[3])
        specs = str(row.iloc[4])
        price = float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0.0
        
        print(f"[{count+1}] İşleniyor: {name}...")
        
        ai_data = get_ai_multilingual_content(name, specs, key_index)
        key_index += 1
        
        img_filename = f"chemdor_{code.replace('.', '_')}.png"
        img_path = f"static/images/products/{img_filename}"
        create_chemdor_image_with_logo(code, name, img_path)
        
        p = {
            "id": code,
            "name": name,
            "price": price,
            "image": img_path,
            "brand": "Chemdor®",
            "content": ai_data
        }
        products_list.append(p)
        count += 1
        time.sleep(1)

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products_list, f, ensure_ascii=False, indent=2)
        
    print(f"\n[*] Başarılı! {count} ürün 3 dilde işlendi.")

if __name__ == "__main__":
    main()