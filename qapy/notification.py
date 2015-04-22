"""Notification"""

from qapy import get_url, raise_on_error

class QNotification(object):
    """A Qarnot Notification
    """
    def __init__(self, jsonnotification, connection):
        """Initialize a notification from a dictionnary

        :param dict jsonnotification: Dictionnary representing the notification,
                must contain following keys:

                  * id: string, the notification's GUID
                  * mask: TaskStateChanged
                  * filter.destination: string, destination (email)
                  * filter.filterKey
                  * filter.filterValue

                optionnal
                  * filter.subject Mail subject for the notification
                  * filter.to To state regex (default to .*)
                  * filter.from From state regex (default to .*)
                  * filter.state From or To state regex (default to .*)


        """
        self._connection = connection

        self._id = jsonnotification['id']
        self._mask = jsonnotification['mask']
        self._destination = jsonnotification['filter']['destination']
        self._subject = jsonnotification['filter']['subject']

        self._filterkey = jsonnotification['filter']['filterKey']
        self._filtervalue = jsonnotification['filter']['filterValue']

        self._from = jsonnotification['filter']['from']
        self._state = jsonnotification['filter']['state']
        self._to = jsonnotification['filter']['to']

    @classmethod
    def _create(cls, connection, destination, filterkey, filtervalue, subject=None, to=None, _from=None, state=None):
        data = {
            "mask" : "TaskStateChanged",
            "filter" : {
                "destination" : destination,
                "filterKey" : filterkey,
                "filterValue" : filtervalue
                }
            }
        if subject is not None:
            data["filter"]["subject"] = subject
        if to is not None:
            data["filter"]["to"] = subject
        if _from is not None:
            data["filter"]["from"] = _from
        if state is not None:
            data["filter"]["state"] = state
        url = get_url('notification')
        response = connection._post(url, json=data)
        raise_on_error(response)
        rid = response.json()['guid']
        response = connection._get(get_url('notification update', uuid=rid))
        raise_on_error(response)
        return QNotification(response.json(), connection)

    def delete(self):
        """Delete the notification represented by this :class:`QNotification`.

        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """

        response = self._connection._delete(
            get_url('notification update', uuid=self._id))
        raise_on_error(response)

    @property
    def id(self):
        """Id Getter
        """
        return self._id

    @property
    def destination(self):
        """Destination getter
        """
        return self._destination

    @destination.setter
    def destination(self, value):
        """Destination setter
        """
        self._destination = value

    @property
    def subject(self):
        """Subject getter
        """
        return self._subject

    @subject.setter
    def subject(self, value):
        """Subject setter
        """
        self._subject = value

    @property
    def filterkey(self):
        """Filterkey getter
        """
        return self._filterkey

    @filterkey.setter
    def filterkey(self, value):
        """Filterkey setter
        """
        self._filterkey = value

    @property
    def filtervalue(self):
        """Filtervalue getter
        """
        return self._filtervalue

    @filtervalue.setter
    def filtervalue(self, value):
        """Filtervalue setter
        """
        self._filtervalue = value

    @property
    def toregex(self):
        """To getter
        """
        return self._to

    @toregex.setter
    def toregex(self, value):
        """To setter
        """
        self._to = value

    @property
    def fromregex(self):
        """To getter
        """
        return self._from

    @fromregex.setter
    def fromregex(self, value):
        """To setter
        """
        self._from = value

    @property
    def stateregex(self):
        """To getter
        """
        return self._state

    @stateregex.setter
    def state_regex(self, value):
        """To setter
        """
        self._state = value
