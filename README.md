# UDN News Scraper

## Description
`UDNNewsScraper` is a Python-based web scraper designed to collect news articles from the UDN News website. The scraper uses Selenium WebDriver for browser automation to fetch articles based on specific search criteria (keyword, start date, end date). It extracts important details like title, publication date, and article content, and saves the results in a CSV file or returns them as a Pandas DataFrame.

## Features
- Fetch news articles by keyword, start date, and end date.
- Extract article details including title, date, and content.
- Supports headless browsing for faster execution.
- Option to use an existing Edge browser profile for logged-in sessions.
- Handles pagination and can scrape multiple pages of results.
- Save scraped articles in a CSV file for further analysis.
- Supports user authentication with manual login mode.

## Requirements
- Python 3.x
- Selenium WebDriver for Microsoft Edge
- tqdm (for progress bars)
- Pandas (for storing and saving data)
- Regular expressions (re) for parsing data

## Installation

1. **Install dependencies**:
   ```bash
   pip install selenium tqdm pandas
   ```

2. **Download Microsoft Edge WebDriver**:
   - Ensure that you have the correct version of the [Microsoft Edge WebDriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/).
   - Place the `msedgedriver` executable in a directory (e.g., `/usr/local/bin/`).

3. **Set up the environment**:
   - Make sure that Microsoft Edge is installed on your machine.
   - If you wish to use a custom user profile for login sessions, specify the path to the user data directory.

## Usage

1. **Initialize the scraper**:
   ```python
   scraper = UDNNewsScraper(edge_driver_path="/path/to/msedgedriver", user_data_dir="/path/to/user/data", headless=True)
   ```

2. **Scrape news**:
   ```python
   # Parameters:
   # keyword - The search keyword (e.g., "Technology")
   # start_date - The start date for filtering (e.g., "2025-01-01")
   # end_date - The end date for filtering (e.g., "2025-03-01")
   # output_file - Optional CSV filename to save the results (e.g., "output.csv")
   # manual_mode - Whether to enable manual login mode (True/False)
   # max_pages - Maximum number of pages to scrape
   # max_articles - Maximum number of articles to scrape

   df = scraper.scrape(keyword="科技", start_date="2025-01-01", end_date="2025-03-01", output_file="output.csv", manual_mode=False, max_pages=5, max_articles=50)
   ```

3. **Close the browser**:
   After scraping, ensure to close the browser instance:
   ```python
   scraper.close()
   ```

## Example Output

The scraper will output a Pandas DataFrame with the following columns:

- **Title**: The article's title.
- **Date**: The article's publication date.
- **Content**: The full content of the article.

If an `output_file` is specified, the DataFrame will be saved to the provided CSV file.

## Notes
- **Headless Mode**: When running in headless mode, the browser will not open a GUI window. This is useful for running the scraper in the background.
- **Login Mode**: If you enable `manual_mode`, the scraper will pause and allow you to complete the login process manually in the browser before continuing.
- **Data Cleaning**: The scraper attempts to clean and extract relevant article content, removing unnecessary elements like menus, footers, and headers.
