import google.generativeai as palm
import pandas as pd
import requests


with open('bard-api-key.txt') as f:
        bard_api_key = f.read()

with open('SR-api-key.txt') as f:
        SR_api_key = f.read()

palm.configure(api_key = bard_api_key)
models = [m for m in palm.list_models() if 'generateText' in m.supported_generation_methods]
model = models[0].name

df = pd.read_excel('Citations.xlsx')

def get_journal_name(citation):
    prompt = f'What is the name of the journal in this citation: {citation}'

    completion = palm.generate_text(
        model=model,
        prompt=prompt,
        temperature=0,
        # The maximum length of the response
        max_output_tokens=800,
    )
    print(completion.result)
    return completion.result

def get_publisher(journal):
    base_url = 'https://v2.sherpa.ac.uk/cgi/retrieve_by_id'
    full_url = base_url + '?item-type=publication&api-key=' + SR_api_key + '&format=Json&identifier=' + str(journal)

    requests.get(full_url)
    response = requests.get(full_url)
    data = response.json()

    if journal:
        try:
            publisher = data['items'][0]['publishers'][0]['publisher']['name'][0]['name']
        except IndexError:
            publisher = 'No Result Found'
        except TypeError:
             publisher = 'No Result Found'
    else:
        publisher = 'No Result Found'

    print(publisher) 
    return publisher

df['Journal Name'] = df['Citation'].apply(get_journal_name)
df['Publisher'] = df['Journal Name'].apply(get_publisher)

print(df)