''' send out activitypub messages '''
from base64 import b64encode
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from datetime import datetime
import json
import requests

from fedireads import incoming
from fedireads.settings import DOMAIN


def get_recipients(user, post_privacy, direct_recipients=None):
    ''' deduplicated list of recipient inboxes '''
    recipients = direct_recipients or []
    if post_privacy == 'direct':
        # all we care about is direct_recipients, not followers
        return recipients

    # load all the followers of the user who is sending the message
    followers = user.followers.all()
    if post_privacy == 'public':
        # post to public shared inboxes
        shared_inboxes = set(u.shared_inbox for u in followers)
        recipients += list(shared_inboxes)
        # TODO: not every user has a shared inbox
        # TODO: direct to anyone who's mentioned
    if post_privacy == 'followers':
        # don't send it to the shared inboxes
        inboxes = set(u.inbox for u in followers)
        recipients += list(inboxes)
    return recipients


def broadcast(sender, activity, recipients):
    ''' send out an event '''
    errors = []
    for recipient in recipients:
        try:
            sign_and_send(sender, activity, recipient)
        except requests.exceptions.HTTPError as e:
            # TODO: maybe keep track of users who cause errors
            errors.append({
                'error': e,
                'recipient': recipient,
                'activity': activity,
            })
    return errors


def sign_and_send(sender, activity, destination):
    ''' crpyto whatever and http junk '''
    # TODO: handle http[s] with regex
    inbox_fragment = sender.inbox.replace('https://%s' % DOMAIN, '')
    now = datetime.utcnow().isoformat()
    signature_headers = [
        '(request-target): post %s' % inbox_fragment,
        'host: https://%s' % DOMAIN,
        'date: %s' %  now
    ]
    message_to_sign = '\n'.join(signature_headers)

    # TODO: raise an error if the user doesn't have a private key
    signer = pkcs1_15.new(RSA.import_key(sender.private_key))
    signed_message = signer.sign(SHA256.new(message_to_sign.encode('utf8')))

    signature = {
        'keyId': '%s#main-key' % sender.actor,
        'algorithm': 'rsa-sha256',
        'headers': '(request-target) host date',
        'signature': b64encode(signed_message).decode('utf8'),
    }
    signature = ','.join('%s="%s"' % (k, v) for (k, v) in signature.items())

    response = requests.post(
        destination,
        data=json.dumps(activity),
        headers={
            'Date': now,
            'Signature': signature,
            'Host': 'https://%s' % DOMAIN,
            'Content-Type': 'application/activity+json; charset=utf-8',
        },
    )
    if not response.ok:
        response.raise_for_status()
    incoming.handle_response(response)

