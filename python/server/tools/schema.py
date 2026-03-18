from pydantic import BaseModel

class EmptySchama(BaseModel):
    pass

class IDSchema(BaseModel):
    id: int