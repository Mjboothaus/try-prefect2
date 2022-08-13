import requests
from prefect import flow, task

##  1st flow

@task
def call_api(url):
    response = requests.get(url)
    print(f"\n{response.status_code}\n")
    return response.json()

@flow
def api_flow(url):
    return call_api(url)

print(f"\n{api_flow('https://catfact.ninja/fact')}\n")


### 2nd flow

@task
def call_api2(url):
    response = requests.get(url)
    print(f"\n{response.status_code}\n")
    return response.json()

@task
def parse_fact(response):
    fact = response["fact"]
    print(f"\n{fact}\n")
    return fact

@flow
def api_flow2(url):
    fact_json = call_api2(url)
    return parse_fact(fact_json)

api_flow2("https://catfact.ninja/fact")
