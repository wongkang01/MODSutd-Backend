import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time


def parse_course(html):
    soup = BeautifulSoup(html, 'html.parser')
    # course id + full title
    og = soup.find('meta', property='og:title')['content']
    # "02.121DH The Question of Being - ...", split off suffix
    full = og.split(' - ')[0]
    cid, title = full.split(' ', 1)
    # description: first <p> in the rich-text span
    span = soup.find('span', id='rich-text-generator')
    desc = span.find('p').get_text(strip=True)
    # terms: look for links under the term-container div
    term_div = soup.find('div', class_='flex flex-row flex-wrap gap-[0.5rem] pl-[1.6rem]')
    terms = []
    for a in term_div.find_all('a'):
        txt = a.get_text(strip=True)
        if not txt.startswith('Term '):
            continue
        try:
            terms.append(int(txt.replace('Term ', '')))
        except ValueError:
            continue

    # course lead: first profile link
    lead = soup.find('a', href=re.compile(r'^/profile/'))
    course_lead = lead.get_text(strip=True)
    course_lead_info = "https://www.sutd.edu.sg" + lead['href']
    # pillar
    p_tag = soup.find('a', href=re.compile(r'pillar-cluster='))
    pillar = p_tag.get_text(strip=True) if p_tag else None
    # course type
    t_tag = soup.find('a', href=re.compile(r'course-type='))
    course_type = t_tag.get_text(strip=True) if t_tag else None

    return {
        'course_id': cid,
        'course_title': title,
        'description': desc,
        'terms_available': terms,
        'course_lead': course_lead,
        'course_lead_info': course_lead_info,
        'pillar': pillar,
        'type': course_type
    }

def process_courses_from_excel(excel_file, url_column='course_website'):
    """
    Process multiple courses from an Excel file containing course URLs.
    
    Args:
        excel_file (str): Path to the Excel file containing course URLs
        url_column (str): Name of the column containing course URLs
    
    Returns:
        pandas.DataFrame: DataFrame containing scraped course data
    """
    # Read the Excel file
    df = pd.read_excel(excel_file)
    
    # Initialize an empty list to store course data
    course_data = []
    
    # Process each URL
    for url in df[url_column]:
        try:
            print(f"Processing: {url}")
            resp = requests.get(url)
            if resp.status_code == 200:
                data = parse_course(resp.text)
                course_data.append(data)
            else:
                print(f"Failed to fetch {url}: Status code {resp.status_code}")
            
            # Add a small delay to be respectful to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
    
    # Convert the list of dictionaries to a DataFrame
    result_df = pd.DataFrame(course_data)
    
    return result_df

if __name__ == '__main__':
    # Example usage
    excel_file = 'input_links.xlsx'  # Replace with your Excel file path
    result_df = process_courses_from_excel(excel_file)
    
    # Save the results to a new Excel file
    output_file = 'scraped_courses.xlsx'
    result_df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")
