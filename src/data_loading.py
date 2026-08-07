"""Data loading module for temperature and dissolved oxygen measurements.

Handles loading from both file formats:
- Temperature files (_C.csv): German format with metadata header
- Oxygen files (_CO.csv): Semicolon-delimited format
"""

import pandas as pd
from pathlib import Path
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


def load_temperature_file(filepath: Path) -> Optional[pd.DataFrame]:
    """Load temperature data from German water quality CSV files.
    
    Handles two file formats:
    1. DWD format: Metadata header with "Tageswerte Wassertemperatur" marker
    2. WaterBase format: Semicolon-delimited long format with Parameter column
    
    Args:
        filepath: Path to the temperature CSV file (as string or Path)
        
    Returns:
        DataFrame with columns: date, temperature_mean, temperature_max, temperature_min
        Returns None if file doesn't exist or loading fails
    """
    # Convert string path to Path if needed
    if isinstance(filepath, str):
        filepath = Path(filepath)
    
    if not filepath.exists():
        logger.warning(f"Temperature file not found: {filepath}")
        return None
    
    try:
        # First, detect file format by checking first 20 lines
        with open(filepath, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(20)]
        
        # Check if this is DWD format (has metadata header with "Quelle:" or "Tageswerte" marker)
        has_dwd_header = any("Quelle:" in line or "Tageswerte" in line for line in first_lines[:15])
        
        if has_dwd_header:
            # === DWD FORMAT: Metadata header + data section ===
            header_idx = None
            for i, line in enumerate(first_lines):
                if "Tageswerte" in line:
                    # Next line has column names: Datum;Mittelwert;Maximum;Minimum;...
                    header_idx = i + 1
                    break
            
            if header_idx is None:
                logger.error(f"Could not find DWD data section in {filepath}")
                return None
            
            df = pd.read_csv(filepath, sep=';', skiprows=header_idx, decimal=',')
            df.columns = df.columns.str.strip()
            
            # Map DWD column names
            df = df.rename(columns={
                'Datum': 'date',
                'Mittelwert': 'temperature_mean',
                'Maximum': 'temperature_max',
                'Minimum': 'temperature_min'
            })
            
            # Select only needed columns
            df = df[['date', 'temperature_mean', 'temperature_max', 'temperature_min']].copy()
            
            # Convert date to datetime (YYYY-MM-DD format in DWD)
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
        
        else:
            # === WATERBASE FORMAT: Semicolon-delimited, long format ===
            df = pd.read_csv(filepath, sep=';', decimal=',', quotechar='"', encoding='utf-8')
            df.columns = df.columns.str.strip().str.strip('"')
            
            # Filter for temperature parameter only
            if 'Parameter' in df.columns:
                df = df[df['Parameter'] == 'Temperatur'].copy()
                if df.empty:
                    logger.error(f"No temperature data found in {filepath}")
                    return None
            else:
                logger.error(f"No 'Parameter' column in {filepath}")
                return None
            
            # Date column is always 'Datum'
            if 'Datum' not in df.columns:
                logger.error(f"No 'Datum' column in {filepath}")
                return None
            
            # Temperature value can be in 'Messwert' or 'Tagesmittelwert'
            temp_col = None
            if 'Messwert' in df.columns:
                temp_col = 'Messwert'
            elif 'Tagesmittelwert' in df.columns:
                temp_col = 'Tagesmittelwert'
            else:
                logger.error(f"No temperature value column (Messwert/Tagesmittelwert) in {filepath}")
                return None
            
            # Select and rename relevant columns
            df = df[['Datum', temp_col]].copy()
            df.columns = ['date', 'temperature_mean']
            df['temperature_max'] = df['temperature_mean']  # Not available in long format
            df['temperature_min'] = df['temperature_mean']  # Not available in long format
            
            # Convert date to datetime (DD.MM.YYYY format in WaterBase)
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
        
        # Convert temperature to numeric, handling German decimal format
        for col in ['temperature_mean', 'temperature_max', 'temperature_min']:
            # Replace '-' and other non-numeric values with NaN
            if col in df.columns:
                df[col] = df[col].replace('-', pd.NA)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows with missing values
        df = df.dropna(subset=['temperature_mean'])
        
        logger.info(f"Loaded {len(df)} temperature observations from {filepath.name}")
        return df[['date', 'temperature_mean', 'temperature_max', 'temperature_min']]
    
    except Exception as e:
        logger.error(f"Error loading temperature file {filepath}: {e}")
        return None


def load_oxygen_file(filepath: Path) -> Optional[pd.DataFrame]:
    """Load dissolved oxygen data from WaterBase CSV format.
    
    File format: Semicolon-delimited, long format with columns:
    Parameter, Datum, Messwert/Tagesmittelwert, Dimension
    
    Args:
        filepath: Path to the oxygen CSV file (as string or Path)
        
    Returns:
        DataFrame with columns: date, oxygen_mean, unit
        Returns None if file doesn't exist
    """
    # Convert string path to Path if needed
    if isinstance(filepath, str):
        filepath = Path(filepath)
    
    if not filepath.exists():
        logger.warning(f"Oxygen file not found: {filepath}")
        return None
    
    try:
        # First, detect file format by checking first 20 lines
        with open(filepath, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(20)]
        
        # Check if this is DWD format (has metadata header with "Quelle:" marker)
        has_dwd_header = any("Quelle:" in line or "Tageswerte" in line for line in first_lines[:15])
        
        if has_dwd_header:
            # === DWD FORMAT: Metadata header + data section ===
            header_idx = None
            for i, line in enumerate(first_lines):
                if "Tageswerte" in line or "Sauerstoff" in line:
                    header_idx = i + 1
                    break
            
            if header_idx is None:
                logger.error(f"Could not find DWD oxygen data section in {filepath}")
                return None
            
            df = pd.read_csv(filepath, sep=';', skiprows=header_idx, decimal=',')
            df.columns = df.columns.str.strip()
            
            # Map DWD column names
            df = df.rename(columns={
                'Datum': 'date',
                'Tagesmittelwert': 'oxygen_mean'
            })
            
            # Get Dimension column if available
            if 'Dimension' in df.columns:
                df['unit'] = df['Dimension']
            else:
                df['unit'] = 'mg/l'
            
            # Select only needed columns
            df = df[['date', 'oxygen_mean', 'unit']].copy()
            
            # Convert date to datetime (YYYY-MM-DD format in DWD)
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            
            # Convert oxygen to numeric, handling German decimal format
            df['oxygen_mean'] = df['oxygen_mean'].replace('-', pd.NA)
            df['oxygen_mean'] = pd.to_numeric(df['oxygen_mean'], errors='coerce')
        
        else:
            # === WATERBASE FORMAT: Semicolon-delimited, long format ===
            df = pd.read_csv(filepath, sep=';', quotechar='"', decimal=',', encoding='utf-8')
            
            # Clean column names (remove leading/trailing quotes and spaces)
            df.columns = df.columns.str.strip().str.strip('"')
            
            # Filter for oxygen parameter only
            if 'Parameter' in df.columns:
                df = df[df['Parameter'] == 'Sauerstoff'].copy()
                if df.empty:
                    logger.error(f"No oxygen (Sauerstoff) data found in {filepath}")
                    return None
            else:
                logger.error(f"No 'Parameter' column in {filepath}")
                return None
            
            # Date column is always 'Datum'
            if 'Datum' not in df.columns:
                logger.error(f"No 'Datum' column in {filepath}")
                return None
            
            # Oxygen value can be in 'Messwert' or 'Tagesmittelwert'
            oxygen_col = None
            if 'Messwert' in df.columns:
                oxygen_col = 'Messwert'
            elif 'Tagesmittelwert' in df.columns:
                oxygen_col = 'Tagesmittelwert'
            else:
                logger.error(f"No oxygen value column (Messwert/Tagesmittelwert) in {filepath}")
                return None
            
            # Select and rename relevant columns
            df = df[['Datum', oxygen_col, 'Dimension']].copy()
            df.columns = ['date', 'oxygen_mean', 'unit']
            
            # Convert date to datetime (DD.MM.YYYY format in WaterBase)
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
            
            # Convert oxygen to numeric, handling German decimal format (comma)
            # Replace '-' and other non-numeric values with NaN
            df['oxygen_mean'] = df['oxygen_mean'].replace('-', pd.NA)
            df['oxygen_mean'] = pd.to_numeric(df['oxygen_mean'], errors='coerce')
        
        # Remove rows with missing values
        df = df.dropna(subset=['oxygen_mean'])
        
        logger.info(f"Loaded {len(df)} oxygen observations from {filepath.name}")
        return df[['date', 'oxygen_mean', 'unit']]
    
    except Exception as e:
        logger.error(f"Error loading oxygen file {filepath}: {e}")
        return None


def find_station_files(data_dir: Path, station_name: str, outcome: str, file_pattern: Optional[str] = None) -> list:
    """Find all data files for a given station and outcome.
    
    Args:
        data_dir: Directory containing data files
        station_name: Name of the station
        outcome: 'temperature' or 'oxygen'
        file_pattern: Optional specific file pattern (e.g., "2011-5_C") to prioritize
        
    Returns:
        List of matching file paths, prioritizing the file_pattern if provided
    """
    suffix = '_C.csv' if outcome == 'temperature' else '_CO.csv'
    
    # Try different name variations
    name_variations = [
        station_name,
        station_name.replace('-', '_'),
        station_name.replace('_', '-'),
        station_name.replace('ö', 'o'),
        station_name.replace('ü', 'u'),
    ]
    
    files = []
    for var in name_variations:
        pattern = f"{var}*{suffix}"
        matching = list(data_dir.glob(pattern))
        files.extend(matching)
    
    files = list(set(files))  # Remove duplicates
    
    # If a specific file pattern is provided, prioritize files matching that pattern
    if file_pattern and files:
        # Filter to files containing the pattern
        pattern_matches = [f for f in files if file_pattern in f.name]
        if pattern_matches:
            return sorted(pattern_matches)
    
    return sorted(files)  # Sort for consistency


if __name__ == "__main__":
    # Simple test
    from config import DATA_DIR
    
    logging.basicConfig(level=logging.INFO)
    
    # Test loading a file
    test_temp = DATA_DIR / "Landshut_Birket_2011-5_C.csv"
    test_oxygen = DATA_DIR / "Besigheim-2011-5_CO.csv"
    
    print("Testing temperature file loading...")
    temp_df = load_temperature_file(test_temp)
    if temp_df is not None:
        print(f"Loaded {len(temp_df)} rows")
        print(temp_df.head())
    
    print("\nTesting oxygen file loading...")
    oxygen_df = load_oxygen_file(test_oxygen)
    if oxygen_df is not None:
        print(f"Loaded {len(oxygen_df)} rows")
        print(oxygen_df.head())
