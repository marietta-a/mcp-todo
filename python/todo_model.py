from pydantic import BaseModel

class TodoModel(BaseModel):
    id: int
    completed: bool = False
    description: str

    def clone(self) -> 'TodoModel':
        return TodoModel(
            id=self.id,
            description=self.description,
            completed=self.completed
        )
    