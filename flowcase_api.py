#!/usr/bin/env python3
"""
Flowcase API Integration
Fetches CVs from Flowcase and saves them as individual markdown files
"""
import os
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime, timezone

import config
from experience_enrichment import ExperienceEnricher

logger = logging.getLogger(__name__)


class FlowcaseAPI:
    """
    Client for Flowcase API
    Handles authentication and CV fetching
    """
    
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Initialize Flowcase API client
        
        Args:
            api_key: Flowcase API key (defaults to config.FLOWCASE_API_KEY)
            api_url: Flowcase API base URL (defaults to config.FLOWCASE_API_URL)
        """
        self.api_key = api_key or config.FLOWCASE_API_KEY
        self.api_url = api_url or config.FLOWCASE_API_URL
        
        if not self.api_key:
            raise ValueError("Flowcase API key is required. Set FLOWCASE_API_KEY in .env")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"Initialized Flowcase API client: {self.api_url}")
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication
        
        Returns:
            True if connection is successful
        """
        try:
            # Test with /v1/users endpoint (standard Flowcase endpoint)
            response = self.session.get(f"{self.api_url}/v1/users", params={'limit': 1})
            response.raise_for_status()
            logger.info("✅ Flowcase API connection successful")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Flowcase API connection failed: {e}")
            logger.error(f"   Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            return False
    
    def list_cvs(self, limit: int = None, updated_since: str = None, offices: List[str] = None) -> List[Dict]:
        """
        List all CVs available via API (actually lists users with CVs)
        
        Args:
            limit: Maximum number of CVs to fetch (after filtering)
            updated_since: ISO date string to filter CVs updated after this date
            offices: Filter by office/location list (e.g., ["Trondheim", "Oslo", "Bergen"])
                    If None or empty, fetches all offices
            
        Returns:
            List of user metadata dictionaries (with CV info)
        """
        try:
            # Flowcase doesn't have a direct /cvs endpoint
            # We get users, which contain CV references
            # NOTE: API has default limit of 100, so we need to set a high limit to get all users
            response = self.session.get(f"{self.api_url}/v1/users", params={'limit': 1000})
            response.raise_for_status()
            users = response.json()
            
            logger.info(f"Fetched {len(users)} total users from API")
            
            # Filter out external users and deactivated users
            # Keep active consultants and international managers (both are active employees)
            initial_count = len(users)
            valid_roles = {'consultant', 'internationalmanager'}
            users = [
                u for u in users
                if u.get('role') in valid_roles  # Only consultants and international managers, not external
                and not u.get('deactivated', False)  # Not deactivated
            ]
            filtered_count = initial_count - len(users)
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} external/deactivated users (kept {len(users)} active employees)")
            
            # Filter by offices if specified
            if offices:
                users = [u for u in users if u.get('office_name') in offices]
                logger.info(f"Filtered to {len(users)} users in offices: {', '.join(offices)}")
            
            # Filter out users without default_cv_id
            users_with_cvs = [u for u in users if u.get('default_cv_id')]
            
            # Apply limit if specified
            if limit:
                users_with_cvs = users_with_cvs[:limit]
            
            logger.info(f"Found {len(users_with_cvs)} active employees with CVs")
            return users_with_cvs
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list users/CVs: {e}")
            logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
            raise
    
    def get_cv(self, user_id: str, cv_id: str) -> Dict:
        """
        Fetch a single CV by user_id and cv_id
        
        Args:
            user_id: User identifier
            cv_id: CV identifier
            
        Returns:
            Dictionary with CV data
        """
        try:
            # Flowcase v3 API uses: /v3/cvs/{user_id}/{cv_id}
            response = self.session.get(f"{self.api_url}/v3/cvs/{user_id}/{cv_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch CV {cv_id} for user {user_id}: {e}")
            raise
    
    def export_cv_json(self, user_id: str, cv_id: str, user_metadata: Dict = None, experience_enricher: ExperienceEnricher = None) -> str:
        """
        Export CV as JSON string with additional user metadata
        
        Args:
            user_id: User identifier (owner of CV)
            cv_id: CV identifier
            user_metadata: Additional metadata from user object (office, etc)
            experience_enricher: Optional enricher to add years_of_experience
            
        Returns:
            JSON string with full CV data plus metadata
        """
        try:
            import json
            # Get CV data from v3 API
            cv_data = self.get_cv(user_id, cv_id)
            
            # Enrich with years of experience if enricher provided
            if experience_enricher:
                cv_data = experience_enricher.enrich_cv(cv_data)
            
            # Add user metadata if provided (office, etc)
            if user_metadata:
                cv_data['_user_metadata'] = user_metadata
            
            # Return as formatted JSON string
            
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to export CV {cv_id} for user {user_id}: {e}")
            raise
    
    def _convert_cv_to_markdown(self, cv_data: Dict) -> str:
        """
        Convert CV JSON data to markdown format
        
        Args:
            cv_data: CV data dictionary from API
            
        Returns:
            Markdown formatted CV
        """
        lines = []
        
        # Extract basic info
        name = cv_data.get('name', cv_data.get('title', 'Unknown'))
        lines.append(f"# {name}")
        lines.append("")
        
        # Add user info if available
        if 'user' in cv_data:
            user = cv_data['user']
            if user.get('email'):
                lines.append(f"Email: {user['email']}")
            if user.get('phone'):
                lines.append(f"Phone: {user['phone']}")
            lines.append("")
        
        # Add description/summary
        if cv_data.get('description'):
            lines.append("## Summary")
            lines.append(cv_data['description'])
            lines.append("")
        
        # Add sections (skills, experience, education, etc.)
        for section in cv_data.get('sections', []):
            section_title = section.get('title', 'Section')
            lines.append(f"## {section_title}")
            
            # Add section content
            if section.get('content'):
                lines.append(section['content'])
            
            # Add section items
            for item in section.get('items', []):
                if item.get('title'):
                    lines.append(f"### {item['title']}")
                if item.get('description'):
                    lines.append(item['description'])
                lines.append("")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def download_all_cvs(
        self,
        output_dir: Path = None,
        limit: int = None,
        updated_since: str = None,
        offices: List[str] = None
    ) -> Dict[str, int]:
        """
        Download all CVs and save as individual JSON files
        
        Args:
            output_dir: Directory to save CVs (defaults to config.CVS_DIR)
            limit: Maximum number of CVs to download
            updated_since: Only download CVs updated after this date
            offices: Filter by office/location list (e.g., ["Trondheim", "Oslo", "Bergen"])
                    If None or empty, downloads from all offices
            
        Returns:
            Dictionary with statistics (success, failed, skipped, removed)
        """
        output_dir = output_dir or config.CVS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading CVs to: {output_dir}")
        if offices:
            logger.info(f"Filtering by offices: {', '.join(offices)}")
        
        # Initialize experience enricher
        experience_enricher = ExperienceEnricher()
        
        # Get list of active CVs (already filtered to exclude external/deactivated)
        cvs = self.list_cvs(limit=limit, updated_since=updated_since, offices=offices)
        
        # Build set of active CV IDs and names for cleanup
        active_cv_ids = {cv.get('default_cv_id') for cv in cvs if cv.get('default_cv_id')}
        active_names = {self._sanitize_filename(cv.get('name', '')) for cv in cvs}
        
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'removed': 0
        }
        
        # Clean up orphaned CV files (from external/deactivated users)
        if output_dir.exists():
            existing_files = list(output_dir.glob('*.json'))
            for cv_file in existing_files:
                # Check if this file belongs to an active CV
                filename_stem = cv_file.stem
                is_active = (
                    filename_stem in active_names or
                    any(cv_file.stem in self._sanitize_filename(cv.get('name', '')) 
                        for cv in cvs)
                )
                
                if not is_active:
                    # Try to read CV to check CV ID
                    try:
                        import json
                        with open(cv_file, 'r', encoding='utf-8') as f:
                            cv_data = json.load(f)
                        cv_id = cv_data.get('_id') or cv_data.get('tilbud_id')
                        
                        if cv_id not in active_cv_ids:
                            logger.info(f"Removing orphaned CV file: {cv_file.name}")
                            cv_file.unlink()
                            stats['removed'] += 1
                    except Exception as e:
                        logger.warning(f"Could not check {cv_file.name} for removal: {e}")
        
        for i, cv_meta in enumerate(cvs, 1):
            # Flowcase users have both user_id and default_cv_id
            user_id = cv_meta.get('user_id') or cv_meta.get('id')
            cv_id = cv_meta.get('default_cv_id')
            name = cv_meta.get('name', user_id)
            
            if not cv_id:
                logger.warning(f"  ⚠️  User {name} has no default_cv_id, skipping")
                stats['skipped'] += 1
                continue
            
            logger.info(f"[{i}/{len(cvs)}] Downloading: {name}")
            
            try:
                # Create filename from name
                filename = self._sanitize_filename(name) + '.json'
                output_path = output_dir / filename
                
                # Check if file exists and if CV has been updated since last download
                if output_path.exists():
                    # Get user's updated_at timestamp from API
                    user_updated_at = cv_meta.get('updated_at')
                    
                    if user_updated_at:
                        try:
                            # Parse API timestamp (UTC)
                            api_time = datetime.fromisoformat(user_updated_at.replace('Z', '+00:00'))
                            
                            # Get file modification time (naive datetime, local time)
                            file_mtime_naive = datetime.fromtimestamp(output_path.stat().st_mtime)
                            
                            # Convert API time to naive for comparison (assume local timezone is same as UTC for comparison)
                            # We compare the timestamps directly since file mtime is in local time
                            api_time_naive = api_time.replace(tzinfo=None)
                            
                            # If file is newer or equal to API timestamp, skip
                            if file_mtime_naive >= api_time_naive:
                                logger.info(f"  ⏭️  Skipped (already up to date): {filename}")
                                stats['skipped'] += 1
                                continue
                            else:
                                logger.info(f"  🔄 CV updated in API (file: {file_mtime_naive.strftime('%Y-%m-%d %H:%M')}, API: {api_time_naive.strftime('%Y-%m-%d %H:%M')}), re-downloading...")
                        except (ValueError, OSError) as e:
                            # If timestamp parsing fails, download anyway to be safe
                            logger.warning(f"  ⚠️  Could not compare timestamps for {filename}, downloading anyway: {e}")
                    elif updated_since:
                        # Fallback to old method if updated_at not available but updated_since is set
                        file_mtime = datetime.fromtimestamp(output_path.stat().st_mtime)
                        if file_mtime > datetime.fromisoformat(updated_since.replace('Z', '+00:00')):
                            logger.info(f"  ⏭️  Skipped (already up to date): {filename}")
                            stats['skipped'] += 1
                            continue
                
                # Prepare user metadata (only office info, no personal data)
                user_metadata = {
                    'office_name': cv_meta.get('office_name', ''),
                    'office_id': cv_meta.get('office_id', ''),
                }
                
                # Download CV content as JSON with metadata and experience enrichment
                content = self.export_cv_json(user_id, cv_id, user_metadata, experience_enricher)
                
                # Save to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"  ✅ Saved: {filename} ({len(content)} bytes)")
                stats['success'] += 1
                
            except Exception as e:
                logger.error(f"  ❌ Failed to download {name}: {e}")
                stats['failed'] += 1
        
        if stats['removed'] > 0:
            logger.info(f"Removed {stats['removed']} orphaned CV files (external/deactivated users)")
        
        return stats
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Convert name to safe filename
        
        Args:
            name: Person name or CV title
            
        Returns:
            Sanitized filename (without extension)
        """
        # Convert to lowercase
        filename = name.lower()
        
        # Replace Norwegian characters
        replacements = {
            'æ': 'ae',
            'ø': 'o',
            'å': 'a',
            'é': 'e',
            'è': 'e',
            'ê': 'e',
            'á': 'a',
            'à': 'a'
        }
        for old, new in replacements.items():
            filename = filename.replace(old, new)
        
        # Replace spaces and special characters with hyphens
        filename = ''.join(c if c.isalnum() or c in '-_' else '-' for c in filename)
        
        # Remove multiple consecutive hyphens
        while '--' in filename:
            filename = filename.replace('--', '-')
        
        # Strip hyphens from start/end
        filename = filename.strip('-')
        
        return filename


def test_api():
    """
    Test Flowcase API connection and list available CVs
    """
    print("=" * 60)
    print("Flowcase API Test")
    print("=" * 60)
    print()
    
    try:
        api = FlowcaseAPI()
        
        print("Testing connection...")
        if api.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return
        
        print()
        print("Fetching CV list (limit 5)...")
        cvs = api.list_cvs(limit=5)
        
        print(f"Found {len(cvs)} CVs:")
        for cv in cvs:
            print(f"  - {cv.get('name', 'Unknown')} (ID: {cv.get('id')})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check that FLOWCASE_API_KEY is set in .env")
        print("2. Verify API key is valid")
        print("3. Check Flowcase API documentation for correct endpoints")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT
    )
    
    # Run test
    test_api()

