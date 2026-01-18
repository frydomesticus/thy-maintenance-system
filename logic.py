"""
THY Bakım Mantığı Modülü - Akademik Versiyon
=============================================
Aircraft Maintenance Logic with Academic References

Bu modül, uçak bakım durumunu hesaplayan algoritmaları içerir.
Akademik literatüre dayalı stokastik (rassal) süreçler ve 
kaynak kısıtları entegre edilmiştir.

REFERANSLAR:
------------
- Papakostas, N., Pintelon, L., & Zeimpekis, V. (2010). Operational Aircraft 
  Maintenance Planning: A Multi-objective Approach.
- Callewaert, P., Seifferth, S., & Schepers, J. (2017). Integrating maintenance 
  work progress monitoring in a stochastic aircraft maintenance scheduling framework.
- Kowalski, M., Kowalczuk, Z., & Seredyński, F. (2021). Resource-constrained 
  project scheduling for aircraft maintenance.
- Hollander, M. (2025). Uncertainty Quantification in Aviation Maintenance Planning.
- Gupta, D., Maravelias, C.T., & Wassick, J.M. (2016). From rescheduling to 
  online scheduling.

BAKIM ARALIĞI STANDARTLARI (EASA/FAA):
--------------------------------------
- A Check: 600 FH veya 400 FC (hangisi önce dolarsa)
- B Check: 6-8 ay / Phased Maintenance (Modern yaklaşım)
- C Check: 6000 FH veya 24 ay (2 yıl)
- D Check: 6 yıl (Heavy Maintenance / Structural Overhaul)
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Tuple, List, Dict, Optional
from enum import Enum


# ============================================
# SABİT DEĞİŞKENLER (Constants)
# ============================================

# REF: Papakostas et al. (2010) - Operational Aircraft Maintenance Planning
# Modern havacılıkta katı A/B/C/D checkler yerine 'Phased' ve 'Block' 
# yaklaşımları kullanılmaktadır. Bu model hibrit bir yapı sunar.
MAINTENANCE_LIMITS = {
    "A": {
        "fh_limit": 600,        # Flight Hours limit
        "fc_limit": 400,        # Flight Cycles limit
        "days_limit": None,     # Zaman bazlı limit yok
        "duration_days": 1,     # Baz bakım süresi
        "priority": 1,          # Öncelik (düşük = daha acil)
        "color": "#00b894",     # UI rengi (yeşil)
        "description": "Light Maintenance Check",
        "academic_note": "Papakostas (2010): Routine line maintenance"
    },
    "B": {
        "fh_limit": None,
        "fc_limit": None,
        "days_limit": 180,      # 6 ay
        "duration_days": 3,     # Baz bakım süresi
        "priority": 2,
        "color": "#0984e3",     # UI rengi (mavi)
        "description": "Phased/Block Check",  # Modern terminoloji
        "academic_note": "Papakostas (2010): Modern airlines use phased approach"
    },
    "C": {
        "fh_limit": 6000,
        "fc_limit": None,
        "days_limit": 730,      # 24 ay (2 yıl)
        "duration_days": 7,     # Baz bakım süresi (hangar gerekli)
        "priority": 3,
        "color": "#fdcb6e",     # UI rengi (sarı)
        "description": "Heavy Base Maintenance",
        "academic_note": "Callewaert (2017): Hangar-based structural inspection"
    },
    "D": {
        "fh_limit": None,
        "fc_limit": None,
        "days_limit": 2190,     # 6 yıl
        "duration_days": 30,    # Ağır bakım süresi
        "priority": 4,
        "color": "#e74c3c",     # UI rengi (kırmızı)
        "description": "Structural Overhaul (Heavy)",
        "academic_note": "Complete aircraft teardown and inspection"
    }
}

# REF: Kowalski et al. (2021) - Resource Constraints in Maintenance
# Gerçek dünyada hangar kapasitesi sınırlıdır. THY Teknik'in Sabiha Gökçen
# ve Atatürk Havalimanı tesislerinde aynı anda bakıma alınabilecek 
# geniş gövde uçak sayısı sınırlıdır.
HANGAR_CAPACITY = {
    "wide_body": 5,      # Aynı anda max 5 geniş gövde (A330, A350, B777, B787)
    "narrow_body": 12,   # Aynı anda max 12 dar gövde (A320, B737 ailesi)
    "total": 15          # Toplam kapasite
}

# REF: Callewaert et al. (2017) & Hollander (2025)
# Stokastik (rassal) parametreler - Gerçek bakımlarda belirsizlik vardır
STOCHASTIC_PARAMS = {
    "non_routine_probability": 0.15,    # %15 ihtimalle rutin dışı bulgu
    "min_delay_days": 1,                # Minimum ek gecikme
    "max_delay_days": 3,                # Maximum ek gecikme
    "corrosion_probability": 0.08,      # %8 korozyon bulgusu
    "fatigue_crack_probability": 0.05,  # %5 yorulma çatlağı
    "system_failure_probability": 0.02  # %2 sistem arızası
}


# ============================================
# ENUM ve DATACLASS TANIMLAMALARI
# ============================================

class MaintenanceStatusLevel(Enum):
    """Bakım durumu seviyeleri"""
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    DEFERRED = "DEFERRED"
    IN_MAINTENANCE = "IN_MAINTENANCE"


class NonRoutineFindingType(Enum):
    """Rutin dışı bulgu tipleri (Callewaert 2017)"""
    NONE = "None"
    CORROSION = "Corrosion"
    FATIGUE_CRACK = "Fatigue Crack"
    SYSTEM_FAILURE = "System Malfunction"
    STRUCTURAL_DAMAGE = "Structural Damage"


@dataclass
class NonRoutineFinding:
    """
    Rutin dışı bulgu detayları
    REF: Callewaert et al. (2017) - Non-routine findings cause delays
    """
    has_finding: bool = False
    finding_type: NonRoutineFindingType = NonRoutineFindingType.NONE
    extra_days: int = 0
    description: str = ""
    academic_reference: str = ""


@dataclass
class MaintenanceStatus:
    """Bakım durumu veri yapısı - Genişletilmiş akademik versiyon"""
    check_type: str
    remaining_fh: Optional[float]
    remaining_fc: Optional[float]
    remaining_days: int
    progress_percent: float
    status: MaintenanceStatusLevel
    action_required: bool
    next_due_date: str
    description: str
    base_duration_days: int
    adjusted_duration_days: int
    non_routine_finding: NonRoutineFinding = field(default_factory=NonRoutineFinding)
    is_deferred: bool = False
    deferral_reason: str = ""
    academic_note: str = ""


@dataclass
class HangarStatus:
    """
    Hangar kapasite durumu
    REF: Kowalski et al. (2021) - Resource-constrained scheduling
    """
    wide_body_count: int = 0
    narrow_body_count: int = 0
    total_count: int = 0
    wide_body_available: int = HANGAR_CAPACITY["wide_body"]
    narrow_body_available: int = HANGAR_CAPACITY["narrow_body"]
    utilization_percent: float = 0.0
    is_full: bool = False


# ============================================
# YARDIMCI FONKSİYONLAR
# ============================================

def get_status_level(progress: float) -> MaintenanceStatusLevel:
    """
    İlerleme yüzdesine göre durum seviyesi döndürür.
    
    Eşik Değerleri:
    - 0-74%: OK (Normal operasyon)
    - 75-89%: WARNING (Bakım penceresi yaklaşıyor)
    - 90-100%: CRITICAL (Acil aksiyon gerekli)
    """
    if progress >= 90:
        return MaintenanceStatusLevel.CRITICAL
    elif progress >= 75:
        return MaintenanceStatusLevel.WARNING
    else:
        return MaintenanceStatusLevel.OK


def calculate_days_between(date1: str, date2: str) -> int:
    """İki tarih arasındaki gün farkını hesaplar"""
    d1 = datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    return (d2 - d1).days


# ============================================
# STOKASTİK MODEL FONKSİYONLARI
# ============================================

def simulate_non_routine_finding(seed: int = None) -> NonRoutineFinding:
    """
    Rutin dışı bulgu simülasyonu
    
    REF: Callewaert et al. (2017) - Integrating maintenance work progress monitoring
    REF: Hollander (2025) - Uncertainty in maintenance planning
    
    Gerçek hayatta bakımlar planlandığı gibi gitmez. EASA raporlarına göre
    bakımların yaklaşık %15'inde rutin dışı bulgular (Non-Routine Findings - NRF)
    tespit edilir ve bakım süresi uzar.
    
    Returns:
        NonRoutineFinding: Bulgu detayları
    """
    if seed is not None:
        random.seed(seed)
    
    # %15 ihtimalle rutin dışı bulgu
    if random.random() < STOCHASTIC_PARAMS["non_routine_probability"]:
        # Bulgu tipini belirle
        roll = random.random()
        
        if roll < STOCHASTIC_PARAMS["corrosion_probability"]:
            finding_type = NonRoutineFindingType.CORROSION
            description = "Korozyon tespit edildi (Corrosion detected in structural components)"
        elif roll < (STOCHASTIC_PARAMS["corrosion_probability"] + 
                     STOCHASTIC_PARAMS["fatigue_crack_probability"]):
            finding_type = NonRoutineFindingType.FATIGUE_CRACK
            description = "Yorulma çatlağı tespit edildi (Fatigue crack found during NDT inspection)"
        elif roll < (STOCHASTIC_PARAMS["corrosion_probability"] + 
                     STOCHASTIC_PARAMS["fatigue_crack_probability"] +
                     STOCHASTIC_PARAMS["system_failure_probability"]):
            finding_type = NonRoutineFindingType.SYSTEM_FAILURE
            description = "Sistem arızası tespit edildi (System malfunction during functional test)"
        else:
            finding_type = NonRoutineFindingType.STRUCTURAL_DAMAGE
            description = "Yapısal hasar tespit edildi (Minor structural damage requiring repair)"
        
        extra_days = random.randint(
            STOCHASTIC_PARAMS["min_delay_days"],
            STOCHASTIC_PARAMS["max_delay_days"]
        )
        
        return NonRoutineFinding(
            has_finding=True,
            finding_type=finding_type,
            extra_days=extra_days,
            description=description,
            academic_reference="Callewaert et al. (2017), Hollander (2025)"
        )
    
    return NonRoutineFinding()


# ============================================
# KAYNAK KISITI FONKSİYONLARI
# ============================================

def calculate_hangar_status(df: pd.DataFrame) -> HangarStatus:
    """
    Mevcut hangar doluluk durumunu hesaplar.
    
    REF: Kowalski et al. (2021) - Resource Constraints in Maintenance
    REF: Gupta et al. (2016) - From rescheduling to online scheduling
    
    Gerçek dünyada bakım kapasitesi sınırlıdır. Bu fonksiyon mevcut
    bakımdaki uçakları sayarak hangar kullanım oranını hesaplar.
    
    Args:
        df: Filo veri DataFrame'i
        
    Returns:
        HangarStatus: Hangar kapasite durumu
    """
    # Bakımdaki uçakları filtrele
    maintenance_df = df[df["Durum"] == "Bakımda"]
    
    # Geniş ve dar gövde ayrımı
    wide_body_categories = ["WIDE", "CARGO"]
    wide_body_count = len(maintenance_df[maintenance_df["Kategori"].isin(wide_body_categories)])
    narrow_body_count = len(maintenance_df[maintenance_df["Kategori"] == "NARROW"])
    total_count = len(maintenance_df)
    
    # Kullanım oranı
    utilization = (total_count / HANGAR_CAPACITY["total"]) * 100
    
    # Kapasite kontrolü
    is_full = (wide_body_count >= HANGAR_CAPACITY["wide_body"] or
               total_count >= HANGAR_CAPACITY["total"])
    
    return HangarStatus(
        wide_body_count=wide_body_count,
        narrow_body_count=narrow_body_count,
        total_count=total_count,
        wide_body_available=HANGAR_CAPACITY["wide_body"] - wide_body_count,
        narrow_body_available=HANGAR_CAPACITY["narrow_body"] - narrow_body_count,
        utilization_percent=round(utilization, 1),
        is_full=is_full
    )


def check_hangar_availability(hangar_status: HangarStatus, aircraft_category: str) -> Tuple[bool, str]:
    """
    Belirli bir uçak kategorisi için hangar müsaitliğini kontrol eder.
    
    REF: Kowalski et al. (2021) - Resource-constrained project scheduling
    
    Eğer hangar doluysa, bakım ertelenir (Maintenance Deferral).
    Bu durum MEL (Minimum Equipment List) kapsamında yönetilir.
    
    Args:
        hangar_status: Mevcut hangar durumu
        aircraft_category: Uçak kategorisi (WIDE, NARROW, CARGO)
        
    Returns:
        Tuple[bool, str]: (Müsait mi?, Açıklama)
    """
    if aircraft_category in ["WIDE", "CARGO"]:
        if hangar_status.wide_body_available <= 0:
            return False, f"Wide-body hangar kapasitesi dolu ({HANGAR_CAPACITY['wide_body']}/{HANGAR_CAPACITY['wide_body']}). Ref: Kowalski (2021)"
        return True, f"Wide-body slot müsait ({hangar_status.wide_body_available} boş)"
    else:
        if hangar_status.narrow_body_available <= 0:
            return False, f"Narrow-body hangar kapasitesi dolu ({HANGAR_CAPACITY['narrow_body']}/{HANGAR_CAPACITY['narrow_body']}). Ref: Kowalski (2021)"
        return True, f"Narrow-body slot müsait ({hangar_status.narrow_body_available} boş)"


# ============================================
# ANA BAKIM HESAPLAMA FONKSİYONLARI
# ============================================

def calculate_maintenance_status(
    aircraft_data: dict, 
    current_date: str = None,
    hangar_status: HangarStatus = None,
    apply_stochastic: bool = True
) -> Dict[str, MaintenanceStatus]:
    """
    Tek bir uçağın tüm bakım durumlarını hesaplar.
    
    Bu fonksiyon akademik literatüre dayalı gelişmiş özellikler içerir:
    1. Standart FH/FC/Zaman bazlı limit hesaplaması
    2. Stokastik (rassal) rutin dışı bulgu simülasyonu
    3. Kaynak kısıtı (hangar kapasitesi) kontrolü
    
    Args:
        aircraft_data: DataFrame'den seçilen uçağın verileri (dict formatında)
        current_date: Referans tarih (varsayılan: bugün)
        hangar_status: Mevcut hangar durumu (opsiyonel)
        apply_stochastic: Stokastik model uygulansın mı?
        
    Returns:
        Dict[str, MaintenanceStatus]: Her bakım tipi için durum bilgileri
    """
    
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")
    
    current_dt = datetime.strptime(current_date, "%Y-%m-%d")
    last_maint_date = datetime.strptime(aircraft_data["Son Bakım Tarihi"], "%Y-%m-%d")
    last_d_check = datetime.strptime(aircraft_data["Son D-Check Tarihi"], "%Y-%m-%d")
    
    # Son bakımdan bu yana geçen gün
    days_since_last_maint = (current_dt - last_maint_date).days
    days_since_d_check = (current_dt - last_d_check).days
    
    # Günlük ortalama uçuş saati
    daily_fh = aircraft_data["Günlük Ort. FH"]
    
    results = {}
    
    # ========================
    # A CHECK HESAPLAMA
    # ========================
    a_fh_used = aircraft_data["Son Bakımdan Beri FH"]
    a_fc_used = aircraft_data["Son Bakımdan Beri FC"]
    a_fh_limit = MAINTENANCE_LIMITS["A"]["fh_limit"]
    a_fc_limit = MAINTENANCE_LIMITS["A"]["fc_limit"]
    
    a_fh_remaining = a_fh_limit - a_fh_used
    a_fc_remaining = a_fc_limit - a_fc_used
    
    a_fh_progress = (a_fh_used / a_fh_limit) * 100
    a_fc_progress = (a_fc_used / a_fc_limit) * 100
    a_progress = max(a_fh_progress, a_fc_progress)
    
    a_days_remaining = int(a_fh_remaining / daily_fh) if daily_fh > 0 else 999
    
    # Stokastik bulgu simülasyonu
    a_finding = simulate_non_routine_finding() if apply_stochastic else NonRoutineFinding()
    a_base_duration = MAINTENANCE_LIMITS["A"]["duration_days"]
    a_adjusted_duration = a_base_duration + a_finding.extra_days
    
    results["A"] = MaintenanceStatus(
        check_type="A Check",
        remaining_fh=round(a_fh_remaining, 1),
        remaining_fc=round(a_fc_remaining, 1),
        remaining_days=a_days_remaining,
        progress_percent=round(min(a_progress, 100), 1),
        status=get_status_level(a_progress),
        action_required=a_progress >= 90,
        next_due_date=(current_dt + timedelta(days=a_days_remaining)).strftime("%Y-%m-%d"),
        description=MAINTENANCE_LIMITS["A"]["description"],
        base_duration_days=a_base_duration,
        adjusted_duration_days=a_adjusted_duration,
        non_routine_finding=a_finding,
        academic_note=MAINTENANCE_LIMITS["A"]["academic_note"]
    )
    
    # ========================
    # B CHECK HESAPLAMA (Phased Maintenance)
    # REF: Papakostas et al. (2010) - Modern yaklaşım
    # ========================
    b_days_limit = MAINTENANCE_LIMITS["B"]["days_limit"]
    b_days_used = days_since_last_maint
    b_days_remaining = max(0, b_days_limit - b_days_used)
    b_progress = min((b_days_used / b_days_limit) * 100, 100)
    
    b_finding = simulate_non_routine_finding() if apply_stochastic else NonRoutineFinding()
    b_base_duration = MAINTENANCE_LIMITS["B"]["duration_days"]
    b_adjusted_duration = b_base_duration + b_finding.extra_days
    
    results["B"] = MaintenanceStatus(
        check_type="B Check / Phased Maintenance",  # Modern terminoloji
        remaining_fh=None,
        remaining_fc=None,
        remaining_days=b_days_remaining,
        progress_percent=round(b_progress, 1),
        status=get_status_level(b_progress),
        action_required=b_progress >= 90,
        next_due_date=(current_dt + timedelta(days=b_days_remaining)).strftime("%Y-%m-%d"),
        description=MAINTENANCE_LIMITS["B"]["description"],
        base_duration_days=b_base_duration,
        adjusted_duration_days=b_adjusted_duration,
        non_routine_finding=b_finding,
        academic_note=MAINTENANCE_LIMITS["B"]["academic_note"]
    )
    
    # ========================
    # C CHECK HESAPLAMA
    # ========================
    c_fh_limit = MAINTENANCE_LIMITS["C"]["fh_limit"]
    c_days_limit = MAINTENANCE_LIMITS["C"]["days_limit"]
    
    c_fh_used = a_fh_used * 2  # C check periyodu için yaklaşık hesap
    c_fh_remaining = max(0, c_fh_limit - c_fh_used)
    c_fh_progress = min((c_fh_used / c_fh_limit) * 100, 100)
    
    c_days_remaining = max(0, c_days_limit - days_since_last_maint)
    c_days_progress = min((days_since_last_maint / c_days_limit) * 100, 100)
    
    c_progress = max(c_fh_progress, c_days_progress)
    
    c_finding = simulate_non_routine_finding() if apply_stochastic else NonRoutineFinding()
    c_base_duration = MAINTENANCE_LIMITS["C"]["duration_days"]
    c_adjusted_duration = c_base_duration + c_finding.extra_days
    
    # Kaynak kısıtı kontrolü (C Check hangar gerektirir)
    c_is_deferred = False
    c_deferral_reason = ""
    if hangar_status and c_progress >= 85:
        available, reason = check_hangar_availability(hangar_status, aircraft_data["Kategori"])
        if not available:
            c_is_deferred = True
            c_deferral_reason = reason
    
    results["C"] = MaintenanceStatus(
        check_type="C Check",
        remaining_fh=round(c_fh_remaining, 1),
        remaining_fc=None,
        remaining_days=c_days_remaining,
        progress_percent=round(c_progress, 1),
        status=MaintenanceStatusLevel.DEFERRED if c_is_deferred else get_status_level(c_progress),
        action_required=c_progress >= 85,
        next_due_date=(current_dt + timedelta(days=c_days_remaining)).strftime("%Y-%m-%d"),
        description=MAINTENANCE_LIMITS["C"]["description"],
        base_duration_days=c_base_duration,
        adjusted_duration_days=c_adjusted_duration,
        non_routine_finding=c_finding,
        is_deferred=c_is_deferred,
        deferral_reason=c_deferral_reason,
        academic_note=MAINTENANCE_LIMITS["C"]["academic_note"]
    )
    
    # ========================
    # D CHECK HESAPLAMA (Heavy Maintenance)
    # ========================
    d_days_limit = MAINTENANCE_LIMITS["D"]["days_limit"]
    d_days_remaining = max(0, d_days_limit - days_since_d_check)
    d_progress = min((days_since_d_check / d_days_limit) * 100, 100)
    
    d_finding = simulate_non_routine_finding() if apply_stochastic else NonRoutineFinding()
    d_base_duration = MAINTENANCE_LIMITS["D"]["duration_days"]
    d_adjusted_duration = d_base_duration + d_finding.extra_days
    
    # Kaynak kısıtı kontrolü (D Check kesinlikle hangar gerektirir)
    d_is_deferred = False
    d_deferral_reason = ""
    if hangar_status and d_progress >= 80:
        available, reason = check_hangar_availability(hangar_status, aircraft_data["Kategori"])
        if not available:
            d_is_deferred = True
            d_deferral_reason = reason
    
    results["D"] = MaintenanceStatus(
        check_type="D Check (Heavy Maintenance)",
        remaining_fh=None,
        remaining_fc=None,
        remaining_days=d_days_remaining,
        progress_percent=round(d_progress, 1),
        status=MaintenanceStatusLevel.DEFERRED if d_is_deferred else get_status_level(d_progress),
        action_required=d_progress >= 80,
        next_due_date=(current_dt + timedelta(days=d_days_remaining)).strftime("%Y-%m-%d"),
        description=MAINTENANCE_LIMITS["D"]["description"],
        base_duration_days=d_base_duration,
        adjusted_duration_days=d_adjusted_duration,
        non_routine_finding=d_finding,
        is_deferred=d_is_deferred,
        deferral_reason=d_deferral_reason,
        academic_note=MAINTENANCE_LIMITS["D"]["academic_note"]
    )
    
    return results


def get_most_critical_maintenance(maintenance_results: Dict[str, MaintenanceStatus]) -> Tuple[str, MaintenanceStatus]:
    """
    En kritik (en yakın) bakımı belirler.
    
    Öncelik sıralaması:
    1. CRITICAL durumunda olanlar (ilerleme >= 90%)
    2. WARNING durumunda olanlar (ilerleme >= 75%)
    3. En yüksek ilerleme yüzdesine sahip bakım
    
    Args:
        maintenance_results: calculate_maintenance_status çıktısı
        
    Returns:
        Tuple[str, MaintenanceStatus]: En kritik bakım tipi ve durumu
    """
    
    critical = None
    critical_type = None
    
    for check_type, status in maintenance_results.items():
        if critical is None:
            critical = status
            critical_type = check_type
        elif status.progress_percent > critical.progress_percent:
            critical = status
            critical_type = check_type
    
    return critical_type, critical


def get_all_non_routine_findings(maintenance_results: Dict[str, MaintenanceStatus]) -> List[Tuple[str, NonRoutineFinding]]:
    """
    Tüm rutin dışı bulguları listeler.
    
    Args:
        maintenance_results: calculate_maintenance_status çıktısı
        
    Returns:
        List[Tuple[str, NonRoutineFinding]]: Bakım tipi ve bulgu çiftleri
    """
    findings = []
    for check_type, status in maintenance_results.items():
        if status.non_routine_finding.has_finding:
            findings.append((check_type, status.non_routine_finding))
    return findings


def generate_academic_report(aircraft_data: dict, maintenance_results: dict) -> str:
    """
    Akademik formatta bakım raporu üretir.
    
    Args:
        aircraft_data: Uçak verileri
        maintenance_results: Bakım durumu sonuçları
        
    Returns:
        str: Formatlanmış akademik rapor
    """
    critical_type, critical = get_most_critical_maintenance(maintenance_results)
    findings = get_all_non_routine_findings(maintenance_results)
    
    report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║     THY AIRCRAFT MAINTENANCE STATUS REPORT (Academic Version)              ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Registration  : {aircraft_data['Kuyruk No']:<20}                                    ║
║  Aircraft Type : {aircraft_data['Model']:<40}           ║
║  Category      : {aircraft_data['Kategori']:<20}                                    ║
║  Total FH      : {aircraft_data['Toplam Uçuş Saati (FH)']:,} hours                                             ║
║  Total FC      : {aircraft_data['Toplam Döngü (FC)']:,} cycles                                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║  CRITICAL MAINTENANCE: {critical.check_type:<30}                       ║
║  Status        : {critical.status.value:<20} ({critical.progress_percent}% utilized)          ║
║  Days Until    : {critical.remaining_days} days                                                  ║
║  Due Date      : {critical.next_due_date}                                              ║
╠════════════════════════════════════════════════════════════════════════════╣
║  STOCHASTIC FINDINGS (Callewaert 2017, Hollander 2025):                    ║
"""
    
    if findings:
        for check_type, finding in findings:
            report += f"║  • {check_type}: {finding.finding_type.value} (+{finding.extra_days} days)                          ║\n"
    else:
        report += "║  • No non-routine findings detected in simulation                         ║\n"
    
    report += "╚════════════════════════════════════════════════════════════════════════════╝"
    
    return report


# ============================================
# TEST KODU
# ============================================

if __name__ == "__main__":
    # Test verisi
    test_aircraft = {
        "Kuyruk No": "TC-JJK25",
        "Model": "Boeing 777-300ER",
        "Kategori": "WIDE",
        "Toplam Uçuş Saati (FH)": 42000,
        "Toplam Döngü (FC)": 5600,
        "Son Bakım Tipi": "A",
        "Son Bakımdan Beri FH": 520,
        "Son Bakımdan Beri FC": 340,
        "Son Bakım Tarihi": "2025-11-01",
        "Son D-Check Tarihi": "2022-06-15",
        "Günlük Ort. FH": 12.5,
        "Durum": "Aktif"
    }
    
    print("=" * 80)
    print("THY MAINTENANCE LOGIC - ACADEMIC VERSION TEST")
    print("=" * 80)
    
    # Bakım durumu hesapla
    results = calculate_maintenance_status(test_aircraft, apply_stochastic=True)
    
    # Akademik rapor
    print(generate_academic_report(test_aircraft, results))
    
    # Stokastik bulgular
    findings = get_all_non_routine_findings(results)
    if findings:
        print("\n📊 STOCHASTIC SIMULATION RESULTS:")
        for check_type, finding in findings:
            print(f"   • {check_type}: {finding.description}")
            print(f"     Extra delay: +{finding.extra_days} days")
            print(f"     Reference: {finding.academic_reference}")
