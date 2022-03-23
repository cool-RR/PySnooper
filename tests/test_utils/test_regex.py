# Copyright 2022 Ram Rachum and collaborators.
# This program is distributed under the MIT license.

import pysnooper
from pysnooper.tracer import ansible_filename_pattern

def test_ansible_filename_pattern():
    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = 'ansible/modules/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name).group(1) == archive_file
    assert ansible_filename_pattern.match(file_name).group(2) == source_code_file

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_with.zip_name.zip'
    source_code_file = 'ansible/modules/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name).group(1) == archive_file
    assert ansible_filename_pattern.match(file_name).group(2) == source_code_file
    
    archive_file = '/my/new/path/payload.zip'
    source_code_file = 'ansible/modules/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name).group(1) == archive_file
    assert ansible_filename_pattern.match(file_name).group(2) == source_code_file

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = 'ansible/modules/in/new/path/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name).group(1) == archive_file
    assert ansible_filename_pattern.match(file_name).group(2) == source_code_file
    
    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = 'ansible/modules/my_module_is_called_.py.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name).group(1) == archive_file
    assert ansible_filename_pattern.match(file_name).group(2) == source_code_file

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = 'ANSIBLE/modules/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name) == None

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = 'ansible/modules/my_module.PY'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name) == None

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.Zip'
    source_code_file = 'ansible/modules/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name) == None

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = 'ansible/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name) == None

    archive_file = '/tmp/ansible_my_module_payload_xyz1234/ansible_my_module_payload.zip'
    source_code_file = ''
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name) == None

    archive_file = ''
    source_code_file = 'ansible/modules/my_module.py'
    file_name = archive_file + '/' + source_code_file
    assert ansible_filename_pattern.match(file_name) == None






