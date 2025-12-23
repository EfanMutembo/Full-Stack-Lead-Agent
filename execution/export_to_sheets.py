"""
Export leads to Google Sheets with formatting.

Usage:
    python export_to_sheets.py --input full_leads.json --title "Leads - SaaS - 2024-12-02"
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']


def get_google_credentials():
    """Get Google OAuth credentials, prompting for auth if needed."""
    creds = None

    # Check for existing token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                return None, "credentials.json not found. Please download from Google Cloud Console."

            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Use fixed port 8080 for OAuth redirect
            creds = flow.run_local_server(port=8080)

        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds, None


def get_lead_segment(lead, segment_mapping):
    """
    Find which segment this lead belongs to based on job title.

    Args:
        lead (dict): Lead data
        segment_mapping (dict): Segment mapping data with segments array

    Returns:
        str: Segment name or "Unknown"
    """
    if not segment_mapping:
        return ""

    job_title = (lead.get('job_title') or lead.get('title') or '').lower()

    if not job_title:
        return "Unknown"

    # Look up job title in segment definitions
    for segment in segment_mapping.get('segments', []):
        job_titles_in_segment = [t.lower() for t in segment.get('job_titles', [])]
        if job_title in job_titles_in_segment:
            return segment.get('segment_name', 'Unknown')

    # Default to Executive Leadership if not found
    return "Executive Leadership"


def export_to_sheets(input_file, sheet_title=None, segments_file=None):
    """
    Export leads to a new Google Sheet.

    Args:
        input_file (str): Path to JSON file with leads
        sheet_title (str): Title for the Google Sheet
        segments_file (str, optional): Path to segment mapping JSON file

    Returns:
        dict: Results with sheet URL and status
    """

    # Load leads
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            leads = json.load(f)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"Input file not found: {input_file}"
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Invalid JSON in file: {input_file}"
        }

    if not leads:
        return {
            "status": "error",
            "message": "No leads found in input file"
        }

    # Load segment mapping if provided
    segment_mapping = None
    if segments_file and os.path.exists(segments_file):
        try:
            with open(segments_file, 'r', encoding='utf-8') as f:
                segment_mapping = json.load(f)
            print(f"✅ Loaded segment mapping with {len(segment_mapping.get('segments', []))} segments")
        except Exception as e:
            print(f"⚠️  Warning: Could not load segment mapping: {str(e)}")

    print(f"📊 Exporting {len(leads)} leads to Google Sheets...")

    # Get credentials
    creds, error = get_google_credentials()
    if error:
        return {"status": "error", "message": error}

    try:
        # Build services
        sheets_service = build('sheets', 'v4', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Generate title if not provided
        if not sheet_title:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            sheet_title = f"Leads Export - {timestamp}"

        # Create new spreadsheet
        spreadsheet = {
            'properties': {'title': sheet_title}
        }
        spreadsheet = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()

        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')

        print(f"✅ Created spreadsheet: {sheet_title}")
        print(f"   ID: {spreadsheet_id}")

        # Prepare data - headers include new Segment and Job Title columns
        headers = [
            "Company Name",
            "Company (Friendly)",
            "Segment",
            "Job Title",
            "Industry/Category",
            "Website",
            "Email",
            "Phone",
            "Location",
            "LinkedIn",
            "Description"
        ]

        rows = [headers]

        for lead in leads:
            # Extract data with fallbacks for different field names
            # Apify leads-finder returns: company_name, company_website, company_description, industry, etc.
            row = [
                lead.get("company_name") or lead.get("name") or lead.get("companyName") or lead.get("title") or "",
                lead.get("company_name_normalized") or lead.get("company_name") or "",  # AI-normalized friendly name
                get_lead_segment(lead, segment_mapping),  # NEW: Segment column
                lead.get("job_title") or lead.get("title") or "",  # NEW: Job Title column
                lead.get("industry") or lead.get("category") or lead.get("type") or "",
                lead.get("company_website") or lead.get("website") or lead.get("url") or "",
                lead.get("email") or lead.get("contactEmail") or "",
                lead.get("mobile_number") or lead.get("phone") or lead.get("phoneNumber") or "",
                lead.get("company_full_address") or lead.get("location") or lead.get("address") or lead.get("city") or "",
                lead.get("linkedin") or lead.get("linkedinUrl") or "",
                lead.get("company_description") or lead.get("description") or lead.get("about") or ""
            ]
            rows.append(row)

        # Write data to sheet in chunks for better performance on large datasets
        chunk_size = 1000  # Write 1000 rows per batch

        if len(rows) <= chunk_size:
            # Small dataset: write all at once
            body = {'values': rows}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            print(f"✅ Wrote {len(rows)} rows to sheet")
        else:
            # Large dataset: write in chunks using batch API
            print(f"   Writing {len(rows)} rows in chunks of {chunk_size}...")

            # Prepare batch requests
            batch_data = []
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                start_row = i + 1  # 1-indexed
                end_row = start_row + len(chunk) - 1

                batch_data.append({
                    'range': f'A{start_row}:K{end_row}',
                    'values': chunk
                })

            # Execute batch update
            batch_body = {
                'valueInputOption': 'RAW',
                'data': batch_data
            }

            sheets_service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=batch_body
            ).execute()

            print(f"✅ Wrote {len(rows)} rows to sheet in {len(batch_data)} chunks")

        # Format the sheet
        requests = [
            # Freeze header row
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {'frozenRowCount': 1}
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            },
            # Bold header row
            {
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True},
                            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            },
            # Auto-resize columns
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': len(headers)
                    }
                }
            }
        ]

        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        print(f"✅ Applied formatting")

        # Make sheet shareable (anyone with link can view)
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission
        ).execute()

        print(f"✅ Made sheet shareable")

        return {
            "status": "success",
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "title": sheet_title,
            "rows_exported": len(rows) - 1  # Exclude header
        }

    except HttpError as e:
        error_msg = f"Google API error: {e}"
        print(f"❌ {error_msg}")
        return {"status": "error", "message": error_msg}

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"status": "error", "message": error_msg}


def main():
    parser = argparse.ArgumentParser(description="Export leads to Google Sheets")
    parser.add_argument("--input", required=True, help="Input JSON file with leads")
    parser.add_argument("--title", help="Title for the Google Sheet")
    parser.add_argument("--segments", help="Path to segment mapping JSON file (optional)")

    args = parser.parse_args()

    result = export_to_sheets(
        input_file=args.input,
        sheet_title=args.title,
        segments_file=args.segments
    )

    # Print result
    print("\n" + "="*50)
    if result["status"] == "success":
        print(f"✅ SUCCESS!")
        print(f"📄 Sheet URL: {result['spreadsheet_url']}")
        print(f"📊 Rows exported: {result['rows_exported']}")
    else:
        print(f"❌ FAILED: {result['message']}")

    print("\n" + json.dumps(result, indent=2))

    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
