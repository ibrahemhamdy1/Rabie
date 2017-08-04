# import create_engine package to point to our database
from sqlalchemy import create_engine
# import sessionmaker to create a session that binded to the created engine which point to database
from sqlalchemy.orm import sessionmaker
# import Base class in addition to all objects in the database which represent our tables 
from database_setup import Category, Base, Item, User

# create an engine points to the itemcatalog database
engine = create_engine('sqlite:///itemscatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit().
session = DBSession()


# Create first user
User1 = User(
    name="Rabie Masoud",
    email="eng.rabiemasoud@gmail.com",
    picture="https://www.facebook.com/photo.php?fbid=17921986" +
    "91051217&l=f57b46f761"
)
session.add(User1)
session.commit()

# items for Air Sports
category1 = Category(user_id=1, name="Air sports")

session.add(category1)
session.commit()

Item1 = Item(
    user_id=1,
    name="Aerobatics",
    description="is the practice of flying maneuvers involving aircraft" +
    "attitudes that are not used in normal flight. Aerobatics are performed " +
    "in airplanes and gliders for training, recreation," +
    "entertainment, and sport",
    category=category1
)

session.add(Item1)
session.commit()

Item2 = Item(
    user_id=1, name="Air racing",
    description="Air racing is a motorsport that involves airplanes or other" +
    "types of aircraft competing over a fixed course, with the winner either" +
    "returning the shortest time, the one to complete it with the" +
    "most points, or to come closest to a previously estimated time.",
    category=category1)

session.add(Item2)
session.commit()

Item3 = Item(
    user_id=1, name="Gliding",
    description="Gliding is a recreational activity and competitive air" +
    "sport[1] in which pilots fly unpowered aircraft known as gliders or" +
    "sailplanes using naturally occurring currents of rising air in the" +
    "atmosphere to remain airborne. The word soaring" +
    "is also used for the sport.",
    category=category1
)

session.add(Item3)
session.commit()


# items for Archery
category2 = Category(user_id=1, name="Archery")

session.add(category2)
session.commit()

Item1 = Item(
    user_id=1,
    name="Flight archery",
    description="In flight archery the aim is to shoot the greatest" +
    "distance; accuracy or penetrating power are not relevant. It" +
    "requires a large flat area such as an aerodrome",
    category=category2)

session.add(Item1)
session.commit()

Item2 = Item(
    user_id=1,
    name="Popinjay",
    description="Popinjay or Papingo (signifying a painted bird), also" +
    " called pole archery, is a shooting sport that can be performed" +
    " with either rifles or archery equipment.",
    category=category2)

session.add(Item2)
session.commit()


# Create second user
User2 = User(
    name="Lamiaa Masoud",
    email="dr.lamiaamasoud@gmail.com",
    picture="https://www.facebook.com/photo.php?fbid=" +
    "1792198691051217&l=f57b46f761"
)
session.add(User2)
session.commit()

# items for Air Sports
category1 = Category(user_id=1, name="Ball-over-net")

session.add(category1)
session.commit()

Item1 = Item(
    user_id=1,
    name="Badminton",
    description="Badminton is a racquet sport played using racquets to hit a" +
    " shuttlecock across a net. Although it may be played with larger teams," +
    " the most common forms of the game are 'singles' (with one player per" +
    " side) and 'doubles' (with two players per side).",
    category=category1)

session.add(Item1)
session.commit()

Item2 = Item(
    user_id=1,
    name="Biribol",
    description="Matches are decided in best-of-three or best-of-five" +
    " sets of 21 points, when the matches go up to the last set this" +
    " set is disputed up to the 20th point instead, and a team" +
    " needs at least two points of advantage in any circumstance" +
    " to win a set.",
    category=category1
)

session.add(Item2)
session.commit()

Item3 = Item(
    user_id=1,
    name="Fistball",
    description="Fistball is a sport of European origin. It is similar" +
    " to volleyball in that players try to hit a ball over a net. The" +
    " current men's fistball World Champion is Germany, winners of both" +
    " the 2011 World Championships and the fistball category at the 2013 .",
    category=category1)

session.add(Item3)
session.commit()


# items for Archery
category2 = Category(user_id=2, name="Basketball")

session.add(category2)
session.commit()

Item1 = Item(
    user_id=2,
    name="Beach basketball",
    description="Beach Basketball is a modified version of basketball," +
    " played on beaches. It was invented in the United States" +
    " by Philip Bryant",
    category=category2)

session.add(Item1)
session.commit()

Item2 = Item(
    user_id=2,
    name="Ringball",
    description="Ringball is a non-contact sport[6] played by both male" +
    " and female humans in separate games. It is similar to the game of" +
    " netball and can be played on an all weather, grass, or in-door court." +
    " The court is divided into three sections. A team consists of three" +
    " goal scorers, three centre players, and three defending players.",
    category=category2)

session.add(Item2)
session.commit()


print "Menu Items have successfully added!"
