from prefect import task, flow

@task
def printer(obj):
    print(f"\nReceived a {type(obj)} with value {obj}\n")

# note that we define the flow with type hints
@flow
def validation_flow(x: int, y: str):
    printer(x)
    printer(y)

# automatic type conversion
validation_flow(x="42", y=100)
