# 🪐 Exoplanet Analysis Agent System (Ashtasiddhi)

A complete multi-agent system for exoplanet research using Python, designed to analyze research papers, extract key data, and perform simulations using GalSim and GREAT3.

## 🌟 Features

- **PDF Analysis**: Extract chemical composition, radial velocity data, transit parameters, and habitability metrics
- **Chemical Detection**: Identify H2O, H2S, SO2, CH4, CO2, sulfur compounds, and other atmospheric species
- **Transit Analysis**: Calculate transit depth, radius ratios, and planetary radii
- **Radial Velocity**: Compute minimum masses using RV amplitude and orbital periods
- **Habitability Assessment**: Determine Goldilocks zone status using insolation calculations
- **Paper Search**: Automated search of arXiv and other repositories
- **Simulations**: GalSim-based transit light curve simulations
- **Web Interface**: Interactive Streamlit dashboard
- **REST API**: FastAPI backend for programmatic access
- **Data Storage**: SQLite database with export capabilities

## 🏗️ Architecture

### Agent Hierarchy

| Agent | File | Role |
|-------|------|------|
| **Anima** | `Anima.py` | Master orchestrator - manages all operations |
| **Prakamya** | `Prakamya.py` | Keywords extraction from PDFs using NLP |
| **Laghima** | `Laghima.py` | Paper search via arXiv and CatalyzeX |
| **Prapti** | `Prapti.py` | Repository management (GalSim, GREAT3) |
| **Garima** | `Garima.py` | Analysis engine - computes all metrics |
| **Isitva** | `Isitva.py` | Unified data storage with SQLite |
| **Vasitva** | `Vasitva.py` | Streamlit UI and visualization |
| **Mahima** | `Mahima.py` | Backend operations and Docker management |

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd ashtasiddhi/repo

# Build and run with Docker Compose
docker-compose up --build

# Access the interfaces
# Streamlit UI: http://localhost:8501
# API Documentation: http://localhost:8000/docs
```

### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Setup external repositories
python Prapti.py setup

# Run the system
python Anima.py --ui  # Start Streamlit UI
# OR
python Anima.py --api  # Start FastAPI backend
```

## 📋 Usage Examples

### 1. Analyze a PDF

```bash
# Command line
python Anima.py --pdf "paper.pdf"

# Python API
from Anima import AnimaAgent
anima = AnimaAgent()
results = anima.analyze_pdf("paper.pdf")
print(results)
```

### 2. Search Papers

```bash
# Command line
python Laghima.py exoplanet atmosphere sulfur

# Python API
papers = anima.search_papers(["exoplanet", "atmosphere", "sulfur"])
```

### 3. Run Transit Simulation

```bash
# Python API
planet_params = {
    'radius_ratio': 0.1,
    'period': 3.0,
    'inclination': 90.0,
    'n_exposures': 100
}
simulation = anima.run_simulation(planet_params)
```

### 4. Access Data

```bash
# Get analysis summary
python Isitva.py summary

# Export data
python Isitva.py export json
python Isitva.py export csv
```

## 🔬 Analysis Capabilities

### Chemical Composition Analysis
- **Atmospheric Species**: H2O, H2S, SO2, CH4, CO2, H2, He, N2
- **Abundance Extraction**: Quantitative values with units (ppm, ppb, %)
- **Unique Materials**: TiO2, VO, metals, clouds, aerosols

### Radial Velocity Analysis
- **Parameter Extraction**: K velocity, orbital period, eccentricity
- **Mass Calculation**: M sin i = (P/2πG)^{1/3} × K × (1-e²)^{1/2}
- **Minimum Mass**: Computed assuming sin(i) = 1

### Transit Method Analysis
- **Transit Depth**: δ = (Rp/R*)²
- **Radius Calculation**: Planet radius from flux measurements
- **Period Detection**: Transit timing analysis

### Habitability Assessment
- **Insolation**: S_eff = L/(4πa²)
- **Habitable Zone**: Conservative bounds (0.95-1.37 √L_star AU)
- **Goldilocks Status**: 0.2 ≤ S_eff ≤ 1.1 S_Earth

## 🖥️ Web Interface

The Streamlit dashboard provides:

- **Dashboard**: Overview statistics and charts
- **PDF Analysis**: Upload and analyze papers
- **Paper Search**: Find relevant research
- **Data Explorer**: Filter and visualize results
- **Simulations**: Interactive transit modeling

Access at `http://localhost:8501` after starting the UI.

## 🔌 API Endpoints

FastAPI provides REST endpoints:

- `POST /analyze` - Analyze PDF file
- `POST /upload-and-analyze` - Upload and analyze
- `POST /search-papers` - Search academic papers  
- `POST /simulate` - Run transit simulation
- `GET /summary` - Analysis summary
- `GET /exoplanets` - Filtered exoplanet data
- `GET /export/{format}` - Export data

API docs available at `http://localhost:8000/docs`

## 📊 Data Schema

### Exoplanets Table
```sql
CREATE TABLE exoplanets (
    id INTEGER PRIMARY KEY,
    pdf_path TEXT,
    filename TEXT,
    timestamp TEXT,
    
    -- Chemical composition flags
    h2o_detected BOOLEAN,
    h2s_detected BOOLEAN,
    sulfur_detected BOOLEAN,
    
    -- Radial velocity data
    rv_k_velocity REAL,
    rv_minimum_mass REAL,
    
    -- Transit data
    transit_depth REAL,
    planet_radius_earth REAL,
    
    -- Habitability
    in_habitable_zone BOOLEAN,
    insolation REAL,
    habitability_index REAL
);
```

## 🧪 Testing

Create a test PDF or use the example:

```bash
# Test with sample data
python Anima.py --pdf "example_exoplanet_paper.pdf"

# Check system status
python Mahima.py --status

# Validate installation
python Mahima.py --check-requirements
```

## 🐳 Docker Details

### Build Options

```bash
# Standard build
docker build -t exoplanet-analysis .

# Multi-service with UI
docker-compose up

# Development with live reload
docker-compose -f docker-compose.dev.yml up
```

### Volume Mapping

- `/data` - Persistent data and database
- `/app/pdfs` - PDF input directory (read-only)

## 📈 Example Output

```json
{
  "pdf_path": "WASP-39b_atmosphere.pdf",
  "chemical_composition": {
    "detected_species": ["h2o", "h2s", "so2"],
    "abundances": {
      "h2o": {"value": 150, "unit": "ppm"},
      "h2s": {"value": 1, "unit": "ppm"}
    }
  },
  "habitable_zone": {
    "in_habitable_zone": false,
    "insolation": 45.2
  },
  "computed_metrics": {
    "habitability_index": 0.15,
    "atmospheric_detectability": 0.7
  }
}
```

## 🛠️ Configuration

### Environment Variables

- `DATA_DIR` - Data directory path (default: `/data`)
- `PYTHONPATH` - Python path for imports

### External Repositories

The system automatically clones:
- **GalSim**: Galaxy simulation toolkit
- **GREAT3**: Gravitational lensing challenge data

## 📝 Development

### Adding New Agents

1. Create agent file following naming convention
2. Implement required methods
3. Register with Anima orchestrator
4. Add to imports and initialization

### Extending Analysis

- Add patterns to `Garima.py` for new detection methods
- Extend chemical species in `Prakamya.py`
- Add visualization in `Vasitva.py`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📚 References

- **GalSim**: [github.com/GalSim-developers/GalSim](https://github.com/GalSim-developers/GalSim)
- **GREAT3**: Gravitational lensing accuracy testing
- **arXiv API**: Academic paper search
- **Exoplanet Detection Methods**: Transit photometry, radial velocity
- **Habitability Metrics**: Habitable zone calculations

## 📄 License

[Specify your license here]

## 🆘 Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **GalSim installation fails**:
   ```bash
   pip install galsim --no-cache-dir
   ```

3. **PDF extraction errors**:
   - Ensure PDF is not corrupted
   - Check file permissions

4. **Database locked**:
   ```bash
   python Isitva.py backup  # Create backup first
   ```

### Getting Help

- Check logs in `/data/logs/`
- Run system diagnostics: `python Mahima.py --check-requirements`
- Validate with test PDF

## 🔄 Updates

The system supports automated updates:

```bash
# Update repositories
python Prapti.py setup

# Check for new papers
python Laghima.py "recent exoplanet discoveries"

# Backup before updates
python Isitva.py backup
```

---

**Built for the future of exoplanet research** 🚀🪐