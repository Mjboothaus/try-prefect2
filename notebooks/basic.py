from prefect import Flow

@flow
def basic_func():
    print("Something done here...")
    return 152