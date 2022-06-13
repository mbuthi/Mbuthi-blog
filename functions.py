def add(n1, n2):
    return n1 + n2


def multiply(n1, n2):
    return n1 * n2


def calculate_function(calculate, n1, n2):
    return calculate(n1, n2)


print(calculate_function(add, 3, 4))


#
# def outer_function():
#     print("I'm outer")
#
#     def inner_function():
#         print("I'm inner")
#
#     inner_function()
#
#
# outer_function()


def outer_function():
    print("I\'m outer ")

    def inner_function():
        print("I'm inner")

    return inner_function


inner = outer_function()
inner()
user_input = input("What is your name ")


def admin_only(function):
    def wrapper(*args, **kwargs):
        if user_input == "Mbuthi":
            function(*args, **kwargs)
        else:
            print("Unauthorised")

    return wrapper


@admin_only
def say_hello(name):
    print(f"Hello {name}")


say_hello(user_input)
