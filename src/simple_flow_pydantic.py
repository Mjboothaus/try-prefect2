from prefect import flow, task, __version__
from pydantic import BaseModel

print(f"\nPrefect version: {__version__}\n")


class Model(BaseModel):
    a: int
    b: float
    c: str

@task
def printer(obj):
    print(f"\nReceived a {type(obj)} with value {obj}\n")

@flow
def model_validator(model: Model):
    printer(model)

model_validator({"a": 42, "b": 0, "c": 55})
