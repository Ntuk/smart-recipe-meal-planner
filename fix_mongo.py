"""Fix script for MongoDB database object comparison issue."""
from motor.motor_asyncio import AsyncIOMotorDatabase

def __bool__(self):
    """Returns True if the database object exists."""
    return True

AsyncIOMotorDatabase.__bool__ = __bool__

print("MongoDB database object comparison patch applied!")
