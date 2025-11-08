"""
Experience Enrichment Module
Reads employee experience data from CSV and enriches CV data
"""
import csv
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ExperienceEnricher:
    """Handles loading and enriching CV data with years of experience"""
    
    def __init__(self, csv_path: str = "data/employee_experience.csv"):
        """
        Initialize with path to CSV file
        
        Args:
            csv_path: Path to CSV file with format: Ansatt-ID;Erfaring totalt
        """
        self.csv_path = Path(csv_path)
        self.experience_map: Dict[str, float] = {}
        self._load_experience_data()
    
    def _load_experience_data(self) -> None:
        """Load experience data from CSV file"""
        if not self.csv_path.exists():
            logger.warning(f"Experience CSV file not found: {self.csv_path}")
            logger.warning("CV enrichment will continue without experience data")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                # Read CSV with semicolon separator (utf-8-sig handles BOM)
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    employee_id = row.get('Ansatt-ID', '').strip()
                    experience_str = row.get('Erfaring totalt', '').strip()
                    
                    if not employee_id or not experience_str:
                        continue
                    
                    # Handle NaN values
                    if experience_str.upper() == 'NAN':
                        logger.debug(f"Skipping employee {employee_id} with NaN experience")
                        continue
                    
                    try:
                        # Convert Norwegian decimal comma to dot
                        experience_years = float(experience_str.replace(',', '.'))
                        self.experience_map[employee_id] = experience_years
                    except ValueError:
                        logger.warning(f"Could not parse experience for employee {employee_id}: {experience_str}")
                        continue
            
            logger.info(f"Loaded experience data for {len(self.experience_map)} employees")
            
        except Exception as e:
            logger.error(f"Error loading experience CSV: {e}")
            self.experience_map = {}
    
    def enrich_cv(self, cv_data: Dict) -> Dict:
        """
        Enrich CV data with years_of_experience field
        
        Args:
            cv_data: CV data dictionary from Flowcase API
            
        Returns:
            Enriched CV data with years_of_experience field added
        """
        # Get employee ID from external_unique_id
        employee_id = cv_data.get('external_unique_id')
        
        if not employee_id:
            logger.debug("No external_unique_id found in CV data")
            return cv_data
        
        # Convert to string for lookup
        employee_id_str = str(employee_id)
        
        # Look up experience
        experience_years = self.experience_map.get(employee_id_str)
        
        if experience_years is not None:
            cv_data['years_of_experience'] = experience_years
            logger.debug(f"Enriched CV for employee {employee_id_str} with {experience_years} years of experience")
        else:
            logger.debug(f"No experience data found for employee {employee_id_str}")
        
        return cv_data
    
    def get_experience(self, employee_id: str) -> Optional[float]:
        """
        Get years of experience for a specific employee ID
        
        Args:
            employee_id: Employee ID as string
            
        Returns:
            Years of experience as float, or None if not found
        """
        return self.experience_map.get(str(employee_id))

