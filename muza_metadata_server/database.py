import sqlite3
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with open('schema.sql') as f:
            schema = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema)

    def insert_track(self, track_data: Dict) -> Dict:
        """
        Insert a track if it doesn't exist.
        
        Args:
            track_data: Dictionary containing track information
            
        Returns:
            Dict with the inserted track data
            
        Raises:
            ValueError: If required fields are missing or if UUID already exists
            sqlite3.Error: If there's a database error
        """
        required_fields = ['uuid', 'song_title']
        
        missing_fields = [field for field in required_fields if not track_data.get(field)]
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        conn = self.get_connection()
        cursor = conn.cursor()

        sanitized_data = track_data.copy()
        sanitized_data.pop('id', None)

        try:
            # Check if track with UUID already exists
            cursor.execute("SELECT id FROM music_tracks WHERE uuid = ?", (sanitized_data["uuid"],))
            if cursor.fetchone():
                error_msg = f"Track with UUID {sanitized_data['uuid']} already exists"
                logger.error(error_msg)
                raise ValueError(error_msg)

            columns = ", ".join(sanitized_data.keys())
            placeholders = ", ".join(["?"] * len(sanitized_data))
            values = list(sanitized_data.values())

            query = f"INSERT INTO music_tracks ({columns}) VALUES ({placeholders})"
            cursor.execute(query, values)
            conn.commit()

            row_id = cursor.lastrowid
            cursor.execute("SELECT * FROM music_tracks WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            return dict(row)

        except (sqlite3.Error, ValueError) as e:
            logger.error(f"Error in insert_track: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
                
    def search_tracks(
        self,
        title_contains=None,
        band_name_contains=None,
        album_title_contains=None,
        label_contains=None,
        artist_main_contains=None,
        other_artist_contains=None,
        composer_contains=None,
        min_year_recorded=None,
        max_year_recorded=None,
        min_year_released=None,
        max_year_released=None
    ):
        query = "SELECT * FROM music_tracks"
        conditions = []
        params = []

        if title_contains:
            conditions.append("LOWER(song_title) LIKE ?")
            params.append(f"%{title_contains.lower()}%")

        if band_name_contains:
            conditions.append("LOWER(band_name) LIKE ?")
            params.append(f"%{band_name_contains.lower()}%")

        if album_title_contains:
            conditions.append("LOWER(album_title) LIKE ?")
            params.append(f"%{album_title_contains.lower()}%")

        if label_contains:
            conditions.append("LOWER(label) LIKE ?")
            params.append(f"%{label_contains.lower()}%")

        if artist_main_contains:
            conditions.append("LOWER(artist_main) LIKE ?")
            params.append(f"%{artist_main_contains.lower()}%")

        if other_artist_contains:
            conditions.append("LOWER(other_artist_playing) LIKE ?")
            params.append(f"%{other_artist_contains.lower()}%")

        if composer_contains:
            conditions.append("LOWER(composer) LIKE ?")
            params.append(f"%{composer_contains.lower()}%")

        if min_year_recorded is not None:
            conditions.append("year_recorded >= ?")
            params.append(min_year_recorded)

        if max_year_recorded is not None:
            conditions.append("year_recorded <= ?")
            params.append(max_year_recorded)

        if min_year_released is not None:
            conditions.append("year_released >= ?")
            params.append(min_year_released)

        if max_year_released is not None:
            conditions.append("year_released <= ?")
            params.append(max_year_released)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database error in search_tracks: {str(e)}")
            raise
        finally:
            conn.close()

    def fetch_all_tracks(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM music_tracks")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database error in fetch_all_tracks: {str(e)}")
            raise
        finally:
            conn.close()

    def fetch_track_by_id(self, track_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM music_tracks WHERE id = ?", (track_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Database error in fetch_track_by_id: {str(e)}")
            raise
        finally:
            conn.close()
