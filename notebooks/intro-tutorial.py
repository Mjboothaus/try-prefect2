# Prefect 2 Tutorial - Intro

from prefect import flow, task, __version_info__
import requests
import asyncio


print(f"Prefect version: {__version_info__}")


## Run a basic flow
# The simplest way to begin with Prefect is to import flow and annotate your a Python function using the `@flow` decorator:


@task 
def add_one(x):
    return x + 1

@flow 
def my_flow():
    result = add_one(1) # return int


@flow 
def my_add_one_flow():
    state = add_one(1, return_state=True) # return State
    return state


state = my_add_one_flow()


state.result()


@flow
def my_favorite_function():
    print("This function doesn't do much")
    return 42

@flow
def my_favorite_function_flow():
    return my_favorite_function(return_state=True)


# Running a Prefect workflow manually is as easy as calling the annotated function. In this case, we run the `my_favorite_function()` snippet shown above:


state = my_favorite_function_flow()


# The first thing you'll notice is the messages surrounding the expected output, "This function doesn't do much".
# By adding the `@flow` decorator to your function, function calls will create a flow run — the Prefect Orion orchestration engine manages task and flow state, including inspecting their progress, regardless of where your flow code runs.
# For clarity in future tutorial examples, we may not show these messages in results except where they are relevant to the discussion.
# Next, examine `state`, which shows the result returned by the `my_favorite_function()` flow.


state


# *Flows return states*
# > You may notice that this call did not return the number 42 but rather a Prefect State object. States are the basic currency of communication between Prefect clients and the Prefect API, and can be used to define the conditions for orchestration rules as well as an interface for client-side logic.

# In this case, the state of `my_favorite_function()` is "Completed", with no further message details ("None" in this example). 
# If you want to see the data returned by the flow, access it via the `.result()` method on the State object.

state.result()

## Run flows with parameters

# As with any Python function, you can pass arguments. The positional and keyword arguments defined on your flow function are called parameters. To demonstrate:

@task
def call_api(url):
    return requests.get(url).json()

@flow
def api_flow(url):
    return call_api(url, return_state=True)


# You can pass any parameters needed by your flow function, and you can pass parameters on the `@flow` decorator for configuration as well. We'll cover that in a future tutorial.
# For now, run the `call_api()` flow, passing a valid URL as a parameter. In this case, we're sending a POST request to an API that should return valid JSON in the response.

state = api_flow("http://time.jsontest.com/")

# Again, Prefect Orion automatically orchestrates the flow run. Again, print the state and note the "Completed" state matches what Prefect Orion prints in your terminal.

state.result()

state

## Error handling
 
# What happens if the Python function encounters an error while your flow is running? To see what happens whenever our flow does not complete successfully, let's intentionally run the `call_api()` flow above with a bad value for the URL:

state_bad = api_flow("foo") # - exception doesn't get caught/handled properly by Prefect?

# In this situation, the call to `requests.get()` encounters an exception, but the flow run still returns! The exception is captured by Orion, which continues to shut down the flow run normally.
# However, in contrast to the 'COMPLETED' state, we now encounter a 'FAILED' state signaling that something unexpected happened during execution.

state_bad

# This behavior is consistent across flow runs and task runs and allows you to respond to failures in a first-class way — whether by configuring orchestration rules in the Orion backend (retry logic) or by directly responding to failed states in client code.

## Run a basic flow with tasks
 
# Let's now add some tasks to a flow so that we can orchestrate and monitor at a more granular level. 
# A task is a function that represents a distinct piece of work executed within a flow. You don't have to use tasks — you can include all of the logic of your workflow within the flow itself. However, encapsulating your business logic into smaller task units gives you more granular observability, control over how specific tasks are run (potentially taking advantage of parallel execution), and reusing tasks across flows and sub-flows.
# Creating and adding tasks follows the exact same pattern as for flows. Import task and use the `@task` decorator to annotate functions as tasks.
# Let's take the previous `call_api()` example and move the actual HTTP request to its own task.

@task(name="cat-url")
def call_api(url):
    response = requests.get(url)
    print(f"Response: {response.status_code}")
    return response.json()

@flow(name="cat-flow")
def api_flow(url):
    fact_json = call_api(url)
    return 


# As you can see, we still call these tasks as normal functions and can pass their return values to other tasks. We can then call our flow function — now called `api_flow()` — just as before and see the printed output. Prefect manages all the relevant intermediate states.

state = api_flow("https://catfact.ninja/fact")

# And of course we can create tasks that take input from and pass input to other tasks.

@task(name="t-example3-1")
def call_api(url):
    response = requests.get(url)
    print(response.status_code)
    return response.json()

@task(name="t-example3-2")
def parse_fact(response):
    print(response["fact"])
    return 

@flow(name="f-example3")
def api_flow(url):
    fact_json = call_api(url)
    parse_fact(fact_json)
    return

state = api_flow("https://catfact.ninja/fact")

print(state)


# Combining tasks with arbitrary Python code

# > Notice in the above example that all of our Python logic is encapsulated within task functions. While there are many benefits to using Prefect in this way, it is not a strict requirement. Interacting with the results of your Prefect tasks requires an understanding of Prefect futures.
 
## Run a flow within a flow
 
# Not only can you call tasks functions within a flow, but you can also call other flow functions! Flows that run within other flows are called sub-flows and allow you to efficiently manage, track, and version common multi-task logic. 
# Consider the following simple example:


@flow
def common_flow(config: dict):
    print("I am a subgraph that shows up in lots of places!")
    intermediate_result = 42
    return intermediate_result

@flow
def main_flow():
    # do some things
    # then call another flow function
    data = common_flow(config={})
    # do more things

# Whenever we run `main_flow` as above, a new run will be generated for `common_flow` as well. Not only is this run tracked as a sub-flow run of `main_flow`, but you can also inspect it independently in the UI!

flow_state = main_flow()

# You can confirm this for yourself by spinning up the UI using the `prefect orion start` CLI command from your terminal.

## Asynchronous functions

# Even asynchronous functions work with Prefect! Here's a variation of the previous examples that makes the API request as an async operation:

@task(name="async-url")
async def call_api(url):
    response = requests.get(url)
    print(response.status_code)
    return response.json()

@flow(name="async-flow")
async def async_flow(url):
    fact_json = await call_api(url)
    return 


# If we run this in the REPL, the output looks just like previous runs.

# Following doesn't seem to run:

asyncio.run(async_flow("https://catfact.ninja/fact"))