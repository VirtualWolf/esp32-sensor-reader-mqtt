#!/bin/sh

ansible-playbook ansible/playbooks/copy_code_dev.yml -e @ansible/vars/default_dev_vars.yml
