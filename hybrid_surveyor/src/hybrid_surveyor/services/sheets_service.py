"""
Google Sheets service with async support and robust error handling.

This service combines the simplicity of gspread with async patterns,
comprehensive error handling, rate limiting, and retry logic.
"""

import asyncio
import gspread
import pandas as pd
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime, timedelta
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow

from ..core.interfaces import ISheetsService
from ..core.exceptions import (
    AuthenticationError, DataExtractionError, RateLimitError,
    TemporaryServiceError, ConfigurationError
)
from ..models.domain import SpreadsheetInfo, WorksheetInfo
from ..config.settings import GoogleSheetsSettings
from ..utils.retry_strategy import IRetryStrategy

logger = logging.getLogger(__name__)


class GoogleSheetsService(ISheetsService):
    """
    Async Google Sheets service with comprehensive error handling.
    
    Features:
    - Async/await support using asyncio
    - Rate limiting and retry logic
    - Multiple authentication methods
    - Comprehensive error handling
    - Data validation and type conversion
    """
    
    def __init__(
        self,
        settings: GoogleSheetsSettings,
        retry_strategy: IRetryStrategy
    ):
        self.settings = settings
        self.retry_strategy = retry_strategy
        self._client: Optional[gspread.Client] = None
        self._rate_limiter = RateLimiter(
            requests_per_period=settings.rate_limit_requests,
            period_seconds=settings.rate_limit_period
        )
        
    async def _get_client(self) -> gspread.Client:
        """Get authenticated gspread client with caching."""
        if self._client is None:
            self._client = await self._create_client()
        return self._client
    
    async def _create_client(self) -> gspread.Client:
        """Create and authenticate gspread client."""
        try:
            # Try service account authentication first
            if self.settings.credentials_file:
                logger.info("Authenticating with service account credentials")
                creds = Credentials.from_service_account_file(
                    str(self.settings.credentials_file),
                    scopes=self.settings.scopes
                )
                return gspread.authorize(creds)
            
            # Try OAuth authentication
            elif self.settings.client_secrets_file:
                logger.info("Authenticating with OAuth credentials")
                creds = await self._get_oauth_credentials()
                return gspread.authorize(creds)
            
            # Try default credentials
            else:
                logger.info("Attempting default authentication")
                return gspread.service_account()
                
        except (DefaultCredentialsError, FileNotFoundError) as e:
            raise AuthenticationError(
                "Failed to authenticate with Google Sheets API",
                details={"error": str(e)},
                cause=e
            )
        except Exception as e:
            raise AuthenticationError(
                "Unexpected authentication error",
                details={"error": str(e)},
                cause=e
            )
    
    async def _get_oauth_credentials(self) -> OAuthCredentials:
        """Get OAuth credentials with token caching."""
        token_file = "token.json"
        creds = None
        
        # Load existing token
        try:
            if Path(token_file).exists():
                creds = OAuthCredentials.from_authorized_user_file(
                    token_file, self.settings.scopes
                )
        except Exception as e:
            logger.warning(f"Failed to load existing token: {e}")
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Failed to refresh token: {e}")
                    creds = None
            
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.settings.client_secrets_file),
                    self.settings.scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            try:
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")
        
        return creds
    
    def extract_spreadsheet_id(self, sheet_url: str) -> str:
        """Extract spreadsheet ID from Google Sheets URL."""
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, sheet_url)
        
        if not match:
            raise DataExtractionError(
                "Invalid Google Sheets URL format",
                details={"url": sheet_url}
            )
        
        return match.group(1)
    
    def _extract_gid(self, sheet_url: str) -> Optional[str]:
        """Extract worksheet GID from URL."""
        pattern = r'[#&]gid=([0-9]+)'
        match = re.search(pattern, sheet_url)
        return match.group(1) if match else None
    
    async def get_spreadsheet_info(self, sheet_url: str) -> SpreadsheetInfo:
        """Get comprehensive spreadsheet information."""
        async def _get_info():
            await self._rate_limiter.acquire()
            
            client = await self._get_client()
            spreadsheet_id = self.extract_spreadsheet_id(sheet_url)
            
            try:
                spreadsheet = client.open_by_key(spreadsheet_id)
                worksheets = spreadsheet.worksheets()
                
                worksheet_infos = [
                    WorksheetInfo(
                        id=str(ws.id),
                        title=ws.title,
                        row_count=ws.row_count,
                        column_count=ws.col_count,
                        gid=str(ws.id)
                    )
                    for ws in worksheets
                ]
                
                return SpreadsheetInfo(
                    id=spreadsheet_id,
                    title=spreadsheet.title,
                    url=sheet_url,
                    worksheets=worksheet_infos
                )
                
            except gspread.exceptions.APIError as e:
                if "RATE_LIMIT_EXCEEDED" in str(e):
                    raise RateLimitError(
                        "Google Sheets API rate limit exceeded",
                        retry_after=60,
                        details={"error": str(e)}
                    )
                elif "SERVICE_UNAVAILABLE" in str(e):
                    raise TemporaryServiceError(
                        "Google Sheets API temporarily unavailable",
                        retry_after=30,
                        details={"error": str(e)}
                    )
                else:
                    raise DataExtractionError(
                        "Google Sheets API error",
                        details={"error": str(e), "spreadsheet_id": spreadsheet_id}
                    )
            except Exception as e:
                raise DataExtractionError(
                    "Failed to get spreadsheet info",
                    details={"error": str(e), "spreadsheet_id": spreadsheet_id},
                    cause=e
                )
        
        return await self.retry_strategy.execute_with_retry(_get_info)
    
    async def get_worksheet_data(
        self,
        sheet_url: str,
        worksheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """Get data from a specific worksheet."""
        async def _get_data():
            await self._rate_limiter.acquire()
            
            client = await self._get_client()
            spreadsheet_id = self.extract_spreadsheet_id(sheet_url)
            
            try:
                spreadsheet = client.open_by_key(spreadsheet_id)
                
                # Select worksheet
                if worksheet_name:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                else:
                    gid = self._extract_gid(sheet_url)
                    if gid:
                        worksheets = spreadsheet.worksheets()
                        worksheet = next(
                            (ws for ws in worksheets if str(ws.id) == gid),
                            spreadsheet.sheet1
                        )
                    else:
                        worksheet = spreadsheet.sheet1
                
                # Get all data
                data = worksheet.get_all_records()
                
                if not data:
                    logger.warning(f"No data found in worksheet: {worksheet.title}")
                    return pd.DataFrame()
                
                # Convert to DataFrame and clean
                df = pd.DataFrame(data)
                df = df.replace('', None)  # Replace empty strings with None
                
                logger.info(
                    f"Retrieved {len(df)} rows from worksheet '{worksheet.title}' "
                    f"in spreadsheet '{spreadsheet.title}'"
                )
                
                return df
                
            except gspread.exceptions.WorksheetNotFound as e:
                raise DataExtractionError(
                    f"Worksheet not found: {worksheet_name}",
                    details={"worksheet_name": worksheet_name, "spreadsheet_id": spreadsheet_id}
                )
            except gspread.exceptions.APIError as e:
                if "RATE_LIMIT_EXCEEDED" in str(e):
                    raise RateLimitError(
                        "Google Sheets API rate limit exceeded",
                        retry_after=60,
                        details={"error": str(e)}
                    )
                else:
                    raise DataExtractionError(
                        "Google Sheets API error",
                        details={"error": str(e), "spreadsheet_id": spreadsheet_id}
                    )
            except Exception as e:
                raise DataExtractionError(
                    "Failed to get worksheet data",
                    details={
                        "error": str(e),
                        "spreadsheet_id": spreadsheet_id,
                        "worksheet_name": worksheet_name
                    },
                    cause=e
                )
        
        return await self.retry_strategy.execute_with_retry(_get_data)
    
    async def get_all_worksheets(self, sheet_url: str) -> List[WorksheetInfo]:
        """Get information about all worksheets."""
        spreadsheet_info = await self.get_spreadsheet_info(sheet_url)
        return spreadsheet_info.worksheets


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, requests_per_period: int, period_seconds: int):
        self.requests_per_period = requests_per_period
        self.period_seconds = period_seconds
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self._lock:
            now = datetime.utcnow()
            
            # Remove old requests outside the current period
            cutoff = now - timedelta(seconds=self.period_seconds)
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            # Check if we can make a request
            if len(self.requests) >= self.requests_per_period:
                # Calculate how long to wait
                oldest_request = min(self.requests)
                wait_time = self.period_seconds - (now - oldest_request).total_seconds()
                
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # Recursive call after waiting
            
            # Record this request
            self.requests.append(now)
