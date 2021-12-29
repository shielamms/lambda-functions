class RequestException(Exception):
    def __init__(self,
                 message="There was an error while processing the request",
                 index=0,
                 error_data=None):
        self.message = message
        self.index = index
        self.error_data = error_data

    def at_record_index(self, index):
        self.index = index

    def at_record_data(self, data):
        self.error_data = data

    def get_msg_data(self):
        if self.error_data is None:
            return self.message
        else:
            return "{0} : on {1}, index: {2}".format(self.message,
                                                     self.error_data,
                                                     self.index)

    def __str__(self):
        return self.message
