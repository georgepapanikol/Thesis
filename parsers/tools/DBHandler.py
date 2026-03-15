import psycopg2
from typing import Dict

class DBHandler:
    """Handles all database operations for resume management"""
    
    def __init__(self, db_config: Dict[str, str]):
        """
        Initialize database handler with configuration
        
        Args:
            db_config: Dictionary with keys: host, database, user, password, port
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
        
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
        
    def get_or_create_category(self, category_name: str) -> int:
        """
        Get category ID or create if doesn't exist
        
        Args:
            category_name: Name of the category
            
        Returns:
            Category ID
        """
        # Try to get existing category
        self.cursor.execute(
            "SELECT id FROM categories WHERE category_name = %s",
            (category_name,)
        )
        result = self.cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new category if doesn't exist
        self.cursor.execute(
            "INSERT INTO categories (category_name) VALUES (%s) RETURNING id",
            (category_name,)
        )
        category_id = self.cursor.fetchone()[0]
        self.conn.commit()
        print(f"  Created new category: {category_name} (ID: {category_id})")
        return category_id
        
    def insert_resume(self, source_id: str, resume_content: str, 
                     category_name: str, source_name: str) -> bool:
        """
        Insert a single resume into the database
        
        Args:
            source_id: Original ID from CSV
            resume_content: Resume text content
            category_name: Category name
            source_name: Name of the source
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get or create category
            category_id = self.get_or_create_category(category_name)
            
            # Insert resume
            self.cursor.execute("""
                INSERT INTO resumes (source_id, source_name, resume_content, category_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source_id) DO UPDATE 
                SET resume_content = EXCLUDED.resume_content,
                    category_id = EXCLUDED.category_id
            """, (source_id, source_name, resume_content, category_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"  ✗ Error inserting resume {source_id}: {e}")
            self.conn.rollback()
            return False
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self):
        """Context manager exit"""
        self.disconnect()