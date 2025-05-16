from fastapi import APIRouter

router = APIRouter()

# Define the static data for API
@router.get("/test")
async def get_test():
    static_data = [
        {"name": "Item 1", "description": "Deskripsi Item 1"},
        {"name": "Item 2", "description": "Deskripsi Item 2"},
        {"name": "Item 3", "description": "Deskripsi Item 3"},
    ]
    return static_data
