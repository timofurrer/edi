# -*- coding: utf-8 -*-
# Copyright (C) 2017 Matthias Luescher
#
# Authors:
#  Matthias Luescher
#
# This file is part of edi.
#
# edi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# edi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with edi.  If not, see <http://www.gnu.org/licenses/>.


from tests.libtesting.optins import requires_lxc, requires_ansible, requires_debootstrap, requires_sudo
from tests.libtesting.contextmanagers.workspace import workspace
import os
from tests.libtesting.helpers import get_random_string, get_project_root
from edi.lib.shellhelpers import run
from edi.lib.lxchelpers import (get_server_image_compression_algorithm,
                                get_file_extension_from_image_compression_algorithm)
from edi.commands.lxccommands.export import Export
from edi.commands.clean import Clean
import edi
import subprocess


@requires_lxc
@requires_ansible
@requires_debootstrap
@requires_sudo
def test_export_jessie_container(capsys):
    print(os.getcwd())
    with workspace():
        edi_exec = os.path.join(get_project_root(), 'bin', 'edi')
        project_name = 'pytest-{}'.format(get_random_string(6))
        config_command = [edi_exec, 'config', 'init', project_name, 'debian-jessie-amd64']
        run(config_command)  # run as non root

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['lxc', 'export', '{}-develop.yml'.format(project_name)])

        Export().run_cli(cli_args)
        out, err = capsys.readouterr()
        print(out)
        assert not err

        lxc_compression_algo = get_server_image_compression_algorithm()
        lxc_export_extension = get_file_extension_from_image_compression_algorithm(lxc_compression_algo)

        images = [
            '{}-develop_edicommand_image_bootstrap.tar.gz'.format(project_name),
            '{}-develop_edicommand_image_lxc.tar.gz'.format(project_name),
            '{}-develop_edicommand_lxc_export{}'.format(project_name, lxc_export_extension)
        ]
        for image in images:
            assert os.path.isfile(image)

        image_store_items = [
            "{}-develop_edicommand_lxc_import".format(project_name),
            "{}-develop_edicommand_lxc_publish".format(project_name)
        ]
        lxc_image_list_cmd = ['lxc', 'image', 'list']
        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        for image_store_item in image_store_items:
            assert image_store_item in result.stdout

        parser = edi._setup_command_line_interface()
        cli_args = parser.parse_args(['-v', 'clean', '{}-develop.yml'.format(project_name)])
        Clean().run_cli(cli_args)

        for image in images:
            assert not os.path.isfile(image)

        result = run(lxc_image_list_cmd, stdout=subprocess.PIPE)
        for image_store_item in image_store_items:
            assert image_store_item not in result.stdout
