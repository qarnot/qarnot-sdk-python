Samples
=======

Code sample

Blender render
--------------
.. code-block:: python
   :linenos:

   import qapy
   import sys
   import os

   print("Loading config...")
   api = qapy.QApy('qarnot.conf')

   print("Creating task...")
   with api.create_task("blender render", "blender", 1) as task:
   	for disk in api.disks():
		print("Reusing disk " + disk.description)
   	   	task.resources = disk
   	  	break

   	print("Sync resources from 'input' directory")
   	task.resources.sync_directory("input", True)
   	task.resources.locked = True
   	task.resources.commit()

   	print("Setting constants...")
   	task.constants['BLEND_FILE'] = "model.blend"
   	task.constants['BLEND_FORMAT'] = "PNG"
   	task.constants['BLEND_ENGINE'] = "CYCLES"
   	task.constants['BLEND_CYCLES_SAMPLES'] = 1000

   	print("Submitting task...")
   	task.submit()

   	print("Waiting for task completion...")
   	task.wait()

   	print("Retrieving results in 'output' directory")
   	if not os.path.exists("output"):
   		os.makedirs("output")
   	task.download_results("output")
