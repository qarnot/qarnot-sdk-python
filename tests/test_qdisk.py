import pytest
import os
import hashlib

from qapy.disk import QDisk, QUploadMode, MaxDiskException, \
    MissingDiskException
from conftest import create_disks, MAX_NB_DISKS, TMP_DIR
import conftest


class TestSuite:
    def test_max_disk_exception(self, connection):
        with pytest.raises(MaxDiskException):
            create_disks(connection, 100 * MAX_NB_DISKS)

    def _test_up_and_down(self, file_size, **kwargs):
        connection = conftest.connection(True)
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
                      mode=QUploadMode.blocking, **kwargs)
        os.remove(src_file_path)
        disk.get_file('filename', dst_file_path)
        hasher = hashlib.md5()
        with open(dst_file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        hash_after = hasher.hexdigest()
        qfileinfo = disk.list_files()[0]
        os.remove(dst_file_path)
        for setting, value in kwargs.items():
            if hasattr(qfileinfo, setting):
                assert getattr(qfileinfo, setting) == value
        assert hash_before == hash_after

    def test_up_and_down(self):
        for file_size in [4*1024, 4*1024**2, 512*1024**2]:
            self._test_up_and_down(file_size)

    def test_file_settings(self):
        file_size = 10*1024**2  # 10MiB
        self._test_up_and_down(file_size, executable=True)
        self._test_up_and_down(file_size, executable=False)

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
