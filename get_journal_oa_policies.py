import google.generativeai as palm
import pandas as pd
import requests
from datetime import datetime

with open('palm-api-key.txt') as f:
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
    full_url = base_url + '?item-type=publication&api-key=' + SR_api_key + '&format=Json&identifier=' + str(journal)

    policies_dict = {'journal': '',
                    'policies': []}

    try:
        response = requests.get(full_url)
        data = response.json()
        
        policies = data['items'][0]['publisher_policy']
        
        range_of_policies = range(len(policies))
        
        policies_dict['journal'] = journal
        list_of_policies = []

        for index in range_of_policies:

            sub_range_policies = range(len(policies[index]['permitted_oa'])) #Some journales have nested policies
            for sub_range in sub_range_policies:
                
                article_version_policy = policies[index]['permitted_oa'][sub_range]

                article_version = ''.join(article_version_policy['article_version'])

                oa_fee = article_version_policy.get('additional_oa_fee', 'no')

                embargo = article_version_policy.get('embargo', {})
                if 'amount' in embargo and 'units' in embargo:
                    formatted_embargo = f"{embargo['amount']} {embargo['units']}"
                else:
                    formatted_embargo = 'no'

                locations = article_version_policy.get('location', {})
                if 'location' in locations:
                    location_list = ', '.join(locations['location'])
                else:
                    location_list = 'none'

                conditions = article_version_policy.get('conditions', 'none')
                if isinstance(conditions, list):
                    formatted_conditions = ', '.join(map(str, conditions))
                else:
                    formatted_conditions = str(conditions)


                compiled_article_version_policy = {'article_version': article_version,
                                                    'oa_fee': oa_fee,
                                                    'embargo': formatted_embargo,
                                                    'locations': location_list,
                                                    'conditions': formatted_conditions}

                list_of_policies.append(compiled_article_version_policy)

        policies_dict['policies'].append(list_of_policies)

        return(policies_dict)
    
    except IndexError:
         policies_dict = {'journal': journal,
                        'policies': 'No information found'}
         
         return(policies_dict)



current_date = datetime.now().date()
formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

output_message = f"""
Queens College Library Research Services
= = = = = = = = = = = = = = = = = = = = =
({formatted_date})

"""

range_of_cv_list = range(len(cv_list))

print('Collection OA policies for each journal...')

for i in range_of_cv_list:
    list_of_journal_policies = []
    for j in cv_list[i]['Journal']:
       list_of_journal_policies.append(build_oa_policies_dictionary(j))


    oa_policies = list_of_journal_policies[0]['policies']

    paragraphs = []
    if oa_policies == 'No information found':
        p = 'No information found'
        paragraphs.append(p)
    else: 
        for policy in oa_policies[0]:
            p = f"""
Version: {policy['article_version'].title()} Manuscript\n
OA Fee: {policy['oa_fee'].title()}
Embargo: {policy['embargo'].title()}\n
Locations: {policy['locations']}\n
Conditions: {policy['conditions']}
        """
            paragraphs.append(p)

    per_journal_oa_policies = f"""
Citation {i+1} + + + + + + + + + + + + + + + + + + + +

{cv_list[i]['Citation'][0]}

Journal: {list_of_journal_policies[0]['journal']} 
    """
    if len(paragraphs) == 1:
        for p in paragraphs:
            per_journal_oa_policies += '\n' + p + '\n'
    else:
        for p in paragraphs:
            per_journal_oa_policies += '\n' + p + '\n' + '-'*50
    
    output_message += per_journal_oa_policies

file_path = 'QCL_CV_OA_Report.txt'
with open(file_path, 'w') as file:
    file.write(output_message)

print('QCL_CV_OA_Report.txt has been created.')