import pandas as pd
import json
import os

# Excel dosyasını oku (V2 kataloğu)
excel_filename = "Progen_Analitik_Fiyat_Listesi_2026_V2.xlsx"
if os.path.exists(excel_filename):
    df = pd.read_excel(excel_filename, sheet_name="Türkçe Katalog", header=3)
    print(f"Excel başarıyla okundu. Toplam satır: {len(df)}")
else:
    print("Excel dosyası bulunamadı! Lütfen dosyayı bu klasöre kopyalayın.")

products_list = []
for idx, row in df.iterrows():
    if pd.isna(row.iloc[1]) or not str(row.iloc[1]).startswith("CHI"):
        continue
    
    name = str(row.iloc[3])
    specs = str(row.iloc[4])
    price = float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0.0
    
    # Chemdor markalı profesyonel görsel ataması (Kategoriye göre)
    n_lower = name.lower()
    if 'acid' in n_lower or 'asit' in n_lower:
        img_url = "https://images.unsplash.com/photo-1603126857599-f6e157fa2fe6?auto=format&fit=crop&w=400&q=80"
    elif 'buffer' in n_lower or 'tampon' in n_lower:
        img_url = "https://images.unsplash.com/photo-1579165466741-7f35e4755660?auto=format&fit=crop&w=400&q=80"
    elif 'acetone' in n_lower or 'aseton' in n_lower or 'alcohol' in n_lower or 'alkol' in n_lower:
        img_url = "https://images.unsplash.com/photo-1563770660941-20978e870e26?auto=format&fit=crop&w=400&q=80"
    elif 'salt' in n_lower or 'tuz' in n_lower or 'chloride' in n_lower or 'sulfate' in n_lower:
        img_url = "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=400&q=80"
    else:
        img_url = "https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=400&q=80"

    p = {
        "id": str(row.iloc[1]),
        "name": name,
        "specifications": specs,
        "min_order": str(row.iloc[5]),
        "unit": str(row.iloc[6]),
        "price": price,
        "image": img_url,
        "brand": "Chemdor",
        "description": f"Chemdor® yüksek saflık standartlarında üretilmiştir. {name} ({specs}). Endüstriyel ve analitik laboratuvar uygulamaları için özel olarak sertifikalandırılmıştır.",
        "safety": "Kişisel koruyucu ekipman kullanın. Serin, kuru ve havalandırılan alanda saklayın."
    }
    products_list.append(p)

# products.json olarak kaydet
with open("products.json", "w", encoding="utf-8") as f:
    json.dump(products_list, f, ensure_ascii=False, indent=2)

print(f"products.json dosyası {len(products_list)} ürünle başarıyla oluşturuldu!")