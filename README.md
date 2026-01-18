# THY Aircraft Maintenance Planning System 🛫

## Decision Support System for Turkish Airlines Fleet Management

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A sophisticated Decision Support System (DSS) developed for Turkish Airlines (THY) fleet maintenance planning. This system incorporates **stochastic modeling** and **resource constraints** based on academic literature for realistic maintenance scheduling.

---

## 📚 Academic References

This project is built upon peer-reviewed research:

| Reference | Key Contribution |
|-----------|-----------------|
| **Papakostas et al. (2010)** | Phased/Block Maintenance approach |
| **Callewaert et al. (2017)** | Stochastic maintenance duration (NRF) |
| **Kowalski et al. (2021)** | Resource-constrained scheduling |
| **Hollander (2025)** | Uncertainty quantification |

---

## 🚀 Features

### Core Functionality
- ✅ **Real-time Maintenance Status** - A, B, C, D check progress tracking
- ✅ **Stochastic Simulation** - 15% Non-Routine Finding (NRF) probability
- ✅ **Resource Constraints** - Hangar capacity limitations (5 wide-body max)
- ✅ **Visual Dashboard** - Premium dark theme with progress bars
- ✅ **Algorithm Flowchart** - Graphviz-powered decision tree visualization

### Fleet Coverage
- 283 aircraft across 14 model types
- Boeing: 737-800, 737-900ER, 737 MAX 8, 777-300ER, 787-9, 777F
- Airbus: A319, A320, A320 NEO, A321, A321 NEO, A330-200, A330-300, A350-900

---

## 📦 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/thy-maintenance-system.git
cd thy-maintenance-system

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Dependencies
```
streamlit>=1.28.0
pandas>=2.0.0
graphviz>=0.20
```

---

## 🖥️ Usage

1. **Select Aircraft Model** - Use the sidebar dropdown to filter by model type
2. **Choose Registration** - Select specific aircraft by tail number
3. **Enable Stochastic Model** - Toggle to simulate non-routine findings
4. **View Dashboard** - Monitor maintenance status with progress bars
5. **Check Flowchart** - Visualize the decision algorithm
6. **Read Academic References** - Understand the theoretical background

---

## 📊 Maintenance Intervals

| Check Type | FH Limit | FC Limit | Time Limit | Duration |
|------------|----------|----------|------------|----------|
| A Check | 600 | 400 | - | 1 day |
| B Check (Phased) | - | - | 180 days | 3 days |
| C Check | 6,000 | - | 730 days | 7 days |
| D Check | - | - | 2,190 days | 30 days |

---

## 🔬 Stochastic Model

Based on Callewaert et al. (2017), the system simulates:

```
T_actual = T_base + T_NRF

Where:
- T_base = Planned maintenance duration
- T_NRF = Non-routine finding delay (P=0.15, range: 1-3 days)
```

**Non-Routine Finding Types:**
- Corrosion (8% probability)
- Fatigue Crack (5% probability)
- System Malfunction (2% probability)

---

## 📁 Project Structure

```
thy-maintenance-system/
├── app.py              # Main Streamlit application
├── data.py             # Fleet data generation module
├── logic.py            # Maintenance calculation logic
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 🎓 Academic Context

This project was developed as a **Graduation Project** for Industrial Engineering studies. It demonstrates:

1. **Operations Research** - Decision support systems
2. **Stochastic Modeling** - Uncertainty in planning
3. **Resource Optimization** - Constraint management
4. **Data Visualization** - Interactive dashboards

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Industrial Engineering Graduate Project**

*University Graduation Thesis 2026*

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📧 Contact

For questions or feedback, please open an issue on GitHub.
