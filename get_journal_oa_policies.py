import google.generativeai as palm
import pandas as pd
import requests
from datetime import datetime

with open('googleAiStudio-api-key.txt') as f:
        palm_api_key = f.read()

with open('SR-api-key.txt') as f:
        SR_api_key = f.read()

palm.configure(api_key = palm_api_key)
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model = models[0].name

df = pd.read_excel('Citations.xlsx')

def clean_citation(citation):
      return citation.strip().replace('\n', '')

print('Isolating journal names from citations...')
def get_journal_name(citation):
    prompt = f'What is the name of the journal in this citation: {citation}'

    completion = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0,
        # The maximum length of the response
        max_output_tokens=800,
    )
    return completion.result

df['Citation'] = df['Citation'].apply(clean_citation)
df['Journal'] = df['Citation'].apply(get_journal_name)

cv_list = []
for index, row in df.iterrows():
    data_dict = {'Citation': [], 'Journal': []}
    data_dict['Citation'].append(row['Citation'])
    data_dict['Journal'].append(row['Journal'])
    cv_list.append(data_dict)

def build_oa_policies_dictionary(journal):
    base_url = 'https://v2.sherpa.ac.uk/cgi/retrieve_by_id'
    full_url = f'{base_url}?item-type=publication&api-key={SR_api_key}&format=Json&identifier={journal}'

    try:
        response = requests.get(full_url)
        data = response.json()
        
        policies = data['items'][0]['publisher_policy']
        
        policies_dict = {
            'journal': journal,
            'policies': []
        }

        for policy in policies:
            list_of_policies = []

            for article_version_policy in policy.get('permitted_oa', []):
                article_version = ''.join(article_version_policy['article_version'])
                oa_fee = article_version_policy.get('additional_oa_fee', 'no')

                embargo = article_version_policy.get('embargo', {})
                formatted_embargo = f"{embargo.get('amount', 'no')} {embargo.get('units', 'no')}"

                locations = article_version_policy.get('location', {})
                location_list = ', '.join(locations.get('location', ['none']))

                conditions = article_version_policy.get('conditions', 'none')
                formatted_conditions = ', '.join(map(str, conditions)) if isinstance(conditions, list) else str(conditions)

                compiled_article_version_policy = {
                    'article_version': article_version,
                    'oa_fee': oa_fee,
                    'embargo': formatted_embargo,
                    'locations': location_list,
                    'conditions': formatted_conditions
                }

                list_of_policies.append(compiled_article_version_policy)

            policies_dict['policies'].append(list_of_policies)

        return policies_dict
    
    except IndexError:
        return {'journal': journal, 'policies': 'No information found'}


current_date = datetime.now().date()
formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

output_message = f"""
Queens College Library Research Services
= = = = = = = = = = = = = = = = = = = = =
({formatted_date})

"""

print('Collection OA policies for each journal...')

output_message = ""

for i, cv_entry in enumerate(cv_list):
    list_of_journal_policies = [build_oa_policies_dictionary(j) for j in cv_entry['Journal']]

    oa_policies = list_of_journal_policies[0]['policies']

    paragraphs = []
    if oa_policies == 'No information found':
        paragraphs.append('No information found')
    else:
        for policy in oa_policies[0]:
            paragraphs.append(f"""
Version: {policy['article_version'].title()} Manuscript
OA Fee: {policy['oa_fee'].title()}
Embargo: {policy['embargo'].title()}
Locations: {policy['locations']}
Conditions: {policy['conditions']}
""")
    
    per_journal_oa_policies = f"""
Citation {i+1} + + + + + + + + + + + + + + + + + + + +

{cv_entry['Citation'][0]}

Journal: {list_of_journal_policies[0]['journal']} 
"""
    
    per_journal_oa_policies += '\n' + '\n'.join(paragraphs) if len(paragraphs) == 1 else '\n' + '\n'.join(paragraphs) + '\n' + '-'*50
    
    output_message += per_journal_oa_policies


file_path = 'QCL_CV_OA_Report.txt'
with open(file_path, 'w') as file:
    file.write(output_message)

print('QCL_CV_OA_Report.txt has been created.')
