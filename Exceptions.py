class CountException(Exception):
    def __init__(self):
        self.message = "Count Must be Positive..."
        super().__init__(self.message)

# try:
#     count = -4
#     if count >= 0:
#         raise CountException()
#     else:
#         print("Here")
# except CountException as ce:
#     print(ce)
