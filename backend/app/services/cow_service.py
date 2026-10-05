import uuid
from app.repository.cow_repository import CowRepository
from app.models.cow import CowModel
from app.schemas.cow import CowCreate, CowUpdate


class CowService:
    def __init__(self, repository: CowRepository):
        self.repository = repository

    def create_cow(self, cow_in: CowCreate, farmer_id: uuid.UUID) -> CowModel:
        cow = CowModel(farmer_id=farmer_id, name=cow_in.name, breed=cow_in.breed)
        return self.repository.create(cow)

    def list_cows_for_farmer(self, farmer_id: uuid.UUID) -> list[CowModel]:
        return self.repository.get_all_for_farmer(farmer_id)

    def get_cow_for_farmer(self, cow_id: uuid.UUID, farmer_id: uuid.UUID) -> CowModel | None:
        cow = self.repository.get_by_id(cow_id)
        if cow is None or cow.farmer_id != farmer_id:
            return None  
        return cow

    def update_cow(self, cow_id: uuid.UUID, cow_in: CowUpdate, farmer_id: uuid.UUID) -> CowModel | None:
        cow = self.get_cow_for_farmer(cow_id, farmer_id)
        if cow is None:
            return None

        if cow_in.name is not None:
            cow.name = cow_in.name
        if cow_in.breed is not None:
            cow.breed = cow_in.breed

        return self.repository.update(cow)

    def delete_cow(self, cow_id: uuid.UUID, farmer_id: uuid.UUID) -> bool:
        cow = self.get_cow_for_farmer(cow_id, farmer_id)
        if cow is None:
            return False
        self.repository.delete(cow)
        return True