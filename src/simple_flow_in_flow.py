from prefect import flow

@flow
def common_flow(config: dict):
    # sourcery skip: inline-immediately-returned-variable
    intermediate_result = 42
    print(f"\nI am a subgraph that shows up in lots of places!\n")
    return intermediate_result

@flow
def main_flow():
    # do some things
    # then call another flow function
    data = common_flow(config={})
    # do more things

main_flow()
