from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Category_item, Category_item

engine = create_engine('sqlite:///sportinggood_users.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Category for Soccer with Items in it
category1 = Category(name="Soccer")

session.add(category1)
session.commit()

catItem2 = Category_item(name="Jersey", description="Board approved Jersey with Classic Logo in the middle",
                     category=category1)

session.add(catItem2)
session.commit()

catItem2 = Category_item(name="Shinguards", description="Board approved Shinguards with Classic Logo ",
                     category=category1)

session.add(catItem2)
session.commit()

catItem2 = Category_item(name="Two Shinguards", description="Board approved Two Shinguards with Classic Logo ",
                     category=category1)

session.add(catItem2)
session.commit()

catItem2 = Category_item(name="Soccer Cleats", description="Board approved Soccer Cleats with Classic Logo ",
                     category=category1)

session.add(catItem2)
session.commit()

# Category for Snowboarding with Items in it
category1 = Category(name="Snowboarding")

session.add(category1)
session.commit()

catItem2 = Category_item(name="Googles", description="Board approved Googles with Classic Logo in the middle",
                     category=category1)

session.add(catItem2)
session.commit()

catItem2 = Category_item(name="Snowboard", description="Board approved Snowboard with Classic Logo ",
                     category=category1)

session.add(catItem2)
session.commit()

catItem2 = Category_item(name="Snowboard Jacket", description="Board approved Snowboard Jacket with Classic Logo ",
                     category=category1)

session.add(catItem2)
session.commit()

catItem2 = Category_item(name="Snowboard shoes", description="Board approved Snowboard shoes with Classic Logo ",
                     category=category1)

session.add(catItem2)
session.commit()




print "added Category Items!"
