#!/usr/bin/env python
# coding: utf-8
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import or_
from sqlalchemy import ForeignKey
from sqlalchemy import Table

sqlalchemy.__version__

# engine = create_engine('sqlite:///:memory:', echo=True)
engine = create_engine('sqlite:///:memory:')

Base = declarative_base()

#
# [3]
# Many-to-Many
# For this relationship an additional table is necessary
# It maps relationships between multiple objects.
# e.g. A User can have multiple shipping addresses (i know it's emails, but lets just assume it's also home addresses)
#
#

association_table = Table('shipping_preferences', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('shipping_address_id', Integer, ForeignKey('addresses.id'))
)


# [1]
#
# Directed One-to-One relationship
#
# One User has one phone number.
# However multiple Users can have the same phone number, or one phone number can belong to many users
# To put it the other way around, exchange the relationship/Foreign key with the relationship column on the User Side
#
class PhoneNumber(Base):
    __tablename__ = 'phone_numbers'
    id = Column(Integer, primary_key=True)
    phone_number = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="phone_number")

# [2]
#
# One User has Many Addresses
#   -> Address must have:
#       user_id = Column(Integer, ForeignKey('users.id'))
#       user = relationship("User", back_populates="addresses")
#                                                       ^
#                                               This property must point to a member defined in the User Model
#   -> User must have:
#       addresses = relationship("Address", order_by=Address.id, back_populates="user")
#                                                                                 ^
#                                                            This myst point to a member defined in Address
#

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    email_address = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="addresses")

    def __repr__(self):
        return "<Address(email_address='%s')>" % self.email_address

# [4]
# This example is e.g. if a user references addresses in multiple cases
# Let's say he has a home address and also a delivery address
# since both ForeignKey indices point to this table, the ambiguity needs to be resolved
# This is what the "foreign_keys" parameter of relationship() does
class HouseAddress(Base):
    __tablename__ = 'house_adresses'
    id = Column(Integer, primary_key=True)
    state = Column(String, nullable=False)
    zip = Column(String, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)
    addresses = relationship("Address", order_by=Address.id, back_populates="user")
    phone_number = relationship("PhoneNumber", uselist=False, order_by=PhoneNumber.id, back_populates="user")
    # this is for example [3]
    shipping_address = relationship("Address", secondary=association_table, backref="users")
    # this is for example [4]
    delivery_address_id = Column(Integer, ForeignKey('house_adresses.id'))
    delivery_address = relationship("HouseAddress", foreign_keys="[User.delivery_address_id]")
    home_address_id = Column(Integer, ForeignKey('house_adresses.id'))
    home_address = relationship("HouseAddress", foreign_keys="User.home_address_id")


    def __repr__(self):
        return "<User(name='%s', fullname='%s', password='%s')>" % (
            self.name, self.fullname, self.password)

Base.metadata.create_all(engine)

ed_user = User(name='ed', fullname='Ed Jones', password='edspassword')
Session = sessionmaker(bind=engine)
session = Session()

session.add(ed_user)
session.add_all([
     PhoneNumber(phone_number=42),
     User(name='wendy', fullname='Wendy Williams', password='foobar'),
     User(name='mary', fullname='Mary Contrary', password='xxg527'),
     User(name='fred', fullname='Fred Flinstone', password='blah'),
     HouseAddress(state='Bavaria', zip='8051'),
     HouseAddress(state='Bavaria', zip='8052')
     ])
session.commit()

mary = session.query(User).filter_by(name='mary').one()
fred = session.query(User).filter_by(name='fred').one()

ed_user.addresses = [Address(email_address='ed@home.de'),
                     Address(email_address='ed@work.de'),
                     Address(email_address='ed@vacation.de')]

h0 = session.query(HouseAddress).all()[0]
h1 = session.query(HouseAddress).all()[1]
ed_user.home_address = h0
ed_user.delivery_address = h1

# This is prevented by the uselist=False argument in User
# ed_user.phone_number = [PhoneNumber(phone_number=123456789), PhoneNumber(phone_number=987654321)]

# This works because it's a one-to one relation ship
ed_user.phone_number = PhoneNumber(phone_number=123456789)

phone_42 = session.query(PhoneNumber).filter_by(phone_number=42).one()

mary.phone_number = phone_42
fred.phone_number = phone_42


common_address = session.query(Address).first()

# This is managed via the relational table in example [3]
ed_user.shipping_address.append(common_address)
mary.shipping_address.append(common_address)

session.commit()

print()
print('================== Test Area ==================')



print('===============================================')
print()
print('Addressses:')
for row in session.query(Address).all():
    print(row.user)

print()
print('Numbers:')
for row in session.query(PhoneNumber).all():
    print(row.user)

print('ZIP:')
print(ed_user.home_address.zip)
print(ed_user.delivery_address.zip)
