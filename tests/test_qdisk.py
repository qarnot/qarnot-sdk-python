import pytest
import os
import hashlib

from qapy.disk import QDisk, QUploadMode, MaxDiskException, \
    MissingDiskException
from tests.conftest import create_disks, call_with_each, MAX_NB_DISKS,\
    TMP_DIR



class TestSuite:
    def test_max_disk_exception(self, connection):
        with pytest.raises(MaxDiskException):
            create_disks(connection, 100 * MAX_NB_DISKS)

    @call_with_each(4*1024, 4*1024**2, 512*1024**2)
    def test_up_and_down(self, connection, param=None):
        assert param is not None
        file_size = param
        src_file_path = os.path.join(TMP_DIR, 'file_to_upload')
        dst_file_path = os.path.join(TMP_DIR, 'file_to_download')
        disk = QDisk._create(connection, 'test_disk')
        hasher = hashlib.md5()
        with open(src_file_path, 'wb') as f:
            for i in range (int(file_size / 1024)):
                buf = os.urandom(1024)
                hasher.update(buf)
                f.write(buf)
        hash_before = hasher.hexdigest()
        disk.add_file(src_file_path, remote='filename',
                      mode=QUploadMode.blocking)
        os.remove(src_file_path)
        disk.get_file('filename', dst_file_path)
        hasher = hashlib.md5()
        with open(dst_file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        hash_after = hasher.hexdigest()
        os.remove(dst_file_path)
        assert hash_before == hash_after


    def test_retrieve_and_delete(self, connection):
        disk_1 = create_disks(connection, 1)[0][0]
        disk_2 = QDisk._retrieve(connection, disk_1.uuid)
        assert disk_1.uuid == disk_2.uuid
        assert disk_1.description == disk_2.description
        disk_2.delete()
        with pytest.raises(MissingDiskException):
            QDisk._retrieve(connection, disk_1.uuid)


    def test_creation(self, connection):
        disk = QDisk._create(connection, 'disk_description')
        assert disk.description == 'disk_description'
