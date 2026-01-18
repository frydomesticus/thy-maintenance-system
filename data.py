"""
THY Filo Veri Üretici Modülü
============================
Bu modül, Türk Hava Yolları'nın gerçek filo yapısına uygun
sentetik bakım verisi üretir.

Kaynak: THY 2024 Filo Verileri (yaklaşık değerler)
"""

import pandas as pd
import random
from datetime import datetime, timedelta


def generate_thy_data():
    """
    THY filosu için gerçekçi bakım geçmişi verileri üretir.
    
    Returns:
        pd.DataFrame: Filo bakım verileri
    """
    
    # THY Filo Yapısı (Gerçek veriler baz alınmıştır - 2024)
    fleet_structure = {
        "Airbus A319-100":  {"count": 6,  "prefix": "TC-JL", "category": "narrow"},
        "Airbus A320-200":  {"count": 14, "prefix": "TC-JP", "category": "narrow"},
        "Airbus A320 NEO":  {"count": 10, "prefix": "TC-NB", "category": "narrow"},
        "Airbus A321-200":  {"count": 20, "prefix": "TC-JR", "category": "narrow"},
        "Airbus A321 NEO":  {"count": 15, "prefix": "TC-LT", "category": "narrow"},
        "Airbus A330-200":  {"count": 12, "prefix": "TC-JN", "category": "wide"},
        "Airbus A330-300":  {"count": 37, "prefix": "TC-JO", "category": "wide"},
        "Airbus A350-900":  {"count": 25, "prefix": "TC-LG", "category": "wide"},
        "Boeing 737-800":   {"count": 30, "prefix": "TC-JV", "category": "narrow"},
        "Boeing 737-900ER": {"count": 15, "prefix": "TC-JY", "category": "narrow"},
        "Boeing 737 MAX 8": {"count": 34, "prefix": "TC-LC", "category": "narrow"},
        "Boeing 777-300ER": {"count": 34, "prefix": "TC-JJ", "category": "wide"},
        "Boeing 787-9":     {"count": 23, "prefix": "TC-LL", "category": "wide"},
        "Boeing 777F":      {"count": 8,  "prefix": "TC-LJ", "category": "cargo"}
    }

    data = []
    today = datetime.now()

    for model, info in fleet_structure.items():
        for i in range(1, info["count"] + 1):
            # Benzersiz kuyruk numarası oluştur
            tail_number = f"{info['prefix']}{chr(65 + (i % 26))}{random.randint(10, 99)}"
            
            # Geniş gövdeler (Long Haul) daha çok uçar
            if info["category"] in ["wide", "cargo"]:
                total_fh = random.randint(5000, 50000)
                avg_flight_time = random.uniform(5, 10)
            else:  # Dar gövdeler (Short Haul)
                total_fh = random.randint(2000, 35000)
                avg_flight_time = random.uniform(1.5, 3.5)
            
            # Döngü sayısı = Toplam saat / Ortalama uçuş süresi
            total_fc = int(total_fh / avg_flight_time)
            
            # Uçağın yaşını teslim tarihinden hesapla (2-15 yıl arası)
            years_in_service = random.randint(2, 15)
            delivery_date = today - timedelta(days=years_in_service * 365)
            
            # Rastgele son bakım durumu
            check_types = ["A", "B", "C"]
            last_check = random.choice(check_types)
            
            # Bakım tipine göre son bakımdan bu yana FH
            if last_check == "A":
                fh_since_check = random.randint(50, 580)   # A Check limiti: 600 FH
                fc_since_check = random.randint(30, 380)   # A Check limiti: 400 FC
            elif last_check == "B":
                fh_since_check = random.randint(100, 2000)
                fc_since_check = random.randint(80, 1200)
            else:  # C Check
                fh_since_check = random.randint(500, 5500) # C Check limiti: 6000 FH
                fc_since_check = random.randint(300, 3500)
            
            # Son bakım tarihi (10-600 gün önce)
            last_maint_date = today - timedelta(days=random.randint(10, 600))
            
            # Son D Check tarihi (Heavy Maintenance)
            # D Check her 6-10 yılda bir yapılır
            years_since_d_check = random.randint(0, 6)
            last_d_check = today - timedelta(days=years_since_d_check * 365 + random.randint(0, 180))
            
            data.append({
                "Kuyruk No": tail_number,
                "Model": model,
                "Kategori": info["category"].upper(),
                "Teslim Tarihi": delivery_date.strftime("%Y-%m-%d"),
                "Toplam Uçuş Saati (FH)": total_fh,
                "Toplam Döngü (FC)": total_fc,
                "Son Bakım Tipi": last_check,
                "Son Bakımdan Beri FH": fh_since_check,
                "Son Bakımdan Beri FC": fc_since_check,
                "Son Bakım Tarihi": last_maint_date.strftime("%Y-%m-%d"),
                "Son D-Check Tarihi": last_d_check.strftime("%Y-%m-%d"),
                "Günlük Ort. FH": round(random.uniform(6, 14), 1),
                "Durum": random.choice(["Aktif", "Aktif", "Aktif", "Bakımda"])
            })

    df = pd.DataFrame(data)
    
    # Kuyruk numarasına göre sırala
    df = df.sort_values("Kuyruk No").reset_index(drop=True)
    
    return df


def get_fleet_summary(df: pd.DataFrame) -> dict:
    """
    Filo özet istatistiklerini hesaplar.
    
    Args:
        df: Filo veri DataFrame'i
        
    Returns:
        dict: Özet istatistikler
    """
    return {
        "Toplam Uçak": len(df),
        "Aktif Uçak": len(df[df["Durum"] == "Aktif"]),
        "Bakımda": len(df[df["Durum"] == "Bakımda"]),
        "Dar Gövde": len(df[df["Kategori"] == "NARROW"]),
        "Geniş Gövde": len(df[df["Kategori"] == "WIDE"]),
        "Kargo": len(df[df["Kategori"] == "CARGO"]),
        "Toplam FH": df["Toplam Uçuş Saati (FH)"].sum(),
        "Modeller": df["Model"].nunique()
    }


# Test için
if __name__ == "__main__":
    df = generate_thy_data()
    print(f"Toplam {len(df)} uçak üretildi.\n")
    print(df.head(10).to_string())
    print("\n--- Filo Özeti ---")
    for k, v in get_fleet_summary(df).items():
        print(f"{k}: {v:,}" if isinstance(v, int) else f"{k}: {v}")
