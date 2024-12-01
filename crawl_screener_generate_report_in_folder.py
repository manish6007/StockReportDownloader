import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import logging
import json
import os
import argparse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak
from io import StringIO

class ScreenerScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.styles = getSampleStyleSheet()
        # Create custom styles
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20
        ))

    def get_folder_path(self, company_code):
        """Create folder based on company code if it doesn't exist"""
        folder_name = company_code.upper()
        folder_path = os.path.abspath(folder_name)
        
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                self.logger.info(f"Created new folder: {folder_path}")
            except Exception as e:
                self.logger.error(f"Error creating folder: {str(e)}")
                raise
        else:
            self.logger.info(f"Using existing folder: {folder_path}")
            
        return folder_path

    def validate_company_code(self, company_code):
        """Validate the company code format"""
        if not company_code:
            raise ValueError("Company code cannot be empty")
            
        if not company_code.isalnum():
            raise ValueError("Invalid company code. Please use alphanumeric characters only")
            
        return company_code.upper()

    def get_page_content(self, url):
        """Fetch page content with retry mechanism"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def extract_key_metrics(self, soup):
        """Extract key metrics from the top section"""
        metrics = {}
        metrics_section = soup.find('div', class_='company-ratios')
        if metrics_section:
            for item in metrics_section.find_all('li'):
                label = item.find('span', class_='name')
                value = item.find('span', class_='number')
                if label and value:
                    metrics[label.text.strip()] = value.text.strip()
        return metrics

    def extract_company_info(self, soup):
        """Extract company information"""
        info = {}
        company_name = soup.find('h1', class_='company-name')
        if company_name:
            info['Company Name'] = company_name.text.strip()

        description = soup.find('div', class_='about')
        if description:
            info['Description'] = description.text.strip()

        return info

    def extract_table_data(self, table):
        """Extract data from a specific table with improved column handling"""
        if not table:
            return None

        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]

        rows_data = []
        data_rows = table.find_all('tr')[1:]
        
        for row in data_rows:
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = [cell.text.strip() for cell in cells]
                while len(row_data) < len(headers):
                    row_data.append('')
                rows_data.append(row_data[:len(headers)])

        if headers and rows_data:
            try:
                df = pd.DataFrame(rows_data, columns=headers)
                return df
            except ValueError as e:
                self.logger.error(f"Error creating DataFrame: {str(e)}")
                return None
        return None

    def parse_screener_data(self, soup):
        """Parse the screener-specific data structure"""
        data = {}
        
        data['Company_Info'] = self.extract_company_info(soup)
        data['Key_Metrics'] = self.extract_key_metrics(soup)

        for section in soup.find_all('section'):
            section_id = section.get('id', '')
            section_title = section.find('h2')
            title = section_title.text.strip() if section_title else section_id

            tables = section.find_all('table')
            if tables:
                section_data = {}
                for i, table in enumerate(tables):
                    df = self.extract_table_data(table)
                    if df is not None:
                        section_data[f'Table_{i+1}'] = df
                if section_data:
                    data[title] = section_data

            pairs = section.find_all(['p', 'div'], class_='flex-row')
            if pairs:
                kv_data = {}
                for pair in pairs:
                    spans = pair.find_all('span')
                    if len(spans) >= 2:
                        key = spans[0].text.strip()
                        value = spans[1].text.strip()
                        kv_data[key] = value
                if kv_data:
                    if title in data:
                        data[title].update(kv_data)
                    else:
                        data[title] = kv_data

        return data

    def create_pdf_table(self, data, style=None):
        """Convert data to a format suitable for PDF tables"""
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to list of lists
            table_data = [data.columns.tolist()] + data.values.tolist()
        elif isinstance(data, dict):
            # Convert dictionary to list of lists
            table_data = [[key, str(value)] for key, value in data.items()]
        else:
            return None

        return table_data

    def format_table_for_pdf(self, table_data):
        """Format table data for PDF, handling large tables"""
        if not table_data:
            return None
        
        # Convert all elements to strings and handle None values
        formatted_data = []
        for row in table_data:
            formatted_row = [str(cell) if cell is not None else '' for cell in row]
            formatted_data.append(formatted_row)
        
        return formatted_data

    def generate_pdf(self, data, folder_path, company_code):
        """Generate PDF report from scraped data"""
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = os.path.join(folder_path, f"{company_code}_report_{timestamp}.pdf")
        
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        story = []
        
        # Add company name and description
        if 'Company_Info' in data:
            company_name = data['Company_Info'].get('Company Name', 'Company Report')
            story.append(Paragraph(company_name, self.styles['CustomTitle']))
            if 'Description' in data['Company_Info']:
                story.append(Paragraph(data['Company_Info']['Description'], self.styles['Normal']))
                story.append(Spacer(1, 20))

        # Add key metrics
        if 'Key_Metrics' in data:
            story.append(Paragraph('Key Metrics', self.styles['SectionHeader']))
            metrics_table = self.create_pdf_table(data['Key_Metrics'])
            if metrics_table:
                formatted_table = self.format_table_for_pdf(metrics_table)
                t = Table(formatted_table)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(t)
                story.append(Spacer(1, 20))

        # Process other sections
        for section_name, section_data in data.items():
            if section_name not in ['Company_Info', 'Key_Metrics']:
                story.append(PageBreak())
                story.append(Paragraph(section_name, self.styles['SectionHeader']))
                
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if isinstance(value, pd.DataFrame):
                            story.append(Paragraph(f"{key}", self.styles['Normal']))
                            table_data = self.create_pdf_table(value)
                            if table_data:
                                formatted_table = self.format_table_for_pdf(table_data)
                                t = Table(formatted_table)
                                t.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                story.append(t)
                                story.append(Spacer(1, 20))

        # Build the PDF
        doc.build(story)
        return pdf_filename

    def scrape_company(self, company_code):
        """Main function to scrape company data and generate PDF"""
        try:
            # Validate company code
            company_code = self.validate_company_code(company_code)
            
            # Create/get folder path
            folder_path = self.get_folder_path(company_code)
            
            # Build URL and scrape data
            url = f"https://www.screener.in/company/{company_code}/"
            self.logger.info(f"Starting scraping for company: {company_code}")
            
            html_content = self.get_page_content(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            data = self.parse_screener_data(soup)
            
            # Generate PDF
            pdf_filename = self.generate_pdf(data, folder_path, company_code)
            
            self.logger.info(f"Successfully generated PDF report: {pdf_filename}")
            return pdf_filename
                
        except Exception as e:
            self.logger.error(f"Error processing {company_code}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise

def main():
    parser = argparse.ArgumentParser(description='Screener.in Data Scraper and Report Generator')
    parser.add_argument('companies', nargs='+', help='One or more company codes (e.g., TATAMOTORS RELIANCE)')
    args = parser.parse_args()

    scraper = ScreenerScraper()
    
    for company_code in args.companies:
        try:
            pdf_file = scraper.scrape_company(company_code)
            print(f"Generated report for {company_code}: {pdf_file}")
        except Exception as e:
            print(f"Failed to generate report for {company_code}: {str(e)}")
            continue

if __name__ == "__main__":
    main()