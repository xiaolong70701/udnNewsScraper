import time
import re
import math
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

class UDNNewsScraper:
    """
    Class for scraping news articles from UDN News website
    """
    
    def __init__(self, edge_driver_path='/usr/local/bin/msedgedriver', user_data_dir=None, headless=False):
        """
        Initialize the UDN News Scraper
        
        Args:
            edge_driver_path (str): Path to the Edge WebDriver executable
            user_data_dir (str): Path to Edge user data directory for using logged-in session
            headless (bool): Whether to run the browser in headless mode
        """
        self.edge_driver_path = edge_driver_path
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.driver = None
        self.wait = None
        self.service = None
        
    def _setup_driver(self):
        """
        Set up the Edge WebDriver with appropriate options
        
        Returns:
            tuple: (webdriver, WebDriverWait, Service) instances
        """
        # Configure Edge browser options
        edge_options = Options()
        edge_options.add_argument("--start-maximized")
        
        # Disable image loading to speed up the process
        edge_options.add_argument("--blink-settings=imagesEnabled=false")
        edge_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.images": 2,
            "profile.managed_default_content_settings.images": 2
        })
        
        # Use system proxy settings to ensure VPN connectivity
        edge_options.add_argument("--proxy-server='direct://'")
        edge_options.add_argument("--proxy-bypass-list=*")
        
        # Performance optimizations
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        
        # Add headless mode if requested
        if self.headless:
            edge_options.add_argument("--headless")
        
        # Use existing user profile if provided
        if self.user_data_dir:
            edge_options.add_argument(f"--user-data-dir={self.user_data_dir}")
        
        # Create service object with logging for debugging
        service = Service(self.edge_driver_path)
        service.log_path = "edge_driver.log"
        
        # Initialize WebDriver
        driver = webdriver.Edge(service=service, options=edge_options)
        wait = WebDriverWait(driver, 10)
        
        return driver, wait, service
    
    def _fetch_article_content(self, driver, link, index, total, wait):
        """
        Fetch content from a single article
        
        Args:
            driver: WebDriver instance
            link: Article link URL
            index: Article index
            total: Total number of articles
            wait: WebDriverWait instance
        
        Returns:
            dict: Dictionary containing title, date, and content
        """
        try:
            # Open the article page
            driver.get(link)
            time.sleep(2)

            # Extract news ID from the URL
            news_id = "Unknown ID"
            try:
                # Use regex to find news_id parameter in the URL
                news_id_match = re.search(r'news_id=(\d+)', link)
                if news_id_match:
                    news_id = news_id_match.group(1)
                else:
                    # Try other patterns that might appear in the URL
                    alt_id_match = re.search(r'/(\d+)$', link)
                    if alt_id_match:
                        news_id = alt_id_match.group(1)
            except Exception as id_error:
                print(f"Error extracting news ID: {id_error}")
            
            # Extract title
            try:
                title_element = wait.until(EC.presence_of_element_located((By.XPATH, "//h1")))
                title = title_element.text
            except:
                # If h1 title not found, try to get it from other sources
                title = f"Article {index} (title extraction failed)"
            
            # Extract date
            try:
                date_element = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@class='story-source']")))
                date_text = date_element.text
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    article_date = date_match.group(1)
                else:
                    article_date = "Unknown date"
            except:
                article_date = "Unknown date"
            
            # Extract content
            try:
                article_selectors = [
                    "//article",
                    "//div[contains(@class, 'article')]",
                    "//div[contains(@class, 'content')]",
                    "//div[contains(@class, 'story')]"
                ]
                
                content = ""
                for selector in article_selectors:
                    try:
                        article_elements = driver.find_elements(By.XPATH, selector)
                        if article_elements:
                            article_element = article_elements[0]
                            paragraphs = article_element.find_elements(By.TAG_NAME, "p")
                            if paragraphs:
                                content = '\n'.join([p.text for p in paragraphs if p.text])
                                if content:
                                    break
                    except:
                        continue
                
                if not content:
                    # If all selectors fail, try to get text from body
                    body_element = driver.find_element(By.TAG_NAME, "body")
                    content = body_element.text
                    # Clean content, remove menus, headers, footers
                    content = re.sub(r'(Login|Register|Member|Home|News|Sports|Entertainment|Finance|Health)', '', content)
            except:
                content = "Content extraction failed"
            
            return {
                'News ID': news_id,
                'Title': title,
                'Date': article_date,
                'Content': content
            }
        except Exception as e:
            print(f"Error processing article: {e}")
            return {
                'Title': f"Article {index} (processing failed)",
                'Date': "Unknown date",
                'Content': f"Content extraction failed: {str(e)}"
            }
    
    def scrape(self, keyword, start_date, end_date, output_file=None, manual_mode=False, max_pages=None, max_articles=50):
        """
        Main scraping method to fetch news articles based on search criteria
        
        Args:
            keyword (str): Search keyword
            start_date (str): Start date in yyyy-mm-dd format
            end_date (str): End date in yyyy-mm-dd format
            output_file (str): Output CSV filename
            manual_mode (bool): Whether to enable manual login mode
            max_pages (int): Maximum number of pages to scrape
            max_articles (int): Maximum number of articles to scrape
            
        Returns:
            DataFrame: Pandas DataFrame containing the scraped news data
        """
        # Initialize WebDriver
        self.driver, self.wait, self.service = self._setup_driver()
        driver = self.driver
        wait = self.wait
        
        # List to store news data
        news_data = []
        
        try:
            # Open UDN search page
            driver.get("https://udndata.com/ndapp/Index?cp=udn")
            print("Opened UDN News search page")
            
            # Click on the "IP Login" link
            try:
                login_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '定址登入')]")))
                driver.execute_script("arguments[0].scrollIntoView(true);", login_link)
                driver.execute_script("arguments[0].click();", login_link)
                time.sleep(3)
                if manual_mode:
                    print("Please complete the login process in the browser and press Enter to continue...")
                    input()
            except Exception as e:
                print(f"Error when clicking 'IP Login': {e}")
                print("Continuing with search process...")
            
            driver.get("https://udndata.com/ndapp/Index?cp=udn")
            
            # Enter search keyword
            search_input = wait.until(EC.element_to_be_clickable((By.ID, "SearchString")))
            driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
            search_input.send_keys(keyword)
            print(f"Entered keyword: {keyword}")
            
            # Enter start date
            start_date_input = wait.until(EC.element_to_be_clickable((By.ID, "datepicker-start")))
            driver.execute_script("arguments[0].scrollIntoView(true);", start_date_input)
            start_date_input.send_keys(start_date)
            
            # Enter end date
            end_date_input = wait.until(EC.element_to_be_clickable((By.ID, "datepicker-end")))
            driver.execute_script("arguments[0].scrollIntoView(true);", end_date_input)
            end_date_input.send_keys(end_date)
            
            # Click the search button
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@name='submit']")))
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            driver.execute_script("arguments[0].click();", submit_button)
            print("Clicked search button")
            
            # Wait for results page to load
            time.sleep(5)
            
            # Get total result count and calculate total pages
            result_message = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='message']")))
            result_text = result_message.text
            total_results_match = re.search(r'共搜尋到\s*<span class="mark">(\d+)</span>筆資料', driver.page_source)
            total_results = int(total_results_match.group(1)) if total_results_match else 0
            total_pages = math.ceil(total_results / 20)
            
            if max_pages is not None and max_pages > 0:
                total_pages = min(max_pages, total_pages)
            
            # Store all news links and titles
            news_links = []
            
            # Use tqdm to show progress
            with tqdm(total=total_pages, desc="抓取文章資訊", unit="頁") as pbar:
                # Process each page of results
                for current_page in range(1, total_pages + 1):
                    if current_page > 1:
                        # Navigate to next page
                        current_url = driver.current_url
                        if "page=" in current_url:
                            next_page_url = re.sub(r'page=\d+', f'page={current_page}', current_url)
                        else:
                            if "?" in current_url:
                                next_page_url = f"{current_url}&page={current_page}"
                            else:
                                next_page_url = f"{current_url}?page={current_page}"
                        driver.get(next_page_url)
                        time.sleep(3)
                    
                    # Get news links and titles from current page
                    title_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//h2[@class='control-pic']/a")))
                    for title_element in title_elements:
                        title = title_element.text
                        link = title_element.get_attribute('href')
                        news_links.append((title, link))
                    
                    pbar.update(1)  # Update progress bar after processing each page
            
            # Set maximum number of articles to process
            news_links = news_links[:min(len(news_links), max_articles)]
            
            # Use tqdm for progress bar
            with tqdm(total=len(news_links), desc=f"{keyword}文章爬取", unit="文章") as pbar:
                for index, (title, link) in enumerate(news_links, 1):
                    try:
                        article_data = self._fetch_article_content(driver, link, index, len(news_links), wait)
                        news_data.append(article_data)
                    except Exception as e:
                        print(f"Error processing news: {e}")
                        news_data.append({
                            'Title': title,
                            'Date': "Unknown date",
                            'Content': "Content extraction failed"
                        })
                    pbar.update(1)  # Update progress bar
            
            # Create DataFrame and save to CSV if output file is specified
            if news_data:
                df = pd.DataFrame(news_data)
                if output_file:
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    print(f"\nSuccessfully saved {len(news_data)} articles to {output_file}")
                return df
            else:
                print("No news content extracted")
                return pd.DataFrame(columns=['Title', 'Date', 'Content'])
        
        except Exception as e:
            print(f"Error occurred: {e}")
            if news_data:
                df = pd.DataFrame(news_data)
                if output_file:
                    df.to_csv(output_file, index=False, encoding='utf-8-sig')
                    print(f"Saved partial data ({len(news_data)} articles) to {output_file}")
                return df
            return pd.DataFrame(columns=['Title', 'Date', 'Content'])
        
        finally:
            if self.driver:
                self.driver.quit()
                print("Browser closed")
    
    def close(self):
        """Close the browser if still open"""
        if self.driver:
            self.driver.quit()
            print("Browser closed")