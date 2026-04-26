# Pydantic — Data Validation

## Basic Model
```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str | None = None

user = User(name="Alice", age=30, email="alice@example.com")
user.name       # 'Alice'
user.model_dump()  # {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}
```

## Validation
```python
from pydantic import BaseModel, Field, field_validator

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price in dollars")
    quantity: int = Field(ge=0, default=0)

    @field_validator('name')
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        if not v[0].isupper():
            raise ValueError('Name must start with uppercase')
        return v
```

## Field Types
```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class Event(BaseModel):
    title: str
    start: datetime
    end: datetime
    priority: Literal["low", "medium", "high"] = "medium"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
```

## Nested Models
```python
class Address(BaseModel):
    street: str
    city: str
    country: str = "US"

class User(BaseModel):
    name: str
    address: Address

user = User(name="Alice", address={"street": "123 Main", "city": "NYC"})
```

## Serialization
```python
user.model_dump()                    # Dict
user.model_dump(exclude_none=True)   # Skip None fields
user.model_dump(include={'name'})    # Only specific fields
user.model_dump_json()               # JSON string

User.model_validate({"name": "Bob", "age": 25})    # From dict
User.model_validate_json('{"name": "Bob", "age": 25}')  # From JSON
```

## Custom Validators
```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start: datetime
    end: datetime

    @model_validator(mode='after')
    def check_dates(self):
        if self.end <= self.start:
            raise ValueError('end must be after start')
        return self
```

## Computed Fields
```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height
```

## Settings Management
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str
    debug: bool = False
    database_url: str = "sqlite:///db.sqlite3"

    model_config = {"env_file": ".env"}

settings = Settings()  # Loads from environment / .env
```

## Discriminated Unions
```python
from pydantic import BaseModel
from typing import Literal, Annotated, Union
from pydantic import Discriminator

class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float

Pet = Annotated[Union[Cat, Dog], Discriminator('pet_type')]

class Model(BaseModel):
    pet: Pet

Model(pet={"pet_type": "cat", "meows": 4})  # Cat
Model(pet={"pet_type": "dog", "barks": 3.5})  # Dog
```
