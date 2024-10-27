def say_hello():
    print("Hello")

say_hello()

def my_decorator(func):
    def wrapper():
        print("Before the function")
        func()
        print("After the function")
    return wrapper

say_hello = my_decorator(say_hello)

say_hello()