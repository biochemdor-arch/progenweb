import os
import json
import time
import requests
from io import BytesIO
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from groq import Groq

api_keys_env = os.environ.get("GROQ_API_KEYS", "")
GROQ_KEYS = [k.strip() for k in api_keys_env.split(",")] if api_keys_env else []

def get_active_model():
    """Stabil Llama modelini zorunlu kılar."""
    return "llama-3.1-8b-instant" if GROQ_KEYS else None

ACTIVE_MODEL = get_active_model()

def get_ai_multilingual_content(product_name, specs, key_index):
    """3 dilde, derinlemesine (min 300 kelime) akademik içerik üretir."""
    client = Groq(api_key=GROQ_KEYS[key_index % len(GROQ_KEYS)])
    
    prompt = f"""
    Sen global bir kimya firması olan Chemdor için çalışan uzman bir farmakolog ve endüstriyel kimyagersin. 
    Ürün: {product_name}
    Özellik: {specs}
    
    KURALLAR:
    1. 'usage' (Kullanım Alanı) kısmı her dil için EN AZ 300 KELİME uzunluğunda, son derece detaylı, akademik ve profesyonel olmalıdır. Farmakolojik reaksiyon mekanizmalarını ve endüstriyel üretim aşamalarını detaylandır.
    2. SADECE aşağıdaki JSON formatında çıktı ver. Markdown (```json) kullanma.
    
    {{
        "tr": {{
            "properties": "Fiziksel ve kimyasal özellikleri (Yoğunluk, kaynama noktası, CAS, moleküler ağırlık vb.)",
            "usage": "Farmakolojik ve endüstriyel kullanım alanları, reaksiyon mekanizmaları hakkında detaylı akademik makale (MİNİMUM 300 KELİME).",
            "safety": "Saklama, taşıma ve güvenlik koşulları."
        }},
        "en": {{
            "properties": "Physical and chemical properties...",
            "usage": "Detailed academic article on pharmacological and industrial applications (MINIMUM 300 WORDS)...",
            "safety": "Safety and storage conditions."
        }},
        "ru": {{
            "properties": "Физико-химические свойства...",
            "usage": "Подробная академическая статья о фармакологическом и промышленном применении (МИНИМУМ 300 СЛОВ)...",
            "safety": "Условия хранения и безопасности."
        }},
        "tags": ["chemical_synthesis", "industrial_grade", "analytical_reagent"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=ACTIVE_MODEL,
            temperature=0.5
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"[-] AI Hatası ({product_name}): {e}")
        return {"tr": {"usage": "Veri hazırlanıyor...", "props": "-", "safety": "-"}, "en": {"usage": "Data pending...", "props": "-", "safety": "-"}, "ru": {"usage": "Ожидание данных...", "props": "-", "safety": "-"}, "tags": []}

def create_chemdor_image_with_logo(code, name, img_path):
    """Thermo Fisher tarzı, kurumsal ve şık bir ürün veri etiketi (Data Label) tasarlar."""
    img = Image.new('RGB', (800, 800), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    
    # Kurumsal Çerçeve ve Üst Bant
    d.rectangle([20, 20, 780, 780], outline=(230, 230, 230), width=2)
    d.rectangle([20, 20, 780, 100], fill=(0, 51, 160)) # Thermo Laciverti
    d.rectangle([20, 100, 780, 110], fill=(204, 0, 0)) # Thermo Kırmızısı
    
    # Canlı logoyu çek ve ortaya yerleştir
    try:
        response = requests.get("[https://www.chemdor.com/images/logo.jpg](https://www.chemdor.com/images/logo.jpg)", timeout=5)
        logo = Image.open(BytesIO(response.content)).convert("RGBA")
        logo = logo.resize((200, int(200 * logo.height / logo.width)))
        img.paste(logo, (300, 180), logo)
    except Exception:
        # Logo inmezse şık bir fontla yaz
        d.text((320, 200), "CHEMDOR", fill=(0, 51, 160))

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 35)
        font_sub = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
    except:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # Metinleri şık bir şekilde ortalayarak yaz
    short_name = name[:40] + ".." if len(name) > 40 else name
    d.text((80, 400), short_name, fill=(50, 50, 50), font=font_title)
    d.text((80, 470), f"Product Reference: {code}", fill=(100, 100, 100), font=font_sub)
    d.text((80, 520), "Grade: Analytical & Research Grade", fill=(0, 51, 160), font=font_sub)
    d.text((80, 570), "Quality: ISO Certified, High Purity", fill=(100, 100, 100), font=font_sub)
    
    img.save(img_path)

def main():
    if not GROQ_KEYS:
        print("[-] HATA: GROQ_API_KEYS bulunamadı.")
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
        
        print(f"[{count+1}] Mükemmelleştiriliyor: {name}...")
        
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
        
    print(f"\n[*] Başarılı! {count} ürün 3 dilde ve yeni görsellerle işlendi.")

if __name__ == "__main__":
    main()