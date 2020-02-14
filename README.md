# fedireads

Social reading and reviewing, decentralized with ActivityPub

## Setting up the developer environment
To get started:

``` bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.default .env    # copy default configuration file
```

You can choose from postgres or sqlite as a database engine.
Postgres is recommended, but if you want to see fedireads up and running before setting up postgres, you can use sqlite.
You can change the database backend in `.env`.

If you're using postgres, you will need it installed and running on your computer. Then...
- Create the fedireads database:
``` bash
createdb fedireads
```

- Create the psql user in `psql fedireads`:
``` psql
CREATE ROLE fedireads WITH LOGIN PASSWORD 'fedireads';
GRANT ALL PRIVILEGES ON DATABASE fedireads TO fedireads;
```

Finally, initialize the database (this will also delete and re-create the migrations, which is not
a good idea for the long term but it's what I'm doing right now).
``` bash
./rebuilddb.sh
```
This creates two users, `mouse` with password `password123` and `rat` with password `ratword`.

And go to the app at `localhost:8000`

For most testing, you'll want to use ngrok. Remember to set the DOMAIN in settings.py to your ngrok domain.


## Structure

All the url routing is in `fedireads/urls.py`. This includes the application views (your home page, user page, book page, etc),
application endpoints (things that happen when you click buttons), and federation api endpoints (inboxes, outboxes, webfinger, etc).

The application views and actions are in `fedireads/views.py`. The internal actions call api handlers which deal with federating content.
Outgoing messages (any action done by a user that is federated out), as well as outboxes, live in `fedireads/outgoing.py`, and all handlers for incoming
messages, as well as inboxes and webfinger, live in `fedireads/incoming.py`. Connection to openlibrary.org to get book data is handled in `fedireads/openlibrary.py`.

The UI is all django templates because that is the default. You can replace it with a complex javascript framework over my ~dead body~ mild objections.


## Thoughts and considerations

### What even are books
The most complex part of this is knowing what books are which and who authors are. Right now I'm only using openlibrary.org as a
single, canonical source of truth for books, works, and authors. But it may be that user should be able to import books that aren't
in openlibrary, which, that's hard. So there's room to wonder if the openlibrary work key is indeed how a work should be identified.

The key needs to be universal (or at least universally comprehensible) across all fedireads servers, which is why I'm using an external
identifier controlled by someone else.

### Explain "review"
There's no actual reason to be beholden to simple 5 star reviews with a text body. Are there other ways of thinking about a review
that could be represented in a database?
