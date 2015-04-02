"""Notification"""

from qapy import get_url, raise_on_error, QApyException

class QNotification(object):
    """A Qarnot Notification
    """
    def __init__(self, jsonnotification, connection):
        """Initialize a notification from a dictionnary

        :param dict jsonnotification: Dictionnary representing the notification,
                must contain following keys:

                  * id: string, the notification's GUID
                  * type: string, notification type
                  * destination: string, destination (email)
                  * filterKey: string, key to watch on tasks
                  * filterValue: string, regex to match for the filter key
                  * mask: list of strings, masks to watch for
                  * event: string, kind of event to act on

                Optional keys (for Filter events):

                 * filterFromRegex: string, regex match from value on state change, default to ".*"
                 * filterToRegex, string, regex match to value on state change, default to ".*"
        """
        self._connection = connection

        self._id = jsonnotification['id']
        self._type = jsonnotification['type']
        self._destination = jsonnotification['destination']
        self._filterkey = jsonnotification['filterKey']
        self._filtervalue = jsonnotification['filterValue']
        self._mask = jsonnotification['mask']
        self._event = jsonnotification['event']

        self._filterfromregex = jsonnotification['filterFromRegex'] if 'filterFromRegex' in jsonnotification else None
        self._filtertoregex = jsonnotification['filterToRegex'] if 'filterToRegex' in jsonnotification else None

    @classmethod
    def _create(cls, connection, destination, ntype, filterkey, filtervalue, masklist, event, filtertoregex=None, filterfromregex=None):
        """Create a new QNotification"""
        if ntype not in ["EMAIL"]:
            raise QApyException("Invalid notification type")

        for x in masklist:
            if x not in ["None", "Submitted", "PartiallyDispatched", \
                         "FullyDispatched", "PartiallyExecuting", "FullyExecuting", \
                         "Cancelled", "Success", "Failure"]:
                raise QApyException("Invalid mak list type")

        if event not in ["Enter", "Leave", "Both", "Filter"]:
            raise QApyException("Invalid event type")
        data = {
            "destination" : destination,
            "mask" : ', '.join(masklist),
            "type" : ntype,
            "filterKey" : filterkey,
            "filterValue" : filtervalue,
            "event" : event
            }

        if filtertoregex is not None:
            data['filterToRegex'] = filtertoregex
        if filterfromregex is not None:
            data['filterFromRegex'] = filterfromregex

        url = get_url('notification')
        response = connection._post(url, json=data)
        raise_on_error(response)
        notification_id = response.json()['guid']

    def delete(self):
        """Delete the notification represented by this :class:`QNotification`.

        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """

        response = self._connection._delete(
            get_url('notification update', uuid=self._id))
        raise_on_error(response)

    def __str__(self):
        return '{0} - {1} - {2} - {3} - {4}={5} - {6} - Event:{7} {8}'.format(self._id, self._type, self._destination, self._mask,
                                                                              self._filterkey, self._filtervalue, self._event,
                                                                              "To: " + self._filtertoregex if self._filtertoregex is not None else "",
                                                                              "From: " + self._filterfromregex if self._filterfromregex is not None else "")
