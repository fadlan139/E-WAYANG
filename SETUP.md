# E-WAYANG Setup Guide

E-WAYANG adalah aplikasi pertunjukan wayang digital interaktif dengan camera tracking menggunakan MediaPipe dan Pygame.

## Prerequisites

- Python 3.10+
- Webcam/Camera
- Windows/Linux/macOS

## Installation

### Option 1: Using pip (Recommended)

```bash
# Clone repository
git clone https://github.com/fadlan139/E-WAYANG.git
cd E-WAYANG

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using Conda

```bash
# Clone repository
git clone https://github.com/fadlan139/E-WAYANG.git
cd E-WAYANG

# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate e-wayang
```

## Running the Application

### Start the main application:

```bash
python main.py
```

### First Run Verification

Pada first run, terminal akan menampilkan:
```
[CHECK] Semua audio, dialog, dan background ditemukan.
```

Jika ada error, aplikasi akan report missing files sebelum program dimulai.

## Controls

| Key | Function |
|-----|----------|
| `SPACE` | Lanjut ke dialog berikutnya (setelah voice selesai) |
| `F11` | Toggle Fullscreen |
| `P` | Mode Projector |
| `ESC` | Keluar aplikasi |

## Project Structure

```
E-WAYANG/
├── main.py              # Entry point aplikasi
├── rigmath.py          # Rigging dan gesture calculation
├── config.json         # Configuration settings
├── requirements.txt    # Python dependencies
├── environment.yml     # Conda environment
├── assets/             # Wayang characters and backgrounds
├── audio/              # Voice/narration MP3 files
└── story.json          # Dialog dan story configuration
```

## Configuration

Edit `config.json` untuk customize:
- Window size (width/height)
- Camera index
- Puppet positioning
- Gesture sensitivity
- Audio timing

## Troubleshooting

### Camera tidak terdeteksi
- Pastikan webcam sudah connected
- Ganti `camera_index` di `config.json` (coba 0, 1, 2, dll)

### Audio tidak terdengar
- Pastikan file MP3 ada di folder `audio/`
- Check volume system operasi
- Verify format MP3 valid

### Performance lambat
- Reduce window size di `config.json`
- Disable camera view dengan set `show_camera: false`
- Close background applications

### Dependencies error
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Atau dengan conda
conda env remove --name e-wayang
conda env create -f environment.yml
```

## System Requirements

### Minimum
- CPU: Dual-core 2.5 GHz
- RAM: 4GB
- GPU: Recommended for smooth performance
- Webcam: USB 2.0+

### Recommended
- CPU: Quad-core 3.0+ GHz
- RAM: 8GB+
- GPU: Dedicated graphics card
- Webcam: USB 3.0+

## Features

✅ Interactive wayang puppet control dengan hand tracking  
✅ Dialog system dengan audio synchronization  
✅ Multi-character support (Bima, Arjuna, Semar, Kapi Angeni)  
✅ Gesture detection (Attack, Defense, etc.)  
✅ Story mode dengan automated narration  
✅ Fullscreen dan projector mode  
✅ Real-time camera tracking dengan MediaPipe  

## Development

### Install dev dependencies
```bash
pip install -r requirements.txt
```

### Code Style
- Follow PEP 8
- Use meaningful variable names
- Add comments untuk complex logic

### Testing
```bash
pytest
```

### Linting
```bash
flake8 . --max-line-length=127
```

## License

Check LICENSE file for details.

## Support

Untuk issues atau pertanyaan:
1. Check README.md untuk catatan versi
2. Check terminal output untuk error details
3. Verify semua dependencies terinstall
4. Check `config.json` untuk settings yang salah

## Version History

- **FIX28**: Multi-character support (Semar, Kapi Angeni)
- **FIX16**: Audio/text synchronization fixes
- **Earlier**: Initial development releases

---

**Last Updated**: 2026-10-08
