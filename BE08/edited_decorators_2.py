from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper():
        print("Before the function")
        func()
        print("After the function")
    return wrapper

@my_decorator
def shout_out():
    print("HELLO")

@my_decorator
def whisper_it():
    print("goodbye")

shout_out()
whisper_it()