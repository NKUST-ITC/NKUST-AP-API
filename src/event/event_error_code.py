


class coviddefenseError(Exception):
    def __init__(self, message,code=None):
        super(Exception, self).__init__(message)
        self.message = message
        self.code = code
    def __str__(self):
        return self.message


class error:
    not_found_seat = coviddefenseError("Not found SeatId.")
    wrong_account_or_password = coviddefenseError("Wrong account.")
    something_error = coviddefenseError("Something error.")
    token_error = coviddefenseError("token_error.",100)
