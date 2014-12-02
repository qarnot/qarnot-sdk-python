#Task module

##Description:
module to handle a Task,
this module describes the QTask object,
as well as exceptions to handle it.

##Content

* Class [QTask][Task]
* Exception [MissingTaskException][MissingTask]
* Exception [MaxTaskException](task.md#MaxTaskException)

---

## QTask

### Description
class to represent a qarnot job.

this represents a job to be executed on qrads.
It allows you to submit or handle such jobs

#### methods

* [submit]()
* [update]()
* [wait]()
* [abort]()
* [delete]()

#### Class Mathods

* [retrieve](task.md#retrieve)

#### properties

* [resources]()
* [results]()

### init
create a new Qtask (this does *not* submit the task.
For submitting, see [submit]())

####Parameters :

* **connection**: *[Qconnection][QConnection]*
the qnode on which to send the task
* **name**: *string*, given name of the task
* **profile**: *string*, which profile to use with this task
* **frameNbr**: *int*, number of frame on which to run task

###retrieve
retreive a submited task given it's uuid.
this method allows to retreive a task started
via the rest api or this one, using only it's id

####Parameters

* connection: *[Qconnection][QConnection]*,
the qnode to retrieve the task from
* uuid: *string*, the uuid of the task to retrieve

####Return value

*[QTask][Task]*: the retrieved task

####Exceptions
the following exceptions may arise:

* *HTTPError*: unhandled response for the underlying http request
* *[UnauthorizedException][Unauthorised]*: invalid credentials
* *[MissingTaskException][MissingTask]*: no task with given uuid
exists on given qnode

###submit
submit the task to it's qnode if not already done.
In the event this task as already been submitted,
submit does nothing (but still return's the task's status)

####Return value

*string*, the current state of the task

####Exceptions

* *HTTPError*: unhandled response for the underlying http request
* *[UnauthorizedException][Unauthorised]*: invalid credentials
* *[MissingDiskException][missingDisk]*: ressource disk of this task
is not a valid one.




[Qconnection]: connection.md
[MissingTask]: task.md#MissingTaskException
[Task]: task.md#QTask
[Unauthorised]:notImpl
[MissingDisk]:notimpl
