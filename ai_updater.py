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

ACTIVE_MODEL = "llama3-70b-8192"

def get_ai_multilingual_content(product_name, specs, api_key):
    client = Groq(api_key=api_key)
    prompt = f"""
    Sen Thermo Fisher tarzı global bir kimya firması olan Chemdor için baş farmakologsun.
    Ürün: {product_name} ({specs})
    
    GÖREV:
    1. Bu ürünün "kimyasal" (chemical) mı yoksa beher, cam, cihaz gibi "ekipman" (equipment) mı olduğunu belirle.
    2. 'usage' kısmı akademik ve detaylı olmalıdır.
    3. TÜRKÇE, İNGİLİZCE VE RUSÇA dillerini EKSİKSİZ ÜRET.
    
    SADECE AŞAĞIDAKİ JSON FORMATINDA ÇIKTI VER, markdown (```json) veya ekstra metin asla kullanma:
    {{
        "type": "chemical",
        "properties_short": "Yogunluk: 1.05 g/cm3, CAS: 64-19-7",
        "tr": {{"properties": "Fiziksel ozellikler", "usage": "Farmakolojik ve endüstriyel kullanim alanlari hakkinda detayli aciklama...", "safety": "Güvenlik koşulları."}},
        "en": {{"properties": "Physical properties", "usage": "Detailed explanation of pharmacological and industrial applications...", "safety": "Safety conditions."}},
        "ru": {{"properties": "Свойства", "usage": "Подробное описание применения...", "safety": "Условия безопасности."}}
    }}
    """
    try:
        response = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=ACTIVE_MODEL, temperature=0.3)
        text = response.choices[0].message.content
        text = text.replace("```json", "").replace("```", "").strip()
        # JSON başlangıç ve bitiş süslü parantezlerini bul
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            parsed = json.loads(text[start:end+1])
            if "tr" in parsed and "en" in parsed and "ru" in parsed:
                return parsed
    except Exception as e:
        pass
    
    # AI hata verirse sistemi asla durdurma, profesyonel yedek ver
    return {
        "type": "chemical",
        "properties_short": f"Grade: Analytical | Ref: {product_name[:15]}",
        "tr": {"properties": specs, "usage": f"Chemdor markalı yüksek saflıkta {product_name}. Analitik ve laboratuvar süreçlerinde, endüstriyel sentezlerde ve Ar-Ge çalışmalarında güvenle kullanılır.", "safety": "Standart laboratuvar kişisel koruyucu ekipmanları kullanın."},
        "en": {"properties": specs, "usage": f"High purity {product_name} by Chemdor. Used in analytical processes, industrial synthesis and R&D applications.", "safety": "Use standard laboratory PPE."},
        "ru": {"properties": specs, "usage": f"Высокочистый продукт {product_name} от Chemdor. Применяется в аналитических процессах и промышленности.", "safety": "Используйте средства индивидуальной защиты."}
    }

def create_smart_image(code, name, product_type, props_short, img_path):
    bg_url = "[https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=80&w=800](https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?q=80&w=800)" if product_type == "equipment" else "[https://images.unsplash.com/photo-1584362917165-526a968579e8?q=80&w=800](https://images.unsplash.com/photo-1584362917165-526a968579e8?q=80&w=800)"
    
    try:
        bg_req = requests.get(bg_url, timeout=5)
        img = Image.open(BytesIO(bg_req.content)).convert("RGBA")
    except:
        img = Image.new('RGBA', (800, 800), color=(240, 244, 248, 255))
    
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(overlay)
    
    if product_type == "chemical":
        d.rectangle([50, 100, 750, 700], fill=(255, 255, 255, 245), outline=(204, 0, 0), width=5)
    else:
        d.rectangle([50, 550, 750, 700], fill=(255, 255, 255, 245), outline=(0, 51, 160), width=5)
        
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)

    try:
        logo_req = requests.get("[https://www.chemdor.com/images/logo.jpg](https://www.chemdor.com/images/logo.jpg)", timeout=5)
        logo = Image.open(BytesIO(logo_req.content)).convert("RGBA")
        logo = logo.resize((180, int(180 * logo.height / logo.width)))
        if product_type == "chemical":
            img.paste(logo, (310, 130), logo)
        else:
            img.paste(logo, (70, 570), logo)
    except:
        d.text((320, 150), "CHEMDOR", fill=(0, 51, 160))

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 20)
    except:
        font_title = font_sub = ImageFont.load_default()
    
    short_name = name[:40] + ".." if len(name) > 40 else name
    
    if product_type == "chemical":
        d.text((80, 280), short_name, fill=(30, 30, 30), font=font_title)
        d.text((80, 330), f"REF: {code}", fill=(204, 0, 0), font=font_sub)
        d.text((80, 370), "Analytical & Research Grade", fill=(0, 51, 160), font=font_sub)
        
        d.text((80, 430), "Properties / Özellikler:", fill=(100, 100, 100), font=font_sub)
        y_text = 470
        wrapped_props = textwrap.wrap(props_short, width=50)
        for line in wrapped_props:
            d.text((80, y_text), line, fill=(30, 30, 30), font=font_sub)
            y_text += 35
    else:
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

    processed_ids = {p["id"] for p in existing_data if p.get("content", {}).get("tr", {}).get("usage") and len(p["content"]["tr"]["usage"]) > 30}

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
            
        if new_processed >= 5: 
            break

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()