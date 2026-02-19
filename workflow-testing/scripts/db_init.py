from sqlmodel import Session, SQLModel, delete, select

from common.database import Database
from common.models import InventoryLevel, Order, Product, User


def tables_exist(engine):
    with Session(engine) as session:
        user_count = session.exec(select(User)).first()
        product_count = session.exec(select(Product)).first()
        return user_count is not None or product_count is not None
    return False


def clean_order(engine):
    stmt = delete(Order)
    with Session(engine) as session:
        session.exec(stmt)
        session.commit()
    print("🧹 Cleaned orders table")


def seed_users(engine):
    users = [
        User(location_code="IND-BLR", user_email="blr@specmatic.io"),
        User(location_code="IND-DEL", user_email="del@specmatic.io"),
    ]

    with Session(engine) as session:
        session.add_all(users)
        session.commit()

        # Refresh to get actual IDs from DB
        session.refresh(users[0])
        session.refresh(users[1])

    user_ids = [user.user_id for user in users]
    print(f"👥 Seeded {len(users)} users with IDs {user_ids}")


def seed_products(engine):
    products = [
        Product(name="Phone", price=999.0, location_code="IND-BLR"),
        Product(name="TWS", price=499.0, location_code="IND-BLR"),
    ]

    with Session(engine) as session:
        session.add_all(products)
        session.commit()

        # Refresh to get actual IDs from DB
        session.refresh(products[0])
        session.refresh(products[1])

    print(f"📱 Seeded {len(products)} products (IDs: {[p.product_id for p in products]})")


def seed_inventory(engine):
    inventory_data = [
        {"product_id": 1, "inventory": 500},
        {"product_id": 2, "inventory": 1000},
    ]

    with Session(engine) as session:
        for data in inventory_data:
            existing = session.exec(select(InventoryLevel).where(InventoryLevel.product_id == data["product_id"])).first()
            if existing:
                existing.inventory = data["inventory"]
            else:
                session.add(InventoryLevel(**data))

        session.commit()

    print(f"📦 Upserted {len(inventory_data)} inventory records")


def seed_user_and_product(engine):
    if tables_exist(engine):
        print("✅ Tables already have data, skipping seed")
        return False

    print("🌱 Seeding empty database...")
    seed_users(engine)
    seed_products(engine)
    return True


def main():
    print("🚀 Initializing database schema...")
    db = Database()
    SQLModel.metadata.create_all(db.engine)

    seed_user_and_product(db.engine)
    seed_inventory(db.engine)
    clean_order(db.engine)
    print("✅ Database schema + sample data ready! 🎉")


if __name__ == "__main__":
    main()
