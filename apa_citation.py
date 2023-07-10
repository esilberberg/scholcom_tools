import pandas as pd
import re
import requests

xlsx = 'Citations.xlsx'
df = pd.read_excel(xlsx, sheet_name='articles')

def remove_whitespace(citation):
    """Removes any newline escape and any whitespace over 2 spaces from a citation string."""
    citation = citation.replace('\n', '')
    citation = re.sub(r"\s+", " ", citation)
    citation = citation.strip()
    return citation

def get_title(citation):
    """Returns the content of a citation, everything after the period after a closed parenthesis."""
    start_index = citation.find(").")
    citation_segment = citation[start_index + 3:]

    title_end_match = re.search(r"\.\s\b", citation_segment)

    if title_end_match:
        end_index = title_end_match.start()
        title = citation_segment[:end_index]
        return title
    else:
        return citation_segment

def get_journal(citation):
    start_index = citation.find(").")
    citation_segment = citation[start_index + 3:]

    title_end_match = re.search(r"\.\s\b", citation_segment)

    if title_end_match:
        title_end_index = title_end_match.end()

        journal_end_match_comma = re.search(r", \d", citation_segment[title_end_index:])
        journal_end_match_period = re.search(r"\.", citation_segment[title_end_index:])
        
        if journal_end_match_comma:
            journal_end_index = journal_end_match_comma.start() + title_end_index
            journal = citation_segment[title_end_index:journal_end_index].strip()
            journal = re.sub(r"[\d.(),]", "", journal)
        elif journal_end_match_period:
            journal_end_index = journal_end_match_period.start() + title_end_index
            journal = citation_segment[title_end_index:journal_end_index].strip()
            journal = re.sub(r"[\d.(),]", "", journal)
        else:
            journal = citation_segment[title_end_index:].strip()
    else:
        journal = citation_segment.strip()

    return journal


def get_publisher(journal):
    """Returns a journal's publisher using Sherpa Romeo's API"""

    # Requires an API key from https://v2.sherpa.ac.uk/cgi/register pasted into a txt file that lives in the same directory.
    with open('SR-api-key.txt') as f:
        api_key = f.read()

    base_url = 'https://v2.sherpa.ac.uk/cgi/retrieve_by_id'
    full_url = base_url + '?item-type=publication&api-key=' + api_key + '&format=Json&identifier=' + journal

    requests.get(full_url)
    response = requests.get(full_url)
    data = response.json()

    if journal:
        try:
            publisher = data['items'][0]['publishers'][0]['publisher']['name'][0]['name']
        except IndexError:
            publisher = 'No Result Found'
    else:
        publisher = 'No Result Found'
    return publisher

# Remove tabs
df['Citation'] = df['Citation'].apply(remove_whitespace)
df['Year'] = df['Citation'].str.extract(r'(\d{4})', expand=False)
df['Title'] = df['Citation'].apply(get_title)
df['Journal'] = df['Citation'].apply(get_journal)
df['Publisher'] = df['Journal'].apply(get_publisher)

print(df)

df.to_excel('output.xlsx')