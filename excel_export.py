"""
THY Maintenance System - Excel Export Module
=============================================
Bu modül, bakım sistemini Excel dosyasına aktarır.

Özellikler:
- Filo Verileri sayfası
- Bakım Hesaplamaları sayfası
- Dashboard özet sayfası
- Koşullu biçimlendirme ile renkli uyarılar
- Grafikler
"""

import pandas as pd
from datetime import datetime, timedelta
import random
from openpyxl import Workbook
from openpyxl.styles import Font, Fill, PatternFill, Border, Side, Alignment
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule, FormulaRule
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter


# ============================================
# STYLES
# ============================================

# Colors
THY_RED = "E31837"
DARK_BLUE = "1a1a2e"
GREEN = "00b894"
YELLOW = "fdcb6e"
ORANGE = "f39c12"
RED = "e74c3c"
LIGHT_BLUE = "74b9ff"

# Fills
header_fill = PatternFill(start_color=THY_RED, end_color=THY_RED, fill_type="solid")
subheader_fill = PatternFill(start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid")
ok_fill = PatternFill(start_color=GREEN, end_color=GREEN, fill_type="solid")
warning_fill = PatternFill(start_color=YELLOW, end_color=YELLOW, fill_type="solid")
critical_fill = PatternFill(start_color=RED, end_color=RED, fill_type="solid")
highlight_fill = PatternFill(start_color=LIGHT_BLUE, end_color=LIGHT_BLUE, fill_type="solid")

# Fonts
header_font = Font(bold=True, color="FFFFFF", size=14)
subheader_font = Font(bold=True, color="FFFFFF", size=11)
title_font = Font(bold=True, size=16, color=THY_RED)
normal_font = Font(size=10)
bold_font = Font(bold=True, size=10)

# Borders
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)

# Alignment
center_align = Alignment(horizontal='center', vertical='center')
left_align = Alignment(horizontal='left', vertical='center')


# ============================================
# MAINTENANCE LIMITS
# ============================================

MAINTENANCE_LIMITS = {
    "A": {"fh_limit": 600, "fc_limit": 400, "days_limit": None, "duration_days": 1},
    "B": {"fh_limit": None, "fc_limit": None, "days_limit": 180, "duration_days": 3},
    "C": {"fh_limit": 6000, "fc_limit": None, "days_limit": 730, "duration_days": 7},
    "D": {"fh_limit": None, "fc_limit": None, "days_limit": 2190, "duration_days": 30}
}


# ============================================
# DATA GENERATION
# ============================================

def generate_fleet_data():
    """THY filo verileri üret"""
    
    fleet_structure = {
        "Airbus A319-100":  {"count": 6,  "prefix": "TC-JL", "category": "NARROW"},
        "Airbus A320-200":  {"count": 14, "prefix": "TC-JP", "category": "NARROW"},
        "Airbus A320 NEO":  {"count": 10, "prefix": "TC-NB", "category": "NARROW"},
        "Airbus A321-200":  {"count": 20, "prefix": "TC-JR", "category": "NARROW"},
        "Airbus A321 NEO":  {"count": 15, "prefix": "TC-LT", "category": "NARROW"},
        "Airbus A330-200":  {"count": 12, "prefix": "TC-JN", "category": "WIDE"},
        "Airbus A330-300":  {"count": 37, "prefix": "TC-JO", "category": "WIDE"},
        "Airbus A350-900":  {"count": 25, "prefix": "TC-LG", "category": "WIDE"},
        "Boeing 737-800":   {"count": 30, "prefix": "TC-JV", "category": "NARROW"},
        "Boeing 737-900ER": {"count": 15, "prefix": "TC-JY", "category": "NARROW"},
        "Boeing 737 MAX 8": {"count": 34, "prefix": "TC-LC", "category": "NARROW"},
        "Boeing 777-300ER": {"count": 34, "prefix": "TC-JJ", "category": "WIDE"},
        "Boeing 787-9":     {"count": 23, "prefix": "TC-LL", "category": "WIDE"},
        "Boeing 777F":      {"count": 8,  "prefix": "TC-LJ", "category": "CARGO"}
    }

    data = []
    today = datetime.now()
    random.seed(42)

    for model, info in fleet_structure.items():
        for i in range(1, info["count"] + 1):
            tail_number = f"{info['prefix']}{chr(65 + (i % 26))}{random.randint(10, 99)}"
            
            if info["category"] in ["WIDE", "CARGO"]:
                total_fh = random.randint(5000, 50000)
                avg_flight_time = random.uniform(5, 10)
            else:
                total_fh = random.randint(2000, 35000)
                avg_flight_time = random.uniform(1.5, 3.5)
            
            total_fc = int(total_fh / avg_flight_time)
            years_in_service = random.randint(2, 15)
            delivery_date = today - timedelta(days=years_in_service * 365)
            
            check_types = ["A", "B", "C"]
            last_check = random.choice(check_types)
            
            if last_check == "A":
                fh_since_check = random.randint(50, 580)
                fc_since_check = random.randint(30, 380)
            elif last_check == "B":
                fh_since_check = random.randint(100, 2000)
                fc_since_check = random.randint(80, 1200)
            else:
                fh_since_check = random.randint(500, 5500)
                fc_since_check = random.randint(300, 3500)
            
            last_maint_date = today - timedelta(days=random.randint(10, 600))
            years_since_d_check = random.randint(0, 6)
            last_d_check = today - timedelta(days=years_since_d_check * 365 + random.randint(0, 180))
            daily_fh = round(random.uniform(6, 14), 1)
            status = random.choice(["Aktif", "Aktif", "Aktif", "Bakımda"])
            
            # Calculate maintenance percentages
            a_check_pct = round(max((fh_since_check / 600) * 100, (fc_since_check / 400) * 100), 1)
            days_since_maint = (today - last_maint_date).days
            b_check_pct = round((days_since_maint / 180) * 100, 1)
            c_check_pct = round(max((fh_since_check * 2 / 6000) * 100, (days_since_maint / 730) * 100), 1)
            days_since_d = (today - last_d_check).days
            d_check_pct = round((days_since_d / 2190) * 100, 1)
            
            # Determine status levels
            def get_status(pct):
                if pct >= 90:
                    return "KRİTİK"
                elif pct >= 75:
                    return "UYARI"
                else:
                    return "NORMAL"
            
            data.append({
                "Kuyruk No": tail_number,
                "Model": model,
                "Kategori": info["category"],
                "Teslim Tarihi": delivery_date.strftime("%Y-%m-%d"),
                "Toplam FH": total_fh,
                "Toplam FC": total_fc,
                "Son Bakım Tipi": last_check,
                "Son Bakımdan Beri FH": fh_since_check,
                "Son Bakımdan Beri FC": fc_since_check,
                "Son Bakım Tarihi": last_maint_date.strftime("%Y-%m-%d"),
                "Son D-Check": last_d_check.strftime("%Y-%m-%d"),
                "Günlük Ort. FH": daily_fh,
                "Durum": status,
                "A Check %": min(a_check_pct, 100),
                "B Check %": min(b_check_pct, 100),
                "C Check %": min(c_check_pct, 100),
                "D Check %": min(d_check_pct, 100),
                "A Check Durum": get_status(a_check_pct),
                "B Check Durum": get_status(b_check_pct),
                "C Check Durum": get_status(c_check_pct),
                "D Check Durum": get_status(d_check_pct),
                "Kalan A Check (gün)": max(0, int((600 - fh_since_check) / daily_fh)) if daily_fh > 0 else 999,
                "Kalan B Check (gün)": max(0, 180 - days_since_maint),
                "Kalan C Check (gün)": max(0, 730 - days_since_maint),
                "Kalan D Check (gün)": max(0, 2190 - days_since_d)
            })

    return pd.DataFrame(data).sort_values("Kuyruk No").reset_index(drop=True)


# ============================================
# EXCEL CREATION
# ============================================

def create_excel_workbook(df):
    """Ana Excel dosyasını oluştur"""
    
    wb = Workbook()
    
    # ========== SHEET 1: DASHBOARD ==========
    ws_dashboard = wb.active
    ws_dashboard.title = "Dashboard"
    create_dashboard(ws_dashboard, df)
    
    # ========== SHEET 2: FLEET DATA ==========
    ws_fleet = wb.create_sheet("Filo Verileri")
    create_fleet_sheet(ws_fleet, df)
    
    # ========== SHEET 3: MAINTENANCE STATUS ==========
    ws_maint = wb.create_sheet("Bakım Durumu")
    create_maintenance_sheet(ws_maint, df)
    
    # ========== SHEET 4: REFERENCES ==========
    ws_refs = wb.create_sheet("Akademik Referanslar")
    create_references_sheet(ws_refs)
    
    return wb


def create_dashboard(ws, df):
    """Dashboard sayfasını oluştur"""
    
    # Title
    ws.merge_cells('A1:H1')
    ws['A1'] = "✈️ THY AIRCRAFT MAINTENANCE PLANNING SYSTEM"
    ws['A1'].font = Font(bold=True, size=20, color=THY_RED)
    ws['A1'].alignment = center_align
    
    ws.merge_cells('A2:H2')
    ws['A2'] = f"Dashboard - Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws['A2'].font = Font(size=11, italic=True)
    ws['A2'].alignment = center_align
    
    # Fleet Summary Section
    ws['A4'] = "FİLO ÖZETİ"
    ws['A4'].font = header_font
    ws['A4'].fill = header_fill
    ws.merge_cells('A4:B4')
    
    # Summary metrics
    metrics = [
        ("Toplam Uçak", len(df)),
        ("Aktif Uçak", len(df[df["Durum"] == "Aktif"])),
        ("Bakımda", len(df[df["Durum"] == "Bakımda"])),
        ("Dar Gövde (Narrow)", len(df[df["Kategori"] == "NARROW"])),
        ("Geniş Gövde (Wide)", len(df[df["Kategori"] == "WIDE"])),
        ("Kargo", len(df[df["Kategori"] == "CARGO"])),
        ("Toplam Uçuş Saati", f"{df['Toplam FH'].sum():,} FH"),
        ("Model Sayısı", df["Model"].nunique())
    ]
    
    for i, (label, value) in enumerate(metrics):
        row = 5 + i
        ws[f'A{row}'] = label
        ws[f'A{row}'].font = bold_font
        ws[f'B{row}'] = value
        ws[f'A{row}'].border = thin_border
        ws[f'B{row}'].border = thin_border
    
    # Critical/Warning/OK Summary
    ws['D4'] = "BAKIM DURUMU ÖZETİ"
    ws['D4'].font = header_font
    ws['D4'].fill = header_fill
    ws.merge_cells('D4:F4')
    
    critical_count = len(df[df["A Check Durum"] == "KRİTİK"]) + len(df[df["B Check Durum"] == "KRİTİK"])
    warning_count = len(df[df["A Check Durum"] == "UYARI"]) + len(df[df["B Check Durum"] == "UYARI"])
    normal_count = len(df) * 4 - critical_count - warning_count
    
    status_data = [
        ("🔴 KRİTİK (≥90%)", critical_count, critical_fill),
        ("🟡 UYARI (75-89%)", warning_count, warning_fill),
        ("🟢 NORMAL (<75%)", normal_count, ok_fill)
    ]
    
    for i, (label, count, fill) in enumerate(status_data):
        row = 5 + i
        ws[f'D{row}'] = label
        ws[f'D{row}'].font = bold_font
        ws[f'E{row}'] = count
        ws[f'F{row}'] = f"{(count / (len(df) * 4) * 100):.1f}%"
        ws[f'D{row}'].fill = fill
        ws[f'D{row}'].border = thin_border
        ws[f'E{row}'].border = thin_border
        ws[f'F{row}'].border = thin_border
    
    # Maintenance Limits Reference
    ws['A15'] = "BAKIM LİMİTLERİ (EASA/FAA Standartları)"
    ws['A15'].font = header_font
    ws['A15'].fill = subheader_fill
    ws.merge_cells('A15:E15')
    
    limits_headers = ["Check Tipi", "FH Limiti", "FC Limiti", "Zaman Limiti", "Süre"]
    for i, header in enumerate(limits_headers):
        col = get_column_letter(i + 1)
        ws[f'{col}16'] = header
        ws[f'{col}16'].font = subheader_font
        ws[f'{col}16'].fill = subheader_fill
        ws[f'{col}16'].border = thin_border
    
    limits_data = [
        ("A Check", "600 FH", "400 FC", "-", "1 gün"),
        ("B Check (Phased)", "-", "-", "180 gün (6 ay)", "3 gün"),
        ("C Check", "6,000 FH", "-", "730 gün (2 yıl)", "7 gün"),
        ("D Check (Heavy)", "-", "-", "2,190 gün (6 yıl)", "30 gün")
    ]
    
    for i, row_data in enumerate(limits_data):
        row = 17 + i
        for j, value in enumerate(row_data):
            col = get_column_letter(j + 1)
            ws[f'{col}{row}'] = value
            ws[f'{col}{row}'].border = thin_border
    
    # Academic References Note
    ws['A23'] = "📚 AKADEMİK REFERANSLAR"
    ws['A23'].font = header_font
    ws['A23'].fill = highlight_fill
    ws.merge_cells('A23:H23')
    
    refs = [
        "• Papakostas et al. (2010) - Phased/Block Maintenance yaklaşımı",
        "• Callewaert et al. (2017) - Stokastik bakım süresi modeli (%15 NRF olasılığı)",
        "• Kowalski et al. (2021) - Kaynak kısıtları (Hangar kapasitesi)",
        "• Hollander (2025) - Bakım planlamada belirsizlik modelleme"
    ]
    
    for i, ref in enumerate(refs):
        ws[f'A{24+i}'] = ref
        ws[f'A{24+i}'].font = Font(size=10, italic=True)
    
    # Column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 5
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15


def create_fleet_sheet(ws, df):
    """Filo verileri sayfasını oluştur"""
    
    # Title
    ws.merge_cells('A1:N1')
    ws['A1'] = "THY FİLO VERİLERİ - 283 Uçak"
    ws['A1'].font = title_font
    ws['A1'].alignment = center_align
    
    # Select columns for fleet sheet
    fleet_columns = ["Kuyruk No", "Model", "Kategori", "Teslim Tarihi", 
                     "Toplam FH", "Toplam FC", "Son Bakım Tipi", 
                     "Son Bakımdan Beri FH", "Son Bakımdan Beri FC",
                     "Son Bakım Tarihi", "Son D-Check", "Günlük Ort. FH", "Durum"]
    
    fleet_df = df[fleet_columns]
    
    # Headers
    for i, col in enumerate(fleet_columns):
        cell = ws.cell(row=3, column=i+1)
        cell.value = col
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center_align
    
    # Data
    for r_idx, row in enumerate(fleet_df.values):
        for c_idx, value in enumerate(row):
            cell = ws.cell(row=r_idx+4, column=c_idx+1)
            cell.value = value
            cell.border = thin_border
            cell.font = normal_font
            
            # Conditional formatting for status
            if c_idx == len(fleet_columns) - 1:  # Durum column
                if value == "Bakımda":
                    cell.fill = warning_fill
                else:
                    cell.fill = ok_fill
    
    # Column widths
    for i, col in enumerate(fleet_columns):
        ws.column_dimensions[get_column_letter(i+1)].width = max(len(col) + 2, 12)


def create_maintenance_sheet(ws, df):
    """Bakım durumu sayfasını oluştur"""
    
    # Title
    ws.merge_cells('A1:L1')
    ws['A1'] = "BAKIM DURUM TAKİP TABLOSU"
    ws['A1'].font = title_font
    ws['A1'].alignment = center_align
    
    # Select columns for maintenance sheet
    maint_columns = ["Kuyruk No", "Model", "A Check %", "A Check Durum", 
                     "B Check %", "B Check Durum", "C Check %", "C Check Durum",
                     "D Check %", "D Check Durum", "Kalan A Check (gün)", "Kalan B Check (gün)"]
    
    maint_df = df[maint_columns]
    
    # Headers
    for i, col in enumerate(maint_columns):
        cell = ws.cell(row=3, column=i+1)
        cell.value = col
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center_align
    
    # Data with conditional formatting
    for r_idx, row in enumerate(maint_df.values):
        for c_idx, value in enumerate(row):
            cell = ws.cell(row=r_idx+4, column=c_idx+1)
            cell.value = value
            cell.border = thin_border
            cell.font = normal_font
            cell.alignment = center_align
            
            # Color coding for percentage columns
            if "%" in maint_columns[c_idx]:
                if value >= 90:
                    cell.fill = critical_fill
                elif value >= 75:
                    cell.fill = warning_fill
                else:
                    cell.fill = ok_fill
            
            # Color coding for status columns
            if "Durum" in maint_columns[c_idx]:
                if value == "KRİTİK":
                    cell.fill = critical_fill
                    cell.font = Font(bold=True, color="FFFFFF")
                elif value == "UYARI":
                    cell.fill = warning_fill
                    cell.font = Font(bold=True)
                else:
                    cell.fill = ok_fill
    
    # Column widths
    for i, col in enumerate(maint_columns):
        ws.column_dimensions[get_column_letter(i+1)].width = max(len(col) + 2, 15)
    
    # Add legend
    ws['A290'] = "RENK KODLARI:"
    ws['A290'].font = bold_font
    
    legend = [
        ("🔴 KRİTİK", "≥90% - Acil bakım gerekli", critical_fill),
        ("🟡 UYARI", "75-89% - Bakım penceresi yaklaşıyor", warning_fill),
        ("🟢 NORMAL", "<75% - Normal operasyon", ok_fill)
    ]
    
    for i, (status, desc, fill) in enumerate(legend):
        ws[f'A{291+i}'] = status
        ws[f'A{291+i}'].fill = fill
        ws[f'B{291+i}'] = desc


def create_references_sheet(ws):
    """Akademik referanslar sayfasını oluştur"""
    
    ws.merge_cells('A1:E1')
    ws['A1'] = "📚 AKADEMİK REFERANSLAR VE METODOLOJİ"
    ws['A1'].font = title_font
    ws['A1'].alignment = center_align
    
    # References
    references = [
        ("1. Papakostas et al. (2010)", 
         "Operational Aircraft Maintenance Planning: A Multi-objective Approach",
         "Modern havayolları Phased/Block Maintenance yaklaşımı kullanır.",
         "B Check = Phased Maintenance olarak adlandırılır."),
        
        ("2. Callewaert et al. (2017)", 
         "Integrating maintenance work progress monitoring in a stochastic framework",
         "Bakım süresi deterministik değildir. %15 ihtimalle Non-Routine Finding çıkar.",
         "T_actual = T_base + T_NRF (1-3 gün ek gecikme)"),
        
        ("3. Kowalski et al. (2021)", 
         "Resource-constrained project scheduling for aircraft maintenance",
         "Hangar kapasitesi sınırlıdır. Aynı anda max 5 geniş gövde bakıma alınabilir.",
         "Kapasite doluysa bakım ertelenir (Deferred Maintenance)."),
        
        ("4. Hollander (2025)", 
         "Uncertainty Quantification in Aviation Maintenance Planning",
         "Bakım planlamada belirsizlik olasılık dağılımlarıyla modellenmelidir.",
         "Stokastik modelleme Callewaert (2017) ile birlikte kullanılır.")
    ]
    
    row = 4
    for ref, title, contribution, application in references:
        ws[f'A{row}'] = ref
        ws[f'A{row}'].font = Font(bold=True, size=12, color=THY_RED)
        ws.merge_cells(f'A{row}:E{row}')
        
        ws[f'A{row+1}'] = f"Başlık: {title}"
        ws[f'A{row+1}'].font = Font(italic=True)
        ws.merge_cells(f'A{row+1}:E{row+1}')
        
        ws[f'A{row+2}'] = f"Katkı: {contribution}"
        ws.merge_cells(f'A{row+2}:E{row+2}')
        
        ws[f'A{row+3}'] = f"Uygulama: {application}"
        ws[f'A{row+3}'].font = Font(color="0066CC")
        ws.merge_cells(f'A{row+3}:E{row+3}')
        
        row += 5
    
    ws.column_dimensions['A'].width = 100


def main():
    """Ana fonksiyon - Excel dosyasını oluştur ve kaydet"""
    
    print("=" * 60)
    print("THY Maintenance System - Excel Export")
    print("=" * 60)
    
    # Generate data
    print("\n📊 Filo verileri oluşturuluyor...")
    df = generate_fleet_data()
    print(f"   ✓ {len(df)} uçak verisi üretildi")
    
    # Create workbook
    print("\n📑 Excel dosyası oluşturuluyor...")
    wb = create_excel_workbook(df)
    
    # Save
    output_path = "THY_Maintenance_System.xlsx"
    wb.save(output_path)
    print(f"   ✓ Dosya kaydedildi: {output_path}")
    
    print("\n" + "=" * 60)
    print("✅ Excel dosyası başarıyla oluşturuldu!")
    print("=" * 60)
    
    print("\n📋 Sayfalar:")
    print("   1. Dashboard - Özet ve istatistikler")
    print("   2. Filo Verileri - 283 uçağın detaylı bilgileri")
    print("   3. Bakım Durumu - A/B/C/D check ilerleme durumları")
    print("   4. Akademik Referanslar - Literatür bilgileri")
    
    return output_path


if __name__ == "__main__":
    main()
