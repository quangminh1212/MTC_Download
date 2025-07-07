# Changes Made to Fix Playwright Issues on Windows Python 3.12+

## Overview of the Issue
The original application encountered errors when running on Windows with Python 3.12+ due to limitations in the `asyncio.create_subprocess_exec` function, which Playwright uses internally to launch browser processes. In Python 3.12 on Windows, this function raises a `NotImplementedError`.

## Changes Implemented

### 1. Platform Detection
- Added explicit detection of Windows platform and Python 3.12+ version
- Set `WindowsSelectorEventLoopPolicy` for better compatibility with Windows

### 2. Browser Launcher Modifications
- Modified `launch_browser_sync` function to skip Playwright browser installation on Windows Python 3.12+
- Added warning message to inform users about the limitations

### 3. Alternative Content Retrieval
- Implemented `get_chapter_http_method` function that uses direct HTTP requests via httpx instead of Playwright
- On Windows Python 3.12+, automatically uses HTTP method instead of Playwright
- Added authentication capabilities to the HTTP method
- Added fallback logic to detect when content can't be retrieved via HTTP method

### 4. Error Handling
- Improved error messages specifically for Windows Python 3.12+ users
- Added graceful fallback when Playwright encounters errors
- Better warnings when content can't be retrieved due to platform limitations

### 5. Session Authentication
- Implemented HTTP session authentication to try accessing content without a browser
- Added warnings when authentication is required but can't be performed via HTTP method

## Special Notes for Windows Python 3.12+ Users

For Windows users running Python 3.12 or newer:
1. The application will automatically use HTTP requests instead of launching a browser
2. You need to log in to your MeTruyenCV account for the application to access chapter content
3. Some content may still be inaccessible due to website JavaScript requirements
4. For best results, consider using Python 3.11 or earlier versions if full functionality is needed

## Testing
The changes have been tested on Windows with Python 3.12, confirming that:
- The application avoids the `NotImplementedError` in `asyncio.create_subprocess_exec`
- Basic HTTP requests work for accessing website content
- Authentication handling is working correctly
- Appropriate warning messages are displayed to users 