#!/bin/bash

# copy .env.default to .env if user didn't do this manually
if [ ! -f .env ]; then
  cp .env.default .env
fi 

# read variables set in .env
export $(grep -v '^#' .env | xargs) > /dev/null

if [ -z $DATABASE_BACKEND ]; then
  echo "DATABASE_BACKEND is not set in .env! Defaulting to postgres."
  DATABASE_BACKEND=postgres
else
  echo "Using $DATABASE_BACKEND as database backend..."
fi

rm fedireads/migrations/0*
set -e

if [ "$DATABASE_BACKEND" = "sqlite" ]; then
  rm fedireads.db
elif [ "$DATABASE_BACKEND" = "postgres" ]; then
  dropdb fedireads
  createdb fedireads
else
  echo "$DATABASE_BACKEND is not supported! Please use postgres or sqlite."
fi

python manage.py makemigrations fedireads
python manage.py migrate

echo "from fedireads.models import User
User.objects.create_user('mouse', 'mouse.reeve@gmail.com', 'password123')" | python manage.py shell
echo "from fedireads.models import User
User.objects.create_user('rat', 'rat@rat.com', 'ratword')
User.objects.get(id=1).followers.add(User.objects.get(id=2))" | python manage.py shell
echo "from fedireads.openlibrary import get_or_create_book
get_or_create_book('OL1715344W')
get_or_create_book('OL102749W')" | python manage.py shell
python manage.py runserver
