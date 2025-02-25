import requests 
from dotenv import load_dotenv
import os 
from openai import OpenAI
from firecrawl import FirecrawlApp
from pydantic import BaseModel

load_dotenv()

""" Structured outputs """
class Answer(BaseModel):
    isAnswer: bool
    reasoning: str
    answer: str

class ChooseLink(BaseModel):
    url: str
    reasoning: str

class Link(BaseModel):
    url: str
    description: str

class LinksList(BaseModel):
    links: list[Link]

# Necessary clients
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_KEY"))

""" Functions """
# Function that finds answer to a question from a given markdown of a website
def find_answer(website_content, question):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Based on a website content provided by user answer the question. Your answer must containt answer to the question and it's reasoning and a boolean value if you were able to find the answer from a provided text."},
            {"role": "user", "content": f"Question: {question} \n Website content: {website_content}"}
        ],
        response_format=Answer
    )

    parsed_response = completion.choices[0].message.parsed

    result = {
        "isAnswer": parsed_response.isAnswer,
        "reasoning": parsed_response.reasoning,
        "answer": parsed_response.answer
    }

    return result

# Function that returns a list of urls and it's descriptions from a website content
def find_urls(website_content):
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Based on a website content provided by user analyze all the links on the website and return it's urls and a descriptions where this links may lead to based on text surrounding the link."},
                {
                    "role": "user",
                    "content": f"Website content: {website_content}"
                }
            ],
            response_format=LinksList
        )

        parsed_response = completion.choices[0].message.parsed
        result = dict()

        for element in parsed_response.links:
            result[element.url] = element.description

        return result

# Based on the user's question this function chooses next link to visit 
def choose_link(links_descriptions: dict, question: str):
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helper in selecting the link that is most likely to contain the answer to your question. You will be given a dictionary of links with it's descriptions and a question. Based on the link descriptions, choose one that leads to content that will help answer the question. Return one link and reasoning why you picked it."},
            {
                "role": "user",
                "content": f"Question: {question} \nLinks and it's descriptions: {links_descriptions}"
            }
        ],
        response_format=ChooseLink
    )

    parsed_response = completion.choices[0].message.parsed

    return parsed_response

# Converts website to markdown format
def get_website_content(url):
    scrape_result = firecrawl.scrape_url(url, params={'formats': ['markdown', 'links'], 'onlyMainContent': False})
    return scrape_result['markdown']

def analyze_website(url, question):
    visited_links = set()
    possible_links = dict()
    flag = True
    iter = 0
    while flag:
        print(f"------ Iteration number: {iter} ------")
        visited_links.add(url)
        # Get website content 
        website_content = get_website_content(url)
        find_answer_result = find_answer(website_content, question)

        if find_answer_result['isAnswer']:
            print("Finished - I found an answer: ")
            print(find_answer_result["answer"])
            print(f"My reasoning: {find_answer_result['reasoning']}")
            return find_answer_result["answer"]
        else:
            # Pick other link that will probably contain an answer 
            print(f"{url} - no answer here, let me check out other links ...")
            new_possible_links = find_urls(website_content)

            # Merge old links descriptions and new ones
            possible_links = possible_links | new_possible_links

            # Delete links that have already been visited
            for el in visited_links:
                if el in possible_links:
                    del possible_links[el]

            print("Links I can visit:")
            for key, value in possible_links.items():
                print(f"{key}: {value}")

            print("The best choice is:")
            next_link = choose_link(possible_links, question)
            print(f"{next_link.url}, poniewaz: {next_link.reasoning}")

            # Update url 
            url = next_link.url

        iter += 1
        if iter > 6:
            flag = False

# Download questions from the server
questions_url = f"https://centrala.ag3nts.org/data/{os.getenv('API_KEY')}/softo.json"
request = requests.get(questions_url)
questions = request.json() 

results = dict()

for id, question in questions.items():
    print(f"Question: {question}")
    results[id] = analyze_website("https://softo.ag3nts.org/", question)


# Send the results to the server
url = "https://centrala.ag3nts.org/report"
headers = {
    "Content-Type": "application/json"
}

server_msg = {
    "task": "softo",
    "apikey": os.getenv("API_KEY"),
    "answer": results
}

response = requests.post(url, headers=headers, json=server_msg)
print(response.json())