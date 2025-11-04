"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

# Example schemas (kept for reference)

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# CTF collections

DIFFICULTY = Literal["Easy", "Medium", "Hard"]

class Ctfchallenge(BaseModel):
    """CTF challenges collection (collection name: ctfchallenge)"""
    challenge_id: str = Field(..., description="Unique identifier (slug)")
    title: str
    category: str = Field(..., description="e.g., Web, Crypto, Pwn")
    difficulty: DIFFICULTY
    description: str
    hint: Optional[str] = None
    flag: str = Field(..., description="Exact expected flag value, e.g., FLAG{...}")
    points: int = Field(..., ge=0, description="Score awarded for correct submission")

class Ctfsubmission(BaseModel):
    """CTF submissions collection (collection name: ctfsubmission)"""
    challenge_id: str
    username: str
    submitted_flag: str
    correct: bool = False
    points_awarded: int = 0

class Ctfuser(BaseModel):
    """CTF user profile (optional, collection name: ctfuser)"""
    username: str
    display_name: Optional[str] = None
    total_points: int = 0
