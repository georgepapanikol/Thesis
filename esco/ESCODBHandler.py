import psycopg2
from typing import Dict, Optional


class ESCODBHandler:
    """Handles all database operations for ESCO data management"""

    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.conn = None
        self.cursor = None

        # In-memory caches to avoid repeated DB lookups
        self._skill_collection_id_cache: Dict[str, int] = {}
        self._occupation_collection_id_cache: Dict[str, int] = {}

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config.get('port', 5432)
            )
            self.cursor = self.conn.cursor()
            print("✓ Database connection established")
        except Exception as e:
            print(f"✗ Error connecting to database: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("✓ Database connection closed")

    # ------------------------------------------------------------------
    # Entity inserts
    # ------------------------------------------------------------------

    def insert_isco_group(self, id: str, url: str, preferred_label: str,
                          status: str, alt_labels: str, description: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO isco_groups (id, url, preferred_label, status, alt_labels, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    id              = EXCLUDED.id,
                    preferred_label = EXCLUDED.preferred_label,
                    status          = EXCLUDED.status,
                    alt_labels      = EXCLUDED.alt_labels,
                    description     = EXCLUDED.description
            """, (id, url, preferred_label, status, alt_labels, description))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting ISCO group {url}: {e}")
            self.conn.rollback()
            return False

    def insert_occupation(self, url: str, preferred_label: str,
                          alt_labels: str, hidden_labels: str, status: str,
                          modified_date: str, isco_group_id: int,
                          regulated_profession_note: str, scope_note: str,
                          definition: str, description: str, code: str,
                          nace_code: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO occupations (
                    url, preferred_label, alt_labels, hidden_labels,
                    status, modified_date, isco_group_id, regulated_profession_note,
                    scope_note, definition, description, code, nace_code
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO UPDATE SET
                    preferred_label = EXCLUDED.preferred_label,
                    status          = EXCLUDED.status,
                    isco_group_id   = EXCLUDED.isco_group_id,
                    description     = EXCLUDED.description
            """, (url, preferred_label, alt_labels, hidden_labels,
                  status, modified_date, isco_group_id, regulated_profession_note,
                  scope_note, definition, description, code, nace_code))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting occupation {url}: {e}")
            self.conn.rollback()
            return False

    def insert_skill_group(self, url: str, preferred_label: str,
                           alt_labels: str, hidden_labels: str, status: str,
                           modified_date: str, scope_note: str, description: str,
                           code: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO skill_groups (
                    url, preferred_label, alt_labels, hidden_labels,
                    status, modified_date, scope_note, description, code
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO UPDATE SET
                    preferred_label = EXCLUDED.preferred_label,
                    status          = EXCLUDED.status,
                    description     = EXCLUDED.description
            """, (url, preferred_label, alt_labels, hidden_labels,
                  status, modified_date, scope_note, description, code))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting skill group {url}: {e}")
            self.conn.rollback()
            return False

    def insert_skill(self, url: str, type: str, reuse_level: str,
                     preferred_label: str, alt_labels: str,
                     hidden_labels: str, status: str, modified_date: str,
                     scope_note: str, definition: str, description: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO skills (
                    url, type, reuse_level, preferred_label,
                    alt_labels, hidden_labels, status, modified_date,
                    scope_note, definition, description
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (url) DO UPDATE SET
                    preferred_label = EXCLUDED.preferred_label,
                    type            = EXCLUDED.type,
                    status          = EXCLUDED.status,
                    description     = EXCLUDED.description
            """, (url, type or None, reuse_level or None, preferred_label,
                  alt_labels, hidden_labels, status, modified_date,
                  scope_note, definition, description))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting skill {url}: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Relationship inserts
    # ------------------------------------------------------------------

    def insert_occ_skill_relation(self, occupation_url: str, skill_url: str,
                                  type: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO occupation_skill_relations
                    (occupation_id, skill_id, type)
                VALUES (
                    (SELECT id FROM occupations WHERE url = %s),
                    (SELECT id FROM skills WHERE url = %s),
                    %s
                )
                ON CONFLICT (occupation_id, skill_id) DO NOTHING
            """, (occupation_url, skill_url, type))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting occ-skill relation {occupation_url} -> {skill_url}: {e}")
            self.conn.rollback()
            return False

    def insert_skill_skill_relation(self, original_skill_url: str,
                                    related_skill_url: str, type: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO skill_skill_relations
                    (original_skill_id, related_skill_id, type)
                VALUES (
                    (SELECT id FROM skills WHERE url = %s),
                    (SELECT id FROM skills WHERE url = %s),
                    %s
                )
                ON CONFLICT (original_skill_id, related_skill_id, type) DO NOTHING
            """, (original_skill_url, related_skill_url, type or None))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting skill-skill relation: {e}")
            self.conn.rollback()
            return False

    def insert_skill_broader_group(self, skill_url: str, skill_group_url: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO skill_broader_groups (skill_id, skill_group_id)
                VALUES (
                    (SELECT id FROM skills WHERE url = %s),
                    (SELECT id FROM skill_groups WHERE url = %s)
                )
                ON CONFLICT (skill_id, skill_group_id) DO NOTHING
            """, (skill_url, skill_group_url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting skill broader group {skill_url} -> {skill_group_url}: {e}")
            self.conn.rollback()
            return False

    def insert_occupation_broader(self, occupation_url: str, broader_occupation_url: str) -> bool:
        try:
            self.cursor.execute("""
                INSERT INTO occupation_broader (occupation_id, broader_occupation_id)
                VALUES (
                    (SELECT id FROM occupations WHERE url = %s),
                    (SELECT id FROM occupations WHERE url = %s)
                )
                ON CONFLICT (occupation_id, broader_occupation_id) DO NOTHING
            """, (occupation_url, broader_occupation_url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting occupation broader {occupation_url} -> {broader_occupation_url}: {e}")
            self.conn.rollback()
            return False

    def insert_skill_broader(self, skill_url: str, broader_skill_url: str) -> bool:
        """Insert a skill-to-skill broader relation (KnowledgeSkillCompetence → KnowledgeSkillCompetence)"""
        try:
            self.cursor.execute("""
                INSERT INTO skill_broader (skill_id, broader_skill_id)
                VALUES (
                    (SELECT id FROM skills WHERE url = %s),
                    (SELECT id FROM skills WHERE url = %s)
                )
                ON CONFLICT (skill_id, broader_skill_id) DO NOTHING
            """, (skill_url, broader_skill_url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting skill broader {skill_url} -> {broader_skill_url}: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Broader URL updates (for self-referencing hierarchies)
    # ------------------------------------------------------------------

    def update_isco_broader(self, url: str, broader_url: str) -> bool:
        try:
            self.cursor.execute("""
                UPDATE isco_groups
                SET broader_isco_group_id = (SELECT id FROM isco_groups WHERE url = %s)
                WHERE url = %s
            """, (broader_url, url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error updating ISCO broader {url} -> {broader_url}: {e}")
            self.conn.rollback()
            return False

    def update_skill_group_broader(self, url: str, broader_url: str) -> bool:
        try:
            self.cursor.execute("""
                UPDATE skill_groups
                SET broader_skill_group_id = (SELECT id FROM skill_groups WHERE url = %s)
                WHERE url = %s
            """, (broader_url, url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error updating skill group broader {url} -> {broader_url}: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Green share updates
    # ------------------------------------------------------------------

    def update_green_share(self, url: str, green_share: float, table: str) -> bool:
        """Update green_share on isco_groups or occupations by URL"""
        if table not in ('isco_groups', 'occupations'):
            print(f"  ✗ Invalid table for green share: {table}")
            return False
        try:
            self.cursor.execute(
                f"UPDATE {table} SET green_share = %s WHERE url = %s",
                (green_share, url)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error updating green share on {table} for {url}: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Skill Collection helpers
    # ------------------------------------------------------------------

    def _get_or_create_skill_collection(self, collection_name: str) -> Optional[int]:
        """Return the id of a skill_collection, creating it if it doesn't exist.
        Uses an in-memory cache to avoid repeated DB round-trips."""
        if collection_name in self._skill_collection_id_cache:
            return self._skill_collection_id_cache[collection_name]
        try:
            self.cursor.execute("""
                INSERT INTO skill_collections (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, (collection_name,))
            row = self.cursor.fetchone()
            self.conn.commit()
            collection_id = row[0]
            self._skill_collection_id_cache[collection_name] = collection_id
            return collection_id
        except Exception as e:
            print(f"  ✗ Error creating skill collection '{collection_name}': {e}")
            self.conn.rollback()
            return None

    def insert_skill_collection_member(self, collection_name: str, skill_url: str) -> bool:
        """Insert a skill into a collection (by URL). Resolves both IDs internally."""
        collection_id = self._get_or_create_skill_collection(collection_name)
        if collection_id is None:
            return False
        try:
            self.cursor.execute("""
                INSERT INTO skill_collection_relations (collection_id, skill_id)
                VALUES (
                    %s,
                    (SELECT id FROM skills WHERE url = %s)
                )
                ON CONFLICT DO NOTHING
            """, (collection_id, skill_url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting skill collection member [{collection_name}] {skill_url}: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Occupation Collection helpers
    # ------------------------------------------------------------------

    def _get_or_create_occupation_collection(self, collection_name: str) -> Optional[int]:
        """Return the id of an occupation_collection, creating it if it doesn't exist."""
        if collection_name in self._occupation_collection_id_cache:
            return self._occupation_collection_id_cache[collection_name]
        try:
            self.cursor.execute("""
                INSERT INTO occupation_collections (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, (collection_name,))
            row = self.cursor.fetchone()
            self.conn.commit()
            collection_id = row[0]
            self._occupation_collection_id_cache[collection_name] = collection_id
            return collection_id
        except Exception as e:
            print(f"  ✗ Error creating occupation collection '{collection_name}': {e}")
            self.conn.rollback()
            return None

    def insert_occupation_collection_member(self, collection_name: str, occupation_url: str) -> bool:
        """Insert an occupation into a collection (by URL). Resolves both IDs internally."""
        collection_id = self._get_or_create_occupation_collection(collection_name)
        if collection_id is None:
            return False
        try:
            self.cursor.execute("""
                INSERT INTO occupation_collection_relations (collection_id, occupation_id)
                VALUES (
                    %s,
                    (SELECT id FROM occupations WHERE url = %s)
                )
                ON CONFLICT DO NOTHING
            """, (collection_id, occupation_url))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"  ✗ Error inserting occupation collection member [{collection_name}] {occupation_url}: {e}")
            self.conn.rollback()
            return False

    # ------------------------------------------------------------------
    # Utility: resolve ISCO code → URL
    # ------------------------------------------------------------------

    def get_isco_url_by_code(self, code: str) -> Optional[str]:
        """Look up an ISCO group URL by its code (e.g. '2654')"""
        try:
            self.cursor.execute(
                "SELECT url FROM isco_groups WHERE code = %s", (code,)
            )
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"  ✗ Error looking up ISCO code {code}: {e}")
            return None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()