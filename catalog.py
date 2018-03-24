from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalogapp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Dummy user
user1 = User(
    name="Andrew JN",
    email="andrewjn@example.com",
    picture='https://c2.staticflickr.com/6/5792/30993091230_084bb18750_b.jpg')
session.add(user1)
session.commit()


# Soccer category
category = Category(name="Soccer",
                    user_id=1)
session.add(category)
session.commit()

item = Item(name="Two shinguards",
            description="A pair of shinguards.",
            category=category,
            user=user1)
session.add(item)
session.commit()

item = Item(name="Shinguards",
            description="The shinguards.",
            category=category,
            user=user1)
session.add(item)
session.commit()

item = Item(name="Jersey",
            description="The shirt.",
            category=category,
            user=user1)
session.add(item)
session.commit()

item = Item(name="Soccer Cleats",
            description="The shoes.",
            category=category,
            user=user1)
session.add(item)
session.commit()


# Basketball category
category = Category(name="Basketball",
                    user_id=1)
session.add(category)
session.commit()


# Baseball category
category = Category(name="Baseball",
                    user_id=1)
session.add(category)
session.commit()

item = Item(name="Bat",
            description="The bat.",
            category=category,
            user=user1)
session.add(item)
session.commit()


# Frisbee category
category = Category(name="Frisbee",
                    user_id=1)
session.add(category)
session.commit()

item = Item(name="Frisbee",
            description="The frisbee.",
            category=category,
            user=user1)
session.add(item)
session.commit()


# Snowboarding category
category = Category(name="Snowboarding",
                    user_id=1)
session.add(category)
session.commit()

item = Item(name="Goggles",
            description="The goggles.",
            category=category,
            user=user1)
session.add(item)
session.commit()

item = Item(name="Snowboard",
            description="Best for any terrain and conditions. "
                        "All-mountain snowboards perform anywhere "
                        "on a mountain -- groomed runs, backcountry, "
                        "even park and pipe. They may be directional "
                        "(meaning downhill only) or twin-tip (for "
                        "riding switch, meaning either direction.) "
                        "Most boarders ride all-mountain boards. "
                        "Because of their versatility, all-mountain "
                        "boards are good for beginners who are still "
                        "learning what terrain they like.",
            category=category,
            user=user1)
session.add(item)
session.commit()


# Rock Climbing category
category = Category(name="Rock Climbing",
                    user_id=1)
session.add(category)
session.commit()


# Foosball category
category = Category(name="Foosball",
                    user_id=1)
session.add(category)
session.commit()


# Skating category
category = Category(name="Skating",
                    user_id=1)
session.add(category)
session.commit()


# Hockey category
category = Category(name="Hockey",
                    user_id=1)
session.add(category)
session.commit()

item = Item(name="Stick",
            description="The stick.",
            category=category,
            user=user1)
session.add(item)
session.commit()


print("Catalog successfully populated.")
