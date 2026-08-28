import os
import json
import time
import requests
from io import BytesIO
import textwrap
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from groq import Groq

api_keys_env = os.environ.get("GROQ_API_KEYS", "")
GROQ_KEYS = [k.strip() for k in api_keys_env.split(",")] if api_keys_env else []

ACTIVE_MODEL = "llama3-70b-8192" # 3 Dil ve 300 kelime yazabilen en zeki model

def get_ai_multilingual_content(product_name, specs, api_key):
    client = Groq(api_key=api_key)
    prompt = f"""
    Sen Thermo Fisher tarzı global bir kimya firması olan Chemdor için baş farmakologsun.
    Ürün: {product_name} ({specs})
    
    GÖREV:
    1. Bu ürünün "kimyasal" (chemical) mı yoksa beher, cam, cihaz gibi "ekipman" (equipment) mı olduğunu belirle.
    2. 'usage' (Kullanım Alanı) EN AZ 300 KELİME olmalı, reaksiyon mekanizmalarını detaylandırmalı.
    3. TÜRKÇE, İNGİLİZCE VE RUSÇA dillerini EKSİKSİZ ÜRET.
    
    SADECE AŞAĞIDAKİ JSON FORMATINDA ÇIKTI VER:
    {{
        "type": "chemical", // YADA "equipment"
        "properties_short": "Yoğunluk: ..., Erime Noktası: ..., CAS: ...", // Sadece kimyasallar için resme yazılacak özellikler.
        "tr": {{"properties": "Fiziksel özellikler detaylı...", "usage": "Min 300 kelimelik makale...", "safety": "Güvenlik..."}},
        "en": {{"properties": "Physical properties...", "usage": "Min 300 words article...", "safety": "Safety..."}},
        "ru": {{"properties": "Физико-химические свойства...", "usage": "Минимум 300 слов...", "safety": "Безопасность..."}}
    }}
    """
    try:
        response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=ACTIVE_MODEL, temperature=0.3)
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(content)
        # 3 dil kontrolü, eksikse reddet diğer döngüye kalsın
        if "tr" in parsed and "en" in parsed and "ru" in parsed:
            return parsed
        return None
    except Exception as e:
        print(f"[-] AI Hatası ({product_name})")
        return None

def create_smart_image(code, name, product_type, props_short, img_path):
    # Ekipmansa gerçek cam cihaz resmi, Kimyasalsa laboratuvar arka planı
    bg_url = "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=80&w=800" if product_type == "equipment" else "https://images.unsplash.com/photo-1584362917165-526a968579e8?q=80&w=800"
    
    try:
        bg_req = requests.get(bg_url, timeout=5)
        img = Image.open(BytesIO(bg_req.content)).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 800), color=(240, 244, 248, 255))
    
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(overlay)
    
    # Kimyasalsa ortaya büyük bir etiket çizip özellikleri yazıyoruz
    if product_type == "chemical":
        d.rectangle([50, 100, 750, 700], fill=(255, 255, 255, 245), outline=(204, 0, 0), width=5)
    else:
        # Cihazsa sadece alt kısma isim bandı çekiyoruz
        d.rectangle([50, 550, 750, 700], fill=(255, 255, 255, 245), outline=(0, 51, 160), width=5)
        
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)

    # Logoyu çek
    try:
        logo_req = requests.get("https://www.chemdor.com/images/logo.jpg", timeout=5)
        logo = Image.open(BytesIO(logo_req.content)).convert("RGBA")
        logo = logo.resize((180, int(180 * logo.height / logo.width)))
        
        if product_type == "chemical":
            img.paste(logo, (310, 130), logo)
        else:
            img.paste(logo, (70, 570), logo)
    except:
        d.text((320, 150), "CHEMDOR", fill=(0, 51, 160))

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    except:
        font_title = font_sub = ImageFont.load_default()
    
    short_name = name[:40] + ".." if len(name) > 40 else name
    
    if product_type == "chemical":
        d.text((80, 280), short_name, fill=(30, 30, 30), font=font_title)
        d.text((80, 330), f"REF: {code}", fill=(204, 0, 0), font=font_sub)
        d.text((80, 370), "Analytical & Research Grade", fill=(0, 51, 160), font=font_sub)
        
        # Fiziksel ve Kimyasal özellikleri resmin üstüne yaz
        d.text((80, 430), "Properties / Özellikler:", fill=(100, 100, 100), font=font_sub)
        y_text = 470
        wrapped_props = textwrap.wrap(props_short, width=50)
        for line in wrapped_props:
            d.text((80, y_text), line, fill=(30, 30, 30), font=font_sub)
            y_text += 35
    else:
        # Cihazlar için tasarım
        d.text((270, 580), short_name, fill=(30, 30, 30), font=font_title)
        d.text((270, 630), f"REF: {code} | Lab Equipment", fill=(204, 0, 0), font=font_sub)
    
    img.convert("RGB").save(img_path)

def main():
    if not GROQ_KEYS: return
    os.makedirs("static/images/products", exist_ok=True)
    
    existing_data = []
    if os.path.exists("products.json"):
        try:
            with open("products.json", "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except: pass

    processed_ids = {p["id"] for p in existing_data if p.get("content", {}).get("tr", {}).get("usage") and len(p["content"]["tr"]["usage"]) > 100}

    df = pd.read_excel("Progen_Analitik_Fiyat_Listesi_2026_V2.xlsx", sheet_name="Türkçe Katalog", header=3)
    new_processed = 0
    key_idx = 0

    for idx, row in df.iterrows():
        code = str(row.iloc[1])
        if pd.isna(row.iloc[1]) or not code.startswith("CHI"): continue
        if code in processed_ids: continue
            
        name, specs, price = str(row.iloc[3]), str(row.iloc[4]), float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0.0
        print(f"[*] İşleniyor: {name}...")
        
        ai_data = get_ai_multilingual_content(name, specs, GROQ_KEYS[key_idx % len(GROQ_KEYS)])
        key_idx += 1
        
        if ai_data:
            img_path = f"static/images/products/chemdor_{code.replace('.', '_')}.png"
            create_smart_image(code, name, ai_data.get("type", "chemical"), ai_data.get("properties_short", ""), img_path)
            
            p_dict = {"id": code, "name": name, "price": price, "image": img_path, "brand": "Chemdor®", "content": ai_data}
            existing_data = [p for p in existing_data if p["id"] != code] + [p_dict]
            new_processed += 1
            
        if new_processed >= 4: # Her 3 dakikada 4 ürün işleyip hızlıca siteye atar
            break

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()