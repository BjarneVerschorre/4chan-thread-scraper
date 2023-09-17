import re



class URL(str):
    """ A string that represents a url """
    def __new__(cls, url:str):
        if not re.match(r"^https?://", url):
            raise ValueError("Invalid url")
        return str.__new__(cls, url)

    

    


