#!/usr/bin/env python3
"""
Survey Database Normalizer

Creates a normalized relational database structure from the raw Google Sheets data
for proper survey analysis and statistical reporting.
"""

import sqlite3
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib


class SurveyNormalizer:
    """Normalizes raw survey data into a proper relational structure."""
    
    def __init__(self, source_db: str = "surveyor_data_improved.db", target_db: str = "survey_normalized.db"):
        self.source_db = source_db
        self.target_db = target_db
        self.auto_import = True
    
    def create_normalized_schema(self):
        """Create the normalized database schema for surveys."""
        conn = sqlite3.connect(self.target_db)
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        tables_to_drop = [
            'survey_responses', 'survey_answers', 'survey_questions', 
            'surveys', 'respondents', 'normalization_jobs'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f'DROP TABLE IF EXISTS {table}')
        
        # Create surveys table
        cursor.execute('''
            CREATE TABLE surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_name TEXT NOT NULL,
                survey_type TEXT NOT NULL,
                spreadsheet_id TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(spreadsheet_id)
            )
        ''')
        
        # Create survey questions table
        cursor.execute('''
            CREATE TABLE survey_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                question_key TEXT NOT NULL,
                question_text TEXT,
                question_type TEXT DEFAULT 'text',
                question_order INTEGER,
                is_required BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (survey_id) REFERENCES surveys (id),
                UNIQUE(survey_id, question_key)
            )
        ''')
        
        # Create respondents table
        cursor.execute('''
            CREATE TABLE respondents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                respondent_hash TEXT UNIQUE NOT NULL,
                browser TEXT,
                device TEXT,
                ip_address TEXT,
                user_agent TEXT,
                first_response_date TIMESTAMP,
                last_response_date TIMESTAMP,
                total_responses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create survey responses table
        cursor.execute('''
            CREATE TABLE survey_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                respondent_id INTEGER NOT NULL,
                response_date TIMESTAMP NOT NULL,
                completion_status TEXT DEFAULT 'complete',
                response_duration_seconds INTEGER,
                source_row_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (survey_id) REFERENCES surveys (id),
                FOREIGN KEY (respondent_id) REFERENCES respondents (id),
                FOREIGN KEY (source_row_id) REFERENCES raw_data (id)
            )
        ''')
        
        # Create survey answers table
        cursor.execute('''
            CREATE TABLE survey_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT,
                answer_numeric REAL,
                answer_boolean BOOLEAN,
                answer_date TIMESTAMP,
                is_empty BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (response_id) REFERENCES survey_responses (id),
                FOREIGN KEY (question_id) REFERENCES survey_questions (id),
                UNIQUE(response_id, question_id)
            )
        ''')
        
        # Create normalization jobs table
        cursor.execute('''
            CREATE TABLE normalization_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                surveys_processed INTEGER DEFAULT 0,
                responses_processed INTEGER DEFAULT 0,
                questions_created INTEGER DEFAULT 0,
                answers_created INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT
            )
        ''')

        # Create sync tracking table
        cursor.execute('''
            CREATE TABLE sync_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spreadsheet_id TEXT UNIQUE NOT NULL,
                last_sync_timestamp TIMESTAMP,
                last_source_update TIMESTAMP,
                row_count INTEGER DEFAULT 0,
                sync_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        indexes = [
            'CREATE INDEX idx_survey_questions_survey ON survey_questions(survey_id)',
            'CREATE INDEX idx_survey_responses_survey ON survey_responses(survey_id)',
            'CREATE INDEX idx_survey_responses_respondent ON survey_responses(respondent_id)',
            'CREATE INDEX idx_survey_responses_date ON survey_responses(response_date)',
            'CREATE INDEX idx_survey_answers_response ON survey_answers(response_id)',
            'CREATE INDEX idx_survey_answers_question ON survey_answers(question_id)',
            'CREATE INDEX idx_respondents_hash ON respondents(respondent_hash)',
            'CREATE INDEX idx_respondents_first_response ON respondents(first_response_date)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        print(f"✅ Created normalized database schema: {self.target_db}")
    
    def identify_survey_types(self) -> Dict[str, str]:
        """Identify which spreadsheets contain survey data vs. question definitions."""
        conn = sqlite3.connect(self.source_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.spreadsheet_id, s.title, s.sheet_type, COUNT(r.id) as row_count
            FROM spreadsheets s
            LEFT JOIN raw_data r ON s.spreadsheet_id = r.spreadsheet_id
            GROUP BY s.spreadsheet_id, s.title, s.sheet_type
        ''')
        
        spreadsheets = cursor.fetchall()
        survey_types = {}
        
        for sheet_id, title, sheet_type, row_count in spreadsheets:
            # Analyze the data to determine if it's responses or questions
            cursor.execute('''
                SELECT data_json FROM raw_data 
                WHERE spreadsheet_id = ? 
                LIMIT 3
            ''', (sheet_id,))
            
            sample_rows = cursor.fetchall()
            
            if sample_rows:
                # Check if this looks like response data or question data
                sample_data = json.loads(sample_rows[0][0])
                
                # Look for response indicators
                response_indicators = ['Date', 'Browser', 'Device', 'Timestamp']
                question_indicators = ['Question', 'Answer', 'Option', 'Choice']
                
                response_score = sum(1 for key in sample_data.keys() 
                                   if any(indicator in key for indicator in response_indicators))
                question_score = sum(1 for key in sample_data.keys() 
                                   if any(indicator in key for indicator in question_indicators))
                
                if response_score > question_score:
                    survey_types[sheet_id] = 'responses'
                elif 'Links' in title or 'Answer Sheet' in title:
                    survey_types[sheet_id] = 'questions'
                else:
                    survey_types[sheet_id] = 'responses'  # Default assumption
            else:
                survey_types[sheet_id] = 'unknown'
        
        conn.close()
        return survey_types
    
    def create_respondent_hash(self, response_data: Dict) -> str:
        """Create a hash to identify unique respondents."""
        # Use browser, device, and rough timestamp to identify respondents
        identifier_parts = [
            response_data.get('Browser', ''),
            response_data.get('Device', ''),
            response_data.get('Date', '')[:10] if response_data.get('Date') else ''  # Date only, not time
        ]
        
        identifier_string = '|'.join(identifier_parts)
        return hashlib.sha256(identifier_string.encode()).hexdigest()[:16]
    
    def parse_response_date(self, date_string: str) -> Optional[datetime]:
        """Parse various date formats from the survey data."""
        if not date_string:
            return None
        
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%Y-%m-%d',
            '%m/%d/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None

    def check_for_new_data(self) -> Dict[str, Any]:
        """Check for new or updated data in the source database."""
        # Ensure target database exists with proper schema
        if not os.path.exists(self.target_db):
            self.create_normalized_schema()

        source_conn = sqlite3.connect(self.source_db)
        source_cursor = source_conn.cursor()

        target_conn = sqlite3.connect(self.target_db)
        target_cursor = target_conn.cursor()

        # Ensure sync_tracking table exists
        target_cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spreadsheet_id TEXT UNIQUE NOT NULL,
                last_sync_timestamp TIMESTAMP,
                last_source_update TIMESTAMP,
                row_count INTEGER DEFAULT 0,
                sync_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Get current state from source
        source_cursor.execute('''
            SELECT
                s.spreadsheet_id,
                s.title,
                s.sheet_type,
                s.last_synced,
                COUNT(r.id) as current_row_count
            FROM spreadsheets s
            LEFT JOIN raw_data r ON s.spreadsheet_id = r.spreadsheet_id
            GROUP BY s.spreadsheet_id, s.title, s.sheet_type, s.last_synced
        ''')

        source_data = source_cursor.fetchall()

        # Get sync tracking state
        target_cursor.execute('SELECT spreadsheet_id, last_sync_timestamp, row_count FROM sync_tracking')
        sync_state = {row[0]: {'last_sync': row[1], 'row_count': row[2]} for row in target_cursor.fetchall()}

        new_data = []
        updated_data = []

        for sheet_id, title, sheet_type, last_synced, row_count in source_data:
            if sheet_id not in sync_state:
                # New spreadsheet
                new_data.append({
                    'spreadsheet_id': sheet_id,
                    'title': title,
                    'sheet_type': sheet_type,
                    'row_count': row_count,
                    'status': 'new'
                })
            else:
                # Check if updated
                sync_info = sync_state[sheet_id]
                if (row_count != sync_info['row_count'] or
                    (last_synced and sync_info['last_sync'] and last_synced > sync_info['last_sync'])):
                    updated_data.append({
                        'spreadsheet_id': sheet_id,
                        'title': title,
                        'sheet_type': sheet_type,
                        'row_count': row_count,
                        'previous_count': sync_info['row_count'],
                        'status': 'updated'
                    })

        source_conn.close()
        target_conn.close()

        return {
            'new_data': new_data,
            'updated_data': updated_data,
            'total_changes': len(new_data) + len(updated_data)
        }

    def auto_import_new_data(self) -> Dict[str, Any]:
        """Automatically import any new or updated spreadsheet data."""
        print("🔍 Checking for new spreadsheet data...")

        changes = self.check_for_new_data()

        if changes['total_changes'] == 0:
            print("✅ No new data detected. Database is up to date.")
            return {'imported': 0, 'updated': 0, 'message': 'No changes detected'}

        print(f"📊 Found {len(changes['new_data'])} new and {len(changes['updated_data'])} updated spreadsheets")

        # Import new and updated data
        imported_count = 0
        updated_count = 0

        # Process new data
        for item in changes['new_data']:
            print(f"  📥 Importing new: {item['title']} ({item['row_count']} rows)")
            try:
                self.import_single_spreadsheet(item['spreadsheet_id'])
                imported_count += 1
            except Exception as e:
                print(f"    ❌ Failed to import {item['title']}: {e}")

        # Process updated data
        for item in changes['updated_data']:
            print(f"  🔄 Updating: {item['title']} ({item['previous_count']} → {item['row_count']} rows)")
            try:
                self.import_single_spreadsheet(item['spreadsheet_id'], update=True)
                updated_count += 1
            except Exception as e:
                print(f"    ❌ Failed to update {item['title']}: {e}")

        result = {
            'imported': imported_count,
            'updated': updated_count,
            'total_processed': imported_count + updated_count,
            'message': f"Successfully processed {imported_count + updated_count} spreadsheets"
        }

        print(f"✅ Auto-import completed: {result['message']}")
        return result

    def import_single_spreadsheet(self, spreadsheet_id: str, update: bool = False):
        """Import or update a single spreadsheet."""
        source_conn = sqlite3.connect(self.source_db)
        source_cursor = source_conn.cursor()

        target_conn = sqlite3.connect(self.target_db)
        target_cursor = target_conn.cursor()

        try:
            # Get spreadsheet info
            source_cursor.execute('''
                SELECT spreadsheet_id, title, sheet_type, url, last_synced
                FROM spreadsheets
                WHERE spreadsheet_id = ?
            ''', (spreadsheet_id,))

            sheet_info = source_cursor.fetchone()
            if not sheet_info:
                raise ValueError(f"Spreadsheet {spreadsheet_id} not found in source database")

            sheet_id, title, sheet_type, url, last_synced = sheet_info

            # Determine survey type
            survey_types = self.identify_survey_types()
            survey_data_type = survey_types.get(sheet_id, 'responses')

            if survey_data_type == 'responses':
                if update:
                    # Clear existing data for update
                    self.clear_spreadsheet_data(target_cursor, spreadsheet_id)

                # Process the spreadsheet
                stats = self.process_survey_responses(
                    source_cursor, target_cursor, sheet_id, title, sheet_type
                )

                # Update sync tracking
                target_cursor.execute('''
                    INSERT OR REPLACE INTO sync_tracking
                    (spreadsheet_id, last_sync_timestamp, last_source_update, row_count, sync_status, updated_at)
                    VALUES (?, ?, ?, ?, 'completed', ?)
                ''', (
                    spreadsheet_id,
                    datetime.now(),
                    last_synced,
                    stats['responses'],
                    datetime.now()
                ))

                target_conn.commit()
                print(f"    ✅ Processed {stats['responses']} responses, {stats['questions']} questions")

            else:
                print(f"    ⚠️  Skipping {title} (question definitions, not responses)")

        except Exception as e:
            # Update sync tracking with error
            target_cursor.execute('''
                INSERT OR REPLACE INTO sync_tracking
                (spreadsheet_id, sync_status, updated_at)
                VALUES (?, 'failed', ?)
            ''', (spreadsheet_id, datetime.now()))
            target_conn.commit()
            raise e

        finally:
            source_conn.close()
            target_conn.close()

    def clear_spreadsheet_data(self, target_cursor, spreadsheet_id: str):
        """Clear existing data for a spreadsheet before re-importing."""
        # Get survey ID
        target_cursor.execute('SELECT id FROM surveys WHERE spreadsheet_id = ?', (spreadsheet_id,))
        survey_result = target_cursor.fetchone()

        if survey_result:
            survey_id = survey_result[0]

            # Delete in correct order due to foreign key constraints
            target_cursor.execute('''
                DELETE FROM survey_answers
                WHERE response_id IN (
                    SELECT id FROM survey_responses WHERE survey_id = ?
                )
            ''', (survey_id,))

            target_cursor.execute('DELETE FROM survey_responses WHERE survey_id = ?', (survey_id,))
            target_cursor.execute('DELETE FROM survey_questions WHERE survey_id = ?', (survey_id,))
            target_cursor.execute('DELETE FROM surveys WHERE id = ?', (survey_id,))

            print(f"    🗑️  Cleared existing data for re-import")

    def normalize_survey_data(self):
        """Main method to normalize all survey data."""
        print("🔄 Starting survey data normalization...")

        # Create normalized schema
        self.create_normalized_schema()

        # Auto-import new data if enabled
        if self.auto_import:
            auto_result = self.auto_import_new_data()
            if auto_result['total_processed'] > 0:
                print(f"📥 Auto-imported {auto_result['total_processed']} spreadsheets")
                return auto_result
        
        # Create normalization job
        target_conn = sqlite3.connect(self.target_db)
        target_cursor = target_conn.cursor()
        
        job_name = f"normalization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target_cursor.execute('''
            INSERT INTO normalization_jobs (job_name)
            VALUES (?)
        ''', (job_name,))
        job_id = target_cursor.lastrowid
        target_conn.commit()
        
        try:
            # Identify survey types
            survey_types = self.identify_survey_types()
            print(f"📊 Identified survey types: {survey_types}")
            
            # Process each spreadsheet
            source_conn = sqlite3.connect(self.source_db)
            source_cursor = source_conn.cursor()
            
            # Get all spreadsheets
            source_cursor.execute('''
                SELECT spreadsheet_id, title, sheet_type, url
                FROM spreadsheets
                ORDER BY title
            ''')
            
            spreadsheets = source_cursor.fetchall()
            surveys_processed = 0
            responses_processed = 0
            questions_created = 0
            answers_created = 0
            
            for sheet_id, title, sheet_type, url in spreadsheets:
                print(f"\n📋 Processing: {title}")
                
                survey_data_type = survey_types.get(sheet_id, 'unknown')
                
                if survey_data_type == 'responses':
                    # Process as survey responses
                    stats = self.process_survey_responses(
                        source_cursor, target_cursor, sheet_id, title, sheet_type
                    )
                    surveys_processed += 1
                    responses_processed += stats['responses']
                    questions_created += stats['questions']
                    answers_created += stats['answers']
                    
                elif survey_data_type == 'questions':
                    # Process as question definitions
                    print(f"  📝 Processing question definitions...")
                    # This could be used to enhance question metadata
                    
                else:
                    print(f"  ⚠️  Unknown data type, skipping...")
            
            # Update job status
            target_cursor.execute('''
                UPDATE normalization_jobs 
                SET status = 'completed',
                    completed_at = ?,
                    surveys_processed = ?,
                    responses_processed = ?,
                    questions_created = ?,
                    answers_created = ?
                WHERE id = ?
            ''', (datetime.now(), surveys_processed, responses_processed, 
                  questions_created, answers_created, job_id))
            
            target_conn.commit()
            
            print(f"\n✅ Normalization completed successfully!")
            print(f"📈 Surveys processed: {surveys_processed}")
            print(f"📝 Responses processed: {responses_processed}")
            print(f"❓ Questions created: {questions_created}")
            print(f"💬 Answers created: {answers_created}")
            
        except Exception as e:
            # Mark job as failed
            target_cursor.execute('''
                UPDATE normalization_jobs 
                SET status = 'failed',
                    completed_at = ?,
                    error_message = ?
                WHERE id = ?
            ''', (datetime.now(), str(e), job_id))
            target_conn.commit()
            print(f"❌ Normalization failed: {e}")
            raise
        
        finally:
            source_conn.close()
            target_conn.close()
    
    def process_survey_responses(self, source_cursor, target_cursor, sheet_id: str, 
                               title: str, sheet_type: str) -> Dict[str, int]:
        """Process survey response data from a spreadsheet."""
        
        # Create or get survey record
        target_cursor.execute('''
            INSERT OR IGNORE INTO surveys (survey_name, survey_type, spreadsheet_id, description)
            VALUES (?, ?, ?, ?)
        ''', (title, sheet_type, sheet_id, f"Survey data from {title}"))
        
        target_cursor.execute('''
            SELECT id FROM surveys WHERE spreadsheet_id = ?
        ''', (sheet_id,))
        survey_id = target_cursor.fetchone()[0]
        
        # Get all raw data for this spreadsheet
        source_cursor.execute('''
            SELECT id, row_number, data_json
            FROM raw_data
            WHERE spreadsheet_id = ?
            ORDER BY row_number
        ''', (sheet_id,))
        
        raw_rows = source_cursor.fetchall()
        
        if not raw_rows:
            return {'responses': 0, 'questions': 0, 'answers': 0}
        
        # Analyze first row to identify questions
        first_row_data = json.loads(raw_rows[0][2])
        question_keys = [key for key in first_row_data.keys() 
                        if not key.startswith('_') and key not in ['Date', 'Browser', 'Device']]
        
        questions_created = 0
        
        # Create question records
        for i, question_key in enumerate(question_keys):
            target_cursor.execute('''
                INSERT OR IGNORE INTO survey_questions 
                (survey_id, question_key, question_text, question_order)
                VALUES (?, ?, ?, ?)
            ''', (survey_id, question_key, question_key, i + 1))
            
            if target_cursor.rowcount > 0:
                questions_created += 1
        
        responses_processed = 0
        answers_created = 0
        
        # Process each response
        for row_id, row_number, data_json in raw_rows:
            try:
                response_data = json.loads(data_json)
                
                # Create or get respondent
                respondent_hash = self.create_respondent_hash(response_data)
                
                target_cursor.execute('''
                    INSERT OR IGNORE INTO respondents 
                    (respondent_hash, browser, device, first_response_date, total_responses)
                    VALUES (?, ?, ?, ?, 1)
                ''', (
                    respondent_hash,
                    response_data.get('Browser', ''),
                    response_data.get('Device', ''),
                    self.parse_response_date(response_data.get('Date', ''))
                ))
                
                # Update respondent stats
                target_cursor.execute('''
                    UPDATE respondents 
                    SET last_response_date = ?,
                        total_responses = total_responses + 1
                    WHERE respondent_hash = ?
                ''', (self.parse_response_date(response_data.get('Date', '')), respondent_hash))
                
                # Get respondent ID
                target_cursor.execute('''
                    SELECT id FROM respondents WHERE respondent_hash = ?
                ''', (respondent_hash,))
                respondent_id = target_cursor.fetchone()[0]
                
                # Create response record
                target_cursor.execute('''
                    INSERT INTO survey_responses 
                    (survey_id, respondent_id, response_date, source_row_id)
                    VALUES (?, ?, ?, ?)
                ''', (
                    survey_id,
                    respondent_id,
                    self.parse_response_date(response_data.get('Date', '')),
                    row_id
                ))
                
                response_id = target_cursor.lastrowid
                responses_processed += 1
                
                # Create answer records
                for question_key in question_keys:
                    # Get question ID
                    target_cursor.execute('''
                        SELECT id FROM survey_questions 
                        WHERE survey_id = ? AND question_key = ?
                    ''', (survey_id, question_key))
                    
                    question_result = target_cursor.fetchone()
                    if not question_result:
                        continue
                    
                    question_id = question_result[0]
                    answer_value = response_data.get(question_key, '')
                    
                    # Parse answer value
                    answer_text = str(answer_value) if answer_value else None
                    answer_numeric = None
                    answer_boolean = None
                    is_empty = not bool(answer_value)
                    
                    # Try to parse as numeric
                    if answer_value and str(answer_value).replace('.', '').replace('-', '').isdigit():
                        try:
                            answer_numeric = float(answer_value)
                        except ValueError:
                            pass
                    
                    # Try to parse as boolean
                    if str(answer_value).lower() in ['true', 'false', 'yes', 'no', '1', '0']:
                        answer_boolean = str(answer_value).lower() in ['true', 'yes', '1']
                    
                    target_cursor.execute('''
                        INSERT INTO survey_answers 
                        (response_id, question_id, answer_text, answer_numeric, 
                         answer_boolean, is_empty)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        response_id, question_id, answer_text, answer_numeric,
                        answer_boolean, is_empty
                    ))
                    
                    answers_created += 1
                
            except Exception as e:
                print(f"  ⚠️  Error processing row {row_number}: {e}")
                continue
        
        print(f"  ✅ Processed {responses_processed} responses, {questions_created} questions, {answers_created} answers")
        
        return {
            'responses': responses_processed,
            'questions': questions_created,
            'answers': answers_created
        }


def main():
    """Main function to run the survey normalization."""
    import sys

    print("🔄 Survey Database Normalizer")
    print("=" * 50)

    # Check command line arguments
    auto_mode = '--auto' in sys.argv or '-a' in sys.argv
    force_full = '--full' in sys.argv or '-f' in sys.argv

    normalizer = SurveyNormalizer()

    if auto_mode and not force_full:
        # Auto-import mode: only process new/updated data
        print("🤖 Running in auto-import mode (new/updated data only)")
        normalizer.auto_import = True

        try:
            # Check if normalized database exists
            if not os.path.exists(normalizer.target_db):
                print("📊 Normalized database not found, creating initial structure...")
                normalizer.create_normalized_schema()

            result = normalizer.auto_import_new_data()

            if result['total_processed'] > 0:
                print(f"\n✅ Auto-import completed successfully!")
                print(f"📥 Imported: {result['imported']} new spreadsheets")
                print(f"🔄 Updated: {result['updated']} existing spreadsheets")
            else:
                print(f"\n✅ {result['message']}")

            print(f"💾 Normalized database: {normalizer.target_db}")

        except Exception as e:
            print(f"\n❌ Auto-import failed: {e}")
            return 1

    else:
        # Full normalization mode
        if force_full:
            print("🔄 Running full normalization (forced)")
        else:
            print("🔄 Running full normalization")

        normalizer.auto_import = False

        try:
            normalizer.normalize_survey_data()
            print(f"\n💾 Normalized database created: {normalizer.target_db}")

        except Exception as e:
            print(f"\n❌ Normalization failed: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
